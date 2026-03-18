"""Clerk JWT verification and user authentication for FastAPI.

Verifies Clerk-issued JWTs using the JWKS endpoint derived from
the publishable key.  Uses the Clerk Backend API (secret key) to
fetch email / name since session JWTs do NOT include those fields.

Provides a FastAPI dependency (`get_current_user`) that protects
routes and upserts user records on first access.
"""

import base64
import ssl
import time
from typing import Optional

import certifi
import jwt
import requests
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient, PyJWKClientError

from app.core.config import CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY
from app.core.db import DatabaseManager, get_db


# ---------------------------------------------------------------------------
# Clerk JWKS client (caches keys automatically via PyJWT's built-in cache)
# ---------------------------------------------------------------------------

def _derive_frontend_api(publishable_key: str) -> str:
    """Derive Clerk Frontend API URL from the publishable key.

    The key format is ``pk_{env}_{base64(frontendApi$)}``.
    """
    parts = publishable_key.split("_", 2)
    if len(parts) < 3:
        raise ValueError("Invalid CLERK_PUBLISHABLE_KEY format")
    decoded = base64.b64decode(parts[2] + "==").decode("utf-8").rstrip("$")
    return decoded


def _build_jwks_url() -> str:
    if not CLERK_PUBLISHABLE_KEY:
        raise RuntimeError(
            "CLERK_PUBLISHABLE_KEY is not set. "
            "Add it to backend/.env (copy from Clerk dashboard → API Keys)."
        )
    frontend_api = _derive_frontend_api(CLERK_PUBLISHABLE_KEY)
    return f"https://{frontend_api}/.well-known/jwks.json"


# Lazy-initialised so the module can be imported even when the key is absent
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        # Create SSL context with certifi's CA bundle to fix macOS SSL verification
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        _jwks_client = PyJWKClient(
            _build_jwks_url(), 
            cache_keys=True, 
            lifespan=3600,
            ssl_context=ssl_context
        )
    return _jwks_client


# ---------------------------------------------------------------------------
# Clerk Backend API — fetch user profile (email, name)
# ---------------------------------------------------------------------------

# In-memory cache: clerk_user_id → {email, name, _ts}
_profile_cache: dict[str, dict] = {}
_PROFILE_CACHE_TTL = 300  # seconds — re-fetch from Clerk after 5 min


def _fetch_clerk_user_profile(user_id: str) -> dict:
    """Call Clerk Backend API to get user profile (email, name).

    Returns {"email": ..., "name": ...} or empty dict on failure.
    Results are cached in-memory for _PROFILE_CACHE_TTL seconds.
    """
    cached = _profile_cache.get(user_id)
    if cached and (time.time() - cached.get("_ts", 0)) < _PROFILE_CACHE_TTL:
        return {"email": cached.get("email", ""), "name": cached.get("name", "")}

    if not CLERK_SECRET_KEY:
        print("[AUTH] WARNING: CLERK_SECRET_KEY not set — cannot fetch user profiles")
        return {}

    try:
        resp = requests.get(
            f"https://api.clerk.com/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
            timeout=5,
        )
        if resp.status_code != 200:
            print(f"[AUTH] Clerk API returned {resp.status_code} for user {user_id}")
            return {}

        data = resp.json()

        # Extract primary email
        email = ""
        primary_email_id = data.get("primary_email_address_id")
        for ea in data.get("email_addresses", []):
            if ea.get("id") == primary_email_id:
                email = ea.get("email_address", "")
                break
        if not email and data.get("email_addresses"):
            email = data["email_addresses"][0].get("email_address", "")

        # Extract name
        first = data.get("first_name") or ""
        last = data.get("last_name") or ""
        name = f"{first} {last}".strip()

        profile = {"email": email, "name": name, "_ts": time.time()}
        _profile_cache[user_id] = profile
        return {"email": email, "name": name}

    except Exception as exc:
        print(f"[AUTH] Failed to fetch Clerk profile for {user_id}: {exc}")
        return {}


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk session JWT and return its payload.

    Raises ``ValueError`` on any verification failure.
    """
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,  # Clerk session tokens may not set aud
                "verify_exp": True,
                "verify_iss": False,  # We trust the JWKS source
            },
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}")
    except PyJWKClientError as exc:
        raise ValueError(f"JWKS key resolution failed: {exc}")


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """FastAPI dependency that enforces Clerk authentication.

    Returns ``{"userId": ..., "email": ..., "name": ...}``.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ", 1)[1]

    try:
        payload = verify_clerk_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    user_id: str = payload.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject claim")

    # ── Resolve email / name ──────────────────────────────────────────
    # 1. Check if we already have email stored in MongoDB
    existing_user = db.find_user_by_id(user_id)
    email = (existing_user or {}).get("email", "")
    name = (existing_user or {}).get("name", "")

    # 2. If no email yet, fetch from Clerk Backend API (session JWTs
    #    do NOT include profile fields by default).
    if not email:
        profile = _fetch_clerk_user_profile(user_id)
        email = profile.get("email", "")
        name = name or profile.get("name", "")

    # 3. Upsert — creates record on first visit, always updates lastSeenAt
    db.upsert_user(user_id, email=email or None, name=name or None)

    return {"userId": user_id, "email": email, "name": name}

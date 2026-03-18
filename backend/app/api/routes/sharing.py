"""
Collaborative Chat Sharing Routes

Endpoints for sharing sessions, generating invite links, managing
collaborators, and redeeming share tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.db import DatabaseManager, get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/sharing", tags=["sharing"])


# ── Request schemas ─────────────────────────────────────────────────────

class InviteByEmailRequest(BaseModel):
    sessionId: str
    email: str
    role: str = "editor"  # "editor" | "viewer"


class CreateShareLinkRequest(BaseModel):
    sessionId: str
    role: str = "editor"
    expiresHours: int = 72  # 0 = never


class RedeemShareLinkRequest(BaseModel):
    token: str


class RemoveCollaboratorRequest(BaseModel):
    sessionId: str
    userId: str


class LeaveSessionRequest(BaseModel):
    sessionId: str


class RevokeShareLinkRequest(BaseModel):
    token: str
    sessionId: str


class SearchUsersRequest(BaseModel):
    query: str


# ── Invite by email ─────────────────────────────────────────────────────

@router.post("/invite")
async def invite_collaborator(
    request: InviteByEmailRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Invite a user to collaborate on a session by their email address."""
    # Verify caller owns the session
    session = db.get_session(request.sessionId, user_id=user["userId"])
    if not session:
        raise HTTPException(404, "Session not found or you are not the owner")

    # Find target user by email (case-insensitive)
    target = db.find_user_by_email(request.email)
    if not target:
        raise HTTPException(
            404,
            "No user found with that email. They must sign in at least once."
        )

    target_id = target["clerkUserId"]
    if target_id == user["userId"]:
        raise HTTPException(400, "You cannot invite yourself")

    # Check if already a collaborator
    collabs = db.get_session_collaborators(request.sessionId)
    if any(c.get("userId") == target_id for c in collabs):
        raise HTTPException(400, "User is already a collaborator")

    # Enforce a max collaborator count (prevent abuse)
    if len(collabs) >= 20:
        raise HTTPException(400, "Maximum collaborator limit (20) reached")

    ok = db.add_collaborator(request.sessionId, user["userId"], target_id, request.role)
    if not ok:
        raise HTTPException(500, "Failed to add collaborator")

    return {
        "status": "success",
        "message": f"Invited {request.email} as {request.role}",
        "collaborator": {
            "userId": target_id,
            "email": target.get("email"),
            "name": target.get("name"),
            "role": request.role,
        },
    }


# ── Share link (anyone with link can join) ──────────────────────────────

@router.post("/create-link")
async def create_share_link(
    request: CreateShareLinkRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Generate a shareable invite link for a session."""
    token = db.create_share_link(
        request.sessionId, user["userId"], request.role, request.expiresHours
    )
    if not token:
        raise HTTPException(404, "Session not found or you are not the owner")

    return {
        "status": "success",
        "token": token,
        "role": request.role,
        "expiresHours": request.expiresHours,
    }


@router.post("/redeem-link")
async def redeem_share_link(
    request: RedeemShareLinkRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Redeem a share link to join a session as a collaborator."""
    result = db.redeem_share_link(request.token, user["userId"])
    if not result:
        raise HTTPException(404, "Invalid or expired share link")

    # Return sessionId at top level for easy frontend consumption
    return {
        "status": "success",
        "sessionId": result.get("sessionId"),
        "session": result,
        "message": "You have been added as a collaborator",
    }


@router.post("/revoke-link")
async def revoke_share_link(
    request: RevokeShareLinkRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Revoke (deactivate) a share link."""
    ok = db.revoke_share_link(request.token, user["userId"])
    if not ok:
        raise HTTPException(404, "Share link not found")
    return {"status": "success", "message": "Share link revoked"}


@router.get("/links/{session_id}")
async def get_share_links(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get all active share links for a session (owner only)."""
    links = db.get_share_links(session_id, user["userId"])
    return {"status": "success", "links": links}


# ── Collaborator management ─────────────────────────────────────────────

@router.get("/collaborators/{session_id}")
async def get_collaborators(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get collaborators for a session. Accessible by owner and collaborators."""
    session, role = db.get_session_with_access(session_id, user["userId"])
    if not session:
        raise HTTPException(404, "Session not found or no access")

    collabs = session.get("collaborators", [])

    # Enrich with user info
    enriched = []
    for c in collabs:
        u = db.find_user_by_id(c["userId"])
        enriched.append({
            "userId": c["userId"],
            "role": c.get("role", "viewer"),
            "addedAt": c.get("addedAt"),
            "email": u.get("email") if u else None,
            "name": u.get("name") if u else None,
        })

    # Also include owner
    owner = db.find_user_by_id(session["userId"])
    owner_info = {
        "userId": session["userId"],
        "role": "owner",
        "email": owner.get("email") if owner else None,
        "name": owner.get("name") if owner else None,
    }

    return {
        "status": "success",
        "owner": owner_info,
        "collaborators": enriched,
        "myRole": role,
    }


@router.post("/remove-collaborator")
async def remove_collaborator(
    request: RemoveCollaboratorRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Remove a collaborator from a session (owner only)."""
    ok = db.remove_collaborator(request.sessionId, user["userId"], request.userId)
    if not ok:
        raise HTTPException(404, "Session not found or collaborator not found")
    return {"status": "success", "message": "Collaborator removed"}


@router.post("/leave")
async def leave_session(
    request: LeaveSessionRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Leave a shared session (as a collaborator, not owner)."""
    # Make sure user is not the owner
    session = db.get_session(request.sessionId)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.get("userId") == user["userId"]:
        raise HTTPException(400, "Owner cannot leave their own session. Delete it instead.")

    ok = db.leave_session(request.sessionId, user["userId"])
    if not ok:
        raise HTTPException(404, "You are not a collaborator on this session")
    return {"status": "success", "message": "Left session"}


# ── Shared sessions listing ─────────────────────────────────────────────

@router.get("/shared-with-me")
async def list_shared_with_me(
    limit: int = 50,
    skip: int = 0,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List sessions that have been shared with the current user."""
    sessions = db.list_shared_sessions(user["userId"], skip, limit)
    return {"status": "success", "sessions": sessions}


# ── User search (for invite autocomplete) ──────────────────────────────

@router.get("/search-users")
async def search_users(
    q: str = Query("", min_length=0, max_length=100),
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Search users by email or name for the invite flow."""
    q = q.strip()
    if len(q) < 2:
        return {"status": "success", "users": []}
    results = db.search_users(q, exclude_user_id=user["userId"], limit=10)
    return {"status": "success", "users": results}

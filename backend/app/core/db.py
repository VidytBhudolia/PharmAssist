"""MongoDB connection utilities and FastAPI dependency helpers."""

from typing import Optional
import re
import uuid
import secrets
from datetime import datetime, timedelta
from fastapi import Request
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

from app.core.config import MONGO_URI, MONGO_DB_NAME, MONGO_CHAT_COLLECTION


class DatabaseManager:
    def __init__(self):
        if not MONGO_URI:
            raise ValueError("MONGO_URI not found in environment variables")

        try:
            # Configure MongoDB with longer timeouts and connection pool settings
            self.client = MongoClient(
                MONGO_URI,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                serverSelectionTimeoutMS=30000,
                socketTimeoutMS=45000,
                connectTimeoutMS=20000,
                retryWrites=True,
                retryReads=True,
            )
            self.db = self.client[MONGO_DB_NAME]
            self.sessions = self.db[MONGO_CHAT_COLLECTION]
            self.users = self.db["users"]
            self.share_links = self.db["share_links"]

            # Test connection
            self.client.admin.command("ping")
            print("[DB] Connected to MongoDB successfully")

            # Ensure indexes
            self._ensure_notifications_indexes()
            self._ensure_users_indexes()
            self._ensure_sharing_indexes()

        except Exception as e:
            print(f"[DB] MongoDB connection failed: {e}")
            raise

    def _ensure_notifications_indexes(self):
        """Create indexes on the notifications collection for fast lookup."""
        try:
            notif = self.db["notifications"]
            notif.create_index(
                [("sessionId", ASCENDING), ("promptId", ASCENDING), ("enabled", ASCENDING)],
                name="idx_session_prompt_enabled",
            )
            notif.create_index(
                [("notificationId", ASCENDING)],
                name="idx_notification_id",
                unique=True,
            )
            print("[DB] Notifications indexes ensured")
        except Exception as e:
            print(f"[DB] Warning: could not create notifications indexes: {e}")

    def _ensure_users_indexes(self):
        """Create indexes on the users collection."""
        try:
            self.users.create_index(
                [("clerkUserId", ASCENDING)],
                name="idx_clerk_user_id",
                unique=True,
            )
            self.users.create_index(
                [("email", ASCENDING)],
                name="idx_user_email",
                sparse=True,
            )
            print("[DB] Users indexes ensured")
        except Exception as e:
            print(f"[DB] Warning: could not create users indexes: {e}")

    def _ensure_sharing_indexes(self):
        """Create indexes for collaborative sharing."""
        try:
            # Index for looking up sessions by collaborator
            self.sessions.create_index(
                [("collaborators.userId", ASCENDING)],
                name="idx_collaborators_userid",
                sparse=True,
            )
            # Index for share link tokens
            self.share_links.create_index(
                [("token", ASCENDING)],
                name="idx_share_token",
                unique=True,
            )
            self.share_links.create_index(
                [("sessionId", ASCENDING)],
                name="idx_share_session",
            )
            print("[DB] Sharing indexes ensured")
        except Exception as e:
            print(f"[DB] Warning: could not create sharing indexes: {e}")

    # ── User operations ─────────────────────────────────────────────────

    def upsert_user(self, clerk_user_id: str, email: str = None, name: str = None) -> dict:
        """Create or touch a user record on every authenticated request."""
        now = datetime.utcnow().isoformat()
        update_set = {"lastSeenAt": now}
        if email:
            update_set["email"] = email
        if name:
            update_set["name"] = name

        result = self.users.find_one_and_update(
            {"clerkUserId": clerk_user_id},
            {
                "$setOnInsert": {"clerkUserId": clerk_user_id, "createdAt": now},
                "$set": update_set,
            },
            upsert=True,
            return_document=True,
        )
        return self._serialize(result)

    def find_user_by_email(self, email: str) -> dict | None:
        """Find a user by email address (case-insensitive)."""
        doc = self.users.find_one(
            {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}
        )
        return self._serialize(doc) if doc else None

    def find_user_by_id(self, clerk_user_id: str) -> dict | None:
        """Find a user by their Clerk ID."""
        doc = self.users.find_one({"clerkUserId": clerk_user_id})
        return self._serialize(doc) if doc else None

    def search_users(self, query: str, exclude_user_id: str = None, limit: int = 10) -> list:
        """Search users by email or name prefix for the invite flow."""
        # Escape regex metacharacters to prevent injection
        safe_q = re.escape(query)
        regex = {"$regex": safe_q, "$options": "i"}
        filter_q = {"$or": [{"email": regex}, {"name": regex}]}
        if exclude_user_id:
            filter_q["clerkUserId"] = {"$ne": exclude_user_id}
        docs = list(
            self.users.find(filter_q, {"clerkUserId": 1, "email": 1, "name": 1, "_id": 0})
            .limit(min(limit, 20))  # hard cap
        )
        return self._serialize(docs)

    # ── Session operations (user-scoped) ────────────────────────────────

    def get_session(self, session_id: str, user_id: str | None = None):
        query = {"sessionId": session_id}
        if user_id is not None:
            query["userId"] = user_id
        doc = self.sessions.find_one(query)
        return self._serialize(doc)

    def get_session_with_access(self, session_id: str, user_id: str):
        """Get a session if the user is the owner OR a collaborator.

        Returns (session_dict, role) where role is 'owner', 'editor', or 'viewer'.
        Returns (None, None) if no access.
        """
        doc = self.sessions.find_one({"sessionId": session_id})
        if not doc:
            return None, None
        doc = self._serialize(doc)

        # Owner check
        if doc.get("userId") == user_id:
            return doc, "owner"

        # Collaborator check
        for collab in doc.get("collaborators", []):
            if collab.get("userId") == user_id:
                return doc, collab.get("role", "viewer")

        return None, None

    def list_sessions(self, skip: int = 0, limit: int = 50, user_id: str | None = None):
        """Return lightweight session summaries scoped to a user."""
        query = {}
        if user_id is not None:
            query["userId"] = user_id
        projection = {
            "agentsData": 0,
            "workflowState": 0,
            "chatHistory": 0,
        }
        docs = list(
            self.sessions.find(query, projection)
            .sort("_id", -1)
            .skip(skip)
            .limit(limit)
        )
        return self._serialize(docs)

    def list_shared_sessions(self, user_id: str, skip: int = 0, limit: int = 50):
        """Return sessions shared WITH this user (where they are a collaborator)."""
        query = {"collaborators.userId": user_id}
        projection = {
            "agentsData": 0,
            "workflowState": 0,
            "chatHistory": 0,
        }
        docs = list(
            self.sessions.find(query, projection)
            .sort("_id", -1)
            .skip(skip)
            .limit(limit)
        )
        sessions = self._serialize(docs)
        for session in sessions:
            role = "viewer"
            collabs = session.pop("collaborators", [])
            for collab in collabs:
                if collab.get("userId") == user_id:
                    role = collab.get("role", "viewer")
                    break
            session["role"] = role
        return sessions

    def _serialize(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, list):
            return [self._serialize(i) for i in obj]
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        return obj

    def create_session(self, title: str = "New Analysis", user_id: str | None = None) -> str:
        """Create a session with a unique UUID and return sessionId."""
        while True:
            session_id = str(uuid.uuid4())
            exists = self.sessions.find_one({"sessionId": session_id})
            if not exists:
                break

        now = datetime.utcnow().isoformat()
        doc = {
            "sessionId": session_id,
            "title": title,
            "createdAt": now,
            "updatedAt": now,
            "chatHistory": [],
            "agentsData": [],
            "collaborators": [],
            "workflowState": {
                "activeAgent": None,
                "showAgentDataByAgent": {},
                "reportReady": False,
                "workflowComplete": False,
                "queryRejected": False,
                "systemResponse": None,
                "panelCollapsed": False,
                "showAgentFlow": False,
            },
        }
        if user_id is not None:
            doc["userId"] = user_id

        self.sessions.insert_one(doc)
        print(f"[DB] Created session {session_id}")
        return session_id

    def delete_session(self, session_id: str, user_id: str | None = None) -> bool:
        """Delete a session by sessionId, optionally scoped to a user."""
        query = {"sessionId": session_id}
        if user_id is not None:
            query["userId"] = user_id
        result = self.sessions.delete_one(query)
        if result.deleted_count > 0:
            # Also delete share links for this session
            self.share_links.delete_many({"sessionId": session_id})
            print(f"[DB] Deleted session {session_id}")
            return True
        print(f"[DB] Session {session_id} not found for deletion")
        return False

    def rename_session(self, session_id: str, new_title: str, user_id: str | None = None) -> bool:
        """Rename a session by updating its title, optionally scoped to a user."""
        query = {"sessionId": session_id}
        if user_id is not None:
            query["userId"] = user_id
        
        update = {
            "$set": {
                "title": new_title,
                "updatedAt": datetime.utcnow().isoformat()
            }
        }
        
        result = self.sessions.update_one(query, update)
        if result.matched_count > 0:
            print(f"[DB] Renamed session {session_id} to '{new_title}'")
            return True
        print(f"[DB] Session {session_id} not found for renaming")
        return False

    # ── Collaboration / sharing operations ──────────────────────────────

    def add_collaborator(self, session_id: str, owner_user_id: str,
                         collab_user_id: str, role: str = "editor") -> bool:
        """Add a collaborator to a session. Only the owner can do this."""
        result = self.sessions.update_one(
            {"sessionId": session_id, "userId": owner_user_id},
            {
                "$addToSet": {
                    "collaborators": {
                        "userId": collab_user_id,
                        "role": role,
                        "addedAt": datetime.utcnow().isoformat(),
                    }
                },
                "$set": {"updatedAt": datetime.utcnow().isoformat()},
            },
        )
        return result.modified_count > 0

    def remove_collaborator(self, session_id: str, owner_user_id: str,
                            collab_user_id: str) -> bool:
        """Remove a collaborator. Only the owner can do this."""
        result = self.sessions.update_one(
            {"sessionId": session_id, "userId": owner_user_id},
            {
                "$pull": {"collaborators": {"userId": collab_user_id}},
                "$set": {"updatedAt": datetime.utcnow().isoformat()},
            },
        )
        return result.modified_count > 0

    def get_session_collaborators(self, session_id: str) -> list:
        """Get collaborator list for a session."""
        doc = self.sessions.find_one(
            {"sessionId": session_id},
            {"collaborators": 1, "userId": 1, "_id": 0},
        )
        if not doc:
            return []
        return self._serialize(doc.get("collaborators", []))

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Allow a collaborator to leave a shared session."""
        result = self.sessions.update_one(
            {"sessionId": session_id},
            {"$pull": {"collaborators": {"userId": user_id}}},
        )
        return result.modified_count > 0

    # ── Share link operations ───────────────────────────────────────────

    def create_share_link(self, session_id: str, owner_user_id: str,
                          role: str = "editor", expires_hours: int = 72) -> str:
        """Create a shareable invite link token. Returns the token."""
        # Verify ownership
        session = self.sessions.find_one({"sessionId": session_id, "userId": owner_user_id})
        if not session:
            return None

        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=expires_hours)).isoformat() if expires_hours > 0 else None
        self.share_links.insert_one({
            "token": token,
            "sessionId": session_id,
            "createdBy": owner_user_id,
            "role": role,
            "createdAt": now.isoformat(),
            "expiresAt": expires_at,
            "usedBy": [],
            "active": True,
        })
        return token

    def redeem_share_link(self, token: str, user_id: str) -> dict | None:
        """Redeem a share link — adds user as collaborator. Returns session or None."""
        link = self.share_links.find_one({"token": token, "active": True})
        if not link:
            return None

        # Enforce expiry
        expires_at = link.get("expiresAt")
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > exp_dt:
                    # Auto-deactivate expired link
                    self.share_links.update_one(
                        {"token": token}, {"$set": {"active": False}}
                    )
                    return None
            except (ValueError, TypeError):
                pass  # malformed date — treat as non-expiring

        session_id = link["sessionId"]
        role = link.get("role", "editor")

        # Validate role value
        if role not in ("editor", "viewer"):
            role = "viewer"

        # Don't let owner join their own session
        session = self.sessions.find_one({"sessionId": session_id})
        if not session:
            return None
        if session.get("userId") == user_id:
            return self._serialize(session)

        # Check if already a collaborator
        existing = [c for c in session.get("collaborators", []) if c.get("userId") == user_id]
        if not existing:
            self.add_collaborator(session_id, session["userId"], user_id, role)

        # Record usage
        self.share_links.update_one(
            {"token": token},
            {"$addToSet": {"usedBy": user_id}},
        )

        updated = self.sessions.find_one({"sessionId": session_id})
        return self._serialize(updated)

    def revoke_share_link(self, token: str, owner_user_id: str) -> bool:
        """Deactivate a share link."""
        result = self.share_links.update_one(
            {"token": token, "createdBy": owner_user_id},
            {"$set": {"active": False}},
        )
        return result.modified_count > 0

    def get_share_links(self, session_id: str, owner_user_id: str) -> list:
        """Get all active share links for a session."""
        docs = list(self.share_links.find(
            {"sessionId": session_id, "createdBy": owner_user_id, "active": True},
            {"_id": 0},
        ))
        return self._serialize(docs)


def init_db() -> DatabaseManager:
    """Create a database manager instance."""
    return DatabaseManager()


def get_db(request: Request) -> DatabaseManager:
    """FastAPI dependency to fetch the shared DatabaseManager."""
    db: Optional[DatabaseManager] = getattr(request.app.state, "db", None)
    if db is None:
        raise RuntimeError("Database not initialized on application state")
    return db

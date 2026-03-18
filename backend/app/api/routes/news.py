"""
News Agent API routes.

Endpoints
---------
POST /news/enable          — Toggle monitoring for a promptId.
POST /news/recheck         — Trigger immediate recheck for a promptId.
GET  /news/monitored       — List all monitored prompts for a session.
GET  /news/details/{id}    — Get notification details by notificationId.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import os

from app.core.db import DatabaseManager, get_db
from app.core.auth import get_current_user
from app.agents.news_agent.news_agent import run_news_agent
from app.agents.news_agent.tools.relevance_matcher import (
    extract_keywords_from_intel,
    is_chat_relevant,
    get_matching_keywords,
)

router = APIRouter(prefix="/news", tags=["news"])


# ── Request Models ──────────────────────────────────────────────────────────

class EnableNotificationRequest(BaseModel):
    sessionId: str
    promptId: str
    tagName: str = ""
    enabled: bool = True


class RecheckRequest(BaseModel):
    sessionId: str
    promptId: str
    rerunAnalysis: bool = False


class BroadcastIntelRequest(BaseModel):
    text: str = Field(..., min_length=1, description="New intel text to compare against monitored chats")


class AcknowledgeRequest(BaseModel):
    sessionIds: Optional[List[str]] = None  # If None, acknowledges ALL


# ── POST /news/enable ──────────────────────────────────────────────────────

@router.post("/enable")
async def enable_notification(
    request: EnableNotificationRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Toggle monitoring for a specific promptId."""
    session = db.get_session(request.sessionId, user_id=user["userId"])
    if not session:
        raise HTTPException(404, "Session not found or access denied")

    # Check promptId exists in agentsData
    found = False
    for entry in session.get("agentsData", []):
        if entry.get("promptId") == request.promptId:
            found = True
            break
    if not found:
        raise HTTPException(404, "promptId not found in session")

    now_iso = datetime.now(timezone.utc).isoformat()

    existing = db.db["notifications"].find_one({
        "sessionId": request.sessionId,
        "promptId": request.promptId,
    })

    if existing:
        db.db["notifications"].update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "enabled": request.enabled,
                "tagName": request.tagName or existing.get("tagName", ""),
                "updatedAt": now_iso,
            }},
        )
        return {
            "status": "success",
            "message": f"Monitoring {'enabled' if request.enabled else 'disabled'}",
            "notificationId": existing.get("notificationId", str(existing["_id"])),
            "enabled": request.enabled,
        }
    else:
        notification_id = str(uuid.uuid4())
        doc = {
            "notificationId": notification_id,
            "sessionId": request.sessionId,
            "promptId": request.promptId,
            "tagName": request.tagName,
            "enabled": request.enabled,
            "lastCheckedAt": None,
            "status": "secure",
            "severity": "low",
            "changedFields": [],
            "details": {},
            "requiresManualReview": False,
            "decision_reason": "",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
        db.db["notifications"].insert_one(doc)
        return {
            "status": "success",
            "message": f"Monitoring {'enabled' if request.enabled else 'disabled'}",
            "notificationId": notification_id,
            "enabled": request.enabled,
        }


# ── POST /news/recheck ────────────────────────────────────────────────────

@router.post("/recheck")
async def recheck_notification(
    request: RecheckRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Trigger immediate recheck for a monitored promptId."""
    session = db.get_session(request.sessionId, user_id=user["userId"])
    if not session:
        raise HTTPException(404, "Session not found or access denied")

    # Find original agent data for this promptId
    old_agent_data = None
    for entry in session.get("agentsData", []):
        if entry.get("promptId") == request.promptId:
            old_agent_data = entry.get("agents", {})
            break

    if old_agent_data is None:
        raise HTTPException(404, "promptId not found in session agentsData")

    # Check if notification exists
    notif = db.db["notifications"].find_one({
        "sessionId": request.sessionId,
        "promptId": request.promptId,
    })
    if not notif:
        raise HTTPException(404, "No monitoring record found for this promptId. Enable monitoring first.")

    # ── Optional: re-run the orchestrator to get fresh agent data ──────
    new_agent_data = None
    if request.rerunAnalysis:
        try:
            # Pull the original extracted_params and prompt for this promptId
            original_prompt = None
            extracted_params = {}
            for entry in session.get("agentsData", []):
                if entry.get("promptId") == request.promptId:
                    original_prompt = entry.get("prompt", "")
                    extracted_params = entry.get("extracted_params", {})
                    break

            if original_prompt:
                from app.services.llm_orchestrator import plan_and_run_session
                fresh_result = await plan_and_run_session(
                    request.sessionId,
                    original_prompt,
                    db,
                    recheck_from_notification=True,
                )
                # If fresh data came back, use it as the "new" side of the diff
                if fresh_result and fresh_result.get("agentsData"):
                    new_agent_data = fresh_result["agentsData"]
        except Exception as exc:
            # Don't fail the whole recheck just because orchestrator had issues
            import traceback; traceback.print_exc()
            new_agent_data = None

    # Look for newly uploaded documents associated with this session
    new_doc_text = None
    try:
        from app.agents.internal_knowledge_agent.internal_knowledge_agent import (
            get_document_for_session,
        )
        doc_info = get_document_for_session(request.sessionId)
        if doc_info and doc_info.get("parsed_text"):
            new_doc_text = doc_info["parsed_text"]
    except Exception:
        pass  # No new docs

    # Run News Agent comparator
    result = run_news_agent(
        session_id=request.sessionId,
        prompt_id=request.promptId,
        old_agent_data=old_agent_data,
        new_agent_data=new_agent_data,
        new_document_text=new_doc_text,
        db=db,
    )

    # If status changed, insert a news-notification message into chat history
    compare_result = result.get("data", {}).get("compareResult", {})
    notification = result.get("data", {}).get("notification", {})

    if compare_result.get("status") == "changed":
        severity = compare_result.get("severity", "medium").upper()
        changed_fields = ", ".join(compare_result.get("changedFields", []))
        reason = compare_result.get("decision_reason", "changes detected")

        # Find original prompt text
        original_prompt = ""
        for entry in session.get("agentsData", []):
            if entry.get("promptId") == request.promptId:
                original_prompt = entry.get("prompt", "your research")
                break
        prompt_label = original_prompt[:50] if original_prompt else "your research"

        notif_message = (
            f"News agent detected {severity} risk change for '{prompt_label}' — "
            f"{reason[:120]}. Click to view details and re-run analysis."
        )
        changed_fields_list = compare_result.get("changedFields", [])

        db.sessions.update_one(
            {"sessionId": request.sessionId},
            {"$push": {"chatHistory": {
                "role": "assistant",
                "content": notif_message,
                "type": "news-notification",
                "promptId": request.promptId,
                "notificationId": notification.get("notificationId", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "severity": severity,
                    "promptLabel": prompt_label,
                    "reason": reason[:200],
                    "changedFields": changed_fields_list,
                    "matchedKeywords": [],
                },
            }}},
        )

    return {
        "status": "success",
        "compareResult": compare_result,
        "notification": notification,
    }


# ── GET /news/monitored ───────────────────────────────────────────────────

@router.get("/monitored-all")
async def list_all_monitored(
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List ALL enabled monitored notifications across every session owned by the authenticated user."""
    notifications = list(db.db["notifications"].find({"enabled": True}))

    # Batch-fetch unique sessions with user filtering
    session_ids = list({n.get("sessionId") for n in notifications if n.get("sessionId")})
    sessions_cache = {}
    for sid in session_ids:
        # Only fetch sessions owned by the current user
        sess = db.get_session(sid, user_id=user["userId"])
        if sess:
            sessions_cache[sid] = sess

    result = []
    for n in notifications:
        sid = n.get("sessionId", "")
        # Skip notifications for sessions not owned by this user
        session = sessions_cache.get(sid)
        if not session:
            continue
        
        n.pop("_id", None)

        # Resolve prompt text from agentsData
        pid = n.get("promptId", "")
        prompt_text = ""
        for entry in session.get("agentsData", []):
            if entry.get("promptId") == pid:
                prompt_text = entry.get("prompt", "")
                break

        n["chatTitle"] = session.get("title", n.get("tagName", "Untitled"))
        n["promptText"] = prompt_text[:80] if prompt_text else n.get("tagName", "")
        result.append(n)

    return {
        "status": "success",
        "notifications": result,
        "count": len(result),
    }


@router.get("/monitored")
async def list_monitored(
    sessionId: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all monitored prompts for a session."""
    query = {"sessionId": sessionId}
    notifications = list(db.db["notifications"].find(query))

    # Serialize and enrich with chat title
    session = db.get_session(sessionId, user_id=user["userId"])
    if not session:
        raise HTTPException(404, "Session not found or access denied")
    
    prompts_map = {}
    for entry in session.get("agentsData", []):
            pid = entry.get("promptId")
            if pid:
                prompts_map[pid] = {
                    "prompt": entry.get("prompt", ""),
                    "timestamp": entry.get("timestamp", ""),
                    "extracted_params": entry.get("extracted_params", {}),
                }

    result = []
    for n in notifications:
        n.pop("_id", None)
        pid = n.get("promptId", "")
        prompt_info = prompts_map.get(pid, {})
        n["chatTitle"] = prompt_info.get("prompt", "")[:60] or n.get("tagName", "Untitled")
        n["extracted_params"] = prompt_info.get("extracted_params", {})
        result.append(n)

    return {
        "status": "success",
        "notifications": result,
        "count": len(result),
    }


# ── GET /news/details/{notificationId} ────────────────────────────────────

@router.get("/details/{notification_id}")
async def get_notification_details(
    notification_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get full details for a notification."""
    notif = db.db["notifications"].find_one({"notificationId": notification_id})
    if not notif:
        raise HTTPException(404, "Notification not found")

    # Verify the session belongs to the user
    session_id = notif.get("sessionId")
    if session_id:
        session = db.get_session(session_id, user_id=user["userId"])
        if not session:
            raise HTTPException(404, "Notification not found or access denied")

    notif.pop("_id", None)
    return {
        "status": "success",
        "notification": notif,
    }


# ── POST /news/parse-document ─────────────────────────────────────────────

@router.post("/parse-document")
async def parse_document_temp(
    file: UploadFile = File(...),
):
    """
    Parse an uploaded document and return its text content.
    
    Temporary endpoint for News Monitor - parses without storing.
    Supports: PDF, PPTX, XLSX, DOCX, TXT, CSV
    """
    from app.agents.internal_knowledge_agent.internal_knowledge_agent import parse_uploaded_file
    
    # Validate file type
    allowed_extensions = ["pdf", "pptx", "xlsx", "xls", "docx", "txt", "csv"]
    filename = file.filename or "unknown"
    file_ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read and parse file
    try:
        content_bytes = await file.read()
        parsed_content, file_type = parse_uploaded_file(content_bytes, filename)
        
        if file_type == "error":
            raise HTTPException(status_code=400, detail=parsed_content)
        
        return {
            "status": "success",
            "parsed_content": parsed_content,
            "file_type": file_type,
            "filename": filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")


# ── POST /news/broadcast-intel ────────────────────────────────────────────

@router.post("/broadcast-intel")
async def broadcast_intel(
    request: BroadcastIntelRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Broadcast new intel text against ALL enabled monitored chats.
    
    Uses LLM to extract keywords from intel, then matches against chat content.
    Only RELEVANT chats are flagged and receive notifications.
    """
    notifications = list(db.db["notifications"].find({"enabled": True}))
    if not notifications:
        return {
            "status": "success",
            "totalChecked": 0,
            "affectedCount": 0,
            "results": [],
        }

    # Extract keywords from intel using LLM
    try:
        from openai import OpenAI
        llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        keywords = extract_keywords_from_intel(request.text, llm_client)
    except Exception as e:
        print(f"LLM keyword extraction failed: {e}")
        # Fallback to simple extraction
        keywords = extract_keywords_from_intel(request.text, llm_client=None)
    
    print(f"Extracted keywords from intel: {keywords}")

    # Cache sessions to avoid repeated fetches
    sessions_cache: dict = {}
    results = []

    for notif in notifications:
        sid = notif.get("sessionId")
        pid = notif.get("promptId")
        if not sid or not pid:
            continue

        session = sessions_cache.get(sid)
        if session is None:
            # Verify session belongs to user before processing
            session = db.get_session(sid, user_id=user["userId"])
            sessions_cache[sid] = session
        if not session:
            # Skip sessions not owned by this user
            continue

        # Find original agent data for this promptId
        old_agent_data = None
        original_prompt = ""
        for entry in session.get("agentsData", []):
            if entry.get("promptId") == pid:
                old_agent_data = entry.get("agents", {})
                original_prompt = entry.get("prompt", "")
                break
        if old_agent_data is None:
            continue
        
        # Check if chat is relevant based on keyword matching
        chat_title = session.get("title", "")
        agent_data_str = str(old_agent_data)[:1000]  # First 1000 chars for matching
        
        if not is_chat_relevant(keywords, chat_title, original_prompt, agent_data_str):
            # Chat not relevant - skip without flagging
            results.append({
                "sessionId": sid,
                "promptId": pid,
                "status": "skipped",
                "severity": "low",
                "chatTitle": chat_title,
                "reason": "Not relevant to intel keywords",
            })
            continue
        
        # Log matched keywords for debugging
        matched_kws = get_matching_keywords(keywords, chat_title, original_prompt, agent_data_str)
        print(f"Chat '{chat_title}' matched keywords: {matched_kws}")

        # Run news comparator with the new intel as document text
        try:
            result = run_news_agent(
                session_id=sid,
                prompt_id=pid,
                old_agent_data=old_agent_data,
                new_agent_data=None,
                new_document_text=request.text,
                db=db,
            )
        except Exception as exc:
            import traceback; traceback.print_exc()
            results.append({
                "sessionId": sid,
                "promptId": pid,
                "status": "error",
                "severity": "low",
                "chatTitle": session.get("title", ""),
            })
            continue

        compare_result = result.get("data", {}).get("compareResult", {})
        notification_doc = result.get("data", {}).get("notification", {})

        # If status changed, mark as affected and push notification to chat history
        if compare_result.get("status") == "changed":
            severity = compare_result.get("severity", "medium").upper()
            reason = compare_result.get("decision_reason", "changes detected")
            prompt_label = original_prompt[:50] if original_prompt else "your research"
            matched_kws = get_matching_keywords(keywords, chat_title, original_prompt, agent_data_str)

            notif_message = (
                f"⚠ News intel: {severity} risk for '{prompt_label}' — "
                f"{reason[:120]}. Matched keywords: {', '.join(matched_kws[:5])}. "
                f"Review and re-run analysis as needed."
            )
            changed_fields_list = compare_result.get("changedFields", [])

            db.sessions.update_one(
                {"sessionId": sid},
                {"$push": {"chatHistory": {
                    "role": "assistant",
                    "content": notif_message,
                    "type": "news-notification",
                    "promptId": pid,
                    "notificationId": notification_doc.get("notificationId", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "severity": severity,
                        "promptLabel": prompt_label,
                        "reason": reason[:200],
                        "changedFields": changed_fields_list,
                        "matchedKeywords": matched_kws[:8],
                    },
                }}},
            )
            
            # Mark notification as affected by intel
            db.db["notifications"].update_one(
                {"sessionId": sid, "promptId": pid},
                {"$set": {
                    "affectedByIntel": True,
                    "acknowledged": False,
                    "lastIntelUpdate": datetime.now(timezone.utc).isoformat(),
                }},
            )

        results.append({
            "sessionId": sid,
            "promptId": pid,
            "status": compare_result.get("status", "secure"),
            "severity": compare_result.get("severity", "low"),
            "chatTitle": session.get("title", ""),
        })

    affected = [r for r in results if r["status"] == "changed"]
    return {
        "status": "success",
        "totalChecked": len(results),
        "affectedCount": len(affected),
        "results": results,
    }


# ── POST /news/acknowledge-all ─────────────────────────────────────────────

@router.post("/acknowledge-all")
async def acknowledge_all_notifications(
    request: AcknowledgeRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Mark notifications as acknowledged (resets affectedByIntel flag).
    
    This is used when the user clicks the refresh button to indicate they've
    reviewed all current intel notifications. Notifications turn green (secure status).
    
    If sessionIds is provided, only acknowledges those sessions (that belong to the user).
    If sessionIds is None, acknowledges ALL enabled notifications for the user's sessions.
    """
    # Get all user's session IDs to ensure we only acknowledge their notifications
    user_sessions = db.list_sessions(user_id=user["userId"], limit=10000)
    user_session_ids = [s["sessionId"] for s in user_sessions]
    
    query = {"enabled": True, "sessionId": {"$in": user_session_ids}}
    
    if request.sessionIds:
        # Further filter to only the requested sessions (intersection with user's sessions)
        filtered_session_ids = [sid for sid in request.sessionIds if sid in user_session_ids]
        query["sessionId"] = {"$in": filtered_session_ids}
    
    result = db.db["notifications"].update_many(
        query,
        {"$set": {
            "acknowledged": True,
            "affectedByIntel": False,
            "acknowledgedAt": datetime.now(timezone.utc).isoformat(),
        }},
    )
    
    return {
        "status": "success",
        "acknowledgedCount": result.modified_count,
        "message": f"Acknowledged {result.modified_count} notifications",
    }

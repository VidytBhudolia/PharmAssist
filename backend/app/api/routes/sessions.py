from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.api.schemas import SessionCreateRequest, SessionRenameRequest
from app.core.db import DatabaseManager, get_db
from app.core.auth import get_current_user
from app.agents.internal_knowledge_agent.internal_knowledge_agent import (
    store_document_for_session,
    get_document_for_session,
    clear_document_for_session,
    parse_uploaded_file,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/create")
async def create_session(
    request: SessionCreateRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session_id = db.create_session(title=request.title, user_id=user["userId"])
    return {"status": "success", "sessionId": session_id, "title": request.title}


@router.get("")
async def list_sessions(
    limit: int = 50,
    skip: int = 0,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sessions = db.list_sessions(skip=skip, limit=limit, user_id=user["userId"])
    return {"status": "success", "sessions": sessions}


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session, role = db.get_session_with_access(session_id, user["userId"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "session": session, "role": role}


@router.delete("/{session_id}/delete")
async def delete_session(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Clear any uploaded document for this session
    clear_document_for_session(session_id)
    ok = db.delete_session(session_id, user_id=user["userId"])
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}


@router.patch("/{session_id}/rename")
async def rename_session(
    session_id: str,
    request: SessionRenameRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Rename a session by updating its title."""
    ok = db.rename_session(session_id, request.title, user_id=user["userId"])
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "title": request.title}


@router.post("/{session_id}/upload-document")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    tagForMonitoring: str = Query(default="", description="promptId to trigger news comparator after upload"),
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Upload a document for internal knowledge analysis.
    Supports: PDF, PPTX, XLSX, DOCX, TXT, CSV
    Document is stored for the current session only.
    """
    # Verify session exists and belongs to user
    session = db.get_session(session_id, user_id=user["userId"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
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
        
        # Store document for session
        store_document_for_session(session_id, filename, parsed_content, file_type)

        # ── Optional: trigger news comparator for a monitored promptId ──
        monitoring_result = None
        if tagForMonitoring:
            try:
                from app.agents.news_agent.news_agent import run_news_agent
                # Find existing agent data for the tagged promptId
                old_agent_data = None
                for entry in session.get("agentsData", []):
                    if entry.get("promptId") == tagForMonitoring:
                        old_agent_data = entry.get("agents", {})
                        break
                if old_agent_data:
                    monitoring_result = run_news_agent(
                        session_id=session_id,
                        prompt_id=tagForMonitoring,
                        old_agent_data=old_agent_data,
                        new_document_text=parsed_content,
                        db=db,
                    )
            except Exception:
                import traceback; traceback.print_exc()
        
        return {
            "status": "success",
            "message": f"Document '{filename}' uploaded successfully",
            "filename": filename,
            "file_type": file_type,
            "content_length": len(parsed_content),
            "monitoringResult": monitoring_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/{session_id}/document")
async def get_document_info(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get information about the uploaded document for a session."""
    session = db.get_session(session_id, user_id=user["userId"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    document = get_document_for_session(session_id)
    
    if not document:
        return {"status": "success", "has_document": False, "document": None}
    
    return {
        "status": "success",
        "has_document": True,
        "document": {
            "filename": document["filename"],
            "file_type": document["file_type"],
            "content_length": len(document["content"]),
        }
    }


@router.delete("/{session_id}/document")
async def delete_document(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Remove the uploaded document for a session."""
    session = db.get_session(session_id, user_id=user["userId"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    clear_document_for_session(session_id)
    return {"status": "success", "message": "Document removed"}

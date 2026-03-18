from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
import uuid
import json
import tempfile
import os
import re
import time
from pathlib import Path

from app.api.schemas import AnalysisRequest
from app.core.db import DatabaseManager, get_db
from app.core.auth import get_current_user
from app.services.task_planning import plan_tasks
from app.services.llm_orchestrator import plan_and_run_session
from app.services.generate_pdf_report import create_comparison_pdf_report
from app.services.report_data_manager import report_data_manager
from app.agents.report_generator_agent import run_report_generator_agent
from app.agents.report_generator_agent.tools import convert_html_to_pdf_async
from app.services.query_classifier import classify_query


router = APIRouter(tags=["analysis"])

# ── In-memory PDF cache ─────────────────────────────────────────────────────
# Maps prompt_id → { "pdf_bytes": bytes, "filename": str, "created_at": float }
# Entries older than _PDF_CACHE_TTL seconds are considered stale and regenerated.
_pdf_cache: dict = {}
_PDF_CACHE_TTL = 300  # 5 minutes


def _get_cached_pdf(prompt_id: str):
    """Return cached (pdf_bytes, filename) if fresh, else None."""
    entry = _pdf_cache.get(prompt_id)
    if entry and (time.time() - entry["created_at"]) < _PDF_CACHE_TTL:
        print(f"📦 PDF CACHE HIT for prompt_id={prompt_id} (age={int(time.time() - entry['created_at'])}s)")
        return entry["pdf_bytes"], entry["filename"]
    if entry:
        print(f"♻️ PDF CACHE STALE for prompt_id={prompt_id}, regenerating")
        del _pdf_cache[prompt_id]
    return None


def _set_cached_pdf(prompt_id: str, pdf_bytes: bytes, filename: str):
    """Store PDF bytes in cache."""
    _pdf_cache[prompt_id] = {
        "pdf_bytes": pdf_bytes,
        "filename": filename,
        "created_at": time.time(),
    }
    print(f"💾 PDF CACHE SET for prompt_id={prompt_id} ({len(pdf_bytes)} bytes, ttl={_PDF_CACHE_TTL}s)")
# ────────────────────────────────────────────────────────────────────────────


def cleanup_temp_file(file_path: str):
    """Cleanup temporary file after response is sent"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def update_session(db: DatabaseManager, session: dict):
    session_id = session["sessionId"]

    safe_session = session.copy()
    safe_session.pop("_id", None)
    safe_session.pop("sessionId", None)

    db.sessions.update_one(
        {"sessionId": session_id},
        {"$set": safe_session}
    )


def _reset_voice_state(session: dict):
    """
    Reset voice state after planning/execution completes.
    Ensures voice agent doesn't persist across workflows.
    """
    if "voiceState" in session:
        session["voiceState"] = {
            "mode": "idle",
            "is_speaking": False,
            "was_interrupted": False,
            "partial_transcript": "",
            "finalized_transcript": "",
            "original_prompt": "",
            "refined_prompt": "",
            "prompt_confirmed": False,
            "current_response": "",
            "interruption_point": 0,
            "clarifying_questions": [],
            "clarifying_responses": [],
            "voice_turns": [],
            "last_activity": "",
            "error": None
        }


def _reset_planning_state(session: dict):
    session["planningState"] = {
        "status": "planning",
        "lastPlan": None,
        "originalPrompt": None,
        "consolidatedPrompt": None,
    }


def _is_execution_confirmation(prompt: str) -> bool:
    text = (prompt or "").strip().lower()
    if not text:
        return False

    compact = re.sub(r"[^a-z0-9\s&]", "", text)
    confirm_patterns = [
        r"^confirm$",
        r"^execute$",
        r"^run$",
        r"^yes$",
        r"^proceed$",
        r"^start research$",
        r"^confirm\s*(and|&)\s*execute$",
        r"^please\s+confirm\s*(and|&)\s*execute$",
        r"^go\s+ahead$",
        r"^run\s+(the\s+)?analysis$",
        r"^start\s+(the\s+)?analysis$",
        r"^execute\s+(the\s+)?analysis$",
        r"^run\s+it$",
        r"^do\s+it$",
    ]
    return any(re.match(pattern, compact) for pattern in confirm_patterns)


def _build_consolidated_prompt(session: dict) -> str:
    """
    Build a consolidated prompt from all user messages in chat history.
    This ensures all context (drug, disease, intent) is passed to agents.
    """
    user_messages = []
    for msg in session.get("chatHistory", []):
        if msg.get("role") == "user":
            user_messages.append(msg.get("content", ""))
    
    if not user_messages:
        return ""
    
    # Combine all user messages into a coherent prompt
    if len(user_messages) == 1:
        return user_messages[0]
    
    # Multiple messages - combine with context
    return " | Context from conversation: ".join(user_messages)


def _get_session_context(session: dict) -> dict:
    """
    Extract accumulated context from session for follow-up prompts.
    Looks at previous agent runs to understand what was analyzed.
    """
    context = {
        "previous_drugs": [],
        "previous_indications": [],
        "previous_agents": [],
        "last_analysis_summary": None
    }
    
    agents_data = session.get("agentsData", [])
    if agents_data:
        last_run = agents_data[-1]
        extracted = last_run.get("extracted_params", {})
        
        if extracted.get("drug"):
            context["previous_drugs"].append(extracted["drug"])
        if extracted.get("indication"):
            context["previous_indications"].append(extracted["indication"])
        
        # Get list of agents that ran
        agents = last_run.get("agents", {})
        context["previous_agents"] = list(agents.keys())
        
        # Get a brief summary from the last run
        for agent_key, agent_data in agents.items():
            data = agent_data.get("data", {})
            if isinstance(data, dict) and data.get("summary"):
                context["last_analysis_summary"] = data.get("summary")
                break
    
    return context


@router.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")

    session, role = db.get_session_with_access(request.sessionId, user["userId"])
    if not session:
        raise HTTPException(404, "Invalid sessionId")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot run analysis")

    if not request.prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")

    # ---- INIT SESSION STATE ----
    session.setdefault("chatHistory", [])
    session.setdefault("planningState", {
        "status": "planning",   # planning | ready | executing
        "lastPlan": None,
        "originalPrompt": None,
        "consolidatedPrompt": None
    })

    planning_state = session["planningState"]
    
    # ---- GET SESSION CONTEXT FOR FOLLOW-UPS ----
    session_context = _get_session_context(session)

    # ---- STORE USER MESSAGE ----
    session["chatHistory"].append({
        "role": "user",
        "content": request.prompt
    })

    # ============================================================
    # ✅ EXECUTION CONFIRMATION (ONLY IF PLAN EXISTS)
    # ============================================================
    if planning_state["status"] == "ready" and planning_state.get("lastPlan"):
        if _is_execution_confirmation(request.prompt):
            session["chatHistory"].append({
                "role": "assistant",
                "content": "Executing the approved analysis plan."
            })

            update_session(db, session)

            return {
                "status": "success",
                "queryType": "confirm",
                "message": "Plan confirmed. Executing analysis.",
                "session": session
            }
        else:
            # User sent a new prompt instead of confirming execution.
            # Reset pending plan so planning can proceed normally.
            _reset_planning_state(session)
            planning_state = session["planningState"]

    # ============================================================
    # ❗ CLASSIFIER ONLY IF NOT PLANNING (skip for follow-ups after workflow)
    # ============================================================
    if planning_state["status"] not in ["planning", "executing"]:
        # Reset to planning for new analysis after workflow completion
        planning_state["status"] = "planning"
        planning_state["lastPlan"] = None
        planning_state["originalPrompt"] = None
        planning_state["consolidatedPrompt"] = None
    
    # Classify query
    classification = classify_query(request.prompt)
    if classification.get("type") in ["greeting", "irrelevant"]:
        session["chatHistory"].append({
            "role": "assistant",
            "content": classification.get("message", "")
        })
        update_session(db, session)
        return {
            "status": "success",
            "queryType": classification["type"],
            "response": classification["message"],
            "session": session
        }

    # ============================================================
    # 🧠 PLANNER - with session context injection
    # ============================================================
    # Inject previous context into chat for the planner to use
    if session_context["previous_drugs"] or session_context["previous_indications"]:
        context_note = f"[Previous analysis context: Drug(s): {', '.join(session_context['previous_drugs']) or 'None'}, Indication(s): {', '.join(session_context['previous_indications']) or 'None'}]"
        # Add as a system note in the planning call
        session["_context_note"] = context_note
    
    planning = plan_tasks(session)
    
    # Clean up temp context
    session.pop("_context_note", None)
    
    # Ensure planning response is valid (should never be None from plan_tasks)
    if not planning or not isinstance(planning, dict):
        print(f"[ERROR] Invalid planning response type: {type(planning)}, value: {planning}")
        planning = {
            "type": "vague",
            "message": "I encountered an issue while planning. Could you please rephrase your request?",
            "agents": [],
            "drug": None,
            "indication": None
        }
    else:
        print(f"[DEBUG] Planning response valid. Type: {planning.get('type')}")
    
    planning=json.loads(json.dumps(planning))  # Ensure planning is JSON-serializable
    # ============================================================
    # 🟡 PLANNING (VAGUE → ASK QUESTIONS)
    # ============================================================
    if planning.get("type") == "vague":
        planning_state["status"] = "planning"
        planning_state["lastPlan"] = None

        session["chatHistory"].append({
            "role": "assistant",
            "content": planning["message"],
            "type": "planning-question"
        })

        update_session(db, session)

        return {
            "status": "success",
            "queryType": "planning",
            "response": planning["message"],
            "session": session
        }

    # ============================================================
    # 🟢 READY (FINAL PLAN GENERATED)
    # ============================================================
    if planning.get("type") == "plan":
        planning_state["status"] = "ready"
        planning_state["lastPlan"] = planning
        planning_state["originalPrompt"] = request.prompt
        
        # Build consolidated prompt from entire chat history
        consolidated = planning.get("consolidated_prompt") or _build_consolidated_prompt(session)
        planning_state["consolidatedPrompt"] = consolidated

        # Add a summary message (not the full plan JSON) to chatHistory
        agent_names = ", ".join(planning.get("agents", []))
        drug_display = planning.get('drug', ['this drug'])
        indication_display = planning.get('indication', ['the indicated condition'])
        
        drug_str = drug_display[0] if isinstance(drug_display, list) and drug_display else str(drug_display or 'this drug')
        indication_str = indication_display[0] if isinstance(indication_display, list) and indication_display else str(indication_display or 'the indicated condition')
        
        session["chatHistory"].append({
            "role": "assistant",
            "content": f"Analysis plan ready. I will analyze {drug_str} for {indication_str} using: {agent_names}.\n\nPlease click 'Confirm & Execute' to proceed.",
            "type": "plan"
        })

        update_session(db, session)

        return {
            "status": "success",
            "queryType": "ready",
            "plan": planning,
            "message": "Planning complete. Confirm to execute.",
            "session": session
        }

    # ============================================================
    # FALLBACK (SHOULD NEVER HIT)
    # ============================================================
    session["chatHistory"].append({
        "role": "assistant",
        "content": "I couldn't determine the next step. Please rephrase."
    })
    update_session(db, session)

    return {
        "status": "error",
        "message": "Unknown planning state",
        "session": session
    }


@router.post("/execute")
async def execute(
    sessionId: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session, role = db.get_session_with_access(sessionId, user["userId"])
    if not session:
        raise HTTPException(404, "Invalid sessionId")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot execute analysis")

    planning_state = session.get("planningState")
    if not planning_state or planning_state["status"] != "ready":
        raise HTTPException(400, "Planning not complete")

    plan = planning_state["lastPlan"]
    prompt_id = str(uuid.uuid4())

    planning_state["status"] = "executing"
    
    # Use consolidated prompt (combines all user context) instead of just original prompt
    consolidated_prompt = planning_state.get("consolidatedPrompt") or planning_state.get("originalPrompt", "")
    
    print(f"\n{'='*60}")
    print(f"🚀 EXECUTE: Starting agent execution")
    print(f"   Session: {session['sessionId']}")
    print(f"   Prompt ID: {prompt_id}")
    print(f"   Drug: {plan.get('drug')}, Indication: {plan.get('indication')}")
    print(f"   Agents: {plan['agents']}")
    print(f"   Prompt: {consolidated_prompt[:150]}...")
    print(f"{'='*60}")

    orchestrator_message = plan_and_run_session(
        db=db,
        session=session,
        user_query=consolidated_prompt,
        agents=plan["agents"],
        prompt_id=prompt_id,
        plan_context={
            "drug": plan.get("drug"),
            "indication": plan.get("indication"),
        }
    )
    
    print(f"\n✅ EXECUTE: Orchestrator completed")
    print(f"   Message: {orchestrator_message}")
    print(f"   Prompt ID for report download: {prompt_id}")

    # Refresh session from DB to get updated agentsData from orchestrator
    # Retry logic for MongoDB connection issues during long-running operations
    max_retries = 3
    retry_count = 0
    updated_session = None
    
    while retry_count < max_retries:
        try:
            updated_session = db.get_session(sessionId)
            break
        except Exception as e:
            retry_count += 1
            print(f"[EXECUTE] MongoDB connection error (attempt {retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                # If all retries fail, use the in-memory session from orchestrator
                print("[EXECUTE] Using in-memory session after DB connection timeout")
                updated_session = session
                break
            import time
            time.sleep(1)  # Wait 1 second before retry
    
    if not updated_session:
        # Fallback: use original session if all retries failed
        updated_session = session
    
    # Reset planning state for next analysis (CRITICAL: allows new workflows)
    _reset_planning_state(updated_session)
    
    # Reset voice state after execution (CRITICAL: voice agent doesn't persist)
    _reset_voice_state(updated_session)
    
    updated_session["chatHistory"].append({
        "role": "assistant",
        "content": orchestrator_message,
        "type": "agent-complete",
        "promptId": prompt_id
    })

    # Try to update session with retry logic
    update_retry = 0
    while update_retry < max_retries:
        try:
            update_session(db, updated_session)
            break
        except Exception as e:
            update_retry += 1
            print(f"[EXECUTE] Failed to update session (attempt {update_retry}/{max_retries}): {e}")
            if update_retry >= max_retries:
                print("[EXECUTE] WARNING: Session update failed, returning data anyway")
            import time
            time.sleep(1)

    return {
        "status": "success",
        "promptId": prompt_id,
        "message": orchestrator_message,
        "session": updated_session
    }


@router.post("/planning/cancel")
async def cancel_planning(
    sessionId: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    session, role = db.get_session_with_access(sessionId, user["userId"])
    if not session:
        raise HTTPException(404, "Invalid sessionId")
    if role == "viewer":
        raise HTTPException(403, "Viewers cannot modify planning state")

    session.setdefault("planningState", {
        "status": "planning",
        "lastPlan": None,
        "originalPrompt": None,
        "consolidatedPrompt": None,
    })

    _reset_planning_state(session)
    update_session(db, session)

    return {
        "status": "success",
        "message": "Pending plan canceled.",
        "session": session,
    }


# ---------------- REPORT DOWNLOAD ---------------- #

@router.get("/generate-report/{prompt_id}")
async def generate_report(
    prompt_id: str,
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    print(f"\n{'='*60}")
    print(f"📥 REPORT DOWNLOAD: Started for prompt_id={prompt_id}")
    print(f"{'='*60}")
    
    # First try to get data from our cached report data manager
    cached_data = report_data_manager.get_report_data(prompt_id)
    
    # Check if cached data actually has meaningful content (not just empty dicts)
    has_meaningful_data = False
    if cached_data:
        agents_data = report_data_manager.get_formatted_agents_data(prompt_id)
        # Check if any agent has actual data
        for agent_key, agent_data in agents_data.items():
            if agent_data and isinstance(agent_data, dict) and len(agent_data) > 0:
                has_meaningful_data = True
                break
        print(f"🔍 Cached data check for prompt_id {prompt_id}: has_meaningful_data={has_meaningful_data}")
    
    if cached_data and has_meaningful_data:
        print(f"🔄 REPORT DOWNLOAD: Using CACHED data for prompt_id: {prompt_id}")
        try:
            # Get the data
            agents_data = report_data_manager.get_formatted_agents_data(prompt_id)
            drug_name = cached_data['drug_name']
            indication = cached_data['indication']
            print(f"📋 REPORT DOWNLOAD: drug={drug_name}, indication={indication}")
            print(f"📋 REPORT DOWNLOAD: agents_data keys={list(agents_data.keys())}")
            
            # Generate report using cached data
            print(f"⏳ REPORT DOWNLOAD: Generating HTML report...")
            result = run_report_generator_agent(
                drug_name=drug_name,
                indication=indication,
                agents_data=agents_data,
                use_crew=False,
                output_format="html",
            )
            
            if result["status"] != "success":
                print(f"❌ REPORT DOWNLOAD: HTML generation failed: {result.get('error')}")
                raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
            
            # Convert HTML to PDF using Playwright
            html_content = result["html_content"]
            print(f"✅ REPORT DOWNLOAD: HTML generated successfully, length={len(html_content)}")
            
            # Create safe filename with timestamp
            from datetime import datetime
            from pathlib import Path
            safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_drug}_Intelligence_Report.pdf"
            
            # Create generated_reports directory if it doesn't exist (absolute path)
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent
            reports_dir = backend_dir / "generated_reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Save to generated_reports folder
            permanent_path = reports_dir / f"{safe_drug}_{timestamp}.pdf"
            
            # Convert to PDF using Playwright (async - directly awaited)
            print(f"⏳ REPORT DOWNLOAD: Converting HTML to PDF via Playwright...")
            print(f"📁 REPORT DOWNLOAD: Output path: {permanent_path}")
            try:
                await convert_html_to_pdf_async(html_content, str(permanent_path))
                print(f"✅ REPORT DOWNLOAD: PDF conversion successful")
            except Exception as pdf_err:
                print(f"❌ REPORT DOWNLOAD: PDF conversion FAILED: {pdf_err}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(pdf_err)}")
            
            # Create temporary copy for FileResponse (gets cleaned up)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_path = tmp_file.name
            
            # Copy the permanent file to temp location for response
            import shutil
            shutil.copy2(permanent_path, tmp_path)
            
            print(f"📄 REPORT DOWNLOAD: Report saved to: {permanent_path}")
            print(f"📤 REPORT DOWNLOAD: Sending PDF response, filename={filename}")
            
            # Add background task to cleanup temporary file only
            background_tasks.add_task(cleanup_temp_file, tmp_path)
            
            return FileResponse(
                path=tmp_path,
                filename=filename,
                media_type="application/pdf"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ REPORT DOWNLOAD: Unexpected error in cached path: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    # Fallback to MongoDB query if no cached data found (or cached data was empty)
    print(f"📂 Falling back to MongoDB for prompt_id: {prompt_id}")
    session = db.sessions.find_one(
        {"agentsData.promptId": prompt_id}, 
        {"agentsData.$": 1, "title": 1, "chatHistory": 1, "sessionId": 1}
    )

    if not session or "agentsData" not in session:
        raise HTTPException(status_code=404, detail="Prompt ID not found")

    entry = session["agentsData"][0]
    agents = entry["agents"]
    extracted_params = entry.get("extracted_params", {})
    
    # Get drug and indication from extracted params or session title
    drug_name = extracted_params.get("drug") or session.get("title", "Drug Analysis")
    indication = extracted_params.get("indication") or "general"

    try:
        # Debug: Print the actual data structure
        print(f"🔍 DEBUG - Entry keys: {list(entry.keys())}")
        print(f"🔍 DEBUG - Agents keys: {list(agents.keys())}")
        print(f"🔍 DEBUG - Extracted params: {extracted_params}")
        print(f"🔍 DEBUG - Drug name: {drug_name}, Indication: {indication}")
        
        # Check what data we actually have
        for agent_key in agents.keys():
            print(f"🔍 DEBUG - {agent_key}: {type(agents[agent_key])}, keys: {list(agents[agent_key].keys()) if isinstance(agents[agent_key], dict) else 'not dict'}")
        
        # Helper function to extract agent data - handles both key formats and nested structure
        def extract_agent_data(agents_dict, *possible_keys):
            """Extract data from agent results, handling multiple key formats and nested structure.
            
            MongoDB structure is: agents.{key}.data.data.{actual fields}
            - agents.iqvia = {timestamp, query, data: {status, data: {actual data}, visualizations}}
            """
            for key in possible_keys:
                agent_result = agents_dict.get(key)
                if agent_result and isinstance(agent_result, dict):
                    # Structure: {timestamp, query, data: {...}}
                    outer_data = agent_result.get('data', {})
                    if isinstance(outer_data, dict):
                        # Structure: {status, data: {actual data}, visualizations}
                        inner_data = outer_data.get('data', {})
                        if isinstance(inner_data, dict) and len(inner_data) > 0:
                            print(f"🔍 DEBUG - Extracted {key} data with {len(inner_data)} keys")
                            return inner_data
                        # Fallback: maybe the outer_data IS the actual data
                        if len(outer_data) > 0 and 'status' not in outer_data:
                            return outer_data
            return {}
        
        # Prepare data for new report generator - extract actual agent data
        # Try multiple key formats: lowercase (iqvia), uppercase (IQVIA_AGENT), short (internal)
        agents_data = {
            "iqvia": extract_agent_data(agents, "iqvia", "IQVIA_AGENT"),
            "clinical": extract_agent_data(agents, "clinical", "CLINICAL_AGENT"),
            "patent": extract_agent_data(agents, "patent", "PATENT_AGENT"),
            "exim": extract_agent_data(agents, "exim", "EXIM_AGENT"),
            "internal_knowledge": extract_agent_data(agents, "internal", "internal_knowledge", "INTERNAL_KNOWLEDGE_AGENT"),
            "web_intelligence": extract_agent_data(agents, "web", "web_intelligence", "WEB_INTELLIGENCE_AGENT"),
        }
        
        print(f"🔍 DEBUG - Agents data prepared: {list(agents_data.keys())}")
        print(f"🔍 DEBUG - IQVIA data type: {type(agents_data['iqvia'])}")
        if isinstance(agents_data['iqvia'], dict):
            print(f"🔍 DEBUG - IQVIA keys: {list(agents_data['iqvia'].keys())}")
        
        # Store the agent data in report data manager for easy access
        storage_key = report_data_manager.store_report_data(
            session_id=session.get("sessionId", "unknown_session"),
            prompt_id=prompt_id,
            drug_name=drug_name,
            indication=indication,
            agents_data=agents_data
        )
        print(f"🔍 DEBUG - Stored data with key: {storage_key}")
        
        # DEBUG: Save the MongoDB-extracted data for debugging
        try:
            import json
            from pathlib import Path
            from datetime import datetime
            
            debug_dir = Path(__file__).resolve().parent.parent.parent.parent / "debug_reports"
            debug_dir.mkdir(exist_ok=True)
            
            safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
            debug_file = debug_dir / f"mongodb_data_{safe_drug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            debug_data = {
                "source": "mongodb",
                "prompt_id": prompt_id,
                "drug_name": drug_name,
                "indication": indication,
                "timestamp": datetime.now().isoformat(),
                "agents_data": agents_data,
                "agents_data_summary": {
                    k: {
                        "type": type(v).__name__,
                        "keys": list(v.keys()) if isinstance(v, dict) else None,
                        "length": len(v) if isinstance(v, (list, dict, str)) else None,
                        "sample_keys": list(v.keys())[:10] if isinstance(v, dict) and len(v) > 5 else None
                    } for k, v in agents_data.items()
                }
            }
            
            with open(debug_file, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)
                
            print(f"🔍 DEBUG: MongoDB agents data saved to {debug_file}")
        except Exception as e:
            print(f"⚠️ DEBUG: Failed to save debug data: {e}")
        
        # Generate report using new report generator
        print(f"⏳ REPORT DOWNLOAD [MongoDB path]: Generating HTML report...")
        result = run_report_generator_agent(
            drug_name=drug_name,
            indication=indication,
            agents_data=agents_data,
            use_crew=False,
            output_format="html",
        )
        
        if result["status"] != "success":
            print(f"❌ REPORT DOWNLOAD [MongoDB path]: HTML generation failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
        
        # Convert HTML to PDF using Playwright
        html_content = result["html_content"]
        print(f"✅ REPORT DOWNLOAD [MongoDB path]: HTML generated, length={len(html_content)}")
        
        # Create safe filename with timestamp
        from datetime import datetime
        from pathlib import Path
        safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_drug}_Intelligence_Report.pdf"
        
        # Create generated_reports directory if it doesn't exist (absolute path)
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        reports_dir = backend_dir / "generated_reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Save to generated_reports folder
        permanent_path = reports_dir / f"{safe_drug}_{timestamp}.pdf"
        
        # Convert to PDF using Playwright (async - directly awaited)
        print(f"⏳ REPORT DOWNLOAD [MongoDB path]: Converting HTML to PDF via Playwright...")
        print(f"📁 REPORT DOWNLOAD [MongoDB path]: Output path: {permanent_path}")
        try:
            await convert_html_to_pdf_async(html_content, str(permanent_path))
            print(f"✅ REPORT DOWNLOAD [MongoDB path]: PDF conversion successful")
        except Exception as pdf_err:
            print(f"❌ REPORT DOWNLOAD [MongoDB path]: PDF conversion FAILED: {pdf_err}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(pdf_err)}")
        
        # Create temporary copy for FileResponse (gets cleaned up)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = tmp_file.name
        
        # Copy the permanent file to temp location for response
        import shutil
        shutil.copy2(permanent_path, tmp_path)
        
        print(f"📄 REPORT DOWNLOAD [MongoDB path]: Report saved to: {permanent_path}")
        print(f"📤 REPORT DOWNLOAD [MongoDB path]: Sending PDF response, filename={filename}")
        
        # Add background task to cleanup temporary file only
        background_tasks.add_task(cleanup_temp_file, tmp_path)
        
        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ REPORT DOWNLOAD [MongoDB path]: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ---------------- REPORT VIEW (INLINE) ---------------- #

@router.get("/view-report/{prompt_id}")
async def view_report_inline(
    prompt_id: str,
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Generate and serve a PDF report for inline viewing (not download).
    Uses Content-Disposition: inline to display in browser/iframe.
    """
    print(f"\n{'='*60}")
    print(f"👁️ REPORT VIEW: Started for prompt_id={prompt_id}")
    print(f"{'='*60}")
    
    # ── Check in-memory PDF cache first ──────────────────────────────────
    cached = _get_cached_pdf(prompt_id)
    if cached:
        pdf_bytes, filename = cached
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=\"{filename}\"",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, max-age=300",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type",
            }
        )
    # ─────────────────────────────────────────────────────────────────────
    
    # First try to get data from our cached report data manager
    cached_data = report_data_manager.get_report_data(prompt_id)
    
    # Check if the cached data has meaningful content
    has_meaningful_data = False
    if cached_data:
        agents_data = cached_data.get('agents_data', {})
        has_meaningful_data = any(
            bool(v) and v != {} and v != [] 
            for v in agents_data.values()
        )
        print(f"🔍 Cached data check for prompt_id {prompt_id}: has_meaningful_data={has_meaningful_data}")
    
    if cached_data and has_meaningful_data:
        print(f"🔄 REPORT VIEW: Using CACHED data for prompt_id: {prompt_id}")
        try:
            # Get the data
            agents_data = report_data_manager.get_formatted_agents_data(prompt_id)
            drug_name = cached_data['drug_name']
            indication = cached_data['indication']
            print(f"📋 REPORT VIEW: drug={drug_name}, indication={indication}")
            
            # Generate report using cached data
            print(f"⏳ REPORT VIEW: Generating HTML report...")
            result = run_report_generator_agent(
                drug_name=drug_name,
                indication=indication,
                agents_data=agents_data,
                use_crew=False,
                output_format="html",
            )
            
            if result["status"] != "success":
                print(f"❌ REPORT VIEW: HTML generation failed: {result.get('error')}")
                raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
            
            # Convert HTML to PDF using Playwright
            html_content = result["html_content"]
            print(f"✅ REPORT VIEW: HTML generated successfully, length={len(html_content)}")
            
            # Create safe filename with timestamp
            from datetime import datetime
            from pathlib import Path
            safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_drug}_Intelligence_Report.pdf"
            
            # Create generated_reports directory if it doesn't exist (absolute path)
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent
            reports_dir = backend_dir / "generated_reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Save to generated_reports folder
            permanent_path = reports_dir / f"{safe_drug}_{timestamp}.pdf"
            
            # Convert to PDF using Playwright
            print(f"⏳ REPORT VIEW: Converting HTML to PDF via Playwright...")
            try:
                await convert_html_to_pdf_async(html_content, str(permanent_path))
                print(f"✅ REPORT VIEW: PDF conversion successful")
            except Exception as pdf_err:
                error_msg = str(pdf_err)
                print(f"❌ REPORT VIEW: PDF conversion FAILED: {error_msg}")
                import traceback
                traceback.print_exc()
                
                # Provide more helpful error message for deployment issues
                if "Printing failed" in error_msg or "printToPDF" in error_msg:
                    user_friendly_msg = (
                        "PDF generation failed in the deployment environment. "
                        "The server is missing required system dependencies for headless rendering. "
                        "Please contact the administrator."
                    )
                else:
                    user_friendly_msg = error_msg
                
                raise HTTPException(status_code=500, detail=f"PDF conversion failed: {user_friendly_msg}")
            
            # Create temporary copy for Response
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_path = tmp_file.name
            
            import shutil
            shutil.copy2(permanent_path, tmp_path)
            
            print(f"📄 REPORT VIEW: Report saved to: {permanent_path}")
            print(f"👁️ REPORT VIEW: Serving PDF inline, filename={filename}")
            
            # Add background task to cleanup temporary file
            background_tasks.add_task(cleanup_temp_file, tmp_path)
            
            # Read the file content for inline response
            with open(tmp_path, "rb") as f:
                pdf_content = f.read()
            
            # Store in PDF cache for fast repeated viewing
            _set_cached_pdf(prompt_id, pdf_content, filename)
            
            # Return with inline content disposition (for viewing, not downloading)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename=\"{filename}\"",
                    "X-Content-Type-Options": "nosniff",
                    "Cache-Control": "private, max-age=300",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Expose-Headers": "Content-Disposition, Content-Type",
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ REPORT VIEW: Unexpected error in cached path: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    # Fallback to MongoDB query if no cached data found
    print(f"📂 REPORT VIEW: Falling back to MongoDB for prompt_id: {prompt_id}")
    session = db.sessions.find_one(
        {"agentsData.promptId": prompt_id}, 
        {"agentsData.$": 1, "title": 1, "chatHistory": 1, "sessionId": 1}
    )

    if not session or "agentsData" not in session:
        raise HTTPException(status_code=404, detail="Prompt ID not found")

    entry = session["agentsData"][0]
    agents = entry["agents"]
    extracted_params = entry.get("extracted_params", {})
    
    drug_name = extracted_params.get("drug") or session.get("title", "Drug Analysis")
    indication = extracted_params.get("indication", "")
    
    # Helper function to extract agent data - handles both key formats and nested structure
    def extract_agent_data(agents_dict, *possible_keys):
        """Extract data from agent results, handling multiple key formats and nested structure.
        
        MongoDB structure is: agents.{key}.data.data.{actual fields}
        - agents.iqvia = {timestamp, query, data: {status, data: {actual data}, visualizations}}
        """
        for key in possible_keys:
            agent_result = agents_dict.get(key)
            if agent_result and isinstance(agent_result, dict):
                # Structure: {timestamp, query, data: {...}}
                outer_data = agent_result.get('data', {})
                if isinstance(outer_data, dict):
                    # Structure: {status, data: {actual data}, visualizations}
                    inner_data = outer_data.get('data', {})
                    if isinstance(inner_data, dict) and len(inner_data) > 0:
                        return inner_data
                    # Fallback: maybe the outer_data IS the actual data
                    if len(outer_data) > 0 and 'status' not in outer_data:
                        return outer_data
        return {}
    
    # Prepare data for report generator - extract actual agent data
    agents_data = {
        "iqvia": extract_agent_data(agents, "iqvia", "IQVIA_AGENT"),
        "clinical": extract_agent_data(agents, "clinical", "CLINICAL_AGENT"),
        "patent": extract_agent_data(agents, "patent", "PATENT_AGENT"),
        "exim": extract_agent_data(agents, "exim", "EXIM_AGENT"),
        "internal_knowledge": extract_agent_data(agents, "internal", "internal_knowledge", "INTERNAL_KNOWLEDGE_AGENT"),
        "web_intelligence": extract_agent_data(agents, "web", "web_intelligence", "WEB_INTELLIGENCE_AGENT"),
    }
    
    print(f"📋 REPORT VIEW [MongoDB]: drug={drug_name}, indication={indication}")
    print(f"📋 REPORT VIEW [MongoDB]: agents_data keys={list(agents_data.keys())}")
    
    try:
        # Generate report using MongoDB data
        print(f"⏳ REPORT VIEW [MongoDB]: Generating HTML report...")
        result = run_report_generator_agent(
            drug_name=drug_name,
            indication=indication,
            agents_data=agents_data,
            use_crew=False,
            output_format="html",
        )
        
        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
        
        html_content = result["html_content"]
        print(f"✅ REPORT VIEW [MongoDB]: HTML generated successfully")
        
        from datetime import datetime
        from pathlib import Path
        safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_drug}_Intelligence_Report.pdf"
        
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        reports_dir = backend_dir / "generated_reports"
        reports_dir.mkdir(exist_ok=True)
        
        permanent_path = reports_dir / f"{safe_drug}_{timestamp}.pdf"
        
        print(f"⏳ REPORT VIEW [MongoDB]: Converting HTML to PDF via Playwright...")
        try:
            await convert_html_to_pdf_async(html_content, str(permanent_path))
            print(f"✅ REPORT VIEW [MongoDB]: PDF conversion successful")
        except Exception as pdf_err:
            error_msg = str(pdf_err)
            print(f"❌ REPORT VIEW [MongoDB]: PDF conversion FAILED: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Provide more helpful error message for deployment issues
            if "Printing failed" in error_msg or "printToPDF" in error_msg:
                user_friendly_msg = (
                    "PDF generation failed in the deployment environment. "
                    "The server is missing required system dependencies for headless rendering. "
                    "Please contact the administrator."
                )
            else:
                user_friendly_msg = error_msg
            
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {user_friendly_msg}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = tmp_file.name
        
        import shutil
        shutil.copy2(permanent_path, tmp_path)
        
        print(f"📄 REPORT VIEW [MongoDB]: Report saved to: {permanent_path}")
        print(f"👁️ REPORT VIEW [MongoDB]: Serving PDF inline")
        
        background_tasks.add_task(cleanup_temp_file, tmp_path)
        
        with open(tmp_path, "rb") as f:
            pdf_content = f.read()
        
        # Store in PDF cache for fast repeated viewing
        _set_cached_pdf(prompt_id, pdf_content, filename)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=\"{filename}\"",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, max-age=300",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ REPORT VIEW [MongoDB]: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/health/playwright")
def playwright_health_check():
    """
    Diagnostic endpoint to check if Playwright and system dependencies are working.
    Useful for debugging deployment issues.
    """
    import os
    import platform
    import subprocess
    
    diagnostics = {
        "status": "checking",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "playwright_installed": False,
        "chromium_available": False,
        "system_libs_available": False,
        "test_pdf_generation": None,
        "errors": []
    }
    
    try:
        # Check if Playwright is installed
        import playwright
        diagnostics["playwright_installed"] = True
        diagnostics["playwright_version"] = playwright.__version__
    except ImportError as e:
        diagnostics["errors"].append(f"Playwright not installed: {e}")
    
    try:
        # Check if Chromium browser is available
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                diagnostics["chromium_available"] = True
                diagnostics["chromium_status"] = "✓ Launches successfully"
            except Exception as e:
                diagnostics["errors"].append(f"Chromium launch failed: {str(e)}")
    except Exception as e:
        diagnostics["errors"].append(f"Playwright sync import failed: {e}")
    
    # Check for required system libraries on Linux
    if platform.system() == "Linux":
        required_libs = [
            "libx11-6", "libxcomposite1", "libxdamage1", "libxext6",
            "libxfixes3", "libxrandr2", "libxtst6", "libxkbcommon0",
            "libnss3", "libssl3"
        ]
        
        available_libs = []
        missing_libs = []
        
        try:
            for lib in required_libs:
                result = subprocess.run(
                    ["dpkg", "-l", f"*{lib}*"], 
                    capture_output=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    available_libs.append(lib)
                else:
                    missing_libs.append(lib)
        except Exception as e:
            diagnostics["system_libs_info"] = f"Could not check system libs: {e}"
        
        if missing_libs:
            diagnostics["errors"].append(f"Missing system libraries: {', '.join(missing_libs)}")
            diagnostics["system_libs_available"] = False
        else:
            diagnostics["system_libs_available"] = True
        
        diagnostics["system_libs_check"] = {
            "available": available_libs,
            "missing": missing_libs
        }
    
    # Try a simple PDF generation test
    try:
        from playwright.sync_api import sync_playwright
        
        html_test = "<html><body><h1>Test</h1><p>PDF Generation Test</p></body></html>"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_test)
            pdf_bytes = page.pdf()
            browser.close()
            
            diagnostics["test_pdf_generation"] = {
                "status": "✓ SUCCESS",
                "pdf_size_bytes": len(pdf_bytes)
            }
    except Exception as e:
        diagnostics["test_pdf_generation"] = {
            "status": "✗ FAILED",
            "error": str(e)
        }
        diagnostics["errors"].append(f"Test PDF generation failed: {str(e)}")
    
    # Determine overall status
    if not diagnostics["errors"]:
        diagnostics["status"] = "✓ HEALTHY"
    elif diagnostics["chromium_available"] and diagnostics["test_pdf_generation"].get("status") == "✓ SUCCESS":
        diagnostics["status"] = "⚠ MOSTLY OK (some warnings)"
    else:
        diagnostics["status"] = "✗ PROBLEM DETECTED"
    
    return diagnostics


@router.get("/debug-report-data/{prompt_id}")
def debug_report_data(prompt_id: str):
    """
    Debug endpoint to see stored report data for a specific prompt ID.
    """
    try:
        # Get raw data
        raw_data = report_data_manager.get_report_data(prompt_id)
        
        # Get formatted data
        formatted_data = report_data_manager.get_formatted_agents_data(prompt_id)
        
        return {
            "status": "success",
            "prompt_id": prompt_id,
            "raw_data": raw_data,
            "formatted_data": formatted_data,
            "data_availability": {
                "iqvia": bool(formatted_data.get("iqvia")),
                "clinical": bool(formatted_data.get("clinical")),
                "patent": bool(formatted_data.get("patent")),
                "exim": bool(formatted_data.get("exim")),
                "internal_knowledge": bool(formatted_data.get("internal_knowledge")),
                "web_intelligence": bool(formatted_data.get("web_intelligence"))
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/list-reports")
def list_available_reports(
    session_id: str = None,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    List all available reports with their metadata.
    """
    try:
        reports = report_data_manager.list_reports(session_id=session_id)
        return {
            "status": "success",
            "reports": reports,
            "total_count": len(reports)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/test-report-generation/{prompt_id}")
def test_report_generation(
    prompt_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Test endpoint to check if report generation would work without actually generating.
    """
    try:
        # Check cached data first
        cached_data = report_data_manager.get_report_data(prompt_id)
        if cached_data:
            agents_data = report_data_manager.get_formatted_agents_data(prompt_id)
            return {
                "status": "success",
                "data_source": "cached",
                "prompt_id": prompt_id,
                "drug_name": cached_data['drug_name'],
                "indication": cached_data['indication'],
                "agents_with_data": [k for k, v in agents_data.items() if v],
                "ready_for_generation": True
            }
        
        # Check MongoDB fallback
        from app.core.db import init_db
        db = init_db()
        session = db.sessions.find_one(
            {"agentsData.promptId": prompt_id}, 
            {"agentsData.$": 1, "title": 1, "sessionId": 1}
        )
        
        if not session:
            return {
                "status": "not_found",
                "prompt_id": prompt_id,
                "message": "Prompt ID not found in cache or database"
            }
            
        return {
            "status": "success", 
            "data_source": "mongodb",
            "prompt_id": prompt_id,
            "session_has_sessionId": "sessionId" in session,
            "session_keys": list(session.keys()),
            "ready_for_generation": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "prompt_id": prompt_id,
            "error": str(e)
        }


# ---------------- COMPARISON REPORT ---------------- #

@router.post("/generate-comparison-report")
def generate_comparison_report(
    prompt_ids: list[str],
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Generate a comparison PDF report for multiple analyses.
    
    Args:
        prompt_ids: List of prompt IDs to compare (2-5 prompts)
    """
    if len(prompt_ids) < 2:
        raise HTTPException(400, "At least 2 prompt IDs required for comparison")
    if len(prompt_ids) > 5:
        raise HTTPException(400, "Maximum 5 prompt IDs allowed for comparison")
    
    # Collect data from all prompts
    comparisons = []
    for prompt_id in prompt_ids:
        session = db.sessions.find_one(
            {"agentsData.promptId": prompt_id}, 
            {"agentsData.$": 1, "title": 1}
        )
        
        if not session or "agentsData" not in session:
            raise HTTPException(404, f"Prompt ID not found: {prompt_id}")
        
        entry = session["agentsData"][0]
        agents = entry["agents"]
        extracted_params = entry.get("extracted_params", {})
        
        comparisons.append({
            "prompt_id": prompt_id,
            "drug_name": extracted_params.get("drug") or session.get("title", "Drug Analysis"),
            "indication": extracted_params.get("indication") or "general",
            "agents": agents
        })
    
    try:
        result = create_comparison_pdf_report(comparisons)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to generate comparison report: {str(e)}")
    
    if result["status"] != "success":
        raise HTTPException(500, result.get("error", "Unknown error"))
    
    return FileResponse(
        path=result["file_path"],
        filename=result["file_name"],
        media_type="application/pdf"
    )

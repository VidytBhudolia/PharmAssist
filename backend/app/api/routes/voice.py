"""
Voice Assistant Routes for PharmAssist

Endpoints for voice input processing, strictly scoped to /analyze functionality.
Does not affect /execute or report generation.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
import base64

from app.api.schemas import (
    VoiceTextRequest,
    VoiceAudioRequest,
    VoiceInterruptRequest,
    VoiceConfirmRequest,
    VoiceResetRequest,
    VoiceAgentResponseModel,
    VoiceStateResponse,
    VoiceAction,
    VoiceMode,
)
from app.core.db import DatabaseManager, get_db
from app.core.auth import get_current_user
from app.agents.voice_assistant_agent import (
    VoiceAssistantAgent,
    VoiceAgentAction,
    VoiceAgentResponse,
    VoiceState,
    VoiceStateManager,
    AGENT_INTENT_WORDS,
    AGENT_BACKCHANNEL_WORDS,
)
from app.agents.voice_assistant_agent.lexicons import (
    contains_intent_word,
    contains_backchannel_word,
    is_confirmation,
)


router = APIRouter(prefix="/voice", tags=["voice-assistant"])


def _action_to_schema(action: VoiceAgentAction) -> VoiceAction:
    """Convert internal action enum to schema enum."""
    mapping = {
        VoiceAgentAction.LISTEN: VoiceAction.LISTEN,
        VoiceAgentAction.SPEAK: VoiceAction.SPEAK,
        VoiceAgentAction.STOP_SPEAKING: VoiceAction.STOP_SPEAKING,
        VoiceAgentAction.ASK_CLARIFICATION: VoiceAction.ASK_CLARIFICATION,
        VoiceAgentAction.CONFIRM_PROMPT: VoiceAction.CONFIRM_PROMPT,
        VoiceAgentAction.FORWARD_TO_PLANNING: VoiceAction.FORWARD_TO_PLANNING,
        VoiceAgentAction.ACKNOWLEDGE: VoiceAction.ACKNOWLEDGE,
        VoiceAgentAction.RESET: VoiceAction.RESET,
        VoiceAgentAction.ERROR: VoiceAction.ERROR,
    }
    return mapping.get(action, VoiceAction.LISTEN)


def _mode_to_schema(mode) -> VoiceMode:
    """Convert internal mode enum to schema enum."""
    from app.agents.voice_assistant_agent.voice_state import VoiceMode as InternalMode
    mapping = {
        InternalMode.IDLE: VoiceMode.IDLE,
        InternalMode.LISTENING: VoiceMode.LISTENING,
        InternalMode.PROCESSING: VoiceMode.PROCESSING,
        InternalMode.SPEAKING: VoiceMode.SPEAKING,
        InternalMode.INTERRUPTED: VoiceMode.INTERRUPTED,
        InternalMode.HOLDING: VoiceMode.HOLDING,
        InternalMode.AWAITING_CONFIRMATION: VoiceMode.AWAITING_CONFIRMATION,
    }
    return mapping.get(mode, VoiceMode.IDLE)


def _state_to_response(state: VoiceState) -> VoiceStateResponse:
    """Convert VoiceState to VoiceStateResponse."""
    return VoiceStateResponse(
        mode=_mode_to_schema(state.mode),
        is_speaking=state.is_speaking or False,
        was_interrupted=state.was_interrupted or False,
        partial_transcript=state.partial_transcript or "",
        original_prompt=state.original_prompt or "",
        refined_prompt=state.refined_prompt or "",
        prompt_confirmed=state.prompt_confirmed or False,
        clarifying_questions=state.clarifying_questions or [],
    )


def _build_response(
    agent_response: VoiceAgentResponse,
    session: Dict[str, Any],
    voice_state: VoiceState
) -> VoiceAgentResponseModel:
    """Build API response from agent response."""
    return VoiceAgentResponseModel(
        status="success",
        action=_action_to_schema(agent_response.action),
        message=agent_response.message,
        voice_response=agent_response.voice_response,
        refined_prompt=agent_response.refined_prompt,
        ready_for_planning=agent_response.ready_for_planning,
        should_reset=agent_response.should_reset,
        voice_state=_state_to_response(voice_state),
        metadata=agent_response.metadata or {},
        session=session,
    )


def _get_session_or_403(db: DatabaseManager, session_id: str, user_id: str):
    """Helper: fetch session only if user has access (owner or collaborator)."""
    session, role = db.get_session_with_access(session_id, user_id)
    if not session:
        raise HTTPException(404, "Invalid sessionId or no access")
    return session


def update_session(db: DatabaseManager, session: dict):
    """Update session in database."""
    session_id = session["sessionId"]
    safe_session = session.copy()
    safe_session.pop("_id", None)
    safe_session.pop("sessionId", None)
    db.sessions.update_one(
        {"sessionId": session_id},
        {"$set": safe_session}
    )


# ===== VOICE TEXT PROCESSING =====

@router.post("/process-text", response_model=VoiceAgentResponseModel)
async def process_voice_text(
    request: VoiceTextRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Process transcribed voice text input.
    
    This is the main endpoint for voice input that has already been
    transcribed by the frontend (e.g., using Web Speech API).
    
    Strictly scoped to /analyze functionality - prepares prompts
    for the planning pipeline but does not auto-execute.
    """
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")
    
    session = _get_session_or_403(db, request.sessionId, user["userId"])
    
    if not request.text or not request.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    
    # Initialize voice state if needed
    session.setdefault("voiceState", {})
    
    # Create voice assistant agent
    agent = VoiceAssistantAgent(session)
    
    # Process the text
    response = await agent.process_text(request.text, request.is_final)
    
    # Handle forwarding to planning
    if response.action == VoiceAgentAction.FORWARD_TO_PLANNING:
        # NOTE: Don't append to chat history here - the frontend will call /analyze
        # which will add the message to chat history. This avoids duplicate messages.
        pass
    
    # Save session state
    update_session(db, session)
    
    # Get updated state
    voice_state = agent.get_state()
    
    return _build_response(response, session, voice_state)


# ===== VOICE AUDIO PROCESSING =====

@router.post("/process-audio", response_model=VoiceAgentResponseModel)
async def process_voice_audio(
    request: VoiceAudioRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Process raw voice audio input.
    
    Accepts base64-encoded audio, transcribes it, and processes
    through the voice assistant pipeline.
    
    Supported formats: webm, wav, mp3, m4a, ogg
    """
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")
    
    session = _get_session_or_403(db, request.sessionId, user["userId"])
    
    if not request.audio_base64:
        raise HTTPException(400, "audio_base64 is required")
    
    # Decode audio
    try:
        # Remove data URL prefix if present
        audio_b64 = request.audio_base64
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
        audio_data = base64.b64decode(audio_b64)
    except Exception as e:
        raise HTTPException(400, f"Invalid base64 audio: {str(e)}")
    
    # Initialize voice state if needed
    session.setdefault("voiceState", {})
    
    # Create voice assistant agent
    agent = VoiceAssistantAgent(session)
    
    # Process the audio
    response = await agent.process_audio(
        audio_data,
        request.audio_format,
        request.language
    )
    
    # Handle forwarding to planning
    if response.action == VoiceAgentAction.FORWARD_TO_PLANNING:
        # NOTE: Don't append here - /analyze will add it to avoid duplicates
        pass
    
    # Save session state
    update_session(db, session)
    
    # Get updated state
    voice_state = agent.get_state()
    
    return _build_response(response, session, voice_state)


# ===== INTERRUPTION HANDLING =====

@router.post("/interrupt", response_model=VoiceAgentResponseModel)
async def handle_interrupt(
    request: VoiceInterruptRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Handle voice interruption during agent speech.
    
    Called when user speaks while the agent is still speaking.
    Checks for intent words (stop, pause, etc.) to interrupt,
    or backchannel words (okay, yeah, etc.) to acknowledge.
    
    Intent words: {AGENT_INTENT_WORDS}
    Backchannel words: {AGENT_BACKCHANNEL_WORDS}
    """
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")
    
    session = _get_session_or_403(db, request.sessionId, user["userId"])
    
    # Initialize voice state if needed
    session.setdefault("voiceState", {})
    
    # Create voice assistant agent
    agent = VoiceAssistantAgent(session)
    state = agent.get_state()
    
    # Quick check for interruption patterns
    text = request.text.strip().lower()
    
    if contains_intent_word(text):
        # Interrupt - stop speaking and switch to listening
        state_manager = VoiceStateManager(session)
        state_manager.interrupt()
        
        update_session(db, session)
        
        return VoiceAgentResponseModel(
            status="success",
            action=VoiceAction.STOP_SPEAKING,
            message="Interrupted - switching to listening mode",
            voice_response="I'm listening.",
            voice_state=_state_to_response(state_manager.state),
            metadata={
                "interrupted": True,
                "trigger_word": text
            },
            session=session,
        )
    
    if contains_backchannel_word(text):
        # Backchannel - acknowledge without interrupting
        return VoiceAgentResponseModel(
            status="success",
            action=VoiceAction.ACKNOWLEDGE,
            message="Backchannel detected - continuing",
            voice_response=None,  # Don't interrupt speech
            voice_state=_state_to_response(state),
            metadata={
                "backchannel": True,
                "word": text
            },
            session=session,
        )
    
    # Significant text - treat as potential interrupt
    if len(text) > 3:
        state_manager = VoiceStateManager(session)
        state_manager.interrupt()
        update_session(db, session)
        
        return VoiceAgentResponseModel(
            status="success",
            action=VoiceAction.STOP_SPEAKING,
            message="User input detected - stopping",
            voice_response="Go ahead.",
            voice_state=_state_to_response(state_manager.state),
            metadata={"user_input": text},
            session=session,
        )
    
    # Not an interrupt - continue
    return VoiceAgentResponseModel(
        status="success",
        action=VoiceAction.SPEAK,
        message="Continuing speech",
        voice_state=_state_to_response(state),
        session=session,
    )


# ===== CONFIRMATION HANDLING =====

@router.post("/confirm", response_model=VoiceAgentResponseModel)
async def handle_confirmation(
    request: VoiceConfirmRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Handle user confirmation or rejection of refined prompt.
    
    If confirmed=True, marks the prompt as ready for planning.
    If confirmed=False, resets to listening mode for modification.
    
    Does NOT auto-execute - the frontend must call /analyze
    with the refined prompt after confirmation.
    """
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")
    
    session = _get_session_or_403(db, request.sessionId, user["userId"])
    
    # Initialize voice state if needed
    session.setdefault("voiceState", {})
    state_manager = VoiceStateManager(session)
    state = state_manager.state
    
    if request.confirmed:
        # User confirmed - ready for planning
        confirmed_prompt = state_manager.confirm_prompt()
        
        # NOTE: Do NOT append to chat history here.
        # /analyze will append it when called, avoiding duplicate messages in chat.
        
        update_session(db, session)
        
        return VoiceAgentResponseModel(
            status="success",
            action=VoiceAction.FORWARD_TO_PLANNING,
            message="Prompt confirmed - ready for planning",
            voice_response="Great! Starting the analysis now.",
            refined_prompt=confirmed_prompt,
            ready_for_planning=True,
            should_reset=True,
            voice_state=_state_to_response(state_manager.state),
            metadata={
                "confirmed_prompt": confirmed_prompt,
                "next_step": "Call /analyze with the refined prompt"
            },
            session=session,
        )
    else:
        # User rejected - allow modification
        if request.additional_text:
            # Process additional text
            agent = VoiceAssistantAgent(session)
            response = await agent.process_text(request.additional_text, is_final=True)
            update_session(db, session)
            
            return _build_response(response, session, agent.get_state())
        else:
            # Just reset to listening
            state_manager.start_listening()
            update_session(db, session)
            
            return VoiceAgentResponseModel(
                status="success",
                action=VoiceAction.LISTEN,
                message="Ready for new input",
                voice_response="What would you like to change?",
                voice_state=_state_to_response(state_manager.state),
                session=session,
            )


# ===== STATE MANAGEMENT =====

@router.get("/state/{session_id}", response_model=VoiceAgentResponseModel)
async def get_voice_state(
    session_id: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Get current voice state for a session.
    
    Returns the full voice state including mode, transcripts,
    refined prompt, and conversation history.
    """
    session = _get_session_or_403(db, session_id, user["userId"])
    
    # Get or initialize voice state
    session.setdefault("voiceState", {})
    state_manager = VoiceStateManager(session)
    
    return VoiceAgentResponseModel(
        status="success",
        action=VoiceAction.LISTEN if state_manager.is_active() else VoiceAction.RESET,
        message="Current voice state",
        voice_state=_state_to_response(state_manager.state),
        refined_prompt=state_manager.state.refined_prompt or None,
        ready_for_planning=state_manager.state.prompt_confirmed,
        session=session,
    )


@router.post("/reset", response_model=VoiceAgentResponseModel)
async def reset_voice_state(
    request: VoiceResetRequest,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Reset voice state for a session.
    
    Called after planning/execution completes to reset the voice
    assistant for the next interaction. Also clears any partial
    transcripts, refined prompts, and conversation context.
    """
    if not request.sessionId:
        raise HTTPException(400, "sessionId is required")
    
    session = _get_session_or_403(db, request.sessionId, user["userId"])
    
    # Reset voice state
    state_manager = VoiceStateManager(session)
    state_manager.reset()
    
    update_session(db, session)
    
    return VoiceAgentResponseModel(
        status="success",
        action=VoiceAction.RESET,
        message="Voice state reset",
        voice_response="Ready for a new conversation.",
        voice_state=_state_to_response(state_manager.state),
        should_reset=True,
        session=session,
    )


# ===== SPEECH CONTROL =====

@router.post("/speaking-started")
async def mark_speaking_started(
    sessionId: str,
    response_text: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Mark that the agent has started speaking.
    Called by frontend when TTS begins.
    """
    session = _get_session_or_403(db, sessionId, user["userId"])
    
    session.setdefault("voiceState", {})
    state_manager = VoiceStateManager(session)
    state_manager.start_speaking(response_text)
    
    update_session(db, session)
    
    return {"status": "success", "message": "Speaking started"}


@router.post("/speaking-ended")
async def mark_speaking_ended(
    sessionId: str,
    db: DatabaseManager = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Mark that the agent has finished speaking.
    Called by frontend when TTS ends.
    """
    session = _get_session_or_403(db, sessionId, user["userId"])
    
    session.setdefault("voiceState", {})
    state_manager = VoiceStateManager(session)
    state_manager.start_listening()
    
    update_session(db, session)
    
    return {"status": "success", "message": "Speaking ended - listening"}


# ===== LEXICON INFO =====

@router.get("/lexicons")
async def get_lexicons():
    """
    Get the intent and backchannel word lexicons.
    
    Useful for frontend to display or use for client-side
    preliminary checking before sending to backend.
    """
    return {
        "intent_words": AGENT_INTENT_WORDS,
        "backchannel_words": AGENT_BACKCHANNEL_WORDS,
        "description": {
            "intent_words": "Words that trigger interruption - agent stops speaking and listens",
            "backchannel_words": "Words for acknowledgment - agent continues without interruption"
        }
    }

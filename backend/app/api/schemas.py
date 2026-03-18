from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
from enum import Enum


class VoiceMode(str, Enum):
    """Voice assistant mode states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    HOLDING = "holding"
    AWAITING_CONFIRMATION = "awaiting_confirmation"


class VoiceAction(str, Enum):
    """Voice assistant actions."""
    LISTEN = "listen"
    SPEAK = "speak"
    STOP_SPEAKING = "stop_speaking"
    ASK_CLARIFICATION = "ask_clarification"
    CONFIRM_PROMPT = "confirm_prompt"
    FORWARD_TO_PLANNING = "forward_to_planning"
    ACKNOWLEDGE = "acknowledge"
    RESET = "reset"
    ERROR = "error"


class Message(BaseModel):
    """Individual message in a chat session"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    type: str = "text"  # 'text' | 'greeting' | 'rejection' | 'agent-complete' | 'voice-transcription' | 'voice-response'
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    """
    Complete chat session document.
    For now, most logic lives inside this object.
    """
    sessionId: str = Field(default_factory=lambda: str(uuid4()))
    title: str = "New Analysis"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    # Full conversation
    chatHistory: List[Message] = Field(default_factory=list)

    # All agent outputs (keyed by agent name)
    agentsData: Dict[str, Any] = Field(default_factory=dict)

    # Unified orchestration / state blob (will evolve later)
    sessionState: Dict[str, Any] = Field(default_factory=dict)

    # Quick counter
    messageCount: int = 0


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Analysis"


class SessionRenameRequest(BaseModel):
    title: str


class AnalysisRequest(BaseModel):
    sessionId: str
    prompt: str


# ===== VOICE ASSISTANT SCHEMAS =====

class VoiceTextRequest(BaseModel):
    """Request for voice text processing (transcribed text input)."""
    sessionId: str
    text: str
    is_final: bool = True  # Whether this is final transcription (not interim)


class VoiceAudioRequest(BaseModel):
    """Request for voice audio processing (raw audio input)."""
    sessionId: str
    audio_base64: str  # Base64-encoded audio data
    audio_format: str = "webm"  # Audio format (webm, wav, mp3, etc.)
    language: str = "en"  # Language code


class VoiceInterruptRequest(BaseModel):
    """Request to handle voice interruption during agent speech."""
    sessionId: str
    text: str  # Transcribed text during interruption


class VoiceConfirmRequest(BaseModel):
    """Request to confirm or reject refined prompt."""
    sessionId: str
    confirmed: bool
    additional_text: Optional[str] = None  # Additional input if rejecting


class VoiceStateResponse(BaseModel):
    """Response containing current voice state."""
    mode: VoiceMode
    is_speaking: bool = False
    was_interrupted: bool = False
    partial_transcript: Optional[str] = ""
    original_prompt: Optional[str] = ""
    refined_prompt: Optional[str] = ""
    prompt_confirmed: bool = False
    clarifying_questions: List[str] = Field(default_factory=list)


class VoiceAgentResponseModel(BaseModel):
    """Response from voice assistant agent."""
    status: str  # 'success' | 'error'
    action: VoiceAction
    message: str
    voice_response: Optional[str] = None  # Text for TTS
    refined_prompt: Optional[str] = None
    ready_for_planning: bool = False
    should_reset: bool = False
    voice_state: Optional[VoiceStateResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    session: Optional[Dict[str, Any]] = None


class VoiceResetRequest(BaseModel):
    """Request to reset voice state."""
    sessionId: str



# ===== COMMENTED OUT (FOR LATER PHASE) =====

"""
class WorkflowState(BaseModel):
    activeAgent: Optional[str] = None
    showAgentDataByAgent: Dict[str, bool] = Field(default_factory=dict)
    reportReady: bool = False
    workflowComplete: bool = False
    queryRejected: bool = False
    systemResponse: Optional[str] = None
    panelCollapsed: bool = False
    showAgentFlow: bool = False
    drugName: Optional[str] = None
    indication: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    agentsData: Optional[Dict[str, Any]] = None
    workflowState: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    sessionId: str
    title: str
    createdAt: datetime
    updatedAt: datetime
    messageCount: int
    agentsData: Dict[str, Any] = Field(default_factory=dict)
    chatHistory: List[Message] = Field(default_factory=list)
    workflowState: WorkflowState


class SessionListItem(BaseModel):
    sessionId: str
    title: str
    createdAt: datetime
    updatedAt: datetime
    messageCount: int
"""

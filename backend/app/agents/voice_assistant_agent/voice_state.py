"""
Voice State Management for Voice Assistant Agent

Manages transient voice state in session["voiceState"], tracking:
- Speaking/listening mode
- Interruption status
- Partial transcripts
- Conversation context
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class VoiceMode(str, Enum):
    """Current mode of the voice assistant."""
    IDLE = "idle"               # Not active
    LISTENING = "listening"     # Actively listening to user
    PROCESSING = "processing"   # Processing speech/transcript
    SPEAKING = "speaking"       # Agent is speaking response
    INTERRUPTED = "interrupted" # Agent was interrupted mid-speech
    HOLDING = "holding"         # Holding partial transcript awaiting more
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Waiting for user to confirm refined prompt


@dataclass
class VoiceState:
    """
    Voice state container stored in session["voiceState"].
    Tracks all transient voice interaction state.
    """
    # Current operational mode
    mode: VoiceMode = VoiceMode.IDLE
    
    # Whether the agent is currently speaking
    is_speaking: bool = False
    
    # Whether the agent was interrupted
    was_interrupted: bool = False
    
    # Partial transcript being accumulated
    partial_transcript: str = ""
    
    # Finalized transcript ready for processing
    finalized_transcript: str = ""
    
    # Original user prompt (before refinement)
    original_prompt: str = ""
    
    # Refined prompt (after LLM processing)
    refined_prompt: str = ""
    
    # Whether user has confirmed the refined prompt
    prompt_confirmed: bool = False
    
    # Agent's current/last response text
    current_response: str = ""
    
    # Point at which agent was interrupted (for resumption)
    interruption_point: int = 0
    
    # Clarifying questions asked by agent
    clarifying_questions: List[str] = field(default_factory=list)
    
    # User responses to clarifying questions
    clarifying_responses: List[str] = field(default_factory=list)
    
    # Conversation turns within voice session
    voice_turns: List[Dict[str, str]] = field(default_factory=list)
    
    # Timestamp of last activity
    last_activity: str = ""
    
    # Error message if any
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for session storage."""
        data = asdict(self)
        data["mode"] = self.mode.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceState":
        """Create from dictionary (from session storage)."""
        if not data:
            return cls()
        
        data = data.copy()
        if "mode" in data:
            data["mode"] = VoiceMode(data["mode"])
        
        # Handle fields that might not exist in older data
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


class VoiceStateManager:
    """
    Manages voice state within a session.
    All state is transient and resets after planning/execution.
    """
    
    def __init__(self, session: Dict[str, Any]):
        """Initialize with session dictionary."""
        self.session = session
        self._ensure_voice_state()
    
    def _ensure_voice_state(self):
        """Ensure voiceState exists in session."""
        if "voiceState" not in self.session:
            self.session["voiceState"] = VoiceState().to_dict()
    
    @property
    def state(self) -> VoiceState:
        """Get current voice state."""
        return VoiceState.from_dict(self.session.get("voiceState", {}))
    
    def save_state(self, state: VoiceState):
        """Save voice state to session."""
        state.last_activity = datetime.utcnow().isoformat()
        self.session["voiceState"] = state.to_dict()
    
    def get_mode(self) -> VoiceMode:
        """Get current voice mode."""
        return self.state.mode
    
    def set_mode(self, mode: VoiceMode):
        """Set voice mode."""
        state = self.state
        state.mode = mode
        
        # Update related flags
        if mode == VoiceMode.SPEAKING:
            state.is_speaking = True
        elif mode in [VoiceMode.LISTENING, VoiceMode.IDLE]:
            state.is_speaking = False
        
        self.save_state(state)
    
    def start_listening(self):
        """Transition to listening mode."""
        state = self.state
        state.mode = VoiceMode.LISTENING
        state.is_speaking = False
        state.was_interrupted = False
        self.save_state(state)
    
    def start_speaking(self, response: str):
        """Transition to speaking mode with response."""
        state = self.state
        state.mode = VoiceMode.SPEAKING
        state.is_speaking = True
        state.current_response = response
        state.interruption_point = 0
        self.save_state(state)
    
    def interrupt(self, at_position: int = 0):
        """Mark agent as interrupted."""
        state = self.state
        state.mode = VoiceMode.INTERRUPTED
        state.is_speaking = False
        state.was_interrupted = True
        state.interruption_point = at_position
        self.save_state(state)
        
        # Immediately switch to listening
        self.start_listening()
    
    def hold_partial_transcript(self, partial: str):
        """Store partial transcript while awaiting more input."""
        state = self.state
        state.mode = VoiceMode.HOLDING
        state.partial_transcript = partial
        self.save_state(state)
    
    def append_partial_transcript(self, text: str):
        """Append to existing partial transcript."""
        state = self.state
        state.partial_transcript = (state.partial_transcript + " " + text).strip()
        self.save_state(state)
    
    def finalize_transcript(self) -> str:
        """Finalize partial transcript and return full transcript."""
        state = self.state
        state.finalized_transcript = state.partial_transcript.strip()
        state.partial_transcript = ""
        state.mode = VoiceMode.PROCESSING
        self.save_state(state)
        return state.finalized_transcript
    
    def set_original_prompt(self, prompt: str):
        """Store original user prompt before refinement."""
        state = self.state
        state.original_prompt = prompt
        self.save_state(state)
    
    def set_refined_prompt(self, refined: str):
        """Store refined prompt after LLM processing."""
        state = self.state
        state.refined_prompt = refined
        state.mode = VoiceMode.AWAITING_CONFIRMATION
        self.save_state(state)
    
    def confirm_prompt(self) -> str:
        """Mark prompt as confirmed and return it."""
        state = self.state
        state.prompt_confirmed = True
        self.save_state(state)
        return state.refined_prompt or state.original_prompt
    
    def add_clarifying_question(self, question: str):
        """Add a clarifying question asked by agent."""
        state = self.state
        state.clarifying_questions.append(question)
        self.save_state(state)
    
    def add_clarifying_response(self, response: str):
        """Add user response to clarifying question."""
        state = self.state
        state.clarifying_responses.append(response)
        self.save_state(state)
    
    def add_voice_turn(self, role: str, content: str):
        """Add a turn to voice conversation history."""
        state = self.state
        state.voice_turns.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save_state(state)
    
    def get_voice_context(self) -> str:
        """Get accumulated voice context as string."""
        state = self.state
        context_parts = []
        
        if state.original_prompt:
            context_parts.append(f"Original: {state.original_prompt}")
        
        for i, (q, r) in enumerate(zip(state.clarifying_questions, state.clarifying_responses)):
            context_parts.append(f"Q{i+1}: {q}")
            context_parts.append(f"A{i+1}: {r}")
        
        return "\n".join(context_parts)
    
    def append_to_chat_history(self, content: str, role: str = "user"):
        """Append finalized content to session chatHistory."""
        if "chatHistory" not in self.session:
            self.session["chatHistory"] = []
        
        self.session["chatHistory"].append({
            "role": role,
            "content": content,
            "type": "voice-transcription" if role == "user" else "voice-response",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def reset(self):
        """Reset voice state completely (after planning/execution)."""
        self.session["voiceState"] = VoiceState().to_dict()
    
    def set_error(self, error: str):
        """Set error message in state."""
        state = self.state
        state.error = error
        self.save_state(state)
    
    def clear_error(self):
        """Clear error message."""
        state = self.state
        state.error = None
        self.save_state(state)
    
    def is_active(self) -> bool:
        """Check if voice session is active."""
        return self.state.mode not in [VoiceMode.IDLE]
    
    def needs_confirmation(self) -> bool:
        """Check if awaiting prompt confirmation."""
        return self.state.mode == VoiceMode.AWAITING_CONFIRMATION

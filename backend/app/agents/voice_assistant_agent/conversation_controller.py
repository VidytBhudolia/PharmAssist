"""
Conversation Controller for Voice Assistant Agent

Handles conversation flow control including:
- Intent word detection (interruption)
- Backchannel word detection (acknowledgment)
- Conversation state management
- Response flow control
"""

from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .lexicons import (
    contains_intent_word,
    contains_backchannel_word,
    is_confirmation,
    is_rejection,
    AGENT_INTENT_WORDS,
    AGENT_BACKCHANNEL_WORDS
)
from .voice_state import VoiceStateManager, VoiceMode


class ConversationSignal(str, Enum):
    """Signals detected from user input."""
    CONTINUE = "continue"           # Normal input, continue conversation
    INTERRUPT = "interrupt"         # User wants to interrupt agent
    BACKCHANNEL = "backchannel"     # User acknowledging, don't interrupt
    CONFIRM = "confirm"             # User confirms prompt
    REJECT = "reject"               # User rejects/wants to modify
    COMPLETE = "complete"           # Input is complete, ready to process
    PARTIAL = "partial"             # Partial input, wait for more
    ERROR = "error"                 # Error in processing


@dataclass
class ConversationResponse:
    """Response from conversation controller."""
    signal: ConversationSignal
    message: str
    should_stop_speaking: bool = False
    should_acknowledge: bool = False
    acknowledgment_text: Optional[str] = None
    processed_text: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConversationController:
    """
    Controls conversation flow for voice assistant.
    
    Responsibilities:
    - Detect user intent from transcribed text
    - Manage interruption and backchannel signals
    - Control when agent should stop speaking
    - Determine if input is complete or partial
    """
    
    # Minimum text length to consider as meaningful input
    MIN_MEANINGFUL_LENGTH = 3
    
    # Note: We no longer use hardcoded acknowledgments
    # The LLM generates all responses for a more natural conversation
    
    def __init__(self, state_manager: VoiceStateManager):
        """
        Initialize controller with state manager.
        
        Args:
            state_manager: Voice state manager for the session
        """
        self.state_manager = state_manager
    
    def process_input(
        self,
        text: str,
        is_final: bool = True
    ) -> ConversationResponse:
        """
        Process user input and determine appropriate response.
        
        Args:
            text: Transcribed text from user
            is_final: Whether this is the final transcription (not partial)
            
        Returns:
            ConversationResponse with signal and actions
        """
        if not text or not text.strip():
            return ConversationResponse(
                signal=ConversationSignal.PARTIAL,
                message="Waiting for input...",
                processed_text=""
            )
        
        text = text.strip()
        current_mode = self.state_manager.get_mode()
        
        # Check for intent words (interruption) - highest priority
        if contains_intent_word(text):
            return self._handle_interrupt(text)
        
        # Check for backchannel words
        if contains_backchannel_word(text):
            return self._handle_backchannel(text)
        
        # Check if awaiting confirmation
        if current_mode == VoiceMode.AWAITING_CONFIRMATION:
            if is_confirmation(text):
                return self._handle_confirmation(text)
            elif is_rejection(text):
                return self._handle_rejection(text)
            else:
                # Treat as additional input/clarification
                return self._handle_additional_input(text, is_final)
        
        # Normal input processing
        if is_final:
            return self._handle_complete_input(text)
        else:
            return self._handle_partial_input(text)
    
    def _handle_interrupt(self, text: str) -> ConversationResponse:
        """Handle user interrupt signal."""
        # Mark as interrupted in state
        self.state_manager.interrupt()
        
        return ConversationResponse(
            signal=ConversationSignal.INTERRUPT,
            message="I'll stop and listen. What would you like to say?",
            should_stop_speaking=True,
            should_acknowledge=True,
            acknowledgment_text="I'm listening.",
            processed_text=text,
            metadata={"interrupted_at": self.state_manager.state.interruption_point}
        )
    
    def _handle_backchannel(self, text: str) -> ConversationResponse:
        """Handle backchannel acknowledgment from user."""
        # Pass through as complete input so LLM can respond naturally
        # No hardcoded acknowledgments - let LLM generate response
        return ConversationResponse(
            signal=ConversationSignal.COMPLETE,
            message="Processing backchannel as input",
            should_stop_speaking=False,
            processed_text=text,
            metadata={"backchannel_word": text, "is_backchannel": True}
        )
    
    def _handle_confirmation(self, text: str) -> ConversationResponse:
        """Handle user confirmation of refined prompt."""
        confirmed_prompt = self.state_manager.confirm_prompt()
        
        return ConversationResponse(
            signal=ConversationSignal.CONFIRM,
            message="Great! Proceeding with your request.",
            should_stop_speaking=True,
            processed_text=confirmed_prompt,
            metadata={
                "confirmation_text": text,
                "confirmed_prompt": confirmed_prompt
            }
        )
    
    def _handle_rejection(self, text: str) -> ConversationResponse:
        """Handle user rejection/modification request."""
        # Reset to listening mode for new input
        self.state_manager.start_listening()
        
        return ConversationResponse(
            signal=ConversationSignal.REJECT,
            message="No problem. What would you like to change?",
            should_stop_speaking=True,
            processed_text=text,
            metadata={"rejection_text": text}
        )
    
    def _handle_complete_input(self, text: str) -> ConversationResponse:
        """Handle complete (final) user input."""
        # Store as finalized transcript
        self.state_manager.set_original_prompt(text)
        self.state_manager.add_voice_turn("user", text)
        
        return ConversationResponse(
            signal=ConversationSignal.COMPLETE,
            message="I understood your request.",
            should_stop_speaking=True,
            processed_text=text,
            metadata={"input_length": len(text)}
        )
    
    def _handle_partial_input(self, text: str) -> ConversationResponse:
        """Handle partial (interim) user input."""
        self.state_manager.hold_partial_transcript(text)
        
        return ConversationResponse(
            signal=ConversationSignal.PARTIAL,
            message="Still listening...",
            should_stop_speaking=False,
            processed_text=text,
            metadata={"is_partial": True}
        )
    
    def _handle_additional_input(
        self,
        text: str,
        is_final: bool
    ) -> ConversationResponse:
        """Handle additional input when awaiting confirmation."""
        # User is providing more context instead of confirming
        self.state_manager.add_clarifying_response(text)
        
        return ConversationResponse(
            signal=ConversationSignal.CONTINUE,
            message="I see, let me incorporate that.",
            should_stop_speaking=True,
            processed_text=text,
            metadata={
                "additional_context": True,
                "is_final": is_final
            }
        )
    
    def check_for_interrupt_during_speech(
        self,
        text: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user input during agent speech is an interrupt signal.
        
        Args:
            text: Real-time transcribed text during agent speech
            
        Returns:
            Tuple of (should_interrupt, acknowledgment_if_backchannel)
        """
        if contains_intent_word(text):
            self.state_manager.interrupt()
            return (True, None)
        
        if contains_backchannel_word(text):
            # No hardcoded acknowledgment - return None
            return (False, None)
        
        # Any other significant text during speech might be interrupt
        if len(text.strip()) > self.MIN_MEANINGFUL_LENGTH:
            # User is trying to say something meaningful
            self.state_manager.interrupt()
            return (True, None)
        
        return (False, None)
    
    def should_ask_clarification(self, text: str) -> bool:
        """
        Determine if clarification is needed based on input.
        
        Returns True if input is too vague or ambiguous.
        """
        # Very short inputs might need clarification
        if len(text.strip()) < 10:
            return True
        
        # Check for question indicators
        question_words = ["what", "which", "how", "when", "where", "who", "why"]
        has_question = any(
            text.lower().strip().startswith(w) 
            for w in question_words
        )
        
        # Questions from user shouldn't trigger clarification
        if has_question:
            return False
        
        return False
    
    def get_clarification_question(self, context: str) -> Optional[str]:
        """
        Generate a minimal clarifying question based on context.
        
        Returns None if no clarification needed.
        """
        # This is a simple implementation
        # In practice, this would use LLM to generate smart questions
        if not context or len(context) < 10:
            return "Could you tell me more about what you'd like to analyze?"
        
        return None


class InterruptionHandler:
    """
    Handles interruption logic during agent speech.
    
    Monitors for intent words and manages speech interruption.
    """
    
    def __init__(self, state_manager: VoiceStateManager):
        """Initialize with state manager."""
        self.state_manager = state_manager
        self.speech_position = 0
        self.total_speech_length = 0
    
    def start_speech(self, response_text: str):
        """Mark start of agent speech."""
        self.state_manager.start_speaking(response_text)
        self.speech_position = 0
        self.total_speech_length = len(response_text)
    
    def update_position(self, position: int):
        """Update current speech position."""
        self.speech_position = position
    
    def check_interrupt(self, user_input: str) -> bool:
        """
        Check if user input during speech is an interrupt.
        
        Returns True if should interrupt.
        """
        if contains_intent_word(user_input):
            self.state_manager.interrupt(self.speech_position)
            return True
        
        return False
    
    def get_remaining_response(self) -> str:
        """Get the remaining unspoken portion of response."""
        state = self.state_manager.state
        if state.current_response and state.interruption_point > 0:
            return state.current_response[state.interruption_point:]
        return ""
    
    def end_speech(self):
        """Mark end of agent speech."""
        self.state_manager.start_listening()

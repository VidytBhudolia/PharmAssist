"""
Voice Assistant Agent for PharmAssist

Main agent class that orchestrates voice input processing,
conversation control, and prompt refinement before the planning pipeline.
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .voice_state import VoiceStateManager, VoiceMode, VoiceState
from .conversation_controller import (
    ConversationController,
    ConversationSignal,
    ConversationResponse,
    InterruptionHandler
)
from .prompt_refiner import PromptRefiner, RefinementResult, get_prompt_refiner
from .speech_to_text import (
    SpeechToTextService,
    TranscriptionResult,
    get_stt_service
)
from .lexicons import (
    contains_intent_word,
    contains_backchannel_word,
    is_confirmation,
    AGENT_INTENT_WORDS,
    AGENT_BACKCHANNEL_WORDS
)


class VoiceAgentAction(str, Enum):
    """Actions the voice agent can take."""
    LISTEN = "listen"                       # Continue listening
    SPEAK = "speak"                         # Agent speaks response
    STOP_SPEAKING = "stop_speaking"         # Stop current speech
    ASK_CLARIFICATION = "ask_clarification" # Ask clarifying question
    CONFIRM_PROMPT = "confirm_prompt"       # Ask user to confirm prompt
    FORWARD_TO_PLANNING = "forward_to_planning"  # Send to planning pipeline
    ACKNOWLEDGE = "acknowledge"             # Brief acknowledgment
    RESET = "reset"                         # Reset voice state
    ERROR = "error"                         # Error occurred


@dataclass
class VoiceAgentResponse:
    """Response from the voice assistant agent."""
    action: VoiceAgentAction
    message: str
    voice_response: Optional[str] = None  # Text for TTS
    refined_prompt: Optional[str] = None
    ready_for_planning: bool = False
    should_reset: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VoiceAssistantAgent:
    """
    Voice Assistant Agent for PharmAssist.
    
    Handles:
    - Voice input processing and transcription
    - Conversational assistance with interruption support
    - Prompt refinement using LLM
    - Integration with the /analyze pipeline
    
    Strictly scoped to /analyze route only.
    Does not affect /execute or report generation.
    """
    
    def __init__(
        self,
        session: Dict[str, Any],
        stt_service: Optional[SpeechToTextService] = None,
        prompt_refiner: Optional[PromptRefiner] = None
    ):
        """
        Initialize the Voice Assistant Agent.
        
        Args:
            session: Session dictionary (must include voiceState)
            stt_service: Speech-to-text service (optional, uses default)
            prompt_refiner: Prompt refiner (optional, uses default)
        """
        self.session = session
        self.state_manager = VoiceStateManager(session)
        self.conversation_controller = ConversationController(self.state_manager)
        self.interruption_handler = InterruptionHandler(self.state_manager)
        
        self.stt_service = stt_service or get_stt_service()
        self.prompt_refiner = prompt_refiner or get_prompt_refiner()
    
    async def process_audio(
        self,
        audio_data: bytes,
        audio_format: str = "webm",
        language: str = "en"
    ) -> VoiceAgentResponse:
        """
        Process audio input from user.
        
        This is the main entry point for voice input.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, etc.)
            language: Language code
            
        Returns:
            VoiceAgentResponse with next action and response
        """
        # Transcribe audio
        transcription = await self.stt_service.transcribe(
            audio_data,
            audio_format,
            language
        )
        
        if not transcription.success:
            return VoiceAgentResponse(
                action=VoiceAgentAction.ERROR,
                message=f"Transcription failed: {transcription.error}",
                voice_response="I couldn't understand that. Could you please try again?",
                metadata={"error": transcription.error}
            )
        
        # Process the transcribed text
        return await self.process_text(
            transcription.text,
            is_final=not transcription.is_partial
        )
    
    async def process_text(
        self,
        text: str,
        is_final: bool = True
    ) -> VoiceAgentResponse:
        """
        Process transcribed text input.
        
        Can be called directly for text input or after transcription.
        
        Args:
            text: Input text (transcribed or direct)
            is_final: Whether this is final (not partial/interim)
            
        Returns:
            VoiceAgentResponse with next action
        """
        current_mode = self.state_manager.get_mode()
        
        # Check for interruption during agent speech
        if current_mode == VoiceMode.SPEAKING:
            return self._handle_input_during_speech(text)
        
        # Process through conversation controller
        conv_response = self.conversation_controller.process_input(text, is_final)
        
        # Handle based on signal
        return await self._handle_conversation_signal(conv_response)
    
    def _handle_input_during_speech(self, text: str) -> VoiceAgentResponse:
        """Handle user input while agent is speaking."""
        
        # Check for intent words (interruption)
        if contains_intent_word(text):
            self.interruption_handler.check_interrupt(text)
            
            return VoiceAgentResponse(
                action=VoiceAgentAction.STOP_SPEAKING,
                message="Interrupted - switching to listening mode",
                voice_response="I'm listening.",
                metadata={
                    "interrupted": True,
                    "remaining_response": self.interruption_handler.get_remaining_response()
                }
            )
        
        # Check for backchannel (acknowledgment without interruption)
        if contains_backchannel_word(text):
            return VoiceAgentResponse(
                action=VoiceAgentAction.ACKNOWLEDGE,
                message="Backchannel detected - continuing speech",
                voice_response=None,  # Don't interrupt with response
                metadata={"backchannel": text}
            )
        
        # Significant input during speech - might be interrupt
        if len(text.strip()) > 3:
            self.interruption_handler.check_interrupt(text)
            return VoiceAgentResponse(
                action=VoiceAgentAction.STOP_SPEAKING,
                message="User input detected - stopping to listen",
                voice_response="Go ahead.",
                metadata={"user_input": text}
            )
        
        # Continue speaking
        return VoiceAgentResponse(
            action=VoiceAgentAction.SPEAK,
            message="Continuing current response",
            voice_response=None
        )
    
    async def _handle_conversation_signal(
        self,
        conv_response: ConversationResponse
    ) -> VoiceAgentResponse:
        """Handle conversation controller signal."""
        
        signal = conv_response.signal
        
        if signal == ConversationSignal.INTERRUPT:
            return VoiceAgentResponse(
                action=VoiceAgentAction.STOP_SPEAKING,
                message="User interrupted",
                voice_response=conv_response.acknowledgment_text or "I'm listening."
            )
        
        if signal == ConversationSignal.BACKCHANNEL:
            return VoiceAgentResponse(
                action=VoiceAgentAction.ACKNOWLEDGE,
                message="Backchannel acknowledged",
                voice_response=conv_response.acknowledgment_text
            )
        
        if signal == ConversationSignal.CONFIRM:
            # User confirmed - forward to planning
            return VoiceAgentResponse(
                action=VoiceAgentAction.FORWARD_TO_PLANNING,
                message="Prompt confirmed - forwarding to planning",
                voice_response="Great! Starting the analysis now.",
                refined_prompt=conv_response.processed_text,
                ready_for_planning=True,
                should_reset=True  # Reset after forwarding
            )
        
        if signal == ConversationSignal.REJECT:
            # User rejected - ask for new input
            self.state_manager.start_listening()
            return VoiceAgentResponse(
                action=VoiceAgentAction.LISTEN,
                message="User wants to modify - listening for changes",
                voice_response="No problem. What would you like to change?"
            )
        
        if signal == ConversationSignal.PARTIAL:
            # Partial input - continue listening
            return VoiceAgentResponse(
                action=VoiceAgentAction.LISTEN,
                message="Partial input - waiting for more",
                voice_response=None
            )
        
        if signal == ConversationSignal.COMPLETE:
            # Complete input - process through refiner
            return await self._refine_and_respond(conv_response.processed_text)
        
        if signal == ConversationSignal.CONTINUE:
            # Additional context provided - re-refine
            context = self.state_manager.get_voice_context()
            return await self._refine_and_respond(
                conv_response.processed_text,
                context
            )
        
        # Default - listen
        return VoiceAgentResponse(
            action=VoiceAgentAction.LISTEN,
            message="Ready to listen",
            voice_response=None
        )
    
    async def _refine_and_respond(
        self,
        text: str,
        context: Optional[str] = None
    ) -> VoiceAgentResponse:
        """
        Refine the prompt and determine next action.
        """
        # Get voice context if not provided
        if not context:
            context = self.state_manager.get_voice_context()
            if not context:
                context = None
        
        # Refine the prompt
        refinement = await self.prompt_refiner.refine(text, context)
        
        if not refinement.success:
            return VoiceAgentResponse(
                action=VoiceAgentAction.SPEAK,
                message="Refinement failed - asking to repeat",
                voice_response=refinement.voice_response,
                metadata={"error": refinement.error}
            )
        
        # Store the refined prompt
        self.state_manager.set_original_prompt(text)
        self.state_manager.set_refined_prompt(refinement.refined_prompt)
        
        # Add to voice conversation
        self.state_manager.add_voice_turn("user", text)
        self.state_manager.add_voice_turn("assistant", refinement.voice_response)
        
        # Check if clarification needed
        if refinement.needs_clarification and refinement.clarifying_questions:
            # Store clarifying questions
            for q in refinement.clarifying_questions:
                self.state_manager.add_clarifying_question(q)
            
            return VoiceAgentResponse(
                action=VoiceAgentAction.ASK_CLARIFICATION,
                message="Needs clarification",
                voice_response=refinement.voice_response,
                metadata={
                    "questions": refinement.clarifying_questions,
                    "drug": refinement.drug,
                    "indication": refinement.indication
                }
            )
        
        # Check if ready for planning (has drug + indication)
        if refinement.ready_for_planning:
            # Ask for confirmation before proceeding
            confirmation_response = self.prompt_refiner.generate_confirmation_prompt(
                refinement.drug or "the drug",
                refinement.indication or "the condition",
                refinement.analysis_type
            )
            
            return VoiceAgentResponse(
                action=VoiceAgentAction.CONFIRM_PROMPT,
                message="Ready for planning - awaiting confirmation",
                voice_response=refinement.voice_response,
                refined_prompt=refinement.refined_prompt,
                metadata={
                    "drug": refinement.drug,
                    "indication": refinement.indication,
                    "analysis_type": refinement.analysis_type,
                    "confirmation_prompt": confirmation_response
                }
            )
        
        # Not enough info yet - respond and listen
        return VoiceAgentResponse(
            action=VoiceAgentAction.SPEAK,
            message="Processed - responding to user",
            voice_response=refinement.voice_response,
            refined_prompt=refinement.refined_prompt,
            metadata={
                "drug": refinement.drug,
                "indication": refinement.indication
            }
        )
    
    def start_speaking(self, response: str):
        """
        Mark that agent has started speaking a response.
        Call this when TTS begins.
        """
        self.interruption_handler.start_speech(response)
    
    def update_speech_position(self, position: int):
        """
        Update current speech position (for resumption after interrupt).
        """
        self.interruption_handler.update_position(position)
    
    def end_speaking(self):
        """
        Mark that agent has finished speaking.
        Call this when TTS ends.
        """
        self.interruption_handler.end_speech()
    
    def reset(self):
        """
        Reset voice assistant state.
        Called after planning/execution completes.
        """
        self.state_manager.reset()
    
    def get_state(self) -> VoiceState:
        """Get current voice state."""
        return self.state_manager.state
    
    def is_active(self) -> bool:
        """Check if voice session is active."""
        return self.state_manager.is_active()
    
    def needs_confirmation(self) -> bool:
        """Check if waiting for user confirmation."""
        return self.state_manager.needs_confirmation()
    
    def get_refined_prompt(self) -> Optional[str]:
        """Get the current refined prompt (if any)."""
        state = self.state_manager.state
        return state.refined_prompt or state.original_prompt or None
    
    def append_to_chat_history(self):
        """
        Append finalized voice transcription to session chatHistory.
        Called when voice session completes and forwards to planning.
        """
        state = self.state_manager.state
        if state.refined_prompt:
            self.state_manager.append_to_chat_history(
                state.refined_prompt,
                role="user"
            )


def run_voice_assistant(
    session: Dict[str, Any],
    text: str,
    is_final: bool = True
) -> VoiceAgentResponse:
    """
    Convenience function to run voice assistant on text input.
    
    Synchronous wrapper for common use case.
    
    Args:
        session: Session dictionary
        text: Input text (transcribed or direct)
        is_final: Whether this is final transcription
        
    Returns:
        VoiceAgentResponse
    """
    import asyncio
    
    agent = VoiceAssistantAgent(session)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(agent.process_text(text, is_final))


async def run_voice_assistant_async(
    session: Dict[str, Any],
    text: str,
    is_final: bool = True
) -> VoiceAgentResponse:
    """
    Async function to run voice assistant on text input.
    
    Args:
        session: Session dictionary
        text: Input text (transcribed or direct)
        is_final: Whether this is final transcription
        
    Returns:
        VoiceAgentResponse
    """
    agent = VoiceAssistantAgent(session)
    return await agent.process_text(text, is_final)

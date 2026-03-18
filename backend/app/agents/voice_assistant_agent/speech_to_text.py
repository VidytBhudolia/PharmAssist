"""
Speech-to-Text Service for Voice Assistant Agent

Handles audio transcription using various providers:
- OpenAI Whisper API (primary)
- Google Speech-to-Text (fallback)
- Local Whisper model (offline option)
"""

import os
import io
import base64
import tempfile
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import audio processing libraries
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class STTProvider(str, Enum):
    """Speech-to-text provider options."""
    OPENAI_WHISPER = "openai_whisper"
    GOOGLE = "google"
    SPHINX = "sphinx"  # Offline
    MOCK = "mock"      # For testing


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    success: bool
    text: str
    confidence: float
    language: Optional[str] = None
    duration: Optional[float] = None
    provider: Optional[str] = None
    is_partial: bool = False
    error: Optional[str] = None


class SpeechToTextService:
    """
    Service for converting speech audio to text.
    Supports multiple providers with fallback.
    """
    
    def __init__(
        self,
        primary_provider: STTProvider = STTProvider.OPENAI_WHISPER,
        fallback_provider: Optional[STTProvider] = STTProvider.GOOGLE,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize STT service.
        
        Args:
            primary_provider: Primary transcription provider
            fallback_provider: Fallback if primary fails
            openai_api_key: OpenAI API key for Whisper
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        # Initialize speech recognition if available
        self.recognizer = None
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
    
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "webm",
        language: str = "en"
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            language: Expected language code
            
        Returns:
            TranscriptionResult with transcribed text
        """
        # Try primary provider
        result = await self._transcribe_with_provider(
            self.primary_provider,
            audio_data,
            audio_format,
            language
        )
        
        # Fallback if primary fails
        if not result.success and self.fallback_provider:
            result = await self._transcribe_with_provider(
                self.fallback_provider,
                audio_data,
                audio_format,
                language
            )
        
        return result
    
    async def transcribe_base64(
        self,
        base64_audio: str,
        audio_format: str = "webm",
        language: str = "en"
    ) -> TranscriptionResult:
        """
        Transcribe base64-encoded audio.
        
        Args:
            base64_audio: Base64-encoded audio string
            audio_format: Audio format
            language: Expected language code
            
        Returns:
            TranscriptionResult
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_audio:
                base64_audio = base64_audio.split(",")[1]
            
            audio_data = base64.b64decode(base64_audio)
            return await self.transcribe(audio_data, audio_format, language)
        except Exception as e:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"Failed to decode base64 audio: {str(e)}"
            )
    
    async def _transcribe_with_provider(
        self,
        provider: STTProvider,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> TranscriptionResult:
        """Transcribe using specific provider."""
        
        if provider == STTProvider.OPENAI_WHISPER:
            return await self._transcribe_openai(audio_data, audio_format, language)
        elif provider == STTProvider.GOOGLE:
            return await self._transcribe_google(audio_data, audio_format, language)
        elif provider == STTProvider.SPHINX:
            return await self._transcribe_sphinx(audio_data, audio_format, language)
        elif provider == STTProvider.MOCK:
            return self._transcribe_mock(audio_data)
        else:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"Unknown provider: {provider}"
            )
    
    async def _transcribe_openai(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> TranscriptionResult:
        """Transcribe using OpenAI Whisper API."""
        if not self.openai_client:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error="OpenAI client not available"
            )
        
        try:
            # Create temporary file with audio data
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Call Whisper API
                with open(tmp_path, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language if language != "auto" else None,
                        response_format="verbose_json"
                    )
                
                return TranscriptionResult(
                    success=True,
                    text=transcript.text,
                    confidence=0.95,  # Whisper doesn't provide confidence scores
                    language=transcript.language if hasattr(transcript, 'language') else language,
                    duration=transcript.duration if hasattr(transcript, 'duration') else None,
                    provider="openai_whisper"
                )
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                
        except Exception as e:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"OpenAI Whisper error: {str(e)}",
                provider="openai_whisper"
            )
    
    async def _transcribe_google(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> TranscriptionResult:
        """Transcribe using Google Speech Recognition (via SpeechRecognition library)."""
        if not self.recognizer:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error="SpeechRecognition library not available"
            )
        
        try:
            # Convert audio to AudioData format
            audio_source = sr.AudioFile(io.BytesIO(audio_data))
            
            with audio_source as source:
                audio = self.recognizer.record(source)
            
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(
                audio,
                language=language,
                show_all=False
            )
            
            return TranscriptionResult(
                success=True,
                text=text,
                confidence=0.85,
                language=language,
                provider="google"
            )
            
        except sr.UnknownValueError:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error="Speech not recognized",
                provider="google"
            )
        except sr.RequestError as e:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"Google API error: {str(e)}",
                provider="google"
            )
        except Exception as e:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"Google transcription error: {str(e)}",
                provider="google"
            )
    
    async def _transcribe_sphinx(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> TranscriptionResult:
        """Transcribe using CMU Sphinx (offline)."""
        if not self.recognizer:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error="SpeechRecognition library not available"
            )
        
        try:
            audio_source = sr.AudioFile(io.BytesIO(audio_data))
            
            with audio_source as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_sphinx(audio)
            
            return TranscriptionResult(
                success=True,
                text=text,
                confidence=0.7,  # Sphinx typically has lower accuracy
                language=language,
                provider="sphinx"
            )
            
        except sr.UnknownValueError:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error="Speech not recognized",
                provider="sphinx"
            )
        except Exception as e:
            return TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"Sphinx error: {str(e)}",
                provider="sphinx"
            )
    
    def _transcribe_mock(self, audio_data: bytes) -> TranscriptionResult:
        """Mock transcription for testing."""
        # Return a test transcription
        return TranscriptionResult(
            success=True,
            text="This is a mock transcription for testing purposes.",
            confidence=1.0,
            language="en",
            provider="mock"
        )


class StreamingSTTService:
    """
    Streaming speech-to-text service for real-time transcription.
    Provides partial results as user speaks.
    """
    
    def __init__(self, stt_service: SpeechToTextService):
        """Initialize with base STT service."""
        self.stt_service = stt_service
        self.buffer: bytes = b""
        self.partial_text: str = ""
    
    def add_audio_chunk(self, chunk: bytes):
        """Add audio chunk to buffer."""
        self.buffer += chunk
    
    async def get_partial_result(self) -> TranscriptionResult:
        """Get partial transcription of current buffer."""
        if not self.buffer:
            return TranscriptionResult(
                success=True,
                text="",
                confidence=0.0,
                is_partial=True
            )
        
        result = await self.stt_service.transcribe(self.buffer, "webm", "en")
        result.is_partial = True
        self.partial_text = result.text
        return result
    
    async def finalize(self) -> TranscriptionResult:
        """Finalize transcription and clear buffer."""
        if not self.buffer:
            return TranscriptionResult(
                success=True,
                text=self.partial_text,
                confidence=0.0,
                is_partial=False
            )
        
        result = await self.stt_service.transcribe(self.buffer, "webm", "en")
        result.is_partial = False
        
        # Clear buffer
        self.buffer = b""
        self.partial_text = ""
        
        return result
    
    def reset(self):
        """Reset the streaming service."""
        self.buffer = b""
        self.partial_text = ""


# Global singleton instance
_stt_service: Optional[SpeechToTextService] = None


def get_stt_service() -> SpeechToTextService:
    """Get or create the global STT service instance."""
    global _stt_service
    if _stt_service is None:
        _stt_service = SpeechToTextService()
    return _stt_service

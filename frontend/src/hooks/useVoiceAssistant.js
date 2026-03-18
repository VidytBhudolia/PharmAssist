import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../services/api";

/**
 * Voice modes
 */
export const VoiceMode = {
  IDLE: "idle",
  LISTENING: "listening",
  PROCESSING: "processing",
  SPEAKING: "speaking",
  AWAITING_CONFIRMATION: "awaiting_confirmation",
};

/**
 * Voice actions from backend
 */
export const VoiceAction = {
  LISTEN: "listen",
  SPEAK: "speak",
  STOP_SPEAKING: "stop_speaking",
  ASK_CLARIFICATION: "ask_clarification",
  CONFIRM_PROMPT: "confirm_prompt",
  FORWARD_TO_PLANNING: "forward_to_planning",
  ACKNOWLEDGE: "acknowledge",
  RESET: "reset",
  ERROR: "error",
};

/**
 * Words that stop TTS speaking (frontend only)
 */
const STOP_WORDS = [
  "stop", "wait", "pause", "hold", "enough", "cancel",
  "quit", "exit", "halt", "stop it"
];

const ASSISTANT_NAME = "Sage";

const isNameQuery = (text) => {
  const normalized = text.toLowerCase();
  return (
    normalized.includes("your name") ||
    normalized.includes("who are you") ||
    normalized.includes("what are you called") ||
    normalized.includes("what is your name")
  );
};

/**
 * Check if text contains a stop word
 */
const containsStopWord = (text) => {
  const normalized = text.toLowerCase().trim();
  const words = normalized.split(/\s+/);
  
  for (const word of words) {
    if (STOP_WORDS.includes(word)) return true;
  }
  
  for (const phrase of STOP_WORDS) {
    if (phrase.includes(" ") && normalized.includes(phrase)) return true;
  }
  
  return false;
};

/**
 * Custom hook for voice assistant with continuous listening
 * 
 * Flow:
 * 1. User clicks mic to activate
 * 2. Listens continuously until user stops speaking (silence detected)
 * 3. Sends transcript to backend for processing
 * 4. Speaks the response via TTS
 * 5. After TTS ends, automatically resumes listening
 * 6. Stop words only stop TTS, then resume listening
 */
export function useVoiceAssistant(sessionId, options = {}) {
  const {
    onTranscript,
    onResponse,
    onError,
    onReadyForPlanning,
    onModeChange,
    language = "en-US",
  } = options;

  // State
  const [isActive, setIsActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [mode, setMode] = useState(VoiceMode.IDLE);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [voiceResponse, setVoiceResponse] = useState("");
  const [refinedPrompt, setRefinedPrompt] = useState("");
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  // Refs
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const utteranceRef = useRef(null);
  const isActiveRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const processingRef = useRef(false);
  const processTranscriptRef = useRef(null);  // Ref to avoid stale closure
  const lastTranscriptRef = useRef("");  // Track last transcript for onend processing

  // Ref for selected female voice
  const femaleVoiceRef = useRef(null);

  // Check browser support and load voices
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;
    
    setIsSupported(!!SpeechRecognition && !!speechSynthesis);
    
    if (speechSynthesis) {
      synthRef.current = speechSynthesis;
      
      // Function to select a female voice
      const selectFemaleVoice = () => {
        const voices = speechSynthesis.getVoices();
        // Prefer these female voices in order
        const preferredVoices = [
          'Microsoft Zira',
          'Google UK English Female',
          'Google US English Female', 
          'Samantha',
          'Victoria',
          'Karen',
          'Moira',
          'Tessa',
          'Fiona'
        ];
        
        // Try to find a preferred female voice
        for (const name of preferredVoices) {
          const voice = voices.find(v => v.name.includes(name));
          if (voice) {
            femaleVoiceRef.current = voice;
            console.log('[Voice] Selected female voice:', voice.name);
            return;
          }
        }
        
        // Fallback: find any female voice
        const femaleVoice = voices.find(v => 
          v.name.toLowerCase().includes('female') || 
          v.name.includes('Zira') ||
          v.name.includes('Samantha') ||
          v.name.includes('Victoria')
        );
        if (femaleVoice) {
          femaleVoiceRef.current = femaleVoice;
          console.log('[Voice] Selected female voice (fallback):', femaleVoice.name);
        }
      };
      
      // Voices may load async
      if (speechSynthesis.getVoices().length > 0) {
        selectFemaleVoice();
      }
      speechSynthesis.onvoiceschanged = selectFemaleVoice;
    }
  }, []);

  // Update mode
  const updateMode = useCallback((newMode) => {
    setMode(newMode);
    onModeChange?.(newMode);
  }, [onModeChange]);

  // Stop TTS speaking
  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  }, []);

  // Forward declare for circular reference
  const startRecognitionRef = useRef(null);

  // Speak text using TTS, then resume listening
  const speak = useCallback((text) => {
    if (!synthRef.current || !text) {
      // No text to speak - resume listening immediately
      if (isActiveRef.current && startRecognitionRef.current) {
        setTimeout(() => startRecognitionRef.current?.(), 300);
      }
      return;
    }

    // Cancel any current speech
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 1.0;
    utterance.pitch = 1.1;  // Slightly higher pitch for friendlier tone
    utterance.volume = 1.0;
    
    // Use female voice if available
    if (femaleVoiceRef.current) {
      utterance.voice = femaleVoiceRef.current;
    }

    utterance.onstart = () => {
      console.log("[Voice] Speaking:", text.substring(0, 50) + "...");
      isSpeakingRef.current = true;
      setIsSpeaking(true);
      updateMode(VoiceMode.SPEAKING);
    };

    utterance.onend = () => {
      console.log("[Voice] Speaking ended");
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      
      // Resume listening if voice assistant is still active
      if (isActiveRef.current) {
        console.log("[Voice] Resuming listening after speech");
        setTimeout(() => startRecognitionRef.current?.(), 300);
      }
    };

    utterance.onerror = (event) => {
      console.error("[Voice] Speech error:", event);
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      
      // Resume listening even on error
      if (isActiveRef.current) {
        setTimeout(() => startRecognitionRef.current?.(), 300);
      }
    };

    utteranceRef.current = utterance;
    synthRef.current.speak(utterance);
  }, [language, updateMode]);

  // Forward declare deactivate
  const deactivateRef = useRef(null);

  // Process transcript through backend
  const processTranscript = useCallback(async (text) => {
    if (!text.trim() || processingRef.current) {
      console.log("[Voice] Skipping - empty text or already processing");
      return;
    }

    if (isNameQuery(text)) {
      const response = `I'm ${ASSISTANT_NAME}.`;
      setVoiceResponse(response);
      onResponse?.(response);
      speak(response);
      return;
    }

    // If no session, forward directly to planning (Dashboard will create session)
    if (!sessionId) {
      console.log("[Voice] No session - forwarding to planning:", text);
      processingRef.current = true;
      setIsProcessing(true);
      updateMode(VoiceMode.PROCESSING);
      
      // Forward to planning which will create the session
      onReadyForPlanning?.(text);
      
      // Give feedback and keep listening for follow-up
      // Note: speak() will resume listening after it finishes
      speak("I'll analyze that for you.");
      
      // Clear processing flag after a short delay
      setTimeout(() => {
        processingRef.current = false;
        setIsProcessing(false);
      }, 500);
      return;
    }

    console.log("[Voice] Processing transcript with session:", sessionId, text);
    processingRef.current = true;
    setIsProcessing(true);
    updateMode(VoiceMode.PROCESSING);
    setError(null);

    try {
      const response = await api.voiceProcessText(sessionId, text, true);
      
      console.log("[Voice] Backend response:", response);

      if (response.status === "success") {
        const { action, voice_response, refined_prompt } = response;

        if (voice_response) {
          setVoiceResponse(voice_response);
          onResponse?.(voice_response);
        }

        if (refined_prompt) {
          setRefinedPrompt(refined_prompt);
        }

        // Handle different actions
        switch (action) {
          case VoiceAction.FORWARD_TO_PLANNING:
            setAwaitingConfirmation(false);
            // Speak confirmation then forward
            speak(voice_response || "Starting the analysis now.");
            onReadyForPlanning?.(refined_prompt || text);
            // Keep voice active - don't deactivate, let user continue conversation
            break;
            
          case VoiceAction.CONFIRM_PROMPT:
            setAwaitingConfirmation(true);
            updateMode(VoiceMode.AWAITING_CONFIRMATION);
            // Speak the confirmation request
            speak(voice_response);
            break;
            
          case VoiceAction.ASK_CLARIFICATION:
          case VoiceAction.SPEAK:
            // Speak response, then resume listening
            speak(voice_response);
            break;
            
          case VoiceAction.LISTEN:
          default:
            // Speak response if any, then resume listening
            if (voice_response) {
              speak(voice_response);
            } else if (isActiveRef.current) {
              // No response - resume listening immediately
              setTimeout(() => startRecognitionRef.current?.(), 300);
            }
            break;
        }
      } else {
        throw new Error(response.message || "Voice processing failed");
      }
    } catch (err) {
      console.error("[Voice] Processing error:", err);
      setError(err.message);
      onError?.(err.message);
      
      // Resume listening on error
      if (isActiveRef.current) {
        speak("Sorry, I encountered an error. Please try again.");
      }
    } finally {
      setIsProcessing(false);
      processingRef.current = false;
    }
  }, [sessionId, onResponse, onReadyForPlanning, onError, updateMode, speak]);

  // Keep processTranscript ref updated
  useEffect(() => {
    processTranscriptRef.current = processTranscript;
  }, [processTranscript]);

  // Start speech recognition
  const startRecognition = useCallback(() => {
    if (!isSupported || !isActiveRef.current) return;
    
    // Don't start if processing or speaking
    if (processingRef.current || isSpeakingRef.current) {
      console.log("[Voice] Skipping start - processing or speaking");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    // Stop any existing recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {}
    }

    // Create new recognition instance
    const recognition = new SpeechRecognition();
    recognition.continuous = false;  // Stop after silence
    recognition.interimResults = true;
    recognition.lang = language;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log("[Voice] Recognition started");
      setIsListening(true);
      setInterimTranscript("");
      lastTranscriptRef.current = "";  // Reset on start
      updateMode(VoiceMode.LISTENING);
    };

    recognition.onend = () => {
      console.log("[Voice] Recognition ended, lastTranscript:", lastTranscriptRef.current);
      setIsListening(false);
      
      // Process any pending transcript that wasn't finalized
      const pending = lastTranscriptRef.current?.trim();
      if (pending && !processingRef.current) {
        console.log("[Voice] Processing pending transcript on end:", pending);
        setTranscript(pending);
        setInterimTranscript("");
        lastTranscriptRef.current = "";
        processTranscriptRef.current?.(pending);
      } else {
        setInterimTranscript("");
        // Restart if still active and not processing
        if (isActiveRef.current && !processingRef.current && !isSpeakingRef.current) {
          console.log("[Voice] Restarting recognition");
          setTimeout(() => startRecognitionRef.current?.(), 500);
        }
      }
    };

    recognition.onerror = (event) => {
      console.error("[Voice] Recognition error:", event.error);
      setIsListening(false);
      
      // Restart on recoverable errors if still active
      if (event.error === "no-speech" || event.error === "aborted") {
        if (isActiveRef.current && !isSpeakingRef.current && !processingRef.current) {
          console.log("[Voice] Restarting after error:", event.error);
          setTimeout(() => startRecognitionRef.current?.(), 500);
        }
        return;
      }
      
      setError(`Speech recognition error: ${event.error}`);
      onError?.(`Speech recognition error: ${event.error}`);
    };

    recognition.onresult = (event) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptText = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcriptText;
        } else {
          interim += transcriptText;
        }
      }

      // Track the latest text (interim or final) for processing on end
      if (interim) {
        lastTranscriptRef.current = interim;
      }
      setInterimTranscript(interim);

      if (final) {
        console.log("[Voice] Final transcript:", final);
        lastTranscriptRef.current = "";  // Clear since we're processing final
        setTranscript(final);
        onTranscript?.(final);

        // Check if user said stop word while TTS is speaking
        if (isSpeakingRef.current && containsStopWord(final)) {
          console.log("[Voice] Stop word detected - stopping TTS");
          stopSpeaking();
          // Resume listening after brief pause
          setTimeout(() => {
            if (isActiveRef.current) {
              startRecognitionRef.current?.();
            }
          }, 300);
          return;
        }

        // Don't process if just a stop word
        if (containsStopWord(final) && final.trim().split(/\s+/).length <= 2) {
          console.log("[Voice] Ignoring standalone stop word");
          // Resume listening
          if (isActiveRef.current && !isSpeakingRef.current) {
            setTimeout(() => startRecognitionRef.current?.(), 300);
          }
          return;
        }

        // Process the transcript using ref to get latest function
        console.log("[Voice] Calling processTranscript via ref");
        processTranscriptRef.current?.(final);
      }
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (err) {
      console.error("[Voice] Start error:", err);
      // Retry after delay
      if (isActiveRef.current) {
        setTimeout(() => startRecognitionRef.current?.(), 500);
      }
    }
  }, [isSupported, language, updateMode, onTranscript, onError, stopSpeaking]);

  // Keep ref updated
  useEffect(() => {
    startRecognitionRef.current = startRecognition;
  }, [startRecognition]);

  // Stop recognition
  const stopRecognition = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (err) {}
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  // Activate voice assistant
  const activate = useCallback(() => {
    if (!isSupported) {
      setError("Speech recognition not supported");
      return;
    }

    console.log("[Voice] Activating voice assistant");
    isActiveRef.current = true;
    setIsActive(true);
    setError(null);
    
    startRecognition();
  }, [isSupported, startRecognition]);

  // Deactivate voice assistant
  const deactivate = useCallback(() => {
    console.log("[Voice] Deactivating voice assistant");
    isActiveRef.current = false;
    setIsActive(false);
    
    stopRecognition();
    stopSpeaking();
    updateMode(VoiceMode.IDLE);
  }, [stopRecognition, stopSpeaking, updateMode]);

  // Keep deactivate ref updated
  useEffect(() => {
    deactivateRef.current = deactivate;
  }, [deactivate]);

  // Toggle voice assistant
  const toggle = useCallback(() => {
    if (isActive) {
      deactivate();
    } else {
      activate();
    }
  }, [isActive, activate, deactivate]);

  // Confirm refined prompt
  const confirmPrompt = useCallback(async (confirmed = true) => {
    if (!sessionId) return;

    setIsProcessing(true);
    
    try {
      const response = await api.voiceConfirm(sessionId, confirmed);
      
      if (response.status === "success") {
        if (confirmed && response.ready_for_planning) {
          setAwaitingConfirmation(false);
          speak(response.voice_response || "Starting the analysis now.");
          onReadyForPlanning?.(response.refined_prompt || refinedPrompt);
          deactivate();
        } else {
          // User rejected - speak response and resume listening
          setAwaitingConfirmation(false);
          speak(response.voice_response || "What would you like to change?");
        }
      }
    } catch (err) {
      console.error("[Voice] Confirm error:", err);
      setError(err.message);
      if (isActiveRef.current) {
        startRecognition();
      }
    } finally {
      setIsProcessing(false);
    }
  }, [sessionId, refinedPrompt, onReadyForPlanning, speak, deactivate, startRecognition]);

  // Reset voice state
  const reset = useCallback(async () => {
    deactivate();
    
    setTranscript("");
    setInterimTranscript("");
    setVoiceResponse("");
    setRefinedPrompt("");
    setError(null);
    setAwaitingConfirmation(false);

    if (sessionId) {
      try {
        await api.voiceReset(sessionId);
      } catch (err) {
        console.error("[Voice] Reset error:", err);
      }
    }
  }, [sessionId, deactivate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isActiveRef.current = false;
      stopRecognition();
      stopSpeaking();
    };
  }, [stopRecognition, stopSpeaking]);

  // Note: We don't reset on session change to keep voice active during new chat creation
  // The voice assistant should persist across chat changes

  return {
    // State
    isActive,
    isListening,
    isSpeaking,
    isProcessing,
    mode,
    transcript,
    interimTranscript,
    voiceResponse,
    refinedPrompt,
    error,
    isSupported,
    awaitingConfirmation,
    
    // Actions
    activate,
    deactivate,
    toggle,
    stopSpeaking,
    confirmPrompt,
    reset,
    
    // Backward compatibility
    startListening: activate,
    stopListening: deactivate,
  };
}

export default useVoiceAssistant;

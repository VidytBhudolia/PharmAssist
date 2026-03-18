import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  Check,
  X,
  RefreshCw,
  Sparkles,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { VoiceMode } from "@/hooks/useVoiceAssistant";

/**
 * Voice assistant panel component showing conversation state and controls
 */
export function VoiceAssistantPanel({
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
  awaitingConfirmation,
  onDeactivate,
  onStopSpeaking,
  onConfirm,
  onReject,
  onReset,
  className,
}) {
  // Show panel when voice assistant is active
  const showPanel = isActive;

  const getModeLabel = () => {
    switch (mode) {
      case VoiceMode.LISTENING:
        return "Listening...";
      case VoiceMode.PROCESSING:
        return "Processing...";
      case VoiceMode.SPEAKING:
        return "Speaking...";
      case VoiceMode.AWAITING_CONFIRMATION:
        return "Confirm your request";
      case VoiceMode.INTERRUPTED:
        return "Interrupted";
      case VoiceMode.HOLDING:
        return "Waiting for more...";
      default:
        return "Sage";
    }
  };

  const getModeColor = () => {
    switch (mode) {
      case VoiceMode.LISTENING:
        return "text-red-400";
      case VoiceMode.PROCESSING:
        return "text-amber-400";
      case VoiceMode.SPEAKING:
        return "text-violet-400";
      case VoiceMode.AWAITING_CONFIRMATION:
        return "text-emerald-400";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <AnimatePresence>
      {showPanel && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className={cn("w-full max-w-2xl mx-auto", className)}
        >
          <Card className="bg-card/95 backdrop-blur-xl border-border/50 shadow-2xl">
            <CardContent className="p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "p-2 rounded-lg",
                    mode === VoiceMode.LISTENING && "bg-red-500/20",
                    mode === VoiceMode.PROCESSING && "bg-amber-500/20",
                    mode === VoiceMode.SPEAKING && "bg-violet-500/20",
                    mode === VoiceMode.AWAITING_CONFIRMATION && "bg-emerald-500/20",
                    mode === VoiceMode.IDLE && "bg-primary/20"
                  )}>
                    {isProcessing ? (
                      <Loader2 className="animate-spin text-amber-400" size={18} />
                    ) : isSpeaking ? (
                      <Volume2 className="text-violet-400" size={18} />
                    ) : isListening ? (
                      <Mic className="text-red-400 animate-pulse" size={18} />
                    ) : (
                      <Sparkles className="text-primary" size={18} />
                    )}
                  </div>
                  <div>
                    <h3 className={cn("text-sm font-semibold", getModeColor())}>
                      {getModeLabel()}
                    </h3>
                  </div>
                </div>

                {/* Control buttons */}
                <div className="flex items-center gap-2">
                  {isSpeaking && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onStopSpeaking}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <VolumeX size={16} />
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onReset}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <RefreshCw size={16} />
                  </Button>
                </div>
              </div>

              {/* Error message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mb-3 p-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs"
                >
                  {error}
                </motion.div>
              )}

              {/* Transcript display */}
              {(transcript || interimTranscript) && (
                <div className="mb-3 p-3 rounded-lg bg-accent/30 border border-border/50">
                  <div className="flex items-start gap-2">
                    <MessageSquare size={14} className="text-muted-foreground mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-muted-foreground mb-1">You said:</p>
                      <p className="text-sm text-foreground">
                        {transcript}
                        {interimTranscript && (
                          <span className="text-muted-foreground italic">
                            {" "}{interimTranscript}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Voice response display */}
              {voiceResponse && (
                <div className="mb-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                  <div className="flex items-start gap-2">
                    <Sparkles size={14} className="text-primary mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-muted-foreground mb-1">Sage:</p>
                      <p className="text-sm text-foreground">{voiceResponse}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Refined prompt display (when awaiting confirmation) */}
              {awaitingConfirmation && refinedPrompt && (
                <div className="mb-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                  <div className="flex items-start gap-2">
                    <Check size={14} className="text-emerald-400 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-muted-foreground mb-1">Refined request:</p>
                      <p className="text-sm text-foreground">{refinedPrompt}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center justify-between gap-2">
                {/* Stop speaking button when TTS is active */}
                {isSpeaking && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onStopSpeaking}
                    className="flex-1"
                  >
                    <VolumeX size={16} className="mr-2" />
                    Stop Speaking
                  </Button>
                )}

                {/* Deactivate button when not in confirmation mode */}
                {!awaitingConfirmation && !isSpeaking && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onDeactivate}
                    disabled={isProcessing}
                    className="flex-1"
                  >
                    <MicOff size={16} className="mr-2" />
                    Deactivate
                  </Button>
                )}

                {/* Confirmation controls */}
                {awaitingConfirmation && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onReject}
                      className="flex-1"
                    >
                      <X size={16} className="mr-2" />
                      Change
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => onConfirm(true)}
                      className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                    >
                      <Check size={16} className="mr-2" />
                      Confirm & Proceed
                    </Button>
                  </>
                )}
              </div>

              {/* Waveform visualization when listening */}
              {isListening && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-3 flex items-center justify-center gap-1 h-8"
                >
                  {[...Array(12)].map((_, i) => (
                    <motion.div
                      key={i}
                      animate={{
                        height: [4, Math.random() * 24 + 4, 4],
                      }}
                      transition={{
                        duration: 0.5,
                        repeat: Infinity,
                        delay: i * 0.05,
                      }}
                      className="w-1 bg-red-400 rounded-full"
                    />
                  ))}
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Compact voice indicator for showing voice state inline
 */
export function VoiceIndicator({
  mode,
  isListening,
  isSpeaking,
  isProcessing,
  className,
}) {
  if (mode === VoiceMode.IDLE) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
        isListening && "bg-red-500/20 text-red-400",
        isSpeaking && "bg-violet-500/20 text-violet-400",
        isProcessing && "bg-amber-500/20 text-amber-400",
        className
      )}
    >
      {isProcessing ? (
        <Loader2 className="animate-spin" size={12} />
      ) : isSpeaking ? (
        <Volume2 size={12} />
      ) : isListening ? (
        <Mic size={12} className="animate-pulse" />
      ) : null}
      <span>
        {isProcessing ? "Processing" : isSpeaking ? "Speaking" : isListening ? "Listening" : ""}
      </span>
    </motion.div>
  );
}

/**
 * Voice transcript bubble component
 */
export function VoiceTranscriptBubble({
  transcript,
  interimTranscript,
  isUser = true,
  className,
}) {
  if (!transcript && !interimTranscript) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "max-w-[80%] p-3 rounded-2xl text-sm",
        isUser
          ? "ml-auto bg-primary text-primary-foreground rounded-br-md"
          : "mr-auto bg-accent text-accent-foreground rounded-bl-md",
        className
      )}
    >
      <p>
        {transcript}
        {interimTranscript && (
          <span className="opacity-60 italic">{" "}{interimTranscript}</span>
        )}
      </p>
    </motion.div>
  );
}

export default VoiceAssistantPanel;

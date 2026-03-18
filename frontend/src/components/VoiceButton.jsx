import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2, Volume2, VolumeX, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { VoiceMode } from "@/hooks/useVoiceAssistant";

/**
 * Voice button component with visual feedback for different states
 */
export function VoiceButton({
  isListening,
  isSpeaking,
  isProcessing,
  mode,
  isSupported,
  onClick,
  onStopSpeaking,
  className,
  size = "default",
  showLabel = true,
}) {
  if (!isSupported) {
    return null;
  }

  const isActive = isListening || isSpeaking || isProcessing;
  
  const getIcon = () => {
    if (isProcessing) {
      return <Loader2 className="animate-spin" size={size === "sm" ? 16 : 20} />;
    }
    if (isSpeaking) {
      return <Volume2 size={size === "sm" ? 16 : 20} />;
    }
    if (isListening) {
      return <Mic size={size === "sm" ? 16 : 20} />;
    }
    return <Mic size={size === "sm" ? 16 : 20} />;
  };

  const getLabel = () => {
    if (isProcessing) return "Processing...";
    if (isSpeaking) return "Speaking";
    if (isListening) return "Listening";
    return "Voice";
  };

  const getStatusColor = () => {
    if (isProcessing) return "bg-amber-500";
    if (isSpeaking) return "bg-violet-500";
    if (isListening) return "bg-red-500";
    return "bg-primary";
  };

  return (
    <div className="relative inline-flex items-center gap-2">
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Button
          variant={isActive ? "default" : "outline"}
          size={size}
          onClick={onClick}
          className={cn(
            "relative transition-all duration-200",
            isListening && "bg-red-500/90 hover:bg-red-500 border-red-500 text-white",
            isSpeaking && "bg-violet-500/90 hover:bg-violet-500 border-violet-500 text-white",
            isProcessing && "bg-amber-500/90 hover:bg-amber-500 border-amber-500 text-white",
            className
          )}
          disabled={isProcessing}
        >
          {getIcon()}
          {showLabel && (
            <span className="ml-2 text-xs font-medium">{getLabel()}</span>
          )}
        </Button>
      </motion.div>

      {/* Pulse animation when listening */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1.5, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="absolute inset-0 rounded-md bg-red-500/30 pointer-events-none"
          />
        )}
      </AnimatePresence>

      {/* Stop speaking button */}
      <AnimatePresence>
        {isSpeaking && onStopSpeaking && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
          >
            <Button
              variant="ghost"
              size="icon"
              onClick={onStopSpeaking}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <Square size={14} />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status indicator dot */}
      {isActive && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className={cn(
            "absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-background",
            getStatusColor(),
            isListening && "animate-pulse"
          )}
        />
      )}
    </div>
  );
}

/**
 * Compact voice button for input field integration
 */
export function VoiceInputButton({
  isListening,
  isSpeaking,
  isProcessing,
  isSupported,
  onClick,
  className,
}) {
  if (!isSupported) {
    return null;
  }

  const isActive = isListening || isSpeaking || isProcessing;

  return (
    <button
      onClick={onClick}
      disabled={isProcessing}
      className={cn(
        "p-2 rounded-lg transition-all duration-200 relative",
        "hover:bg-accent/50 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary/50",
        isListening && "bg-red-500/20 text-red-500",
        isSpeaking && "bg-violet-500/20 text-violet-500",
        isProcessing && "bg-amber-500/20 text-amber-500",
        !isActive && "text-muted-foreground hover:text-foreground",
        className
      )}
    >
      {isProcessing ? (
        <Loader2 className="animate-spin" size={18} />
      ) : isListening ? (
        <MicOff size={18} />
      ) : (
        <Mic size={18} />
      )}
      
      {/* Pulse ring when listening */}
      {isListening && (
        <span
          className="absolute inset-0 rounded-lg bg-red-500/30 animate-ping"
        />
      )}
    </button>
  );
}

export default VoiceButton;

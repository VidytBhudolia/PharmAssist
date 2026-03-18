/**
 * ChatInput - Modern glassmorphism chat input with integrated file attach
 *
 * Features:
 * - Glassmorphism styling
 * - File attach button inside input
 * - Animated send button with accent color
 * - Beautiful glow effects
 */

import React, { forwardRef } from "react";
import { motion } from "framer-motion";
import { Send, Paperclip, Loader2, X, File } from "lucide-react";

export const ChatInput = forwardRef(
  (
    {
      value,
      onChange,
      onKeyPress,
      onSend,
      onAttach,
      onRemoveFile,
      isLoading = false,
      isUploading = false,
      disabled = false,
      uploadedFile = null,
      placeholder = "Ask anything...",
      className = "",
    },
    ref,
  ) => {
    const handleKeyPress = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (value?.trim() && !isLoading) {
          onSend?.();
        }
      }
      onKeyPress?.(e);
    };

    return (
      <div className={`relative ${className}`}>
        {/* Uploaded file indicator */}
        {uploadedFile && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute -top-12 left-4 right-4 flex items-center gap-2 px-3 py-2 bg-card/80 backdrop-blur-xl border border-primary/20 rounded-xl shadow-lg"
          >
            <File size={14} className="text-primary flex-shrink-0" />
            <span className="text-xs text-foreground flex-1 truncate">{uploadedFile.name}</span>
            <span className="text-[10px] text-muted-foreground">
              {(uploadedFile.size / 1024).toFixed(1)} KB
            </span>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onRemoveFile}
              className="p-1 hover:bg-destructive/20 rounded-md transition-colors"
            >
              <X size={12} className="text-muted-foreground hover:text-destructive" />
            </motion.button>
          </motion.div>
        )}

        {/* Main input container with glassmorphism */}
        <div className="relative flex items-center gap-2 p-2 bg-card/60 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl">
          {/* Attach button - inside input */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onAttach}
            disabled={isUploading || disabled}
            className={`flex-shrink-0 p-2.5 rounded-xl transition-all duration-200 ${
              uploadedFile
                ? "text-primary bg-primary/10"
                : isUploading
                  ? "text-muted-foreground cursor-not-allowed"
                  : "text-muted-foreground hover:text-primary hover:bg-primary/10"
            }`}
            title="Attach document"
          >
            {isUploading ? <Loader2 className="animate-spin" size={18} /> : <Paperclip size={18} />}
          </motion.button>

          {/* Text input */}
          <input
            ref={ref}
            type="text"
            value={value}
            onChange={onChange}
            onKeyPress={handleKeyPress}
            disabled={disabled || isLoading}
            placeholder={placeholder}
            className="flex-1 bg-transparent border-none outline-none text-foreground text-sm placeholder:text-muted-foreground/50 py-2"
          />

          {/* Send button with accent color */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onSend}
            disabled={isLoading || !value?.trim() || disabled}
            className={`flex-shrink-0 p-2.5 rounded-xl transition-all duration-200 ${
              isLoading || !value?.trim() || disabled
                ? "bg-muted text-muted-foreground cursor-not-allowed"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            }`}
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={18} />
            ) : (
              <motion.div
                animate={value?.trim() ? { rotate: [0, -10, 10, 0] } : {}}
                transition={{ duration: 0.3 }}
              >
                <Send size={18} />
              </motion.div>
            )}
          </motion.button>
        </div>
      </div>
    );
  },
);

ChatInput.displayName = "ChatInput";

export default ChatInput;

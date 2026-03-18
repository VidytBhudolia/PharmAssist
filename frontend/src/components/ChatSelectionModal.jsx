import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Search, MessageSquare, Check, ArrowRight } from "lucide-react";

/**
 * ChatSelectionModal — allows users to pick exactly two chat sessions
 * for side-by-side study comparison.
 */
export function ChatSelectionModal({ isOpen, chats, onConfirm, onCancel }) {
  const [selected, setSelected] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) return chats;
    const q = searchQuery.toLowerCase();
    return chats.filter(
      (c) =>
        (c.title || "").toLowerCase().includes(q) ||
        (c.chatHistory || []).some((m) => (m.content || "").toLowerCase().includes(q)),
    );
  }, [chats, searchQuery]);

  const toggleChat = (chat) => {
    setSelected((prev) => {
      const exists = prev.find((c) => c.sessionId === chat.sessionId);
      if (exists) return prev.filter((c) => c.sessionId !== chat.sessionId);
      if (prev.length >= 2) return prev; // max 2
      return [...prev, chat];
    });
  };

  const handleConfirm = () => {
    if (selected.length === 2) {
      onConfirm(selected[0], selected[1]);
      setSelected([]);
      setSearchQuery("");
    }
  };

  const handleCancel = () => {
    setSelected([]);
    setSearchQuery("");
    onCancel();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={handleCancel}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative z-10 w-full max-w-lg mx-4 rounded-2xl border border-border/60 bg-card/95 backdrop-blur-xl shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/60">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Compare Studies</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Select exactly 2 chat sessions to compare side by side
                </p>
              </div>
              <button
                onClick={handleCancel}
                className="p-2 rounded-xl hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Search */}
            <div className="px-6 pt-4">
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                />
                <input
                  type="text"
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-10 pl-10 pr-4 bg-background/60 border border-border/60 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                />
              </div>
            </div>

            {/* Selection indicator */}
            <div className="px-6 pt-3 pb-1 flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Selected:</span>
              <div className="flex items-center gap-1.5">
                {[0, 1].map((idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                      selected[idx]
                        ? "bg-primary/15 border-primary/30 text-primary"
                        : "bg-muted/30 border-border/40 text-muted-foreground"
                    }`}
                  >
                    {selected[idx] ? (
                      <>
                        <Check size={12} />
                        <span className="max-w-[120px] truncate">
                          {selected[idx].title || "Untitled"}
                        </span>
                      </>
                    ) : (
                      <span>Study {idx + 1}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Chat list */}
            <div className="px-6 py-3 max-h-[350px] overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
              {filteredChats.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                  <MessageSquare size={32} className="mb-2 opacity-40" />
                  <p className="text-sm">No chats found</p>
                </div>
              ) : (
                filteredChats.map((chat) => {
                  const isSelected = selected.some((s) => s.sessionId === chat.sessionId);
                  const isDisabled = !isSelected && selected.length >= 2;
                  const messageCount = (chat.chatHistory || chat.messages || []).length;

                  return (
                    <motion.button
                      key={chat.sessionId}
                      whileHover={!isDisabled ? { x: 2 } : {}}
                      whileTap={!isDisabled ? { scale: 0.98 } : {}}
                      onClick={() => !isDisabled && toggleChat(chat)}
                      disabled={isDisabled}
                      className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-left transition-all duration-150 ${
                        isSelected
                          ? "bg-primary/10 border border-primary/30 ring-1 ring-primary/20"
                          : isDisabled
                            ? "bg-muted/20 border border-transparent opacity-40 cursor-not-allowed"
                            : "bg-background/40 border border-border/40 hover:border-primary/30 hover:bg-primary/5"
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                          isSelected
                            ? "bg-primary/20 border border-primary/30"
                            : "bg-muted/30 border border-border/40"
                        }`}
                      >
                        {isSelected ? (
                          <Check size={14} className="text-primary" />
                        ) : (
                          <MessageSquare
                            size={14}
                            className="text-muted-foreground"
                          />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm font-medium truncate ${
                            isSelected ? "text-foreground" : "text-foreground/80"
                          }`}
                        >
                          {chat.title || "Untitled Chat"}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {messageCount} message{messageCount !== 1 ? "s" : ""}
                          {chat.updatedAt && (
                            <>
                              {" · "}
                              {new Date(chat.updatedAt).toLocaleDateString()}
                            </>
                          )}
                        </p>
                      </div>
                      {isSelected && (
                        <span className="text-xs font-semibold text-primary px-2 py-0.5 rounded-md bg-primary/10">
                          #{selected.findIndex((s) => s.sessionId === chat.sessionId) + 1}
                        </span>
                      )}
                    </motion.button>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-border/60">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground rounded-xl hover:bg-muted/50 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={selected.length !== 2}
                className={`flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-xl transition-all shadow-lg ${
                  selected.length === 2
                    ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-primary/25"
                    : "bg-muted text-muted-foreground cursor-not-allowed shadow-none"
                }`}
              >
                <span>Compare</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
  ChevronDown,
  Search,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  Pill,
  Bell,
  BellOff,
  Eye,
  Radar,
  Share2,
  Users,
  Columns2,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";

/**
 * ChatSidebar Component
 * Provides ChatGPT-like chat management interface with collapsible sidebar
 */
export function ChatSidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRestoreChat,
  onRenameChat,
  onToggleMonitoring,
  onOpenNewsMonitor,
  onOpenCompare = () => {},
  canCompare = false,
  isComparing = false,
  monitoredPromptIds = new Set(),
  monitoredSessionIds = new Set(),
  affectedSessionIds = new Set(),
  isCollapsed = false,
  onToggleCollapse,
  onShareChat,
  sharedWithMe = [],
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredId, setHoveredId] = useState(null);
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [deletedChat, setDeletedChat] = useState(null);
  const [showUndo, setShowUndo] = useState(false);
  const editInputRef = useRef(null);
  const menuRef = useRef(null);
  const undoTimeoutRef = useRef(null);
  const searchInputRef = useRef(null);

  // Focus search input when expanding from search button
  const handleSearchExpand = () => {
    onToggleCollapse();
    // Focus search input after animation completes
    setTimeout(() => {
      if (searchInputRef.current) {
        searchInputRef.current.focus();
      }
    }, 350);
  };

  // Focus input when editing starts
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!menuOpenId) return;
      const target = e.target;
      if (target instanceof Element && target.closest("[data-chat-menu-root='true']")) return;
      setMenuOpenId(null);
    };
    const handleEscape = (e) => {
      if (e.key === "Escape") {
        setMenuOpenId(null);
      }
    };

    document.addEventListener("pointerdown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpenId]);

  // Cleanup undo timeout on unmount
  useEffect(() => {
    return () => {
      if (undoTimeoutRef.current) {
        clearTimeout(undoTimeoutRef.current);
      }
    };
  }, []);

  // Filter chats based on search
  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Sort chats by most recent
  const sortedChats = [...filteredChats].sort(
    (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt),
  );

  // Group chats by date
  const groupChatsByDate = (chatList) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);
    const lastMonth = new Date(today);
    lastMonth.setMonth(lastMonth.getMonth() - 1);

    const groups = {
      today: [],
      yesterday: [],
      lastWeek: [],
      lastMonth: [],
      older: [],
    };

    chatList.forEach((chat) => {
      const chatDate = new Date(chat.updatedAt || chat.createdAt);
      if (chatDate >= today) {
        groups.today.push(chat);
      } else if (chatDate >= yesterday) {
        groups.yesterday.push(chat);
      } else if (chatDate >= lastWeek) {
        groups.lastWeek.push(chat);
      } else if (chatDate >= lastMonth) {
        groups.lastMonth.push(chat);
      } else {
        groups.older.push(chat);
      }
    });

    return groups;
  };

  const groupedChats = groupChatsByDate(sortedChats);

  const handleStartEdit = (chat) => {
    setEditingId(chat.id);
    setEditTitle(chat.title);
    setMenuOpenId(null);
  };

  const handleSaveEdit = () => {
    if (editingId && editTitle.trim()) {
      onRenameChat(editingId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle("");
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSaveEdit();
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  const handleDelete = (chatId) => {
    setMenuOpenId(null);

    // Find and store the chat before deleting
    const chatToDelete = chats.find((c) => c.id === chatId);
    if (!chatToDelete) return;

    // Clear any existing undo timeout
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }

    // Store deleted chat and show undo toast
    setDeletedChat(chatToDelete);
    setShowUndo(true);

    // Delete the chat
    onDeleteChat(chatId);

    // Auto-hide undo after 5 seconds
    undoTimeoutRef.current = setTimeout(() => {
      setShowUndo(false);
      setDeletedChat(null);
    }, 5000);
  };

  const handleUndo = () => {
    if (deletedChat && onRestoreChat) {
      onRestoreChat(deletedChat);
      setShowUndo(false);
      setDeletedChat(null);
      if (undoTimeoutRef.current) {
        clearTimeout(undoTimeoutRef.current);
      }
    }
  };

  const handleDismissUndo = () => {
    setShowUndo(false);
    setDeletedChat(null);
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }
  };

  const renderChatItem = (chat) => {
    const isActive = chat.id === activeChatId;
    const isEditing = chat.id === editingId;
    const isHovered = chat.id === hoveredId;
    const isMenuOpen = chat.id === menuOpenId;
    // Check if this chat's session is monitored (persistent across all chats)
    const isMonitored = monitoredSessionIds.has(chat.id);
    const isShared = Boolean(chat.isShared);

    return (
      <motion.div
        key={chat.id}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -10 }}
        transition={{ duration: 0.15 }}
        className="relative group"
        onMouseEnter={() => setHoveredId(chat.id)}
        onMouseLeave={() => {
          setHoveredId(null);
          if (!isMenuOpen) setMenuOpenId(null);
        }}
      >
        {isEditing ? (
          <div className="flex items-center gap-1.5 px-2 py-2 bg-card/70 rounded-2xl border border-primary/30">
            <input
              ref={editInputRef}
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSaveEdit}
              className="flex-1 bg-background text-foreground text-sm px-3 py-1.5 rounded-xl outline-none border border-border/70 focus:border-primary transition-colors"
            />
            <button
              onClick={handleSaveEdit}
              className="p-1.5 hover:bg-emerald-500/20 rounded-lg text-emerald-500 transition-colors"
            >
              <Check size={14} />
            </button>
            <button
              onClick={handleCancelEdit}
              className="p-1.5 hover:bg-destructive/20 rounded-lg text-destructive transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <div
            onClick={() => onSelectChat(chat.id)}
            className={`relative flex items-center gap-3 px-3 py-3 rounded-2xl cursor-pointer transition-all duration-200 ease-out ${
              isActive
                ? "bg-card/90 border border-primary/35 ring-1 ring-primary/20"
                : "border border-transparent hover:border-border/70 hover:bg-card/65"
            }`}
          >
            <div
              className={`relative w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 border border-border/60 ${
                isActive ? "bg-primary/15" : "bg-card/70"
              }`}
            >
              <MessageSquare
                size={14}
                className={isActive ? "text-primary" : "text-muted-foreground"}
              />
              {/* Monitored badge - RED if affected by intel, AMBER if just monitoring */}
              {isMonitored && (
                <span
                  className={`absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border border-card flex items-center justify-center ${
                    affectedSessionIds.has(chat.id)
                      ? "bg-red-500/90 animate-pulse"
                      : "bg-amber-500/90"
                  }`}
                  title={
                    affectedSessionIds.has(chat.id) ? "New intel affecting this chat" : "Monitored"
                  }
                >
                  <Eye size={8} className="text-white" />
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 min-w-0">
                <p
                  className={`text-sm font-medium truncate ${
                    isActive ? "text-foreground" : "text-foreground/80"
                  }`}
                >
                  {chat.title}
                </p>
                {isShared && (
                  <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-primary/15 text-primary flex-shrink-0">
                    {chat.role || "shared"}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {chat.messages && chat.messages.length > 0
                  ? `${chat.messages.filter((m) => m.role === "user").length} message${chat.messages.filter((m) => m.role === "user").length !== 1 ? "s" : ""}`
                  : "No messages yet"}
              </p>
            </div>

            {/* Three-dots menu button — replaces hover edit/delete */}
            <AnimatePresence>
              {(isHovered || isMenuOpen) && !isEditing && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.1 }}
                  className="relative"
                  data-chat-menu-root="true"
                  ref={isMenuOpen ? menuRef : null}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(isMenuOpen ? null : chat.id);
                    }}
                    className={`p-1.5 rounded-lg text-muted-foreground hover:text-foreground transition-all duration-200 ${
                      isMenuOpen ? "bg-muted/70 text-foreground scale-105" : "hover:bg-muted/70"
                    }`}
                    title="Actions"
                  >
                    <MoreVertical size={16} />
                  </button>

                  {/* Dropdown menu */}
                  <AnimatePresence>
                    {isMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.82, y: -8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.88, y: -8 }}
                        transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                        style={{ transformOrigin: "top right" }}
                        className="absolute right-0 top-9 z-50 w-52 overflow-hidden rounded-2xl border border-border/70 bg-card/95 backdrop-blur-xl shadow-2xl"
                      >
                      {/* Enable Notifications toggle */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuOpenId(null);
                          if (onToggleMonitoring) {
                            // Use the last promptId from agentsData if available, otherwise use session ID as placeholder
                            const chatPromptIds = (chat.agentsData || [])
                              .map((e) => e.promptId)
                              .filter(Boolean);
                            const lastPromptId = chatPromptIds[chatPromptIds.length - 1];
                            if (lastPromptId) {
                              onToggleMonitoring(
                                chat.sessionId || chat.id,
                                lastPromptId,
                                !isMonitored,
                              );
                            }
                          }
                        }}
                        className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-foreground/85 hover:bg-muted/70 hover:text-foreground transition-colors"
                      >
                        {isMonitored ? (
                          <BellOff size={14} className="text-amber-400" />
                        ) : (
                          <Bell size={14} />
                        )}
                        {isMonitored ? "Disable Notifications" : "Enable Notifications"}
                      </button>
                      {!isShared && (
                        <>
                          {/* Share */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setMenuOpenId(null);
                              if (onShareChat) onShareChat(chat.id, chat.title);
                            }}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-foreground/85 hover:bg-muted/70 hover:text-foreground transition-colors"
                          >
                            <Share2 size={14} />
                            Share
                          </button>
                          {/* Edit */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartEdit(chat);
                            }}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-foreground/85 hover:bg-muted/70 hover:text-foreground transition-colors"
                          >
                            <Edit2 size={14} />
                            Edit
                          </button>
                          <div className="my-1 h-px bg-border/70" />
                          {/* Delete */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(chat.id);
                            }}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-destructive/85 hover:bg-destructive/15 hover:text-destructive transition-colors"
                          >
                            <Trash2 size={14} />
                            Delete
                          </button>
                        </>
                      )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </motion.div>
    );
  };

  const renderGroup = (title, chatList) => {
    if (chatList.length === 0) return null;

    return (
      <div key={title} className="mb-5">
        <div className="flex items-center gap-2 px-3 mb-2">
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            {title}
          </p>
          <div className="flex-1 h-px bg-border"></div>
        </div>
        <div className="space-y-1">
          <AnimatePresence>{chatList.map(renderChatItem)}</AnimatePresence>
        </div>
      </div>
    );
  };

  return (
    <motion.div
      animate={{ width: isCollapsed ? "76px" : "296px" }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="bg-card/85 border-r border-border/60 backdrop-blur-xl flex flex-col h-screen overflow-hidden"
    >
      {isCollapsed ? (
        /* Collapsed Sidebar */
        <div className="flex flex-col items-center h-full py-4 gap-4">
          {/* Expand Button - Same position as collapse */}
          <button
            onClick={onToggleCollapse}
            className="w-12 h-12 rounded-2xl border border-border/70 bg-card/60 hover:border-primary/40 flex items-center justify-center transition-colors"
            title="Expand Sidebar"
          >
            <ChevronRight size={20} className="text-muted-foreground" />
          </button>

          {/* Logo - Opens new chat */}
          <button
            onClick={onNewChat}
            className="w-12 h-12 rounded-2xl border border-primary/40 bg-primary/15 flex items-center justify-center hover:scale-105 transition-transform duration-200"
            title="New Analysis"
          >
            <Pill className="text-primary" size={22} />
          </button>

          {/* Search Button - Expands and focuses search */}
          <button
            onClick={handleSearchExpand}
            className="w-12 h-12 rounded-2xl border border-border/70 bg-card/60 hover:border-primary/40 flex items-center justify-center transition-colors"
            title="Search Conversations"
          >
            <Search size={20} className="text-muted-foreground" />
          </button>

          {/* News Monitor icon */}
          <button
            onClick={onOpenNewsMonitor}
            className="w-12 h-12 rounded-2xl border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 flex items-center justify-center transition-colors"
            title="News Monitor"
          >
            <Radar size={20} className="text-amber-400" />
          </button>

          {/* Compare Studies icon */}
          <button
            onClick={onOpenCompare}
            disabled={!canCompare || isComparing}
            className={`w-12 h-12 rounded-2xl border flex items-center justify-center transition-colors ${
              !canCompare || isComparing
                ? "border-border/40 bg-card/40 text-muted-foreground/60 cursor-not-allowed"
                : "border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20"
            }`}
            title={canCompare ? "Compare Studies" : "Select two chats to compare"}
          >
            <Columns2 size={20} className={canCompare ? "text-cyan-400" : ""} />
          </button>
        </div>
      ) : (
        /* Expanded Sidebar */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
          className="flex flex-col h-full overflow-hidden"
        >
          {/* Logo/Brand Header - Fixed at top */}
          <div className="flex-shrink-0 p-4 border-b border-border/60">
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => onSelectChat(null)}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer group flex-1"
                title="Home"
              >
                <div className="w-11 h-11 rounded-2xl border border-primary/40 bg-primary/15 flex items-center justify-center group-hover:scale-105 transition-transform duration-200">
                  <Pill className="text-primary" size={20} />
                </div>
                <div className="text-left">
                  <div className="dossier-label">PharmAssist</div>
                  <h1 className="text-lg font-display text-foreground group-hover:text-primary transition-colors">
                    Portfolio Studio
                  </h1>
                </div>
              </button>

              {/* Collapse Button */}
              <button
                onClick={onToggleCollapse}
                className="p-2 rounded-xl border border-border/60 hover:border-primary/40 transition-colors"
                title="Collapse Sidebar"
              >
                <ChevronLeft size={18} className="text-muted-foreground" />
              </button>
            </div>
            <motion.button
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={onNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl font-semibold text-primary-foreground transition-all duration-300 bg-primary hover:bg-primary/90 shadow-lg shadow-primary/25 hover:shadow-primary/40"
            >
              <Plus size={18} />
              <span>New Analysis</span>
            </motion.button>
          </div>

          {/* Search - Fixed at top */}
          <div className="flex-shrink-0 px-4 py-3 border-b border-border/60">
            <div className="relative">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-card/70 border border-border/60 rounded-2xl pl-10 pr-8 py-2.5 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary/50 focus:bg-card transition-all duration-200"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 hover:bg-muted rounded text-muted-foreground hover:text-foreground"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Chat List - Scrollable area */}
          <div className="flex-1 overflow-y-auto px-3 py-3 min-h-0">
            {sortedChats.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center px-4">
                <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
                  <MessageSquare size={28} className="text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">
                  {searchQuery ? "No conversations found" : "No conversations yet"}
                </p>
                <p className="text-xs text-muted-foreground mt-1.5 max-w-[180px]">
                  {searchQuery
                    ? "Try a different search term"
                    : "Start a new analysis to begin exploring drug repurposing opportunities"}
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {renderGroup("Today", groupedChats.today)}
                {renderGroup("Yesterday", groupedChats.yesterday)}
                {renderGroup("Last 7 Days", groupedChats.lastWeek)}
                {renderGroup("Last 30 Days", groupedChats.lastMonth)}
                {renderGroup("Older", groupedChats.older)}

                {/* Shared with me section */}
                {sharedWithMe.length > 0 && (
                  <div className="mb-5 mt-4 pt-4 border-t border-border/60">
                    <div className="flex items-center gap-2 px-3 mb-2">
                      <Users size={12} className="text-primary" />
                      <p className="text-[11px] font-semibold text-primary uppercase tracking-wider">
                        Shared with me
                      </p>
                      <div className="flex-1 h-px bg-primary/30"></div>
                    </div>
                    <div className="space-y-1">
                      <AnimatePresence>
                        {sharedWithMe.map((chat) => renderChatItem(chat))}
                      </AnimatePresence>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Undo Toast - Fixed at bottom of scrollable area */}
          <AnimatePresence>
            {showUndo && deletedChat && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ duration: 0.2 }}
                className="mx-3 mb-3 p-3 bg-card border border-border rounded-xl shadow-lg"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {deletedChat.title}
                    </p>
                    <p className="text-xs text-muted-foreground">Chat deleted</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleUndo}
                      className="px-3 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition-colors"
                    >
                      Undo
                    </motion.button>
                    <button
                      onClick={handleDismissUndo}
                      className="p-1.5 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer - Fixed at bottom */}
          <div className="flex-shrink-0 p-4 border-t border-border bg-card">
            {/* News Monitor link */}
            <button
              onClick={onOpenNewsMonitor}
              className="w-full flex items-center gap-2.5 px-3 py-2 mb-2 rounded-xl text-sm text-amber-300/80 hover:bg-amber-500/10 hover:text-amber-300 border border-amber-500/20 transition-colors"
            >
              <Radar size={16} />
              <span>News Monitor</span>
            </button>
            {/* Compare Studies link */}
            <button
              onClick={onOpenCompare}
              disabled={!canCompare || isComparing}
              className={`w-full flex items-center gap-2.5 px-3 py-2 mb-3 rounded-xl text-sm border transition-colors ${
                !canCompare || isComparing
                  ? "text-muted-foreground/60 border-border/40 bg-card/40 cursor-not-allowed"
                  : "text-cyan-300/80 hover:bg-cyan-500/10 hover:text-cyan-300 border-cyan-500/20"
              }`}
            >
              <Columns2 size={16} />
              <span>Compare Studies</span>
            </button>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-xs text-muted-foreground">
                  {chats.length} conversation{chats.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">v1.0</div>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default ChatSidebar;

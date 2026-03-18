import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Copy,
  Check,
  Link2,
  UserPlus,
  Users,
  Crown,
  Edit2,
  Eye,
  Trash2,
  Loader2,
  Mail,
  Search,
  Share2,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { api } from "@/services/api";

const ROLES = [
  { value: "editor", label: "Editor", icon: Edit2, desc: "Can analyze and edit" },
  { value: "viewer", label: "Viewer", icon: Eye, desc: "Can view only" },
];

/**
 * ShareChatModal — lets the session owner invite collaborators
 * via email or generate a shareable invite link.
 */
export function ShareChatModal({
  sessionId,
  sessionTitle,
  isOpen,
  onClose,
  onCollaboratorsChanged,
}) {
  const [tab, setTab] = useState("invite"); // "invite" | "link" | "members"
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState("");
  const [inviteError, setInviteError] = useState("");

  // Link tab
  const [shareLink, setShareLink] = useState("");
  const [linkRole, setLinkRole] = useState("editor");
  const [isCreatingLink, setIsCreatingLink] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [activeLinks, setActiveLinks] = useState([]);
  const [linkError, setLinkError] = useState("");

  // Members tab
  const [owner, setOwner] = useState(null);
  const [collaborators, setCollaborators] = useState([]);
  const [myRole, setMyRole] = useState(null);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);

  const searchTimeout = useRef(null);
  const emailInputRef = useRef(null);

  // Load collaborators when modal opens — also reset transient state
  useEffect(() => {
    if (isOpen && sessionId) {
      // Reset transient state for fresh open
      setEmail("");
      setSearchResults([]);
      setInviteSuccess("");
      setInviteError("");
      setShareLink("");
      setLinkCopied(false);
      setLinkError("");
      loadMembers();
      loadLinks();
    }
  }, [isOpen, sessionId]);

  // Focus email input when invite tab is active
  useEffect(() => {
    if (isOpen && tab === "invite" && emailInputRef.current) {
      setTimeout(() => emailInputRef.current?.focus(), 200);
    }
  }, [isOpen, tab]);

  const loadMembers = async () => {
    setIsLoadingMembers(true);
    try {
      const res = await api.getCollaborators(sessionId);
      setOwner(res.owner);
      setCollaborators(res.collaborators || []);
      setMyRole(res.myRole);
    } catch (e) {
      console.error("Failed to load collaborators:", e);
    } finally {
      setIsLoadingMembers(false);
    }
  };

  const loadLinks = async () => {
    try {
      const res = await api.getShareLinks(sessionId);
      setActiveLinks(res.links || []);
    } catch {
      // owner-only, may fail for collaborators
    }
  };

  // Debounced user search
  const handleEmailChange = (val) => {
    setEmail(val);
    setInviteError("");
    setInviteSuccess("");
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (val.length >= 2) {
      setIsSearching(true);
      searchTimeout.current = setTimeout(async () => {
        try {
          const res = await api.searchUsers(val);
          setSearchResults(res.users || []);
        } catch {
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      }, 300);
    } else {
      setSearchResults([]);
      setIsSearching(false);
    }
  };

  const handleInvite = async (targetEmail) => {
    setIsInviting(true);
    setInviteError("");
    setInviteSuccess("");
    try {
      const res = await api.inviteCollaborator(sessionId, targetEmail, role);
      setInviteSuccess(`Invited ${targetEmail} as ${role}`);
      setEmail("");
      setSearchResults([]);
      loadMembers();
      onCollaboratorsChanged?.();
    } catch (e) {
      setInviteError(e.message);
    } finally {
      setIsInviting(false);
    }
  };

  const handleCreateLink = async () => {
    setIsCreatingLink(true);
    setLinkError("");
    try {
      const res = await api.createShareLink(sessionId, linkRole, 72);
      const url = `${window.location.origin}/join/${res.token}`;
      setShareLink(url);
      loadLinks();
    } catch (e) {
      setLinkError(e.message || "Failed to create share link");
    } finally {
      setIsCreatingLink(false);
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch {
      // fallback
      const ta = document.createElement("textarea");
      ta.value = shareLink;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    }
  };

  const handleRemoveMember = async (userId) => {
    try {
      await api.removeCollaborator(sessionId, userId);
      loadMembers();
      onCollaboratorsChanged?.();
    } catch (e) {
      console.error("Failed to remove:", e);
    }
  };

  const handleRevokeLink = async (token) => {
    try {
      await api.revokeShareLink(token, sessionId);
      loadLinks();
      if (shareLink.includes(token)) setShareLink("");
    } catch (e) {
      console.error("Failed to revoke:", e);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
          />
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-0 flex items-center justify-center z-[101] pointer-events-none"
          >
            <div
              className="bg-card border border-border/70 rounded-3xl shadow-2xl w-[480px] max-h-[80vh] flex flex-col pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-border/60">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center">
                    <Share2 size={18} className="text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Share Chat</h2>
                    <p className="text-xs text-muted-foreground truncate max-w-[280px]">
                      {sessionTitle || "Untitled"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-muted rounded-xl text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-border/60">
                {[
                  { id: "invite", label: "Invite", icon: UserPlus },
                  { id: "link", label: "Share Link", icon: Link2 },
                  { id: "members", label: "Members", icon: Users },
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors border-b-2 ${
                      tab === t.id
                        ? "border-primary text-primary"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <t.icon size={15} />
                    {t.label}
                    {t.id === "members" && collaborators.length > 0 && (
                      <span className="ml-1 text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded-full">
                        {collaborators.length}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* ── Invite by Email ── */}
                {tab === "invite" && (
                  <div className="space-y-4">
                    {/* Role selector */}
                    <div className="flex gap-2">
                      {ROLES.map((r) => (
                        <button
                          key={r.value}
                          onClick={() => setRole(r.value)}
                          className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                            role === r.value
                              ? "border-primary/50 bg-primary/10 text-primary"
                              : "border-border/60 text-muted-foreground hover:border-primary/30"
                          }`}
                        >
                          <r.icon size={14} />
                          <div className="text-left">
                            <div>{r.label}</div>
                            <div className="text-[10px] opacity-70">{r.desc}</div>
                          </div>
                        </button>
                      ))}
                    </div>

                    {/* Email input */}
                    <div className="relative">
                      <Mail
                        size={16}
                        className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                      />
                      <input
                        ref={emailInputRef}
                        type="email"
                        placeholder="Enter email to invite..."
                        value={email}
                        onChange={(e) => handleEmailChange(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && email.includes("@")) handleInvite(email);
                        }}
                        className="w-full bg-background border border-border/60 rounded-xl pl-10 pr-4 py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary/50 transition-colors"
                      />
                      {isSearching && (
                        <Loader2
                          size={16}
                          className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-muted-foreground"
                        />
                      )}
                    </div>

                    {/* Search results dropdown */}
                    {searchResults.length > 0 && (
                      <div className="border border-border/60 rounded-xl overflow-hidden">
                        {searchResults.map((u) => (
                          <button
                            key={u.clerkUserId}
                            onClick={() => handleInvite(u.email)}
                            disabled={isInviting}
                            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors text-left"
                          >
                            <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center text-xs font-bold text-primary">
                              {(u.name || u.email || "?")[0].toUpperCase()}
                            </div>
                            <div className="flex-1 min-w-0">
                              {u.name && (
                                <p className="text-sm font-medium text-foreground truncate">
                                  {u.name}
                                </p>
                              )}
                              <p className="text-xs text-muted-foreground truncate">{u.email}</p>
                            </div>
                            <UserPlus size={14} className="text-primary flex-shrink-0" />
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Direct invite button */}
                    {email.includes("@") && searchResults.length === 0 && !isSearching && (
                      <button
                        onClick={() => handleInvite(email)}
                        disabled={isInviting}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl font-medium text-sm transition-colors disabled:opacity-50"
                      >
                        {isInviting ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Mail size={16} />
                        )}
                        Invite {email}
                      </button>
                    )}

                    {/* Status messages */}
                    {inviteSuccess && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 px-4 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl"
                      >
                        <Check size={16} className="text-emerald-500" />
                        <span className="text-sm text-emerald-400">{inviteSuccess}</span>
                      </motion.div>
                    )}
                    {inviteError && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 px-4 py-3 bg-destructive/10 border border-destructive/30 rounded-xl"
                      >
                        <X size={16} className="text-destructive" />
                        <span className="text-sm text-destructive">{inviteError}</span>
                      </motion.div>
                    )}
                  </div>
                )}

                {/* ── Share Link ── */}
                {tab === "link" && (
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Generate a link anyone can use to join this chat session.
                    </p>

                    {/* Role selector */}
                    <div className="flex gap-2">
                      {ROLES.map((r) => (
                        <button
                          key={r.value}
                          onClick={() => setLinkRole(r.value)}
                          className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                            linkRole === r.value
                              ? "border-primary/50 bg-primary/10 text-primary"
                              : "border-border/60 text-muted-foreground hover:border-primary/30"
                          }`}
                        >
                          <r.icon size={14} />
                          {r.label}
                        </button>
                      ))}
                    </div>

                    {!shareLink ? (
                      <button
                        onClick={handleCreateLink}
                        disabled={isCreatingLink}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl font-medium text-sm transition-colors disabled:opacity-50"
                      >
                        {isCreatingLink ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Link2 size={16} />
                        )}
                        Generate Invite Link
                      </button>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 p-3 bg-background border border-border/60 rounded-xl">
                          <Link2 size={14} className="text-primary flex-shrink-0" />
                          <span className="text-xs text-muted-foreground truncate flex-1">
                            {shareLink}
                          </span>
                          <button
                            onClick={handleCopyLink}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/15 hover:bg-primary/25 text-primary rounded-lg text-xs font-medium transition-colors flex-shrink-0"
                          >
                            {linkCopied ? <Check size={12} /> : <Copy size={12} />}
                            {linkCopied ? "Copied!" : "Copy"}
                          </button>
                        </div>
                        <button
                          onClick={() => {
                            setShareLink("");
                            handleCreateLink();
                          }}
                          className="w-full flex items-center justify-center gap-2 py-2.5 border border-border/60 hover:border-primary/40 text-muted-foreground hover:text-primary rounded-xl text-sm transition-colors"
                        >
                          <RefreshCw size={14} />
                          Generate New Link
                        </button>
                      </div>
                    )}

                    {/* Link error message */}
                    {linkError && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 px-4 py-3 bg-destructive/10 border border-destructive/30 rounded-xl"
                      >
                        <X size={16} className="text-destructive" />
                        <span className="text-sm text-destructive">{linkError}</span>
                      </motion.div>
                    )}

                    {/* Active links */}
                    {activeLinks.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          Active Links ({activeLinks.length})
                        </p>
                        {activeLinks.map((link) => (
                          <div
                            key={link.token}
                            className="flex items-center justify-between px-3 py-2 bg-background/50 border border-border/40 rounded-xl"
                          >
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Link2 size={12} />
                              <span>{link.role}</span>
                              <span>·</span>
                              <span>{link.usedBy?.length || 0} joined</span>
                            </div>
                            <button
                              onClick={() => handleRevokeLink(link.token)}
                              className="text-xs text-destructive/70 hover:text-destructive transition-colors"
                            >
                              Revoke
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ── Members ── */}
                {tab === "members" && (
                  <div className="space-y-3">
                    {isLoadingMembers ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 size={24} className="animate-spin text-primary" />
                      </div>
                    ) : (
                      <>
                        {/* Owner */}
                        {owner && (
                          <div className="flex items-center gap-3 px-4 py-3 bg-primary/5 border border-primary/20 rounded-xl">
                            <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold text-primary">
                              {(owner.name || owner.email || "O")[0].toUpperCase()}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground truncate">
                                {owner.name || owner.email || owner.userId}
                              </p>
                              {owner.email && (
                                <p className="text-xs text-muted-foreground truncate">
                                  {owner.email}
                                </p>
                              )}
                            </div>
                            <span className="flex items-center gap-1 text-xs font-semibold text-primary bg-primary/10 px-2 py-1 rounded-lg">
                              <Crown size={12} />
                              Owner
                            </span>
                          </div>
                        )}

                        {/* Collaborators */}
                        {collaborators.length === 0 ? (
                          <div className="text-center py-6">
                            <Users size={32} className="mx-auto mb-2 text-muted-foreground/50" />
                            <p className="text-sm text-muted-foreground">No collaborators yet</p>
                            <p className="text-xs text-muted-foreground/70 mt-1">
                              Invite others using the Invite or Share Link tab
                            </p>
                          </div>
                        ) : (
                          collaborators.map((c) => (
                            <div
                              key={c.userId}
                              className="flex items-center gap-3 px-4 py-3 bg-background/50 border border-border/40 rounded-xl"
                            >
                              <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center text-sm font-bold text-muted-foreground">
                                {(c.name || c.email || "U")[0].toUpperCase()}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-foreground truncate">
                                  {c.name || c.email || c.userId}
                                </p>
                                {c.email && (
                                  <p className="text-xs text-muted-foreground truncate">
                                    {c.email}
                                  </p>
                                )}
                              </div>
                              <span className="flex items-center gap-1 text-xs text-muted-foreground bg-muted px-2 py-1 rounded-lg capitalize">
                                {c.role === "editor" ? <Edit2 size={10} /> : <Eye size={10} />}
                                {c.role}
                              </span>
                              {myRole === "owner" && (
                                <button
                                  onClick={() => handleRemoveMember(c.userId)}
                                  className="p-1.5 hover:bg-destructive/10 rounded-lg text-muted-foreground hover:text-destructive transition-colors"
                                  title="Remove collaborator"
                                >
                                  <Trash2 size={14} />
                                </button>
                              )}
                            </div>
                          ))
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default ShareChatModal;

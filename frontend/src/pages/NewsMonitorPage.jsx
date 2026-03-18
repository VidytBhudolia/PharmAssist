import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radar,
  ArrowLeft,
  RefreshCw,
  Eye,
  EyeOff,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Clock,
  X,
  Loader2,
  Bell,
  FileText,
  ShieldAlert,
  Play,
} from "lucide-react";
import { api } from "@/services/api";

/**
 * Status dot colour mapping
 */
const STATUS_DOT = {
  secure: "bg-emerald-500",
  changed: "bg-red-500",
  error: "bg-gray-400",
};

const STATUS_LABEL = {
  secure: "Secure",
  changed: "Changed",
  error: "Error",
};

const SEVERITY_COLORS = {
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  high: "bg-red-500/15 text-red-400 border-red-500/30",
};

function SeverityBadge({ severity }) {
  const cls = SEVERITY_COLORS[severity] || SEVERITY_COLORS.low;
  const label = severity ? severity.charAt(0).toUpperCase() + severity.slice(1) : "Low";
  return (
    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${cls}`}>{label}</span>
  );
}

function StatusDot({ status }) {
  const color = STATUS_DOT[status] || "bg-gray-500";
  return (
    <span title={STATUS_LABEL[status] || status} className="flex items-center gap-1.5">
      <span
        className={`w-2.5 h-2.5 rounded-full ${color} ${status === "changed" ? "animate-pulse" : ""}`}
      />
      <span className="text-xs text-muted-foreground">{STATUS_LABEL[status] || status}</span>
    </span>
  );
}

/**
 * Detail panel for a single notification
 */
function NotificationDetailPanel({ notification, onClose, onRerunCheck, isRechecking }) {
  if (!notification) return null;

  const details = notification.details || {};
  const changedFields = notification.changedFields || [];

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="bg-card border border-border rounded-2xl p-5 shadow-xl"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert size={18} className="text-amber-400" />
          <h3 className="text-sm font-semibold text-foreground">Change Details</h3>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-muted rounded-lg transition-colors">
          <X size={16} className="text-muted-foreground" />
        </button>
      </div>

      {/* Summary banner */}
      <div className="mb-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
        <p className="text-xs font-semibold text-amber-300">
          Researcher Takeaway: {notification.decision_reason || "Review recommended"}
        </p>
        <p className="text-xs text-amber-200/70 mt-1">
          Changed fields: {changedFields.join(", ") || "None"}
        </p>
      </div>

      {/* Detailed fields */}
      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {Object.entries(details).map(([fieldKey, fieldDetail]) => {
          if (!fieldDetail || typeof fieldDetail !== "object") return null;
          // fieldDetail may be nested (for patents, it can have sub-keys)
          const entries =
            fieldDetail.oldValue !== undefined
              ? [[fieldKey, fieldDetail]]
              : Object.entries(fieldDetail);

          return entries.map(([subKey, detail]) => (
            <div
              key={`${fieldKey}-${subKey}`}
              className="p-3 rounded-lg bg-muted/30 border border-border/50"
            >
              <p className="text-xs font-semibold text-foreground mb-1">{subKey}</p>
              {detail.note && <p className="text-xs text-muted-foreground mb-1.5">{detail.note}</p>}
              <div className="flex gap-4 text-xs">
                <div className="flex-1">
                  <span className="text-muted-foreground">Old: </span>
                  <span className="text-red-300">
                    {detail.oldValue != null ? JSON.stringify(detail.oldValue) : "—"}
                  </span>
                </div>
                <div className="flex-1">
                  <span className="text-muted-foreground">New: </span>
                  <span className="text-emerald-300">
                    {detail.newValue != null ? JSON.stringify(detail.newValue) : "—"}
                  </span>
                </div>
              </div>
              {detail.confidenceScore != null && (
                <p className="text-[10px] text-muted-foreground mt-1">
                  Confidence: {(detail.confidenceScore * 100).toFixed(0)}%
                </p>
              )}
            </div>
          ));
        })}
      </div>

      {notification.requiresManualReview && (
        <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center gap-2">
          <AlertTriangle size={14} className="text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">
            Manual review recommended — some comparisons are ambiguous.
          </p>
        </div>
      )}

      {/* Rerun button */}
      <button
        onClick={onRerunCheck}
        disabled={isRechecking}
        className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-semibold transition-colors disabled:opacity-50"
      >
        {isRechecking ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
        {isRechecking ? "Rechecking..." : "Rerun Analysis"}
      </button>
    </motion.div>
  );
}

/**
 * NewsMonitorPage — main component
 *
 * Shows ALL monitored notifications across every session.
 * Includes an intel input bar to broadcast new intelligence against all monitored chats.
 */
export default function NewsMonitorPage({
  onBack,
  onSelectChat,
  onRefreshMonitored,
  broadcastResult,
  onClearBroadcastResult,
  registerRefetch,
}) {
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNotif, setSelectedNotif] = useState(null);
  const [recheckingId, setRecheckingId] = useState(null);
  const [error, setError] = useState(null);

  // Intel input state — lifted to Dashboard; broadcastResult comes in as a prop

  const fetchMonitored = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAllMonitored();
      setNotifications(data.notifications || []);
    } catch (e) {
      console.error("[NewsMonitor] Failed to fetch:", e);
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMonitored();
  }, [fetchMonitored]);

  // Register refetch callback so Dashboard can trigger a refresh after broadcast
  useEffect(() => {
    if (registerRefetch) registerRefetch(fetchMonitored);
  }, [registerRefetch, fetchMonitored]);

  const handleRerunCheck = async (notif, rerunAnalysis = false) => {
    setRecheckingId(notif.promptId);
    try {
      const result = await api.recheckNotification(notif.sessionId, notif.promptId, rerunAnalysis);
      // Update local state
      setNotifications((prev) =>
        prev.map((n) =>
          n.promptId === notif.promptId
            ? {
                ...n,
                status: result.notification?.status || n.status,
                severity: result.notification?.severity || n.severity,
                changedFields: result.notification?.changedFields || n.changedFields,
                details: result.notification?.details || n.details,
                lastCheckedAt: result.notification?.lastCheckedAt || n.lastCheckedAt,
                requiresManualReview: result.notification?.requiresManualReview || false,
                decision_reason: result.notification?.decision_reason || n.decision_reason,
              }
            : n,
        ),
      );
      if (selectedNotif?.promptId === notif.promptId) {
        setSelectedNotif((prev) => ({
          ...prev,
          ...result.notification,
        }));
      }
    } catch (e) {
      console.error("[NewsMonitor] Recheck failed:", e);
    } finally {
      setRecheckingId(null);
    }
  };

  const handleDisable = async (notif) => {
    try {
      await api.enableNotification(notif.sessionId, notif.promptId, "", false);
      setNotifications((prev) => prev.filter((n) => n.promptId !== notif.promptId));
      // Sync parent's monitored sets
      if (onRefreshMonitored) onRefreshMonitored();
    } catch (e) {
      console.error("[NewsMonitor] Disable failed:", e);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await api.acknowledgeAllNotifications();
      // Refresh to get updated acknowledgement status
      await fetchMonitored();
      // Refresh parent's monitored sets to update badges
      if (onRefreshMonitored) onRefreshMonitored();
    } catch (e) {
      console.error("[NewsMonitor] Acknowledge failed:", e);
    }
  };

  return (
    <div className="flex flex-col h-full p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-muted rounded-xl transition-colors">
            <ArrowLeft size={20} className="text-muted-foreground" />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
              <Radar size={20} className="text-amber-400" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">News Monitor</h1>
              <p className="text-xs text-muted-foreground">Track changes across your research</p>
            </div>
          </div>
        </div>
        <button
          onClick={handleAcknowledgeAll}
          disabled={isLoading || notifications.length === 0}
          title="Mark all as reviewed (clears red badges)"
          className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
        >
          <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Content */}
      <div className="flex gap-6 flex-1 min-h-0">
        {/* List */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={24} className="animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <AlertTriangle size={28} className="text-destructive mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-20">
              <Bell size={32} className="text-muted-foreground mx-auto mb-3 opacity-40" />
              <p className="text-sm font-medium text-foreground">No monitored research</p>
              <p className="text-xs text-muted-foreground mt-1.5 max-w-[250px] mx-auto">
                Enable notifications on a chat to start monitoring for changes
              </p>
            </div>
          ) : (
            notifications.map((notif) => {
              const isSelected = selectedNotif?.notificationId === notif.notificationId;
              return (
                <motion.div
                  key={notif.notificationId}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200
                    ${
                      isSelected
                        ? "bg-card border-amber-500/40 shadow-lg"
                        : "bg-card/60 border-border hover:border-amber-500/30 hover:bg-card/80"
                    }`}
                  onClick={() => setSelectedNotif(notif)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <StatusDot status={notif.status || "secure"} />
                        <SeverityBadge severity={notif.severity} />
                      </div>
                      <p
                        className="text-sm font-medium text-foreground truncate cursor-pointer hover:text-primary transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onSelectChat) onSelectChat(notif.sessionId);
                        }}
                      >
                        {notif.chatTitle || notif.tagName || "Untitled Research"}
                      </p>
                      <div className="flex items-center gap-3 mt-1.5">
                        {notif.lastCheckedAt ? (
                          <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                            <Clock size={10} />
                            {new Date(notif.lastCheckedAt).toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-[11px] text-muted-foreground">Never checked</span>
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedNotif(notif);
                        }}
                        className="p-1.5 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                        title="View Details"
                      >
                        <FileText size={14} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRerunCheck(notif);
                        }}
                        disabled={recheckingId === notif.promptId}
                        className="p-1.5 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
                        title="Rerun Check"
                      >
                        {recheckingId === notif.promptId ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          <RefreshCw size={14} />
                        )}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDisable(notif);
                        }}
                        className="p-1.5 hover:bg-destructive/10 rounded-lg text-muted-foreground hover:text-destructive transition-colors"
                        title="Disable Monitoring"
                      >
                        <EyeOff size={14} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>

        {/* Detail panel */}
        <AnimatePresence>
          {selectedNotif && (
            <div className="w-[380px] flex-shrink-0">
              <NotificationDetailPanel
                notification={selectedNotif}
                onClose={() => setSelectedNotif(null)}
                onRerunCheck={() => handleRerunCheck(selectedNotif, true)}
                isRechecking={recheckingId === selectedNotif?.promptId}
              />
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* Broadcast result banner */}
      <AnimatePresence>
        {broadcastResult && !broadcastResult.error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className={`mb-3 p-3 rounded-xl border flex items-center justify-between ${
              broadcastResult.affectedCount > 0
                ? "bg-amber-500/10 border-amber-500/30"
                : "bg-emerald-500/10 border-emerald-500/30"
            }`}
          >
            <div className="flex items-center gap-2">
              {broadcastResult.affectedCount > 0 ? (
                <AlertTriangle size={16} className="text-amber-400" />
              ) : (
                <CheckCircle2 size={16} className="text-emerald-400" />
              )}
              <p className="text-xs text-foreground">
                Checked {broadcastResult.totalChecked} monitored chat
                {broadcastResult.totalChecked !== 1 ? "s" : ""}.
                {broadcastResult.affectedCount > 0
                  ? ` ${broadcastResult.affectedCount} affected — notifications added to chat history.`
                  : " No changes detected."}
              </p>
            </div>
            <button
              onClick={() => onClearBroadcastResult?.()}
              className="p-1 hover:bg-muted rounded-lg text-muted-foreground"
            >
              <X size={14} />
            </button>
          </motion.div>
        )}
        {broadcastResult?.error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mb-3 p-3 rounded-xl bg-destructive/10 border border-destructive/30 flex items-center justify-between"
          >
            <p className="text-xs text-destructive">{broadcastResult.error}</p>
            <button
              onClick={() => onClearBroadcastResult?.()}
              className="p-1 hover:bg-muted rounded-lg text-muted-foreground"
            >
              <X size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

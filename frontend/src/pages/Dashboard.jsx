import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth, UserButton } from "@clerk/clerk-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Send,
  Plus,
  Loader2,
  Network,
  TrendingUp,
  Scale,
  Microscope,
  Database,
  FileText,
  Globe,
  Shield,
  Activity,
  BookOpen,
  FileBarChart,
  X,
  AlertCircle,
  Eye,
  ChevronLeft,
  ChevronRight,
  Paperclip,
  File,
  Sparkles,
  Mic,
  MicOff,
  Volume2,
  Bell,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ShareChatModal } from "@/components/ShareChatModal";
import { PDFViewerModal } from "@/components/PDFViewerModal_v2";
import { useChatManager } from "@/hooks/useChatManager";
import { useVoiceAssistant, VoiceMode } from "@/hooks/useVoiceAssistant";
import { LandingPage } from "@/components/LandingPage";
import { api } from "@/services/api";
import { VoiceAssistantPanel, VoiceIndicator } from "@/components/VoiceAssistantPanel";
import {
  IQVIADataDisplay,
  EXIMDataDisplay,
  PatentDataDisplay,
  ClinicalDataDisplay,
  InternalKnowledgeDisplay,
  WebIntelDisplay,
} from "@/components/AgentDataDisplaysNew";
import { getAgentSummary } from "@/components/AgentDataDisplays";
import { VizList } from "@/components/visualizations";
import { AgentErrorBoundary } from "@/components/ErrorBoundary";
import NewsMonitorPage from "@/pages/NewsMonitorPage";
import { useCompareStudies } from "@/hooks/useCompareStudies";
import { ChatSelectionModal } from "@/components/ChatSelectionModal";
import { CompareStudiesView } from "@/components/CompareStudiesView";

const AGENT_ID_MAP = {
  iqvia: 0,
  exim: 1,
  patent: 2,
  clinical: 3,
  internal: 4,
  internal_knowledge: 4,
  web: 5,
  webintel: 5,
  webintelligence: 5,
};

const AGENTS = [
  {
    id: 0,
    key: "iqvia",
    name: "IQVIA Insights",
    desc: "Market size, growth & competitive analysis",
    icon: TrendingUp,
    color: "blue",
    features: ["Sales data analytics", "Market trends & forecasts", "Competitive intelligence"],
  },
  {
    id: 1,
    key: "exim",
    name: "Exim Trends",
    desc: "Export-Import & trade analysis",
    icon: Globe,
    color: "cyan",
    features: ["Trade volume tracking", "API price analysis", "Tariff & regulation insights"],
  },
  {
    id: 2,
    key: "patent",
    name: "Patent Landscape",
    desc: "FTO analysis & lifecycle strategy",
    icon: Shield,
    color: "amber",
    features: ["Patent expiry tracking", "FTO risk assessment", "IP landscape mapping"],
  },
  {
    id: 3,
    key: "clinical",
    name: "Clinical Trials",
    desc: "MoA mapping & pipeline analysis",
    icon: Activity,
    color: "green",
    features: ["Trial database search", "MoA identification", "Pipeline opportunity scan"],
  },
  {
    id: 4,
    key: "internal",
    name: "Internal Knowledge",
    desc: "Company data & previous research",
    icon: BookOpen,
    color: "pink",
    features: ["Past research archive", "Expert network access", "Document intelligence"],
  },
  {
    id: 5,
    key: "web",
    name: "Web Intelligence",
    desc: "Real-time web signals & market trends",
    icon: Globe,
    color: "violet",
    features: [
      "Trending topics tracking",
      "News & updates monitoring",
      "Community discussions analysis",
    ],
  },
];

const colorClasses = {
  blue: {
    active: "from-sky-500/15 via-sky-500/5 to-transparent",
    inactive: "from-sky-900/10 border-border hover:border-sky-500/50",
    icon: "bg-sky-500/15 border border-sky-500/30",
    iconColor: "text-sky-400",
    dot: "text-sky-400",
    border: "border-sky-500/30",
  },
  cyan: {
    active: "from-teal-500/15 via-teal-500/5 to-transparent",
    inactive: "from-teal-900/10 border-border hover:border-teal-500/50",
    icon: "bg-teal-500/15 border border-teal-500/30",
    iconColor: "text-teal-400",
    dot: "text-teal-400",
    border: "border-teal-500/30",
  },
  amber: {
    active: "from-amber-500/15 via-amber-500/5 to-transparent",
    inactive: "from-amber-900/10 border-border hover:border-amber-500/50",
    icon: "bg-amber-500/15 border border-amber-500/30",
    iconColor: "text-amber-400",
    dot: "text-amber-400",
    border: "border-amber-500/30",
  },
  green: {
    active: "from-emerald-500/15 via-emerald-500/5 to-transparent",
    inactive: "from-emerald-900/10 border-border hover:border-emerald-500/50",
    icon: "bg-emerald-500/15 border border-emerald-500/30",
    iconColor: "text-emerald-400",
    dot: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  pink: {
    active: "from-cyan-500/15 via-cyan-500/5 to-transparent",
    inactive: "from-cyan-900/10 border-border hover:border-cyan-500/50",
    icon: "bg-cyan-500/15 border border-cyan-500/30",
    iconColor: "text-cyan-400",
    dot: "text-cyan-400",
    border: "border-cyan-500/30",
  },
  violet: {
    active: "from-indigo-500/15 via-indigo-500/5 to-transparent",
    inactive: "from-indigo-900/10 border-border hover:border-indigo-500/50",
    icon: "bg-indigo-500/15 border border-indigo-500/30",
    iconColor: "text-indigo-400",
    dot: "text-indigo-400",
    border: "border-indigo-500/30",
  },
};

// Helper function to get hex color from Tailwind color class
const getColorHex = (colorClass) => {
  if (colorClass.includes("sky")) return "#38bdf8";
  if (colorClass.includes("teal")) return "#2dd4bf";
  if (colorClass.includes("cyan")) return "#22d3ee";
  if (colorClass.includes("amber")) return "#fbbf24";
  if (colorClass.includes("emerald") || colorClass.includes("green")) return "#34d399";
  if (colorClass.includes("indigo")) return "#818cf8";
  return "#2dd4bf"; // Default to teal
};

export default function GeminiDashboard() {
  const { isSignedIn, isLoaded: authLoaded } = useAuth();
  const navigate = useNavigate();

  const {
    chats,
    sharedWithMe,
    activeChatId,
    activeChat,
    createChatFromPrompt,
    sendPrompt,
    selectChat,
    deleteChat,
    renameChat,
    updateChatSession,
    loadSharedSessions,
  } = useChatManager({ enabled: !!isSignedIn });
  const [planningPlan, setPlanningPlan] = useState(null);
  const [planningReady, setPlanningReady] = useState(false);

  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [downloadError, setDownloadError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showAgentFlowLocal, setShowAgentFlowLocal] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // PDF Viewer Modal state
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfViewerUrl, setPdfViewerUrl] = useState(null);
  const [pdfViewerLoading, setPdfViewerLoading] = useState(false);
  const [pdfViewerError, setPdfViewerError] = useState(null);

  // Frontend blob URL cache: promptId → { blobUrl, createdAt }
  const pdfBlobCacheRef = useRef({});
  const PDF_BLOB_CACHE_TTL = 5 * 60 * 1000; // 5 minutes in ms

  // Cleanup all blob URLs on unmount
  useEffect(() => {
    return () => {
      Object.values(pdfBlobCacheRef.current).forEach(({ blobUrl }) => {
        try {
          URL.revokeObjectURL(blobUrl);
        } catch {}
      });
      pdfBlobCacheRef.current = {};
    };
  }, []);

  // File upload state for Internal Knowledge Agent
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const agentContentRef = useRef(null);

  // Track used prompt suggestions to avoid duplicates
  const [usedPrompts, setUsedPrompts] = useState(new Set());

  // News Monitor state
  const [showNewsMonitor, setShowNewsMonitor] = useState(false);
  const [monitoredPromptIds, setMonitoredPromptIds] = useState(new Set());
  const [monitoredSessionIds, setMonitoredSessionIds] = useState(new Set());
  const [affectedSessionIds, setAffectedSessionIds] = useState(new Set());

  // News Monitor — broadcast intel state (lifted from NewsMonitorPage)
  const [intelText, setIntelText] = useState("");
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState(null);
  const [broadcastUploadedFile, setBroadcastUploadedFile] = useState(null);
  const [isBroadcastUploading, setIsBroadcastUploading] = useState(false);
  const broadcastFileInputRef = useRef(null);
  const newsMonitorRefetchRef = useRef(null);

  // Compare Studies state
  const compare = useCompareStudies();

  // Share Chat modal state
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareSessionId, setShareSessionId] = useState(null);
  const [shareSessionTitle, setShareSessionTitle] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  // Handle invite token and direct session links from URL
  useEffect(() => {
    const inviteToken = searchParams.get("invite");
    const sessionParam = searchParams.get("session");

    if (sessionParam && isSignedIn) {
      selectChat(sessionParam);
      const nextParams = new URLSearchParams(searchParams);
      nextParams.delete("session");
      setSearchParams(nextParams, { replace: true });
    }

    if (inviteToken && isSignedIn) {
      (async () => {
        try {
          const res = await api.redeemShareLink(inviteToken);
          const sessionId = res.session?.sessionId || res.sessionId;
          if (sessionId) {
            loadSharedSessions?.();
            selectChat(sessionId);
          }
        } catch (e) {
          console.error("[Dashboard] Failed to redeem invite:", e);
        } finally {
          // Remove token from URL
          const nextParams = new URLSearchParams(searchParams);
          nextParams.delete("invite");
          setSearchParams(nextParams, { replace: true });
        }
      })();
    }
  }, [isSignedIn, searchParams, setSearchParams, loadSharedSessions, selectChat]);

  const handleShareChat = (sessionId, title) => {
    setShareSessionId(sessionId);
    setShareSessionTitle(title);
    setShareModalOpen(true);
  };

  // Voice Assistant Integration
  const voice = useVoiceAssistant(activeChatId, {
    autoSpeak: true,
    language: "en-US",
    onTranscript: (text) => {
      console.log("[Voice] Transcript received:", text);
    },
    onResponse: (response) => {
      console.log("[Voice] Response:", response);
    },
    onError: (error) => {
      console.error("[Voice] Error:", error);
      setApiError(error);
    },
    onReadyForPlanning: async (refinedPrompt) => {
      console.log("[Voice] Ready for planning with prompt:", refinedPrompt);
      // Submit the refined prompt through normal flow
      setPrompt(refinedPrompt);
      // Trigger send after a brief delay to allow state update
      setTimeout(() => {
        handleVoiceSendPrompt(refinedPrompt);
      }, 100);
    },
    onModeChange: (mode) => {
      console.log("[Voice] Mode changed to:", mode);
    },
  });

  // Handle voice-triggered prompt submission
  const handleVoiceSendPrompt = async (text) => {
    if (!text?.trim() || isLoading) return;

    setIsLoading(true);
    setApiError(null);

    try {
      let result;
      if (!activeChatId) {
        result = await createChatFromPrompt(text);
      } else {
        result = await sendPrompt(text);
      }

      // Reset voice state after successful submission
      voice.reset();

      // Handle planning states
      if (result?.queryType === "planning") {
        setPlanningReady(false);
        setPlanningPlan(null);
        return;
      }

      // Voice already confirmed — auto-execute without showing the confirm dialog
      if (result?.queryType === "ready") {
        setShowAgentFlowLocal(true);
        setIsSidebarCollapsed(true);
        const execRes = await api.executePlan(activeChatId);
        if (execRes.session && execRes.session.sessionId) {
          updateChatSession(execRes.session);
        }
        setPlanningReady(false);
        setPlanningPlan(null);
        return;
      }
    } catch (error) {
      console.error("[Voice] Submit error:", error);
      setApiError("Failed to process voice input");
    } finally {
      setIsLoading(false);
      setPrompt("");
    }
  };

  // Map chats to have 'id' property for ChatSidebar compatibility
  // Filter out any chats without sessionId to prevent errors
  const mappedChats = chats
    .filter((chat) => chat && chat.sessionId)
    .map((chat) => ({
      ...chat,
      id: chat.sessionId,
      messages: chat.chatHistory || [],
      updatedAt: chat.updatedAt || chat.createdAt || new Date().toISOString(),
    }));

  useEffect(() => {
    setPlanningPlan(null);
    setPlanningReady(false);
  }, [activeChatId]);

  // Normalize latest prompt's agent data (agentsData is now an array of prompt entries)
  const latestAgentsEntry = Array.isArray(activeChat?.agentsData)
    ? activeChat.agentsData[activeChat.agentsData.length - 1]
    : null;

  // Normalize agent keys so both "CLINICAL_AGENT" and "clinical" map consistently
  const normalizeAgentKeys = (agentsObj = {}) => {
    const out = {};
    Object.entries(agentsObj).forEach(([key, value]) => {
      // Skip non-agent keys
      if (!key || typeof key !== "string") return;

      let normalizedKey = key
        .toLowerCase()
        .replace(/_agent$/, "")
        .replace(/\s+/g, "");

      // Handle special mappings BEFORE removing underscores
      if (
        normalizedKey === "internal_knowledge" ||
        normalizedKey === "internalknowledge" ||
        normalizedKey === "internal"
      ) {
        normalizedKey = "internal";
      } else if (
        normalizedKey === "web_intelligence" ||
        normalizedKey === "webintelligence" ||
        normalizedKey === "webintel" ||
        normalizedKey === "web"
      ) {
        normalizedKey = "web";
      } else if (
        normalizedKey === "report_generator" ||
        normalizedKey === "reportgenerator" ||
        normalizedKey === "report"
      ) {
        normalizedKey = "report";
      } else if (
        normalizedKey === "clinical_trials" ||
        normalizedKey === "clinicaltrials" ||
        normalizedKey === "clinical"
      ) {
        normalizedKey = "clinical";
      } else {
        // Remove underscores for other keys (iqvia, exim, patent stay as-is)
        normalizedKey = normalizedKey.replace(/_/g, "");
      }

      // Store with normalized key (only if not already present and has valid data)
      if (!out[normalizedKey] && value) {
        out[normalizedKey] = value;
      }
    });
    return out;
  };

  // Try multiple sources for agent data
  const rawAgentData =
    latestAgentsEntry?.agents ||
    (typeof activeChat?.agentsData === "object" && !Array.isArray(activeChat?.agentsData)
      ? activeChat.agentsData
      : {});
  const agentData = normalizeAgentKeys(rawAgentData);

  // Count only agents with actual data and use the same source of truth everywhere
  const VALID_AGENT_KEYS = ["iqvia", "exim", "patent", "clinical", "internal", "web"];
  const hasAgentPayload = (value) => {
    if (value === null || value === undefined) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    if (typeof value === "string") return value.trim().length > 0;
    return Boolean(value);
  };
  const ranAgentKeys = VALID_AGENT_KEYS.filter((key) => hasAgentPayload(agentData[key]));
  const ranAgentKeySet = new Set(ranAgentKeys);
  const agentDataCount = ranAgentKeys.length;

  const hasAgentData = agentDataCount > 0;

  // Get suggested next prompts from latest entry or session, filter out used prompts
  const allSuggestedPrompts =
    latestAgentsEntry?.suggestedNextPrompts || activeChat?.suggestedNextPrompts || [];

  const suggestedNextPrompts = allSuggestedPrompts.filter(
    (suggestion) => !usedPrompts.has(suggestion.prompt),
  );

  // Get aggregated agent scores and critical blockers from orchestrator
  const agentScores = latestAgentsEntry?.agentScores || {};
  const criticalBlockers = latestAgentsEntry?.criticalBlockers || [];

  // Debug logging
  useEffect(() => {
    console.log("[Dashboard] Agent Data Debug:");
    console.log("  Raw agentsData:", activeChat?.agentsData);
    console.log("  Latest entry:", latestAgentsEntry);
    console.log("  Raw agent data (pre-normalization):", rawAgentData);
    console.log("  Normalized agentData:", agentData);
    console.log("  Agent keys in normalized data:", Object.keys(agentData));

    console.log("[Dashboard] Agent Status:");
    AGENTS.forEach((agent) => {
      const data = agentData[agent.key];
      console.log(
        `  ${agent.name} (${agent.key}):`,
        data ? `✓ HAS DATA (keys: ${Object.keys(data).join(", ")})` : "✗ NO DATA",
      );
    });
    console.log("[Dashboard] Raw agentData keys:", Object.keys(agentData));
    console.log("[Dashboard] Normalized agent data:", agentData);
    console.log("[Dashboard] Agent count:", agentDataCount);
  }, [agentData, agentDataCount]);

  const workflowState = activeChat?.workflowState || {
    activeAgent: null,
    showAgentDataByAgent: {},
    reportReady: false,
    workflowComplete: false,
    queryRejected: false,
    systemResponse: null,
    panelCollapsed: false,
    showAgentFlow: false,
  };
  const chatHistory = activeChat?.chatHistory || [];

  const normalizePlanValues = (value) => {
    if (!value) return [];
    if (Array.isArray(value)) return value.filter(Boolean);
    return [value];
  };

  const planAgents = normalizePlanValues(planningPlan?.agents);
  const planDrugs = normalizePlanValues(planningPlan?.drug);
  const planIndications = normalizePlanValues(planningPlan?.indication);

  useEffect(() => {
    setPrompt("");
    setIsLoading(false);
    setApiError(null);
    setIsPinned(false);
    setSelectedAgent(null);

    // Don't auto-show agent flow when selecting a chat - show chat view first
    setShowAgentFlowLocal(false);

    setUploadedFile(null);

    // Reset used prompts when changing chats
    setUsedPrompts(new Set());
  }, [activeChatId]);

  const handleNewChat = () => {
    setApiError(null);
    // Reset used prompts for new chat
    setUsedPrompts(new Set());
    // Close news monitor if open
    setShowNewsMonitor(false);
    // Just deselect current chat to show landing page
    selectChat(null);
  };

  const handleSelectChat = (chatId) => {
    setShowNewsMonitor(false);
    selectChat(chatId);
  };

  const handleDeleteChat = (chatId) => {
    deleteChat(chatId);
  };

  const handleRenameChat = async (chatId, newTitle) => {
    try {
      await renameChat(chatId, newTitle);
    } catch (error) {
      console.error("[Dashboard] Failed to rename chat:", error);
    }
  };

  // --- News Monitor handlers ---
  const handleToggleMonitoring = async (sessionId, promptId, enabled) => {
    try {
      await api.enableNotification(sessionId, promptId, "", enabled);
      setMonitoredPromptIds((prev) => {
        const next = new Set(prev);
        if (enabled) next.add(promptId);
        else next.delete(promptId);
        return next;
      });
      setMonitoredSessionIds((prev) => {
        const next = new Set(prev);
        if (enabled) next.add(sessionId);
        // Note: only remove session if no other promptIds are monitored for it
        // For simplicity, re-fetch all after toggle
        return next;
      });
      // Re-fetch all monitored to stay in sync
      refreshAllMonitored();
    } catch (e) {
      console.error("[Dashboard] Toggle monitoring failed:", e);
    }
  };

  const handleOpenNewsMonitor = () => {
    setShowNewsMonitor(true);
    setIsSidebarCollapsed(true);
  };

  // Fetch ALL monitored promptIds/sessionIds on mount (and after toggle)
  const refreshAllMonitored = useCallback(async () => {
    try {
      const data = await api.getAllMonitored();
      const notifications = (data.notifications || []).filter((n) => n.enabled);
      setMonitoredPromptIds(new Set(notifications.map((n) => n.promptId)));
      setMonitoredSessionIds(new Set(notifications.map((n) => n.sessionId)));
      // Track which sessions have unacknowledged intel notifications
      const affected = notifications.filter((n) => n.affectedByIntel && !n.acknowledged);
      setAffectedSessionIds(new Set(affected.map((n) => n.sessionId)));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if (isSignedIn) {
      refreshAllMonitored();
    }
  }, [isSignedIn, refreshAllMonitored]);

  // Handle suggested prompt clicks from agent displays
  const handleSuggestedPromptClick = (promptText) => {
    // Track this prompt as used to avoid showing it again
    setUsedPrompts((prev) => new Set([...prev, promptText]));
    setPrompt(promptText);
    setShowAgentFlowLocal(false);
  };

  // File upload handlers for Internal Knowledge Agent
  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/vnd.ms-powerpoint",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
      "text/csv",
    ];

    if (!allowedTypes.includes(file.type)) {
      setApiError("Unsupported file type. Please upload PDF, PPT, Excel, Word, TXT, or CSV files.");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setApiError("File too large. Maximum size is 10MB.");
      return;
    }

    setIsUploading(true);
    setApiError(null);

    try {
      // Get or create session ID
      let sessionId = localStorage.getItem("activeSessionId");
      if (!sessionId) {
        // Create a new session if none exists
        const result = await api.createSession();
        sessionId = result.sessionId;
        localStorage.setItem("activeSessionId", sessionId);
      }

      // Upload the file
      const response = await api.uploadDocument(sessionId, file);
      setUploadedFile({
        name: file.name,
        size: file.size,
        type: file.type,
        ...response,
      });
      console.log("[Dashboard] File uploaded successfully:", response);
    } catch (error) {
      console.error("[Dashboard] File upload failed:", error);
      setApiError("Failed to upload file. Please try again.");
    } finally {
      setIsUploading(false);
      // Reset input so same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleRemoveFile = async () => {
    const sessionId = localStorage.getItem("activeSessionId");
    if (sessionId && uploadedFile) {
      try {
        await api.deleteDocument(sessionId);
      } catch (error) {
        console.error("[Dashboard] Failed to delete document:", error);
      }
    }
    setUploadedFile(null);
  };

  const handleSendPrompt = async () => {
    const text = prompt.trim();
    if (!text || isLoading) return;

    // Require authentication to send prompts
    if (!isSignedIn) {
      navigate("/sign-in");
      return;
    }

    setPrompt("");
    setIsLoading(true);
    setApiError(null);

    try {
      let result;
      if (!activeChatId) {
        result = await createChatFromPrompt(text);
      } else {
        result = await sendPrompt(text);
      }

      // 🧠 PLANNING MODE
      if (result?.queryType === "planning") {
        setPlanningReady(false);
        setPlanningPlan(null);
        return;
      }

      if (result?.queryType === "ready") {
        setPlanningPlan(result.plan);
        setPlanningReady(true);
        return;
      }

      // "run analysis" keyword → auto-execute pending plan
      if (result?.queryType === "confirm") {
        setShowAgentFlowLocal(true);
        setIsSidebarCollapsed(true);
        const execRes = await api.executePlan(activeChatId);
        if (execRes.session && execRes.session.sessionId) {
          updateChatSession(execRes.session);
        }
        setPlanningReady(false);
        setPlanningPlan(null);
        return;
      }
    } catch {
      setApiError("Failed to process prompt");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendPrompt();
    }
  };

  // ── News Monitor broadcast helpers (lifted from NewsMonitorPage) ──────────
  const handleBroadcastFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/vnd.ms-powerpoint",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
      "text/csv",
    ];
    if (!allowedTypes.includes(file.type)) {
      setBroadcastResult({
        error: "Unsupported file type. Please upload PDF, PPT, Excel, Word, TXT, or CSV files.",
      });
      return;
    }
    setBroadcastUploadedFile(file);
    if (broadcastFileInputRef.current) broadcastFileInputRef.current.value = "";
  };

  const handleBroadcastRemoveFile = () => {
    setBroadcastUploadedFile(null);
  };

  const handleBroadcastIntel = async () => {
    if ((!intelText.trim() && !broadcastUploadedFile) || isBroadcasting) return;
    setIsBroadcasting(true);
    setBroadcastResult(null);
    try {
      let textToSend = intelText.trim();
      if (broadcastUploadedFile) {
        setIsBroadcastUploading(true);
        const formData = new FormData();
        formData.append("file", broadcastUploadedFile);
        const uploadResponse = await fetch("http://localhost:8000/news/parse-document", {
          method: "POST",
          body: formData,
        });
        if (!uploadResponse.ok) throw new Error("File upload failed");
        const uploadData = await uploadResponse.json();
        const parsedText = uploadData.parsed_content || "";
        textToSend = textToSend ? `${textToSend}\n\n${parsedText}` : parsedText;
        setIsBroadcastUploading(false);
      }
      const result = await api.broadcastIntel(textToSend);
      setBroadcastResult(result);
      setIntelText("");
      setBroadcastUploadedFile(null);
      // Refresh the NewsMonitorPage notification list via a callback ref
      if (newsMonitorRefetchRef.current) newsMonitorRefetchRef.current();
    } catch (e) {
      console.error("[Dashboard] Broadcast failed:", e);
      setBroadcastResult({ error: e.message });
      setIsBroadcastUploading(false);
    } finally {
      setIsBroadcasting(false);
    }
  };

  const handleBroadcastKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleBroadcastIntel();
    }
  };
  // ─────────────────────────────────────────────────────────────────────────

  const handleViewReport = async (promptId) => {
    try {
      console.log("[ViewReport] Opening report viewer for promptId:", promptId);

      // Check frontend blob URL cache first
      const cached = pdfBlobCacheRef.current[promptId];
      if (cached && Date.now() - cached.createdAt < PDF_BLOB_CACHE_TTL) {
        console.log(
          "[ViewReport] Using cached blob URL (age=" +
            Math.round((Date.now() - cached.createdAt) / 1000) +
            "s)",
        );
        setPdfViewerUrl(cached.blobUrl);
        setPdfViewerOpen(true);
        setPdfViewerLoading(false);
        setPdfViewerError(null);
        return;
      }

      // Open the modal immediately with loading state
      setPdfViewerOpen(true);
      setPdfViewerLoading(true);
      setPdfViewerError(null);
      setPdfViewerUrl(null);

      // Call the API to generate and get the report URL
      console.log("[ViewReport] Calling api.getReportViewUrl...");
      const blobUrl = await api.getReportViewUrl(promptId);

      console.log(`[ViewReport] Blob URL received: ${blobUrl}`);

      // Cache the blob URL for repeated viewing
      pdfBlobCacheRef.current[promptId] = { blobUrl, createdAt: Date.now() };

      // Set the URL to display in the viewer
      setPdfViewerUrl(blobUrl);
      setPdfViewerLoading(false);

      console.log("[ViewReport] Report viewer opened successfully");
    } catch (error) {
      console.error("[ViewReport] Error viewing report:", error);
      const errMsg = error.message || "Failed to load report. Please try again.";
      setPdfViewerError(errMsg);
      setPdfViewerLoading(false);
    }
  };

  const handleClosePdfViewer = useCallback(() => {
    // Don't revoke blob URL — keep it cached for repeated viewing
    setPdfViewerOpen(false);
    setPdfViewerUrl(null);
    setPdfViewerError(null);
    setPdfViewerLoading(false);
  }, []);

  const handleToggleAgentFlow = () => {
    setShowAgentFlowLocal((prev) => {
      const newValue = !prev;
      // Auto-collapse sidebar when opening agent panel
      if (newValue) {
        setIsSidebarCollapsed(true);
      }
      return newValue;
    });
  };

  // Get the current display state
  const activeAgent = workflowState.activeAgent;
  const workflowComplete = workflowState.workflowComplete;
  const queryRejected = workflowState.queryRejected;
  const reportReady = workflowState.reportReady;
  const panelCollapsed = workflowState.panelCollapsed;
  const showAgentFlow = showAgentFlowLocal;

  const activeAgentIndex = activeAgent !== null ? AGENT_ID_MAP[activeAgent] : null;
  const selectedAgentIndex =
    selectedAgent !== null
      ? typeof selectedAgent === "string"
        ? AGENT_ID_MAP[selectedAgent]
        : selectedAgent
      : null;

  // Auto-select first agent with data when workflow is complete and no agent selected
  const firstAgentWithDataIndex = useMemo(() => {
    if (workflowComplete && selectedAgentIndex === null) {
      for (let i = 0; i < AGENTS.length; i++) {
        if (agentData[AGENTS[i].key]) {
          return i;
        }
      }
    }
    return null;
  }, [workflowComplete, selectedAgentIndex, agentData]);

  const currentAgentIndex = selectedAgentIndex ?? firstAgentWithDataIndex ?? activeAgentIndex;

  console.log(
    "[Dashboard] hasAgentData:",
    hasAgentData,
    "| agentData keys:",
    Object.keys(agentData),
  );

  const shouldShowAgentFlow = hasAgentData && showAgentFlow;
  const isDefaultSignedInLanding =
    !activeChatId && !showNewsMonitor && !shouldShowAgentFlow && !compare.isComparing;

  const sessionId = localStorage.getItem("activeSessionId");

  const renderAgentDataDisplay = (agentIndex) => {
    const agent = AGENTS[agentIndex];
    if (!agent) {
      console.warn("[renderAgentDataDisplay] No agent found for index:", agentIndex);
      return null;
    }

    let agentResponse = agentData[agent.key];
    console.log(
      `[renderAgentDataDisplay] Agent ${agent.key} (index ${agentIndex}) raw:`,
      agentResponse,
    );

    // Handle array response (new format from orchestrator)
    if (Array.isArray(agentResponse)) {
      // Get the latest result
      const latest = agentResponse[agentResponse.length - 1];
      if (latest && latest.result) {
        agentResponse = latest.result;
        console.log(`[renderAgentDataDisplay] Extracted result from array:`, agentResponse);
      } else if (agentResponse.length > 0) {
        agentResponse = agentResponse[agentResponse.length - 1];
      }
    }

    if (!agentResponse) {
      console.warn(`[renderAgentDataDisplay] No data for agent ${agent.key}`);
      return null;
    }

    // Check if this agent is currently active/running
    const isAgentRunning = activeAgent === agent.key && !workflowComplete;
    console.log(
      `[renderAgentDataDisplay] Agent ${agent.key} - isRunning: ${isAgentRunning}, activeAgent: ${activeAgent}, workflowComplete: ${workflowComplete}`,
    );

    // Extract visualizations - can be at top level or nested in data
    let visualizations = agentResponse.visualizations || agentResponse.data?.visualizations || [];

    // Filter out unwanted trade intelligence text for EXIM agent
    if (agent.key === "exim" && Array.isArray(visualizations)) {
      visualizations = visualizations.filter((v) => {
        const title = v.title?.toLowerCase() || "";
        const content = v.content?.toLowerCase() || "";
        // Remove any visualization containing "trade intelligence summary"
        return (
          !title.includes("trade intelligence summary") &&
          !content.includes("trade intelligence summary")
        );
      });
    }

    console.log(`[renderAgentDataDisplay] ${agent.key} visualizations:`, visualizations);

    // Extract actual data (could be nested)
    const data = agentResponse.data || agentResponse;
    console.log(`[renderAgentDataDisplay] ${agent.key} fallback data:`, data);

    // All agents use their dedicated AgentDisplayShell-wrapped components.
    // VizList is appended below when the agent also has standardised visualizations.
    const hasViz = Array.isArray(visualizations) && visualizations.length > 0;

    switch (agent.key) {
      case "iqvia": {
        // Filter out chart types already rendered inline by IQVIADataDisplay
        const iqviaTableViz = Array.isArray(visualizations)
          ? visualizations.filter((v) => ["table", "actions"].includes(v.vizType))
          : [];
        const hasTableViz = iqviaTableViz.length > 0;
        return (
          <AgentErrorBoundary agentName="IQVIA">
            <IQVIADataDisplay
              data={data}
              isFirstPrompt={true}
              onPromptClick={handleSuggestedPromptClick}
            />
            {hasTableViz && (
              <div className="mt-4">
                <VizList visualizations={iqviaTableViz} agentName="IQVIA" />
              </div>
            )}
          </AgentErrorBoundary>
        );
      }
      case "exim":
        return (
          <AgentErrorBoundary agentName="EXIM Trade">
            <EXIMDataDisplay
              data={data}
              showChart={true}
              onPromptClick={handleSuggestedPromptClick}
            />
          </AgentErrorBoundary>
        );
      case "patent":
        return (
          <AgentErrorBoundary agentName="Patent">
            <PatentDataDisplay
              data={data}
              isFirstPrompt={true}
              onPromptClick={handleSuggestedPromptClick}
            />
          </AgentErrorBoundary>
        );
      case "clinical": {
        return (
          <AgentErrorBoundary agentName="Clinical Trials">
            <ClinicalDataDisplay
              data={data}
              isFirstPrompt={true}
              onPromptClick={handleSuggestedPromptClick}
            />
          </AgentErrorBoundary>
        );
      }
      case "internal":
        return (
          <AgentErrorBoundary agentName="Internal Knowledge">
            <InternalKnowledgeDisplay data={data} onPromptClick={handleSuggestedPromptClick} />
          </AgentErrorBoundary>
        );
      case "web":
        return (
          <AgentErrorBoundary agentName="Web Intelligence">
            <WebIntelDisplay data={data} onPromptClick={handleSuggestedPromptClick} />
            {hasViz && (
              <div className="mt-4">
                <VizList visualizations={visualizations} agentName="Web Intelligence" />
              </div>
            )}
          </AgentErrorBoundary>
        );
      case "report":
        return (
          <AgentErrorBoundary agentName="Report Generator">
            <VizList visualizations={data.visualizations || []} agentName="Report" />
          </AgentErrorBoundary>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex dossier-shell">
      {/* ── Signed-out: public landing page only ── */}
      {!authLoaded || !isSignedIn ? (
        <main className="flex-1 flex flex-col h-screen">
          <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
            <div className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-2xl border border-primary/40 bg-primary/15 flex items-center justify-center">
                  <Microscope className="text-primary" size={18} />
                </div>
                <div>
                  <div className="dossier-label">PharmAssist</div>
                  <div className="text-xl font-display text-foreground">
                    Repurposing Intelligence Desk
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate("/sign-in")}
                  className="px-5 py-2 rounded-2xl text-sm font-semibold border border-border hover:border-primary/50 text-foreground hover:text-primary transition-all"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate("/sign-up")}
                  className="px-5 py-2 rounded-2xl text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/25 transition-all"
                >
                  Get Started
                </button>
              </div>
            </div>
          </header>
          <LandingPage showFullGrid={true} />
          {/* Prompt bar that redirects to sign-in */}
          <div className="sticky bottom-0 border-t border-border/60 bg-background/80 backdrop-blur-xl px-6 py-4">
            <button
              onClick={() => navigate("/sign-in")}
              className="w-full max-w-3xl mx-auto flex items-center gap-3 px-6 py-4 rounded-2xl border border-border/70 bg-card/50 hover:border-primary/50 text-muted-foreground hover:text-foreground transition-all cursor-pointer"
            >
              <Sparkles size={18} className="text-primary flex-shrink-0" />
              <span className="text-sm">
                Sign in to start analyzing molecules, diseases, and markets...
              </span>
            </button>
          </div>
        </main>
      ) : (
        /* ── Signed-in: full dashboard ── */
        <>
          {/* Chat Sidebar */}
          <ChatSidebar
            chats={mappedChats}
            activeChatId={activeChatId}
            onNewChat={handleNewChat}
            onSelectChat={handleSelectChat}
            onDeleteChat={handleDeleteChat}
            onRestoreChat={() => {}}
            onRenameChat={handleRenameChat}
            onToggleMonitoring={handleToggleMonitoring}
            onOpenNewsMonitor={handleOpenNewsMonitor}
            onOpenCompare={compare.startCompare}
            canCompare={mappedChats.length >= 2}
            isComparing={compare.isComparing}
            onShareChat={handleShareChat}
            sharedWithMe={sharedWithMe}
            monitoredPromptIds={monitoredPromptIds}
            monitoredSessionIds={monitoredSessionIds}
            affectedSessionIds={affectedSessionIds}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />

          {/* Chat Selection Modal for Compare Studies */}
          <ChatSelectionModal
            isOpen={compare.showSelectionModal}
            chats={mappedChats}
            onConfirm={(a, b) => {
              compare.confirmSelection(a, b);
              setIsSidebarCollapsed(true);
              setShowAgentFlowLocal(false);
              setShowNewsMonitor(false);
            }}
            onCancel={compare.cancelSelection}
          />

          {/* Share Chat Modal */}
          <ShareChatModal
            sessionId={shareSessionId}
            sessionTitle={shareSessionTitle}
            isOpen={shareModalOpen}
            onClose={() => setShareModalOpen(false)}
            onCollaboratorsChanged={() => loadSharedSessions?.()}
          />

          {/* PDF Viewer Modal */}
          <PDFViewerModal
            isOpen={pdfViewerOpen}
            onClose={handleClosePdfViewer}
            pdfUrl={pdfViewerUrl}
            title="Intelligence Report"
            isLoading={pdfViewerLoading}
            error={pdfViewerError}
          />

          {/* Main Area */}
          <main className="flex-1 flex flex-col h-screen justify-between relative">
            <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
              <div className="flex items-center justify-between px-6 py-4">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl border border-primary/40 bg-primary/15 flex items-center justify-center">
                    <Microscope className="text-primary" size={18} />
                  </div>
                  <div>
                    <div className="dossier-label">PharmAssist</div>
                    <div className="text-xl font-display text-foreground">
                      Repurposing Intelligence Desk
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  {hasAgentData && !showAgentFlow && !showNewsMonitor && !compare.isComparing && (
                    <button
                      onClick={handleToggleAgentFlow}
                      className="group flex items-center gap-3 px-5 py-2.5 rounded-full bg-card/80 border border-border/60 text-foreground/90 hover:text-foreground hover:border-primary/50 hover:bg-card transition-all duration-200 hover:-translate-y-0.5"
                    >
                      <Network size={14} className="text-primary" />
                      <span className="text-sm font-semibold">Agent Cabinet</span>
                      <span className="flex items-center justify-center min-w-[28px] px-2 py-0.5 rounded-lg bg-primary/15 text-xs font-semibold text-primary">
                        {agentDataCount}
                      </span>
                      <ChevronRight
                        size={16}
                        className="transition-transform duration-200 group-hover:translate-x-0.5"
                      />
                    </button>
                  )}
                  <div className="flex items-center px-5 py-2.5 rounded-full bg-card/80 border border-border/60 text-sm font-semibold text-foreground/90 hover:text-foreground hover:border-primary/40 hover:bg-card transition-all duration-200 hover:-translate-y-0.5 cursor-default">
                    Sessions {mappedChats.length}
                  </div>
                  <UserButton
                    afterSignOutUrl="/"
                    appearance={{
                      elements: {
                        avatarBox: "w-9 h-9 rounded-xl border border-border/60",
                      },
                    }}
                  />
                </div>
              </div>
            </header>
            {/* Main Content Area */}
            <div
              className={`flex-1 flex flex-col hide-scrollbar ${
                isDefaultSignedInLanding ? "overflow-hidden" : "overflow-auto"
              }`}
            >
              {/* Content Area */}
              <div
                className={`flex-1 ${isDefaultSignedInLanding ? "overflow-hidden" : "overflow-y-auto"} ${
                  shouldShowAgentFlow ? "py-0" : ""
                }`}
              >
                <AnimatePresence mode="wait">
                  {compare.isComparing ? (
                    /* Compare Studies View */
                    <CompareStudiesView
                      leftChat={compare.leftChat}
                      rightChat={compare.rightChat}
                      leftAgent={compare.leftAgent}
                      rightAgent={compare.rightAgent}
                      onLeftAgentChange={(agentKey) => {
                        compare.setLeftAgent(agentKey);
                        compare.setRightAgent(agentKey);
                      }}
                      onRightAgentChange={(agentKey) => {
                        compare.setRightAgent(agentKey);
                        compare.setLeftAgent(agentKey);
                      }}
                      onExit={() => {
                        compare.exitCompare();
                        setIsSidebarCollapsed(false);
                      }}
                    />
                  ) : showNewsMonitor ? (
                    /* News Monitor Page */
                    <motion.div
                      key="news-monitor"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className="h-full flex flex-col"
                    >
                      <NewsMonitorPage
                        onBack={() => setShowNewsMonitor(false)}
                        onSelectChat={handleSelectChat}
                        onRefreshMonitored={refreshAllMonitored}
                        broadcastResult={broadcastResult}
                        onClearBroadcastResult={() => setBroadcastResult(null)}
                        registerRefetch={(fn) => {
                          newsMonitorRefetchRef.current = fn;
                        }}
                      />
                    </motion.div>
                  ) : shouldShowAgentFlow ? (
                    /* Agent Flow Visualization - Premium UI */
                    <motion.div
                      key="agent-flow"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full p-4 gap-4"
                    >
                      {/* Left Sidebar - Floating Detached Design */}
                      <motion.div
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        className="w-[270px] shrink-0 rounded-3xl dossier-panel flex flex-col overflow-hidden"
                      >
                        {/* Orchestrator Header with Hide Button */}
                        <div className="p-4 space-y-2">
                          <div className="flex items-center gap-3 p-3 rounded-2xl border border-border/70 bg-card/70">
                            <div className="relative">
                              <div className="p-2 rounded-xl bg-primary/15 border border-primary/30">
                                <motion.div
                                  animate={{ rotate: workflowComplete ? 0 : 360 }}
                                  transition={{
                                    duration: 8,
                                    repeat: workflowComplete ? 0 : Infinity,
                                    ease: "linear",
                                  }}
                                >
                                  <Network className="text-primary" size={16} />
                                </motion.div>
                              </div>
                              <div
                                className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-card ${workflowComplete ? "bg-teal-400" : "bg-primary animate-pulse"}`}
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <span className="text-sm font-semibold text-foreground">
                                Orchestrator
                              </span>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span
                                  className={`text-[10px] font-medium ${workflowComplete ? "text-teal-400" : "text-primary"}`}
                                >
                                  {workflowComplete ? "Analysis Complete" : "Processing..."}
                                </span>
                                {!workflowComplete && (
                                  <Loader2 className="animate-spin text-primary" size={10} />
                                )}
                              </div>
                            </div>
                            <div className="text-[10px] text-muted-foreground px-2 py-1 rounded-md bg-card/60 border border-border/60">
                              {agentDataCount}/6
                            </div>
                          </div>

                          {/* Hide Agents Button - Moved to top */}
                          <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleToggleAgentFlow}
                            className="w-full py-2 px-2.5 rounded-xl text-xs font-medium flex items-center justify-center gap-2 bg-card/60 hover:bg-card text-muted-foreground hover:text-foreground border border-border/60 hover:border-primary/40 transition-all duration-200"
                          >
                            <ChevronLeft size={13} />
                            <span>Hide Agents</span>
                          </motion.button>
                        </div>

                        {/* Agent List */}
                        <div className="flex-1 px-3 py-2 overflow-y-auto">
                          <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
                            Agents
                          </div>
                          <div className="space-y-0.5">
                            {AGENTS.map((agent, index) => {
                              const Icon = agent.icon;
                              const isSelected = currentAgentIndex === agent.id;
                              const isRunning = activeAgentIndex === agent.id && !workflowComplete;
                              const hasData = ranAgentKeySet.has(agent.key);
                              const colors = colorClasses[agent.color];

                              return (
                                <motion.button
                                  key={agent.id}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  whileHover={{
                                    x: 2,
                                    transition: { duration: 0.15, ease: "easeOut" },
                                  }}
                                  whileTap={{ scale: 0.98 }}
                                  transition={{
                                    delay: 0.03 * index,
                                    type: "spring",
                                    stiffness: 200,
                                  }}
                                  onClick={() => {
                                    setSelectedAgent(agent.id);
                                    if (agentContentRef.current) {
                                      agentContentRef.current.scrollTop = 0;
                                    }
                                  }}
                                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all duration-200 relative group cursor-pointer
                                ${
                                  isSelected
                                    ? "bg-white/[0.08]"
                                    : hasData
                                      ? "hover:bg-white/[0.06]"
                                      : "opacity-50 hover:bg-white/[0.04] hover:opacity-70"
                                }`}
                                >
                                  {/* Current/selected agent indicator with glow */}
                                  {isSelected && (
                                    <motion.div
                                      layoutId="agent-indicator"
                                      className={`absolute left-0 top-1 bottom-1 w-[2px] rounded-full z-10 ${colors.dot.replace("text-", "bg-")}`}
                                      style={{
                                        boxShadow: `0 0 8px ${getColorHex(colors.dot)}40`,
                                      }}
                                    />
                                  )}

                                  <motion.div
                                    whileHover={{ scale: 1.1 }}
                                    transition={{ duration: 0.15 }}
                                    className={`p-1.5 rounded-md transition-all duration-200 ${isSelected ? colors.icon : "bg-white/[0.05] group-hover:bg-white/[0.08]"}`}
                                  >
                                    <Icon
                                      className={`transition-colors duration-200 ${isSelected ? colors.iconColor : hasData ? "text-muted-foreground group-hover:text-foreground/70" : "text-muted-foreground"}`}
                                      size={14}
                                    />
                                  </motion.div>
                                  <span
                                    className={`flex-1 text-left text-[12px] font-medium transition-colors duration-200 ${isSelected ? "text-foreground" : hasData ? "text-muted-foreground group-hover:text-foreground/80" : "text-muted-foreground"}`}
                                  >
                                    {agent.name}
                                  </span>
                                  {isRunning && (
                                    <motion.div
                                      animate={{ rotate: 360 }}
                                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    >
                                      <Loader2 className={colors.iconColor} size={14} />
                                    </motion.div>
                                  )}
                                  {/* Right-side status dot removed to avoid visual clutter */}
                                </motion.button>
                              );
                            })}
                          </div>
                        </div>
                      </motion.div>

                      {/* Right Panel - Agent Output */}
                      <AnimatePresence mode="wait">
                        {(activeAgentIndex !== null || workflowComplete) &&
                          !queryRejected &&
                          !panelCollapsed &&
                          currentAgentIndex !== null && (
                            <motion.div
                              key={`agent-panel-${currentAgentIndex}`}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="flex-1 min-w-0 flex flex-col rounded-3xl dossier-panel"
                            >
                              {/* Agent Content - match sidebar margins for alignment */}
                              <div
                                ref={agentContentRef}
                                className="flex-1 overflow-y-auto p-4 pb-8"
                              >
                                {(() => {
                                  const currentAgent = AGENTS[currentAgentIndex];
                                  const hasCurrentAgentData =
                                    currentAgent && agentData[currentAgent.key];

                                  if (currentAgentIndex !== null && !hasCurrentAgentData) {
                                    return (
                                      <div className="flex flex-col items-center justify-center h-full gap-4 py-12">
                                        <motion.div
                                          animate={{ rotate: 360 }}
                                          transition={{
                                            duration: 2,
                                            repeat: Infinity,
                                            ease: "linear",
                                          }}
                                        >
                                          <Loader2 className="text-primary" size={32} />
                                        </motion.div>
                                        <div className="text-center">
                                          <p className="text-sm text-foreground font-medium">
                                            {currentAgentIndex === 0 && "Analyzing market data..."}
                                            {currentAgentIndex === 1 &&
                                              "Processing trade trends..."}
                                            {currentAgentIndex === 2 &&
                                              "Scanning patent landscape..."}
                                            {currentAgentIndex === 3 &&
                                              "Querying clinical trials..."}
                                            {currentAgentIndex === 4 &&
                                              "Searching knowledge base..."}
                                            {currentAgentIndex === 5 &&
                                              "Gathering web intelligence..."}
                                          </p>
                                          <p className="text-xs text-muted-foreground mt-1">
                                            This may take a moment
                                          </p>
                                        </div>
                                      </div>
                                    );
                                  }

                                  return (
                                    <div className="text-foreground leading-relaxed w-full">
                                      {currentAgentIndex !== null &&
                                        renderAgentDataDisplay(currentAgentIndex)}
                                    </div>
                                  );
                                })()}
                              </div>
                            </motion.div>
                          )}
                      </AnimatePresence>
                    </motion.div>
                  ) : !activeChatId ? (
                    /* Landing Page - Show when no chat is selected */
                    <div className="flex-1 flex items-center justify-center overflow-hidden hide-scrollbar">
                      <LandingPage
                        onStartNewChat={handleNewChat}
                        showFullGrid={true}
                        apiError={apiError}
                        isLoading={isLoading}
                      />
                    </div>
                  ) : (
                    /* Chat Interface View */
                    <motion.div
                      key="chat-view"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className="h-full flex flex-col"
                    >
                      {/* Chat Messages */}
                      <div className="flex-1 overflow-y-auto">
                        <div className="space-y-5 py-4 pb-24 max-w-3xl mx-auto px-6">
                          {!activeChat || chatHistory.length === 0 ? (
                            <LandingPage
                              onSelectFeature={(title) => {
                                setPrompt(`Analyze ${title.toLowerCase()} for Semaglutide`);
                              }}
                              showFullGrid={false}
                            />
                          ) : (
                            <>
                              {chatHistory.map((msg, idx) => (
                                <motion.div
                                  key={msg.id || idx}
                                  initial={{ opacity: 0, y: 10 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{ delay: idx * 0.03, ease: [0.22, 1, 0.36, 1] }}
                                  className={
                                    msg.type === "news-notification"
                                      ? "w-full"
                                      : `flex ${msg.role === "user" ? "justify-end" : "justify-start"}`
                                  }
                                >
                                  {msg.type === "news-notification" ? (
                                    (() => {
                                      const meta = msg.metadata || {};
                                      const severity =
                                        meta.severity ||
                                        (msg.content?.includes("HIGH")
                                          ? "HIGH"
                                          : msg.content?.includes("MEDIUM")
                                            ? "MEDIUM"
                                            : "LOW");
                                      const promptLabel = meta.promptLabel || "your research";
                                      const reason = meta.reason || "";
                                      const keywords = meta.matchedKeywords || [];
                                      const fields = meta.changedFields || [];
                                      const isHigh = severity === "HIGH";
                                      const isMed = severity === "MEDIUM";
                                      const accentLeft = isHigh
                                        ? "border-l-red-500"
                                        : isMed
                                          ? "border-l-amber-500"
                                          : "border-l-emerald-500";
                                      const sevBadge = isHigh
                                        ? "text-red-300 bg-red-500/20 border-red-500/40"
                                        : isMed
                                          ? "text-amber-300 bg-amber-500/20 border-amber-500/40"
                                          : "text-emerald-300 bg-emerald-500/20 border-emerald-500/40";
                                      const sevDot = isHigh
                                        ? "bg-red-400"
                                        : isMed
                                          ? "bg-amber-400"
                                          : "bg-emerald-400";
                                      return (
                                        <div
                                          className={`w-full rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/[0.06] to-card/60 backdrop-blur-sm overflow-hidden border-l-4 ${accentLeft} shadow-lg`}
                                        >
                                          {/* ── Top bar ── */}
                                          <div className="flex items-center gap-3 px-5 py-3.5 border-b border-white/[0.06] bg-amber-500/[0.05]">
                                            <div className="p-2 rounded-xl bg-amber-500/25 border border-amber-500/40 shrink-0">
                                              <Bell size={15} className="text-amber-400" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                              <p className="text-xs font-bold text-amber-400 uppercase tracking-widest leading-none">
                                                News Monitor Alert
                                              </p>
                                              <p className="text-[11px] text-muted-foreground mt-0.5">
                                                Regulatory intelligence detected
                                              </p>
                                            </div>
                                            <span
                                              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-bold ${sevBadge}`}
                                            >
                                              <span
                                                className={`w-2 h-2 rounded-full ${sevDot} animate-pulse`}
                                              />
                                              {severity} RISK
                                            </span>
                                          </div>

                                          {/* ── Body ── */}
                                          <div className="px-5 py-4 space-y-4">
                                            {/* Query */}
                                            <div>
                                              <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold mb-1.5">
                                                Monitored Query
                                              </p>
                                              <p className="text-base font-semibold text-foreground leading-snug">
                                                {promptLabel}
                                              </p>
                                            </div>

                                            <div className="h-px bg-white/[0.06]" />

                                            {/* Reason */}
                                            {reason && (
                                              <p className="text-sm text-foreground/75 leading-relaxed">
                                                {reason}
                                              </p>
                                            )}

                                            {/* Changed fields + Keywords */}
                                            {(fields.length > 0 || keywords.length > 0) && (
                                              <div className="flex flex-col gap-2.5">
                                                {fields.length > 0 && (
                                                  <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider w-16 shrink-0">
                                                      Changed
                                                    </span>
                                                    {fields.map((f) => (
                                                      <span
                                                        key={f}
                                                        className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-500/15 border border-amber-500/30 text-amber-300"
                                                      >
                                                        {f}
                                                      </span>
                                                    ))}
                                                  </div>
                                                )}
                                                {keywords.length > 0 && (
                                                  <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider w-16 shrink-0">
                                                      Keywords
                                                    </span>
                                                    {keywords.map((k) => (
                                                      <span
                                                        key={k}
                                                        className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/[0.06] border border-white/[0.1] text-foreground/60"
                                                      >
                                                        {k}
                                                      </span>
                                                    ))}
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                          </div>

                                          {/* ── Footer ── */}
                                          <div className="flex items-center gap-4 px-5 py-3 border-t border-white/[0.06] bg-white/[0.02]">
                                            <button
                                              onClick={() => setShowNewsMonitor(true)}
                                              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-xs font-semibold text-amber-400 hover:bg-amber-500/25 hover:text-amber-300 transition-all"
                                            >
                                              <Bell size={12} />
                                              Open News Monitor
                                            </button>
                                            <span className="text-[11px] text-muted-foreground/50">
                                              Review and re-run analysis if needed
                                            </span>
                                          </div>
                                        </div>
                                      );
                                    })()
                                  ) : (
                                    <div
                                      className={`max-w-[85%] rounded-2xl px-5 py-3.5 ${
                                        msg.role === "user"
                                          ? "bg-gradient-to-br from-teal-600 to-teal-700 text-white border border-teal-500/40 shadow-lg shadow-teal-900/30"
                                          : msg.type === "greeting"
                                            ? "bg-card/80 border border-border/70 text-foreground shadow-sm"
                                            : msg.type === "rejection"
                                              ? "bg-destructive/15 border border-destructive/40 text-foreground"
                                              : msg.type === "agent-complete"
                                                ? "bg-emerald-500/10 border border-emerald-500/30 text-foreground"
                                                : "bg-card/70 backdrop-blur-sm border border-border/60 text-foreground"
                                      }`}
                                    >
                                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                        {msg.content}
                                      </p>
                                      {msg.type === "agent-complete" && msg.promptId && (
                                        <>
                                          {/* ── Critical Blockers Warning ── */}
                                          {criticalBlockers.length > 0 && (
                                            <motion.div
                                              initial={{ opacity: 0, y: 5 }}
                                              animate={{ opacity: 1, y: 0 }}
                                              transition={{ delay: 0.15 }}
                                              className="mt-3 p-3 rounded-xl bg-red-500/[0.1] border border-red-500/30"
                                            >
                                              <div className="flex items-center gap-2 mb-1.5">
                                                <AlertCircle
                                                  size={15}
                                                  className="text-red-400 flex-shrink-0"
                                                />
                                                <span className="text-xs font-bold text-red-400 uppercase tracking-wider">
                                                  Critical Blocker
                                                  {criticalBlockers.length > 1 ? "s" : ""} Detected
                                                </span>
                                              </div>
                                              {criticalBlockers.map((b, i) => (
                                                <p
                                                  key={i}
                                                  className="text-xs text-red-300/80 ml-[23px]"
                                                >
                                                  <span className="font-semibold">
                                                    {(b.agent || "").toUpperCase()}:
                                                  </span>{" "}
                                                  {b.reason}
                                                </p>
                                              ))}
                                              <p className="text-[11px] text-red-300/60 mt-2 ml-[23px]">
                                                This research has a critical blocker that may
                                                prevent feasibility. Review the flagged agent for
                                                details.
                                              </p>
                                            </motion.div>
                                          )}
                                          {/* ── Score Summary Strip ── */}
                                          {Object.keys(agentScores).length > 0 && (
                                            <motion.div
                                              initial={{ opacity: 0, y: 5 }}
                                              animate={{ opacity: 1, y: 0 }}
                                              transition={{ delay: 0.2 }}
                                              className="mt-2 flex flex-wrap gap-1.5"
                                            >
                                              {Object.entries(agentScores).map(([key, info]) => {
                                                const s = info?.score ?? null;
                                                if (s === null) return null;
                                                let dotColor = "bg-muted-foreground/40";
                                                if (s === 0) dotColor = "bg-red-500";
                                                else if (s <= 20) dotColor = "bg-red-400";
                                                else if (s <= 40) dotColor = "bg-orange-400";
                                                else if (s <= 60) dotColor = "bg-amber-400";
                                                else if (s <= 80) dotColor = "bg-emerald-400";
                                                else dotColor = "bg-teal-400";
                                                const agentName =
                                                  AGENTS.find((a) => a.key === key)?.name || key;
                                                return (
                                                  <span
                                                    key={key}
                                                    className="inline-flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-md bg-white/[0.04] border border-white/[0.06] text-muted-foreground"
                                                  >
                                                    <span
                                                      className={`w-2 h-2 rounded-full ${dotColor}`}
                                                    />
                                                    {agentName}: {s}
                                                  </span>
                                                );
                                              })}
                                            </motion.div>
                                          )}
                                          <motion.button
                                            initial={{ opacity: 0, y: 5 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.3 }}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => handleViewReport(msg.promptId)}
                                            disabled={pdfViewerLoading}
                                            className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-2xl font-medium text-sm transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                          >
                                            {pdfViewerLoading ? (
                                              <>
                                                <Loader2 className="animate-spin" size={16} />
                                                Generating Report...
                                              </>
                                            ) : (
                                              <>
                                                <Eye size={16} />
                                                View Report
                                              </>
                                            )}
                                          </motion.button>
                                        </>
                                      )}
                                    </div>
                                  )}
                                </motion.div>
                              ))}

                              {/* Continue Research Suggestions - In Chat */}
                              {workflowComplete && suggestedNextPrompts.length > 0 && (
                                <motion.div
                                  initial={{ opacity: 0, y: 20 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{ delay: 0.5 }}
                                  className="pt-4"
                                >
                                  <div className="flex items-center gap-2 mb-3">
                                    <Sparkles className="text-primary" size={14} />
                                    <span className="text-xs font-semibold text-muted-foreground">
                                      Continue your research
                                    </span>
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    {suggestedNextPrompts.slice(0, 3).map((suggestion, idx) => (
                                      <motion.button
                                        key={idx}
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: 0.6 + idx * 0.1 }}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() =>
                                          handleSuggestedPromptClick(suggestion.prompt)
                                        }
                                        className="px-4 py-2.5 text-sm rounded-2xl bg-card/80 border border-border/60 hover:border-primary/50 hover:bg-primary/10 transition-all text-muted-foreground hover:text-foreground"
                                      >
                                        {suggestion.prompt}
                                      </motion.button>
                                    ))}
                                  </div>
                                </motion.div>
                              )}
                            </>
                          )}
                          {isLoading && (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="flex justify-start"
                            >
                              <div className="bg-muted rounded-2xl px-4 py-3 flex items-center gap-3">
                                <Loader2 className="animate-spin text-primary" size={16} />
                                <span className="text-sm text-muted-foreground">
                                  Processing your request...
                                </span>
                              </div>
                            </motion.div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Input Section - Clean Seamless Design with Smooth Fade */}
            {!compare.isComparing && (
              <div className="relative">
                {/* Smooth fade gradient - content appears to emerge from below */}
                <div
                  className="absolute -top-28 left-0 right-0 h-28 pointer-events-none z-10"
                  style={{
                    background:
                      "linear-gradient(to top, hsl(var(--background)) 0%, hsl(var(--background) / 0.92) 20%, hsl(var(--background) / 0.55) 55%, transparent 100%)",
                  }}
                />

                <div className="relative z-20 px-6 pt-3 pb-6 bg-background/80 backdrop-blur-xl">
                  <div className="max-w-3xl mx-auto relative">
                    <div className="relative flex flex-col gap-3">
                      {/* Voice Assistant Panel */}
                      <VoiceAssistantPanel
                        isActive={voice.isActive}
                        isListening={voice.isListening}
                        isSpeaking={voice.isSpeaking}
                        isProcessing={voice.isProcessing}
                        mode={voice.mode}
                        transcript={voice.transcript}
                        interimTranscript={voice.interimTranscript}
                        voiceResponse={voice.voiceResponse}
                        refinedPrompt={voice.refinedPrompt}
                        error={voice.error}
                        awaitingConfirmation={voice.awaitingConfirmation}
                        onDeactivate={voice.deactivate}
                        onStopSpeaking={voice.stopSpeaking}
                        onConfirm={voice.confirmPrompt}
                        onReject={() => voice.confirmPrompt(false)}
                        onReset={voice.reset}
                      />

                      {/* Analysis Plan Ready */}
                      {planningReady && planningPlan && (
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mb-2 rounded-2xl border border-primary/25 bg-card/95 backdrop-blur-xl overflow-hidden"
                        >
                          <div className="px-4 py-3 border-b border-primary/20 bg-primary/10">
                            <div className="flex items-center gap-2">
                              <Sparkles size={14} className="text-primary" />
                              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                                Confirmation Required
                              </span>
                            </div>
                          </div>

                          <div className="p-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="space-y-3">
                                <h3 className="text-base font-semibold text-foreground">
                                  Analysis Plan Ready
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                  Review the plan details below and confirm execution.
                                </p>

                                {planAgents.length > 0 && (
                                  <div>
                                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                                      Agents selected
                                    </p>
                                    <div className="flex flex-wrap gap-1.5">
                                      {planAgents.map((agent) => (
                                        <span
                                          key={agent}
                                          className="px-2 py-1 rounded-md bg-primary/10 border border-primary/20 text-xs font-medium text-foreground"
                                        >
                                          {agent}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {planDrugs.length > 0 && (
                                  <p className="text-sm text-muted-foreground">
                                    <span className="text-foreground/90 font-medium">Drug:</span>{" "}
                                    {planDrugs.join(", ")}
                                  </p>
                                )}

                                {planIndications.length > 0 && (
                                  <p className="text-sm text-muted-foreground">
                                    <span className="text-foreground/90 font-medium">
                                      Indication:
                                    </span>{" "}
                                    {planIndications.join(", ")}
                                  </p>
                                )}
                              </div>

                              <div className="shrink-0 flex items-center gap-2">
                                <Button
                                  variant="outline"
                                  onClick={async () => {
                                    try {
                                      if (activeChatId) {
                                        const res = await api.cancelPlan(activeChatId);
                                        if (res.session && res.session.sessionId) {
                                          updateChatSession(res.session);
                                        }
                                      }
                                      setPlanningReady(false);
                                      setPlanningPlan(null);
                                      setApiError(null);
                                    } catch (error) {
                                      console.error("[Dashboard] Cancel plan failed:", error);
                                      setApiError("Failed to cancel plan. Please try again.");
                                    }
                                  }}
                                  disabled={isLoading}
                                >
                                  Cancel
                                </Button>

                                <Button
                                  onClick={async () => {
                                    try {
                                      setIsLoading(true);
                                      setApiError(null);
                                      setShowAgentFlowLocal(true);
                                      setIsSidebarCollapsed(true);
                                      const res = await api.executePlan(activeChatId);
                                      if (res.session && res.session.sessionId) {
                                        updateChatSession(res.session);
                                      }
                                      setPlanningReady(false);
                                      setPlanningPlan(null);
                                    } catch (error) {
                                      console.error("[Dashboard] Execute failed:", error);
                                      setApiError("Failed to execute plan. Please try again.");
                                    } finally {
                                      setIsLoading(false);
                                    }
                                  }}
                                  className="shrink-0"
                                  disabled={isLoading}
                                >
                                  {isLoading ? (
                                    <>
                                      <Loader2 className="mr-2 animate-spin" size={16} />
                                      Executing...
                                    </>
                                  ) : (
                                    <>
                                      <Sparkles className="mr-2" size={16} />
                                      Confirm & Execute
                                    </>
                                  )}
                                </Button>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {/* Uploaded file indicator — normal or broadcast mode */}
                      {showNewsMonitor
                        ? /* ── Broadcast mode file indicator ── */
                          broadcastUploadedFile && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/20 rounded-xl"
                            >
                              <File size={16} className="text-primary" />
                              <span className="text-sm text-foreground flex-1 truncate">
                                {broadcastUploadedFile.name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {(broadcastUploadedFile.size / 1024).toFixed(1)} KB
                              </span>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={handleBroadcastRemoveFile}
                                className="p-1 hover:bg-destructive/20 rounded-md transition-colors"
                              >
                                <X
                                  size={14}
                                  className="text-muted-foreground hover:text-destructive"
                                />
                              </motion.button>
                            </motion.div>
                          )
                        : /* ── Normal mode file indicator ── */
                          uploadedFile && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/20 rounded-xl"
                            >
                              <File size={16} className="text-primary" />
                              <span className="text-sm text-foreground flex-1 truncate">
                                {uploadedFile.name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {(uploadedFile.size / 1024).toFixed(1)} KB
                              </span>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={handleRemoveFile}
                                className="p-1 hover:bg-destructive/20 rounded-md transition-colors"
                              >
                                <X
                                  size={14}
                                  className="text-muted-foreground hover:text-destructive"
                                />
                              </motion.button>
                            </motion.div>
                          )}

                      <div className="flex items-center gap-2">
                        {/* Hidden file inputs — normal + broadcast */}
                        <input
                          type="file"
                          ref={fileInputRef}
                          onChange={handleFileSelect}
                          accept=".pdf,.pptx,.ppt,.xlsx,.xls,.docx,.txt,.csv"
                          className="hidden"
                        />
                        <input
                          type="file"
                          ref={broadcastFileInputRef}
                          onChange={handleBroadcastFileSelect}
                          accept=".pdf,.pptx,.ppt,.xlsx,.xls,.docx,.txt,.csv"
                          className="hidden"
                        />

                        <div className="relative flex-1">
                          {showNewsMonitor ? (
                            /* ── Broadcast mode input ── */
                            <>
                              <Input
                                placeholder="Share new intel — e.g. 'competitor filed azithromycin patent for oncology'..."
                                className="w-full h-14 pl-16 pr-16 bg-card/80 backdrop-blur-xl border-border/60 rounded-3xl text-base shadow-lg focus-visible:ring-2 focus-visible:ring-primary/40 transition-all placeholder:text-muted-foreground/60"
                                value={intelText}
                                onChange={(e) => setIntelText(e.target.value)}
                                onKeyPress={handleBroadcastKeyPress}
                                disabled={isBroadcasting}
                              />

                              {/* Paperclip for broadcast */}
                              <button
                                onClick={() => broadcastFileInputRef.current?.click()}
                                disabled={isBroadcastUploading || isBroadcasting}
                                className={`absolute left-4 top-1/2 -translate-y-1/2 h-9 w-9 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                                  broadcastUploadedFile
                                    ? "bg-primary/20 text-primary scale-100"
                                    : isBroadcastUploading
                                      ? "text-muted-foreground cursor-not-allowed scale-100"
                                      : "text-muted-foreground hover:text-primary hover:bg-primary/10 hover:scale-110"
                                }`}
                                title="Attach document to broadcast"
                              >
                                {isBroadcastUploading ? (
                                  <Loader2 className="animate-spin" size={18} />
                                ) : (
                                  <Paperclip size={18} />
                                )}
                              </button>

                              {/* Broadcast send button */}
                              <button
                                onClick={handleBroadcastIntel}
                                disabled={
                                  isBroadcasting || (!intelText.trim() && !broadcastUploadedFile)
                                }
                                className={`absolute right-4 top-1/2 -translate-y-1/2 h-9 w-9 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                                  isBroadcasting || (!intelText.trim() && !broadcastUploadedFile)
                                    ? "bg-muted text-muted-foreground cursor-not-allowed scale-100"
                                    : "bg-primary text-primary-foreground shadow-lg hover:shadow-xl hover:scale-110 hover:bg-primary/90"
                                }`}
                                title="Broadcast intel to all monitored chats"
                              >
                                {isBroadcasting ? (
                                  <Loader2 className="animate-spin" size={18} />
                                ) : (
                                  <Zap size={18} />
                                )}
                              </button>
                            </>
                          ) : (
                            /* ── Normal analysis input ── */
                            <>
                              <Input
                                placeholder={
                                  voice.isActive
                                    ? voice.isListening
                                      ? "Listening..."
                                      : voice.isSpeaking
                                        ? "Speaking..."
                                        : "Processing..."
                                    : "Ask anything..."
                                }
                                className={`w-full h-14 pl-16 pr-28 bg-card/80 backdrop-blur-xl border-border/60 rounded-3xl text-base shadow-lg focus-visible:ring-2 focus-visible:ring-primary/40 transition-all placeholder:text-muted-foreground/60 ${
                                  voice.isActive
                                    ? voice.isListening
                                      ? "border-red-500/50 ring-2 ring-red-500/20"
                                      : voice.isSpeaking
                                        ? "border-violet-500/50 ring-2 ring-violet-500/20"
                                        : "border-emerald-500/50 ring-2 ring-emerald-500/20"
                                    : ""
                                }`}
                                value={voice.interimTranscript || prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                onKeyPress={handleKeyPress}
                                disabled={isLoading || voice.isActive}
                              />

                              <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isUploading || isLoading || voice.isActive}
                                className={`absolute left-4 top-1/2 -translate-y-1/2 h-9 w-9 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                                  uploadedFile
                                    ? "bg-primary/20 text-primary scale-100"
                                    : isUploading
                                      ? "text-muted-foreground cursor-not-allowed scale-100"
                                      : "text-muted-foreground hover:text-primary hover:bg-primary/10 hover:scale-110"
                                }`}
                                title="Attach document for Internal Knowledge Agent"
                              >
                                {isUploading ? (
                                  <Loader2 className="animate-spin" size={18} />
                                ) : (
                                  <Paperclip size={18} />
                                )}
                              </button>

                              {/* Voice button */}
                              {voice.isSupported && (
                                <button
                                  onClick={voice.toggle}
                                  disabled={isLoading || voice.isProcessing}
                                  className={`absolute right-14 top-1/2 -translate-y-1/2 h-9 w-9 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                                    voice.isActive
                                      ? voice.isListening
                                        ? "bg-red-500 text-white shadow-lg shadow-red-500/30 animate-pulse"
                                        : voice.isSpeaking
                                          ? "bg-violet-500 text-white shadow-lg shadow-violet-500/30"
                                          : voice.isProcessing
                                            ? "bg-amber-500 text-white"
                                            : "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
                                      : "text-muted-foreground hover:text-primary hover:bg-primary/10 hover:scale-105"
                                  }`}
                                  title={
                                    voice.isActive
                                      ? "Deactivate voice assistant"
                                      : "Activate voice assistant"
                                  }
                                >
                                  {voice.isProcessing ? (
                                    <Loader2 className="animate-spin" size={18} />
                                  ) : voice.isSpeaking ? (
                                    <Volume2 size={18} />
                                  ) : voice.isActive ? (
                                    <Mic
                                      size={18}
                                      className={voice.isListening ? "animate-pulse" : ""}
                                    />
                                  ) : (
                                    <Mic size={18} />
                                  )}
                                </button>
                              )}

                              <button
                                onClick={handleSendPrompt}
                                disabled={isLoading || !prompt.trim() || voice.isActive}
                                className={`absolute right-4 top-1/2 -translate-y-1/2 h-9 w-9 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                                  isLoading || !prompt.trim() || voice.isActive
                                    ? "bg-muted text-muted-foreground cursor-not-allowed scale-100"
                                    : "bg-primary text-primary-foreground shadow-lg hover:shadow-xl hover:scale-110 hover:bg-primary/90"
                                }`}
                              >
                                {isLoading ? (
                                  <Loader2 className="animate-spin" size={18} />
                                ) : (
                                  <Send size={18} />
                                )}
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </main>
        </>
      )}
    </div>
  );
}

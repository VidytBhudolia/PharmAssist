import React, { useMemo, useRef } from "react";
import { motion } from "framer-motion";
import {
  X,
  ChevronDown,
  TrendingUp,
  Globe,
  Shield,
  Activity,
  BookOpen,
  Columns2,
} from "lucide-react";
import {
  IQVIADataDisplay,
  EXIMDataDisplay,
  PatentDataDisplay,
  ClinicalDataDisplay,
  InternalKnowledgeDisplay,
  WebIntelDisplay,
} from "@/components/AgentDataDisplaysNew";
import { AgentErrorBoundary } from "@/components/ErrorBoundary";

/**
 * Agent metadata — reused from Dashboard constants
 */
const AGENTS = [
  { key: "iqvia", name: "IQVIA Insights", icon: TrendingUp, color: "sky" },
  { key: "exim", name: "Exim Trends", icon: Globe, color: "teal" },
  { key: "patent", name: "Patent Landscape", icon: Shield, color: "amber" },
  { key: "clinical", name: "Clinical Trials", icon: Activity, color: "emerald" },
  { key: "internal", name: "Internal Knowledge", icon: BookOpen, color: "cyan" },
  { key: "web", name: "Web Intelligence", icon: Globe, color: "indigo" },
];

// ──────────────────────────────────────────────────────────────
// Normalise agent keys exactly like Dashboard does
// ──────────────────────────────────────────────────────────────
function normalizeAgentKeys(agentsObj = {}) {
  const out = {};
  Object.entries(agentsObj).forEach(([key, value]) => {
    if (!key || typeof key !== "string") return;
    let k = key.toLowerCase().replace(/_agent$/, "").replace(/\s+/g, "");
    if (["internal_knowledge", "internalknowledge", "internal"].includes(k)) k = "internal";
    else if (["web_intelligence", "webintelligence", "webintel", "web"].includes(k)) k = "web";
    else if (["report_generator", "reportgenerator", "report"].includes(k)) k = "report";
    else if (["clinical_trials", "clinicaltrials", "clinical"].includes(k)) k = "clinical";
    else k = k.replace(/_/g, "");
    if (!out[k] && value) out[k] = value;
  });
  return out;
}

/** Derive normalised agent data from a chat object */
function useAgentDataForChat(chat) {
  return useMemo(() => {
    if (!chat) return {};
    const latestEntry = Array.isArray(chat.agentsData)
      ? chat.agentsData[chat.agentsData.length - 1]
      : null;
    const raw =
      latestEntry?.agents ||
      (typeof chat.agentsData === "object" && !Array.isArray(chat.agentsData)
        ? chat.agentsData
        : {});
    return normalizeAgentKeys(raw);
  }, [chat]);
}

/** Available agents for a given chat (only those that have data) */
function useAgentsWithAvailability(agentData) {
  return useMemo(
    () => AGENTS.map((a) => ({ ...a, hasData: Boolean(agentData[a.key]) })),
    [agentData],
  );
}

// ──────────────────────────────────────────────────────────────
// Agent dropdown selector
// ──────────────────────────────────────────────────────────────
function AgentDropdown({ agents, selected, onChange }) {
  const selectedAgent = agents.find((a) => a.key === selected) || agents[0];

  return (
    <div className="relative">
      <div className="relative inline-flex items-center">
        <select
          value={selected || ""}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none bg-card/80 border border-border/60 rounded-xl pl-10 pr-9 py-2 text-sm font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer transition-all hover:border-primary/40"
        >
          {agents.map((a) => (
            <option key={a.key} value={a.key} disabled={!a.hasData}>
              {a.name}{!a.hasData ? " (no data)" : ""}
            </option>
          ))}
        </select>

        {/* Left icon */}
        {selectedAgent && (
          <div className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none">
            <selectedAgent.icon size={16} className="text-muted-foreground" />
          </div>
        )}

        {/* Chevron */}
        <ChevronDown
          size={14}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground"
        />
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Render a single agent data display (mirrors renderAgentDataDisplay)
// ──────────────────────────────────────────────────────────────
function AgentDisplay({ agentKey, agentData }) {
  let response = agentData[agentKey];
  if (!response) return <EmptySlot message="No data for this agent" />;

  // Handle array format
  if (Array.isArray(response)) {
    const latest = response[response.length - 1];
    response = latest?.result || (response.length > 0 ? response[response.length - 1] : null);
  }
  if (!response) return <EmptySlot message="No data for this agent" />;

  const data = response.data || response;

  switch (agentKey) {
    case "iqvia":
      return (
        <AgentErrorBoundary agentName="IQVIA">
          <IQVIADataDisplay data={data} isFirstPrompt />
        </AgentErrorBoundary>
      );
    case "exim":
      return (
        <AgentErrorBoundary agentName="EXIM Trade">
          <EXIMDataDisplay data={data} showChart />
        </AgentErrorBoundary>
      );
    case "patent":
      return (
        <AgentErrorBoundary agentName="Patent">
          <PatentDataDisplay data={data} isFirstPrompt />
        </AgentErrorBoundary>
      );
    case "clinical":
      return (
        <AgentErrorBoundary agentName="Clinical Trials">
          <ClinicalDataDisplay data={data} isFirstPrompt />
        </AgentErrorBoundary>
      );
    case "internal":
      return (
        <AgentErrorBoundary agentName="Internal Knowledge">
          <InternalKnowledgeDisplay data={data} />
        </AgentErrorBoundary>
      );
    case "web":
      return (
        <AgentErrorBoundary agentName="Web Intelligence">
          <WebIntelDisplay data={data} />
        </AgentErrorBoundary>
      );
    default:
      return null;
  }
}

function EmptySlot({ message }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-muted-foreground/60">
      <Columns2 size={32} className="mb-3 opacity-40" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Single comparison split/panel
// ──────────────────────────────────────────────────────────────
function ComparisonPanel({ chat, selectedAgent, onAgentChange, label }) {
  const agentData = useAgentDataForChat(chat);
  const availableAgents = useAgentsWithAvailability(agentData);
  const contentRef = useRef(null);

  // Auto‑select first agent with data if none selected
  const fallbackAgent = availableAgents.find((a) => a.hasData)?.key || null;
  const currentAgent = selectedAgent || fallbackAgent;

  // Notify parent of auto‑selection
  if (currentAgent && currentAgent !== selectedAgent) {
    // Use a microtask so we don't setState during render
    Promise.resolve().then(() => onAgentChange(currentAgent));
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col rounded-2xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border/40 bg-card/60">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
          {label}
        </span>
        <span className="text-xs text-muted-foreground truncate flex-1" title={chat?.title}>
          {chat?.title || "Untitled Chat"}
        </span>
        {availableAgents.length > 0 && (
          <AgentDropdown
            agents={availableAgents}
            selected={currentAgent}
            onChange={onAgentChange}
          />
        )}
      </div>

      {/* Panel content */}
      <div ref={contentRef} className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {currentAgent ? (
          <AgentDisplay agentKey={currentAgent} agentData={agentData} />
        ) : (
          <EmptySlot message="No agent data available for this chat" />
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// CompareStudiesView — full‑screen side‑by‑side comparison
// ──────────────────────────────────────────────────────────────
export function CompareStudiesView({
  leftChat,
  rightChat,
  leftAgent,
  rightAgent,
  onLeftAgentChange,
  onRightAgentChange,
  onExit,
}) {
  return (
    <motion.div
      key="compare-view"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col h-full"
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border/40 bg-card/30 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-2.5">
          <Columns2 size={16} className="text-primary" />
          <span className="text-sm font-semibold text-foreground">Study Comparison</span>
          <span className="text-xs text-muted-foreground ml-1">
            Side-by-side analysis
          </span>
        </div>
        <button
          onClick={onExit}
          className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-xl border border-border/60 bg-card/60 hover:border-destructive/40 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
        >
          <X size={14} />
          Exit Comparison
        </button>
      </div>

      {/* Split panels */}
      <div className="flex-1 flex gap-3 p-3 overflow-hidden min-h-0">
        <ComparisonPanel
          chat={leftChat}
          selectedAgent={leftAgent}
          onAgentChange={onLeftAgentChange}
          label="Study A"
        />

        {/* Divider */}
        <div className="w-px bg-border/30 shrink-0 self-stretch my-4" />

        <ComparisonPanel
          chat={rightChat}
          selectedAgent={rightAgent}
          onAgentChange={onRightAgentChange}
          label="Study B"
        />
      </div>
    </motion.div>
  );
}

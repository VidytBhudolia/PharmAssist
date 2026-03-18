/**
 * AgentOutputWrapper - Beautiful shadcn-based wrapper for agent outputs
 *
 * Provides consistent, professional styling for all agent data displays
 * with animations, loading states, and error handling.
 */

import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Loader2,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  Table as TableIcon,
  FileText,
  TrendingUp,
  Globe,
  Shield,
  Activity,
  BookOpen,
  FileBarChart,
} from "lucide-react";

// Agent icon mapping
const agentIcons = {
  iqvia: TrendingUp,
  exim: Globe,
  patent: Shield,
  clinical: Activity,
  internal: BookOpen,
  web: Globe,
  report: FileBarChart,
};

// Agent color mapping — aligned with Teal + Deep Navy theme
const agentColors = {
  iqvia: {
    primary: "text-sky-400",
    bg: "bg-sky-500/8",
    border: "border-sky-500/25",
    gradient: "from-sky-500/15 via-sky-500/5 to-transparent",
  },
  exim: {
    primary: "text-teal-400",
    bg: "bg-teal-500/8",
    border: "border-teal-500/25",
    gradient: "from-teal-500/15 via-teal-500/5 to-transparent",
  },
  patent: {
    primary: "text-amber-400",
    bg: "bg-amber-500/8",
    border: "border-amber-500/25",
    gradient: "from-amber-500/15 via-amber-500/5 to-transparent",
  },
  clinical: {
    primary: "text-emerald-400",
    bg: "bg-emerald-500/8",
    border: "border-emerald-500/25",
    gradient: "from-emerald-500/15 via-emerald-500/5 to-transparent",
  },
  internal: {
    primary: "text-cyan-400",
    bg: "bg-cyan-500/8",
    border: "border-cyan-500/25",
    gradient: "from-cyan-500/15 via-cyan-500/5 to-transparent",
  },
  web: {
    primary: "text-indigo-400",
    bg: "bg-indigo-500/8",
    border: "border-indigo-500/25",
    gradient: "from-indigo-500/15 via-indigo-500/5 to-transparent",
  },
  report: {
    primary: "text-violet-400",
    bg: "bg-violet-500/8",
    border: "border-violet-500/25",
    gradient: "from-violet-500/15 via-violet-500/5 to-transparent",
  },
};

/**
 * AgentOutputWrapper - Main wrapper for agent outputs
 */
export function AgentOutputWrapper({
  agentKey = "iqvia",
  title,
  subtitle,
  status = "success", // success | loading | error | empty
  children,
  visualizations,
  tables,
  className = "",
}) {
  const Icon = agentIcons[agentKey] || TrendingUp;
  const colors = agentColors[agentKey] || agentColors.iqvia;

  // Determine what tabs to show
  const hasVisualizations = visualizations && React.Children.count(visualizations) > 0;
  const hasTables = tables && React.Children.count(tables) > 0;
  const hasMultipleTabs = hasVisualizations || hasTables;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      className={className}
    >
      <Card
        className={`overflow-hidden bg-gradient-to-br ${colors.gradient} to-card/80 border ${colors.border} shadow-lg backdrop-blur-sm rounded-2xl`}
      >
        {/* Header */}
        <CardHeader className="pb-3 border-b border-white/[0.04]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.div
                className={`p-2.5 rounded-xl ${colors.bg} border ${colors.border} backdrop-blur-sm`}
                whileHover={{ scale: 1.05, rotate: 2 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Icon className={colors.primary} size={22} />
              </motion.div>
              <div>
                <CardTitle className="text-lg font-bold text-foreground tracking-tight font-[family-name:var(--font-heading)]">{title}</CardTitle>
                {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
              </div>
            </div>
            <StatusBadge status={status} />
          </div>
        </CardHeader>

        {/* Content */}
        <CardContent className="p-0">
          {status === "loading" ? (
            <LoadingState agentKey={agentKey} />
          ) : status === "error" ? (
            <ErrorState />
          ) : status === "empty" ? (
            <EmptyState agentKey={agentKey} />
          ) : hasMultipleTabs ? (
            <Tabs defaultValue="overview" className="w-full">
              <div className="px-4 pt-3 border-b border-border/30">
                <TabsList className="grid w-full max-w-md grid-cols-3 h-9">
                  <TabsTrigger value="overview" className="text-xs gap-1.5">
                    <FileText size={14} />
                    Overview
                  </TabsTrigger>
                  {hasVisualizations && (
                    <TabsTrigger value="charts" className="text-xs gap-1.5">
                      <BarChart3 size={14} />
                      Charts
                    </TabsTrigger>
                  )}
                  {hasTables && (
                    <TabsTrigger value="data" className="text-xs gap-1.5">
                      <TableIcon size={14} />
                      Data
                    </TabsTrigger>
                  )}
                </TabsList>
              </div>
              <TabsContent value="overview" className="p-4 mt-0">
                <ScrollArea className="max-h-[500px]">{children}</ScrollArea>
              </TabsContent>
              {hasVisualizations && (
                <TabsContent value="charts" className="p-4 mt-0">
                  <ScrollArea className="max-h-[500px]">{visualizations}</ScrollArea>
                </TabsContent>
              )}
              {hasTables && (
                <TabsContent value="data" className="p-4 mt-0">
                  <ScrollArea className="max-h-[500px]">{tables}</ScrollArea>
                </TabsContent>
              )}
            </Tabs>
          ) : (
            <div className="p-4">
              <ScrollArea className="max-h-[500px]">{children}</ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * Status Badge Component
 */
function StatusBadge({ status }) {
  if (status === "loading") {
    return (
      <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30 gap-1.5">
        <Loader2 size={12} className="animate-spin" />
        Processing
      </Badge>
    );
  }
  if (status === "error") {
    return (
      <Badge
        variant="outline"
        className="bg-destructive/10 text-destructive border-destructive/30 gap-1.5"
      >
        <AlertCircle size={12} />
        Error
      </Badge>
    );
  }
  if (status === "success") {
    return (
      <Badge
        variant="outline"
        className="bg-emerald-500/10 text-emerald-500 border-emerald-500/30 gap-1.5"
      >
        <CheckCircle2 size={12} />
        Complete
      </Badge>
    );
  }
  return null;
}

/**
 * Loading State
 */
function LoadingState({ agentKey }) {
  const messages = {
    iqvia: "Fetching market intelligence data...",
    exim: "Analyzing export-import trends...",
    patent: "Querying patent databases...",
    clinical: "Searching clinical trial records...",
    internal: "Scanning internal knowledge base...",
    web: "Gathering web intelligence signals...",
    report: "Generating comprehensive report...",
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      >
        <Loader2 className="text-primary" size={40} />
      </motion.div>
      <p className="text-muted-foreground text-sm">{messages[agentKey] || "Processing data..."}</p>
    </div>
  );
}

/**
 * Error State
 */
function ErrorState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="p-3 rounded-full bg-destructive/10">
        <AlertCircle className="text-destructive" size={32} />
      </div>
      <div className="text-center">
        <p className="text-foreground font-medium">Failed to load data</p>
        <p className="text-muted-foreground text-sm mt-1">
          Please try again or contact support if the issue persists.
        </p>
      </div>
    </div>
  );
}

/**
 * Empty State
 */
function EmptyState({ agentKey }) {
  const Icon = agentIcons[agentKey] || TrendingUp;

  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="p-3 rounded-full bg-muted">
        <Icon className="text-muted-foreground" size={32} />
      </div>
      <div className="text-center">
        <p className="text-foreground font-medium">No data available</p>
        <p className="text-muted-foreground text-sm mt-1">
          This agent hasn&apos;t returned any results yet.
        </p>
      </div>
    </div>
  );
}

/**
 * MetricCard - Display a single metric with icon and trend
 */
export function MetricCard({
  label,
  value,
  trend,
  trendDirection = "up", // up | down | neutral
  icon: Icon,
  color = "blue",
}) {
  const colors = agentColors[color] || agentColors.iqvia;
  const TrendIcon =
    trendDirection === "up" ? TrendingUp : trendDirection === "down" ? TrendingUp : null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-4 rounded-xl ${colors.bg} border ${colors.border} transition-all hover:shadow-md`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
          <p className={`text-2xl font-bold ${colors.primary} mt-1`}>{value}</p>
          {trend && (
            <div
              className={`flex items-center gap-1 mt-1 text-xs ${
                trendDirection === "up"
                  ? "text-emerald-500"
                  : trendDirection === "down"
                    ? "text-red-500"
                    : "text-muted-foreground"
              }`}
            >
              {TrendIcon && (
                <TrendIcon size={12} className={trendDirection === "down" ? "rotate-180" : ""} />
              )}
              <span>{trend}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg ${colors.bg}`}>
            <Icon className={colors.primary} size={18} />
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * DataSection - Section with title and content
 */
export function DataSection({ title, children, className = "" }) {
  return (
    <div className={`space-y-3 ${className}`}>
      <h4 className="text-sm font-semibold text-foreground uppercase tracking-wider">{title}</h4>
      {children}
    </div>
  );
}

/**
 * InfoRow - Key-value display row
 */
export function InfoRow({ label, value, highlight = false }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`text-sm font-medium ${highlight ? "text-primary" : "text-foreground"}`}>
        {value || "—"}
      </span>
    </div>
  );
}

export default AgentOutputWrapper;

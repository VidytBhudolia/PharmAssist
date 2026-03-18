/**
 * Unified Agent Data Displays
 *
 * Consistent, theme-aware displays for all agent outputs.
 * Layout order: Summary Banner → Visualizations → Details → Content → Prompts
 * All agents share the AgentDisplayShell wrapper for visual consistency.
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MetricCard,
  DataTable,
  InfoCard,
  SectionHeader,
  SummaryBanner,
} from "@/components/ui/metric-card";
import {
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Area,
  AreaChart as RechartsAreaChart,
  BarChart as RechartsBarChart,
  Bar,
} from "recharts";
import {
  TrendingUp,
  Globe,
  Shield,
  Activity,
  BookOpen,
  AlertTriangle,
  CheckCircle,
  FileText,
  Users,
  DollarSign,
  Package,
  MapPin,
  Calendar,
  Microscope,
  Building,
  Scale,
  BarChart3,
  PieChart,
  ExternalLink,
  Zap,
} from "lucide-react";

// ============================================================================
// AGENT DISPLAY SHELL — Shared wrapper for consistent layout
// ============================================================================
const shellColors = {
  sky: {
    accent: "bg-sky-500",
    border: "border-sky-500/15",
    headerBg: "bg-sky-500/[0.04]",
    iconBg: "bg-sky-500/15 border-sky-500/30",
    iconText: "text-sky-400",
    tag: "bg-sky-500/10 text-sky-400",
  },
  teal: {
    accent: "bg-teal-500",
    border: "border-teal-500/15",
    headerBg: "bg-teal-500/[0.04]",
    iconBg: "bg-teal-500/15 border-teal-500/30",
    iconText: "text-teal-400",
    tag: "bg-teal-500/10 text-teal-400",
  },
  amber: {
    accent: "bg-amber-500",
    border: "border-amber-500/15",
    headerBg: "bg-amber-500/[0.04]",
    iconBg: "bg-amber-500/15 border-amber-500/30",
    iconText: "text-amber-400",
    tag: "bg-amber-500/10 text-amber-400",
  },
  emerald: {
    accent: "bg-emerald-500",
    border: "border-emerald-500/15",
    headerBg: "bg-emerald-500/[0.04]",
    iconBg: "bg-emerald-500/15 border-emerald-500/30",
    iconText: "text-emerald-400",
    tag: "bg-emerald-500/10 text-emerald-400",
  },
  cyan: {
    accent: "bg-cyan-500",
    border: "border-cyan-500/15",
    headerBg: "bg-cyan-500/[0.04]",
    iconBg: "bg-cyan-500/15 border-cyan-500/30",
    iconText: "text-cyan-400",
    tag: "bg-cyan-500/10 text-cyan-400",
  },
  indigo: {
    accent: "bg-indigo-500",
    border: "border-indigo-500/15",
    headerBg: "bg-indigo-500/[0.04]",
    iconBg: "bg-indigo-500/15 border-indigo-500/30",
    iconText: "text-indigo-400",
    tag: "bg-indigo-500/10 text-indigo-400",
  },
};

function AgentDisplayShell({ icon: Icon, title, subtitle, tag, color = "sky", children }) {
  const c = shellColors[color] || shellColors.sky;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={`relative rounded-2xl border ${c.border} bg-card/60 backdrop-blur-sm overflow-hidden`}
    >
      {/* Top accent bar */}
      <div className={`h-[3px] ${c.accent} w-full opacity-60`} />

      {/* Agent header */}
      <div
        className={`flex items-center gap-3.5 px-6 py-4 ${c.headerBg} border-b border-white/[0.04]`}
      >
        <div className={`p-2.5 rounded-xl border ${c.iconBg}`}>
          <Icon className={c.iconText} size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-semibold text-foreground font-[family-name:var(--font-heading)] tracking-tight leading-none">
            {title}
          </h2>
          {subtitle && <p className="text-xs text-muted-foreground mt-1 truncate">{subtitle}</p>}
        </div>
        {tag && (
          <span className={`text-xs font-semibold px-3 py-1 rounded-full ${c.tag}`}>{tag}</span>
        )}
      </div>

      {/* Content — consistent padding */}
      <div className="p-6 space-y-6">{children}</div>
    </motion.div>
  );
}

// ============================================================================
// IQVIA AGENT DISPLAY — Market Intelligence
// Layout: Summary → Metrics (Viz) → Charts (Viz) → Articles (Content) → Prompts
// ============================================================================

export function IQVIADataDisplay({ data, isFirstPrompt, onPromptClick }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="IQVIA" icon={TrendingUp} color="sky" />;
  }

  // Handle error responses from the agent
  if (data.status === "error" && data.message) {
    return (
      <AgentDisplayShell
        icon={TrendingUp}
        title="IQVIA Market Intelligence"
        subtitle="Sales data, growth & competitive analysis"
        color="sky"
      >
        <div className="flex items-center gap-3 p-4 bg-red-500/[0.06] border border-red-500/20 rounded-xl">
          <AlertTriangle className="text-red-400 flex-shrink-0" size={20} />
          <p className="text-[15px] text-red-300">{data.message}</p>
        </div>
      </AgentDisplayShell>
    );
  }

  // Data can be at top level or nested in .data (handles double-nesting from orchestrator)
  const actualData = data.data || data;

  const marketForecast = actualData.market_forecast || data.market_forecast;
  const competitiveShare = actualData.competitive_share || data.competitive_share;
  const summary = actualData.summary || data.summary;
  const infographics = actualData.infographics || data.infographics || [];
  const cagrAnalysis = actualData.cagr_analysis || data.cagr_analysis;
  const marketSizeUSD = actualData.marketSizeUSD || data.marketSizeUSD;
  const cagrPercent = actualData.cagrPercent || data.cagrPercent;
  const totalGrowthPercent = actualData.totalGrowthPercent || data.totalGrowthPercent;
  const marketLeader = actualData.marketLeader || data.marketLeader;
  const topArticles = actualData.topArticles || data.topArticles || [];
  const dataAvailability = actualData.dataAvailability || data.dataAvailability || {};

  const parseShareValue = (share) => {
    if (!share) return 0;
    if (typeof share === "number") return share;
    const cleaned = String(share).replace(/[~%]/g, "").trim();
    return parseFloat(cleaned) || 0;
  };

  // Determine what content is available
  const hasMarketMetrics = !!(marketSizeUSD || cagrPercent || totalGrowthPercent || marketLeader);
  const hasForecastChart = !!(marketForecast?.data && marketForecast.data.length > 0);
  const hasCompetitiveChart = !!(competitiveShare?.data && competitiveShare.data.length > 0);
  const hasCAGR = !!(
    cagrAnalysis &&
    (cagrAnalysis.cagr_percent || cagrAnalysis.total_growth_percent)
  );
  const hasArticles = topArticles.length > 0;
  const hasInfographics = infographics.length > 0;
  const usingMockData = dataAvailability.usingMockData === true;

  const metricCount = [marketSizeUSD, cagrPercent, totalGrowthPercent, marketLeader].filter(
    Boolean,
  ).length;
  const totalSections = [
    hasMarketMetrics,
    hasForecastChart,
    hasCompetitiveChart,
    hasArticles,
    hasInfographics,
  ].filter(Boolean).length;

  // Deduplicate infographics that overlap with topArticles (by URL)
  const articleUrls = new Set(topArticles.map((a) => a.url));
  const uniqueInfographics = infographics.filter((ig) => !articleUrls.has(ig.url));

  return (
    <AgentDisplayShell
      icon={TrendingUp}
      title="IQVIA Market Intelligence"
      subtitle="Sales data, growth & competitive analysis"
      tag={
        metricCount ? `${metricCount} metrics` : totalSections ? `${totalSections} sections` : null
      }
      color="sky"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {summary && <SummaryBanner summary={summary} color="sky" />}

      {/* ── Mock data disclaimer ── */}
      {usingMockData && (
        <div className="flex items-center gap-2 px-3.5 py-2 bg-amber-500/[0.07] border border-amber-500/20 rounded-xl text-xs text-amber-300/90">
          <AlertTriangle size={14} className="flex-shrink-0 text-amber-400" />
          <span>
            Market data shown is an <strong>illustrative estimate</strong> based on industry
            benchmarks. Specific market data for this query was not available.
          </span>
        </div>
      )}

      {/* ── 2. VISUALIZATIONS — Key Metrics ── */}
      {hasMarketMetrics && (
        <div>
          <SectionHeader title="Market Overview" color="sky" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {marketSizeUSD != null && (
              <MetricCard
                label="Market Size"
                value={
                  typeof marketSizeUSD === "number" ? `$${marketSizeUSD.toFixed(1)}` : marketSizeUSD
                }
                unit="B"
                color="sky"
                icon={DollarSign}
                delay={0}
              />
            )}
            {cagrPercent != null && (
              <MetricCard
                label="CAGR"
                value={typeof cagrPercent === "number" ? cagrPercent.toFixed(1) : cagrPercent}
                unit="%"
                color="emerald"
                icon={TrendingUp}
                trend={cagrPercent > 5 ? "up" : "neutral"}
                delay={1}
              />
            )}
            {totalGrowthPercent != null && (
              <MetricCard
                label="Total Growth"
                value={
                  typeof totalGrowthPercent === "number"
                    ? totalGrowthPercent.toFixed(1)
                    : totalGrowthPercent
                }
                unit="%"
                color="teal"
                icon={Activity}
                delay={2}
              />
            )}
            {marketLeader && (
              <MetricCard
                label="Market Leader"
                value={marketLeader.therapy || marketLeader.company || "N/A"}
                subValue={marketLeader.share}
                color="violet"
                icon={Building}
                delay={3}
              />
            )}
          </div>
        </div>
      )}

      {/* ── CAGR Analysis (when metrics unavailable but CAGR data exists) ── */}
      {!hasMarketMetrics && hasCAGR && (
        <div>
          <SectionHeader title="Growth Analysis" color="sky" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {cagrAnalysis.cagr_percent != null && (
              <MetricCard
                label="CAGR"
                value={
                  typeof cagrAnalysis.cagr_percent === "number"
                    ? cagrAnalysis.cagr_percent.toFixed(1)
                    : cagrAnalysis.cagr_percent
                }
                unit="%"
                color="emerald"
                icon={TrendingUp}
                trend={cagrAnalysis.cagr_percent > 5 ? "up" : "neutral"}
                delay={0}
              />
            )}
            {cagrAnalysis.total_growth_percent != null && (
              <MetricCard
                label="Total Growth"
                value={
                  typeof cagrAnalysis.total_growth_percent === "number"
                    ? cagrAnalysis.total_growth_percent.toFixed(1)
                    : cagrAnalysis.total_growth_percent
                }
                unit="%"
                color="teal"
                icon={Activity}
                delay={1}
              />
            )}
            {cagrAnalysis.start_value_usd_millions != null && (
              <MetricCard
                label="Start Value"
                value={`$${cagrAnalysis.start_value_usd_millions}`}
                unit="B"
                color="sky"
                icon={DollarSign}
                delay={2}
              />
            )}
            {cagrAnalysis.end_value_usd_millions != null && (
              <MetricCard
                label="End Value"
                value={`$${cagrAnalysis.end_value_usd_millions}`}
                unit="B"
                color="sky"
                icon={DollarSign}
                delay={3}
              />
            )}
          </div>
          {cagrAnalysis.interpretation && (
            <p className="text-[15px] text-muted-foreground mt-3 px-1">
              {cagrAnalysis.interpretation}
            </p>
          )}
        </div>
      )}

      {/* Market Forecast Chart — Interactive Recharts */}
      {hasForecastChart && (
        <div>
          <SectionHeader title={marketForecast.title || "Market Growth Trajectory"} color="sky" />

          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsAreaChart
                  data={marketForecast.data}
                  margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="iqviaAreaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.2} />
                  <XAxis
                    dataKey="year"
                    stroke="var(--muted-foreground)"
                    fontSize={13}
                    tickLine={false}
                    axisLine={{ stroke: "var(--border)" }}
                    tick={{ fill: "#ffffff" }}
                  />
                  <YAxis
                    stroke="var(--muted-foreground)"
                    fontSize={13}
                    tickLine={false}
                    axisLine={{ stroke: "var(--border)" }}
                    tickFormatter={(v) => `$${v}B`}
                    tick={{ fill: "#ffffff" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: "12px",
                      padding: "10px 14px",
                      fontSize: "14px",
                    }}
                    labelStyle={{ color: "var(--foreground)", fontWeight: 600, marginBottom: 4 }}
                    itemStyle={{ color: "var(--muted-foreground)" }}
                    formatter={(value) => [`$${value}B`, "Market Size"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#38bdf8"
                    strokeWidth={3}
                    fill="url(#iqviaAreaGrad)"
                    dot={{ r: 6, fill: "#38bdf8", stroke: "#0f1628", strokeWidth: 2 }}
                    activeDot={{ r: 8, fill: "#38bdf8", stroke: "#fff", strokeWidth: 2 }}
                  />
                </RechartsAreaChart>
              </ResponsiveContainer>
            </div>

            {marketForecast.description && (
              <p className="text-[15px] text-muted-foreground mt-4 pt-4 border-t border-border">
                {marketForecast.description}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Competitive Share — Interactive Recharts Donut */}
      {hasCompetitiveChart &&
        (() => {
          const PIE_COLORS = ["#38bdf8", "#2dd4bf", "#a78bfa", "#fbbf24", "#818cf8", "#f472b6"];
          const pieData = competitiveShare.data.map((item) => ({
            name: item.company,
            value: parseShareValue(item.share),
            originalShare: item.share,
          }));
          const pieTotal = pieData.reduce((s, d) => s + d.value, 0);

          const renderPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
            if (percent < 0.04) return null;
            const RADIAN = Math.PI / 180;
            const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
            const x = cx + radius * Math.cos(-midAngle * RADIAN);
            const y = cy + radius * Math.sin(-midAngle * RADIAN);
            return (
              <text
                x={x}
                y={y}
                fill="white"
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={15}
                fontWeight={700}
              >
                {`${(percent * 100).toFixed(0)}%`}
              </text>
            );
          };

          return (
            <div>
              <SectionHeader
                title={competitiveShare.title || "Competitive Landscape"}
                color="emerald"
              />

              <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
                  {/* Interactive Donut Chart */}
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={70}
                          outerRadius={120}
                          paddingAngle={3}
                          dataKey="value"
                          labelLine={false}
                          label={renderPieLabel}
                          animationDuration={800}
                          animationEasing="ease-out"
                        >
                          {pieData.map((_, idx) => (
                            <Cell
                              key={`cell-${idx}`}
                              fill={PIE_COLORS[idx % PIE_COLORS.length]}
                              stroke="var(--background)"
                              strokeWidth={3}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "var(--popover)",
                            border: "1px solid var(--border)",
                            borderRadius: "12px",
                            padding: "10px 14px",
                            fontSize: "14px",
                            color: "#ffffff",
                          }}
                          labelStyle={{ color: "#ffffff", fontWeight: 600, marginBottom: 4 }}
                          itemStyle={{ color: "#ffffff" }}
                          formatter={(value, name) => {
                            const pct = pieTotal > 0 ? ((value / pieTotal) * 100).toFixed(1) : 0;
                            return [`${pct}%`, name];
                          }}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Legend — right side */}
                  <div className="space-y-2.5">
                    {competitiveShare.data.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                      >
                        <div className="flex items-center gap-2.5">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                          />
                          <span className="text-[15px] text-foreground">{item.company}</span>
                        </div>
                        <span
                          className="text-[15px] font-semibold"
                          style={{ color: PIE_COLORS[idx % PIE_COLORS.length] }}
                        >
                          {item.share}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

      {/* ── Statista Infographics (rich visual cards) ── */}
      {uniqueInfographics.length > 0 && (
        <div>
          <SectionHeader
            title="Market Infographics"
            badge={`${uniqueInfographics.length} visuals`}
            color="sky"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {uniqueInfographics.map((ig, idx) => (
              <motion.a
                key={idx}
                href={ig.url}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group bg-card/60 border border-white/[0.06] rounded-xl overflow-hidden hover:border-sky-400/30 transition-all duration-200"
              >
                {/* Infographic image */}
                {ig.content && (
                  <div className="w-full h-36 bg-muted/30 overflow-hidden">
                    <img
                      src={ig.content}
                      alt={ig.title || ""}
                      className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300"
                      onError={(e) => {
                        e.target.style.display = "none";
                      }}
                    />
                  </div>
                )}
                <div className="p-3.5">
                  <p className="text-sm font-medium text-foreground line-clamp-2 group-hover:text-sky-400 transition-colors">
                    {ig.title}
                  </p>
                  {ig.description && (
                    <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
                      {ig.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span className="text-sky-400 font-medium">Statista</span>
                    {ig.premium && (
                      <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[11px]">
                        Premium
                      </span>
                    )}
                    <ExternalLink
                      size={11}
                      className="ml-auto opacity-40 group-hover:opacity-100"
                    />
                  </div>
                </div>
              </motion.a>
            ))}
          </div>
        </div>
      )}

      {/* ── CONTENT — Market Research Articles ── */}
      {hasArticles && (
        <div>
          <SectionHeader
            title="Market Research & Insights"
            badge={`${topArticles.length} sources`}
            color="cyan"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {topArticles.map((item, idx) => (
              <motion.a
                key={idx}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group p-4 bg-sky-500/[0.04] border border-sky-500/15 rounded-xl hover:border-sky-400/30 transition-all duration-200"
              >
                <div className="flex gap-3">
                  {/* Thumbnail if available */}
                  {item.imageUrl && (
                    <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-muted/50 border border-white/[0.06]">
                      <img
                        src={item.imageUrl}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={(e) => (e.target.parentElement.style.display = "none")}
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-[15px] font-medium text-foreground line-clamp-2 group-hover:text-sky-400 transition-colors">
                      {item.title}
                    </p>
                    {(item.snippet || item.subtitle) && (
                      <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2">
                        {item.snippet || item.subtitle}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-2.5 text-[13px] text-muted-foreground">
                      <span className="text-sky-400 font-medium">{item.source || "Statista"}</span>
                      {item.premium && (
                        <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-xs">
                          Premium
                        </span>
                      )}
                      <ExternalLink
                        size={13}
                        className="ml-auto opacity-50 group-hover:opacity-100"
                      />
                    </div>
                  </div>
                </div>
              </motion.a>
            ))}
          </div>
        </div>
      )}

      {/* ── Infographics-only fallback (when no separate articles exist) ── */}
      {!hasArticles && hasInfographics && uniqueInfographics.length === 0 && (
        <div>
          <SectionHeader
            title="Market Research & Insights"
            badge={`${infographics.length} sources`}
            color="cyan"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {infographics.map((item, idx) => (
              <motion.a
                key={idx}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group p-4 bg-sky-500/[0.04] border border-sky-500/15 rounded-xl hover:border-sky-400/30 transition-all duration-200"
              >
                <div className="flex gap-3">
                  {item.content && (
                    <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-muted/50 border border-white/[0.06]">
                      <img
                        src={item.content}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={(e) => (e.target.parentElement.style.display = "none")}
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-[15px] font-medium text-foreground line-clamp-2 group-hover:text-sky-400 transition-colors">
                      {item.title}
                    </p>
                    {(item.description || item.subtitle) && (
                      <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2">
                        {item.description || item.subtitle}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-2.5 text-[13px] text-muted-foreground">
                      <span className="text-sky-400 font-medium">Statista</span>
                      {item.premium && (
                        <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-xs">
                          Premium
                        </span>
                      )}
                      <ExternalLink
                        size={13}
                        className="ml-auto opacity-50 group-hover:opacity-100"
                      />
                    </div>
                  </div>
                </div>
              </motion.a>
            ))}
          </div>
        </div>
      )}

      {/* ── Data Availability Status (shown when no market data available) ── */}
      {!hasMarketMetrics && !hasForecastChart && !hasCompetitiveChart && (
        <div className="flex items-start gap-3 p-4 bg-sky-500/[0.04] border border-sky-500/15 rounded-xl">
          <BarChart3 className="text-sky-400 flex-shrink-0 mt-0.5" size={18} />
          <div>
            <p className="text-[15px] text-foreground font-medium">Limited Market Data</p>
            <p className="text-sm text-muted-foreground mt-1">
              Detailed market sizing, growth forecasts, and competitive share data is not available
              for this query.
              {(hasArticles || hasInfographics) &&
                " Market research reports and infographics from Statista are shown below."}
            </p>
            {Object.keys(dataAvailability).length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2.5">
                {dataAvailability.hasMarketForecast && (
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full">
                    ✓ Forecast
                  </span>
                )}
                {dataAvailability.hasCompetitiveShare && (
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full">
                    ✓ Competition
                  </span>
                )}
                {dataAvailability.hasInfographics && (
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full">
                    ✓ Infographics
                  </span>
                )}
                {dataAvailability.hasCAGR && (
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full">
                    ✓ CAGR
                  </span>
                )}
                {!dataAvailability.hasMarketForecast && (
                  <span className="text-xs bg-muted/50 text-muted-foreground px-2 py-0.5 rounded-full">
                    ✗ Forecast
                  </span>
                )}
                {!dataAvailability.hasCompetitiveShare && (
                  <span className="text-xs bg-muted/50 text-muted-foreground px-2 py-0.5 rounded-full">
                    ✗ Competition
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </AgentDisplayShell>
  );
}

// ============================================================================
// EXIM AGENT DISPLAY — Trade Intelligence
// Layout: Summary → Overview → Metrics → Charts → Risk Assessment → Sourcing → Table
// ============================================================================

export function EXIMDataDisplay({ data, showChart, onPromptClick }) {
  const [tradePage, setTradePage] = React.useState(0);
  const [expandView, setExpandView] = React.useState(false);

  // Handle escape key for modal
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape" && expandView) {
        setExpandView(false);
      }
    };
    if (expandView) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [expandView]);

  const TRADES_PER_PAGE = 20;

  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="EXIM" icon={Globe} color="teal" />;
  }

  // Unwrap double-nested data
  const actualData = data.data || data;

  // Correct data mapping to actual backend structure
  const bannerSummary = (actualData.summary || data.summary)?.researcherQuestion
    ? actualData.summary || data.summary
    : null;
  const tradeData = actualData.trade_data || data.trade_data || {};
  const analysis = actualData.analysis || data.analysis || {};
  const llmInsights = actualData.llm_insights || data.llm_insights || {};
  const inputInfo = actualData.input || data.input || {};

  // Extract from analysis.summary for metrics
  const analysisSummary = analysis.summary || {};
  const topPartners = analysis.top_partners || [];

  // Extract insights sections
  const sourcingInsights = llmInsights.sourcing_insights || {};
  const importDependency = llmInsights.import_dependency || {};
  const tradeDescription =
    llmInsights.trade_volume_description || llmInsights.summary_description || "";

  // Build trade rows from trade_data.rows (actual backend format)
  const allTrades =
    tradeData.rows ||
    topPartners.map((p) => ({
      Country: p.name,
      "2024 - 2025": p.current_value,
      "2023 - 2024": p.previous_value,
      "%Growth": p.growth,
      "%Share": p.share,
    })) ||
    [];

  const totalPages = Math.ceil(allTrades.length / TRADES_PER_PAGE);
  const startIdx = tradePage * TRADES_PER_PAGE;
  const endIdx = Math.min(startIdx + TRADES_PER_PAGE, allTrades.length);
  const paginatedTrades = allTrades.slice(startIdx, endIdx);

  // Prepare chart data from top_partners or trade rows
  const chartData = (
    topPartners.length > 0
      ? topPartners
      : allTrades.map((r) => ({
          name: r.Country || r.country,
          current_value: parseFloat(r["2024 - 2025"] || r.current_value || 0),
          growth: parseFloat(r["%Growth"] || r.growth || 0),
          share: parseFloat(r["%Share"] || r.share || 0),
        }))
  )
    .slice(0, 8)
    .map((p) => ({
      name: p.name || p.Country || p.country,
      value: parseFloat(p.current_value || 0),
      growth: parseFloat(p.growth || 0),
      share: parseFloat(p.share || 0),
    }));

  const CHART_COLORS = [
    "#0ea5e9",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    "#2dd4bf",
    "#fb7185",
  ];

  // Key metrics from analysis.summary
  const totalTradeValue = analysisSummary.total_current_year || tradeData.totals?.Total;
  const overallGrowth = analysisSummary.overall_growth;
  const partnersCount = analysisSummary.top_partners_count || allTrades.length;

  // Detect column names from backend
  const currentYearCol = analysis.columns_used?.current_year || "2024 - 2025";
  const previousYearCol = analysis.columns_used?.previous_year || "2023 - 2024";

  return (
    <AgentDisplayShell
      icon={Globe}
      title="EXIM Trade Intelligence"
      subtitle="Export-Import & trade flow analysis"
      tag={allTrades.length ? `${allTrades.length} markets` : null}
      color="teal"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {bannerSummary && <SummaryBanner summary={bannerSummary} color="teal" />}

      {/* ── 2. TRADE OVERVIEW ── */}
      <div>
        <SectionHeader title="Trade Overview" color="teal" />
        <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
          <p className="text-[15px] text-foreground leading-relaxed">
            {tradeDescription ||
              `Comprehensive analysis of ${inputInfo.trade_type || "export"}-import patterns for ${inputInfo.product || "the product"} across ${partnersCount} key trading partners.`}
          </p>
        </div>
      </div>

      {/* ── 3. KEY METRICS ── */}
      <div>
        <SectionHeader title="Key Metrics" color="teal" />
        <div className="grid grid-cols-3 gap-3">
          <MetricCard
            label="Total Trade Value"
            value={
              totalTradeValue
                ? typeof totalTradeValue === "number"
                  ? `$${totalTradeValue.toFixed(1)}M`
                  : `$${totalTradeValue}M`
                : "N/A"
            }
            color="teal"
            icon={DollarSign}
            delay={0}
          />
          <MetricCard
            label="YoY Growth"
            value={
              overallGrowth !== undefined
                ? `${typeof overallGrowth === "number" ? overallGrowth.toFixed(1) : overallGrowth}%`
                : "N/A"
            }
            color="emerald"
            icon={TrendingUp}
            trend={overallGrowth > 0 ? "up" : "down"}
            delay={1}
          />
          <MetricCard
            label="Trading Partners"
            value={partnersCount || "N/A"}
            color="sky"
            icon={Users}
            delay={2}
          />
        </div>
      </div>

      {/* ── 4. TRADE VOLUME DISTRIBUTION (Bar Chart — Clinical Trials style) ── */}
      {chartData.length > 0 && (
        <div>
          <SectionHeader title="Trade Volume Distribution" color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <ResponsiveContainer width="100%" height={300}>
              <RechartsBarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#ffffff", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.2)"
                  angle={-35}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fill: "#ffffff", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.2)"
                  tickFormatter={(v) => `$${v}M`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "transparent",
                    border: "none",
                    color: "#ffffff",
                  }}
                  labelStyle={{ color: "#ffffff" }}
                  itemStyle={{ color: "#ffffff" }}
                  formatter={(value) => [`$${value}M`, "Trade Volume"]}
                  cursor={false}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </RechartsBarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── 5. MARKET SHARE BREAKDOWN (Pie Chart — Clinical Trials style) ── */}
      {chartData.length > 0 && (
        <div>
          <SectionHeader title="Market Share Breakdown" color="teal" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
              {/* Pie Chart — left side */}
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={chartData.slice(0, 6)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={110}
                      paddingAngle={3}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="name"
                      labelLine={false}
                      label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
                        if (percent < 0.04) return null;
                        const RADIAN = Math.PI / 180;
                        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                        const x = cx + radius * Math.cos(-midAngle * RADIAN);
                        const y = cy + radius * Math.sin(-midAngle * RADIAN);
                        return (
                          <text
                            x={x}
                            y={y}
                            fill="white"
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize={15}
                            fontWeight={700}
                          >
                            {`${(percent * 100).toFixed(0)}%`}
                          </text>
                        );
                      }}
                      animationDuration={800}
                      animationEasing="ease-out"
                    >
                      {chartData.slice(0, 6).map((_, idx) => (
                        <Cell
                          key={`cell-${idx}`}
                          fill={CHART_COLORS[idx % CHART_COLORS.length]}
                          stroke="var(--background)"
                          strokeWidth={3}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(10, 15, 26, 0.95)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                        color: "#ffffff",
                      }}
                      labelStyle={{ color: "#ffffff" }}
                      itemStyle={{ color: "#ffffff" }}
                      formatter={(value, name) => [`$${value}M`, name]}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend — right side */}
              <div className="space-y-2.5">
                {chartData.slice(0, 6).map((item, idx) => {
                  const totalValue = chartData
                    .slice(0, 6)
                    .reduce((sum, d) => sum + (d.value || 0), 0);
                  const percentage =
                    totalValue > 0 ? ((item.value / totalValue) * 100).toFixed(1) : 0;
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}
                        />
                        <span className="text-[15px] text-foreground">{item.name}</span>
                      </div>
                      <span
                        className="text-[15px] font-semibold"
                        style={{ color: CHART_COLORS[idx % CHART_COLORS.length] }}
                      >
                        {percentage}% (${item.value}M)
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── 6. SUPPLY CHAIN RISK ASSESSMENT ── */}
      {importDependency &&
        (importDependency.critical_dependencies ||
          importDependency.risk_assessment ||
          importDependency.description) && (
          <div>
            <SectionHeader title="Supply Chain Risk Assessment" color="amber" />
            <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-4">
              {/* Risk Description */}
              {(importDependency.description || importDependency.risk_assessment) && (
                <div className="p-4 bg-amber-500/[0.06] border border-amber-500/20 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle size={18} className="text-amber-400 flex-shrink-0 mt-0.5" />
                    <p className="text-[15px] text-foreground leading-relaxed">
                      {importDependency.risk_assessment || importDependency.description}
                    </p>
                  </div>
                </div>
              )}

              {/* Critical Dependencies Table */}
              {importDependency.critical_dependencies &&
                importDependency.critical_dependencies.length > 0 && (
                  <div>
                    <h4 className="text-[15px] font-semibold text-foreground mb-3 flex items-center gap-2">
                      <Shield size={16} className="text-amber-400" />
                      Critical Import Dependencies
                    </h4>
                    <DataTable
                      headers={["Country", "Import Share", "Risk Level", "Alternatives"]}
                      rows={importDependency.critical_dependencies.map((dep) => [
                        dep.country || "N/A",
                        <span key="share" className="text-sky-400 font-medium">
                          {dep.import_share}%
                        </span>,
                        <span
                          key="risk"
                          className={`font-medium px-2.5 py-1 rounded-full text-[13px] ${
                            dep.risk === "High"
                              ? "bg-red-500/15 text-red-400"
                              : dep.risk === "Medium"
                                ? "bg-amber-500/15 text-amber-400"
                                : "bg-emerald-500/15 text-emerald-400"
                          }`}
                        >
                          {dep.risk}
                        </span>,
                        (dep.alternative_sources || []).join(", ") || "N/A",
                      ])}
                      color="amber"
                    />
                  </div>
                )}

              {/* Key Metrics Row */}
              {(importDependency.total_import_value || importDependency.dependency_ratio) && (
                <div className="grid grid-cols-2 gap-3">
                  {importDependency.total_import_value && (
                    <div className="p-4 bg-muted/30 rounded-lg text-center">
                      <p className="text-[13px] text-muted-foreground mb-1">Total Import Value</p>
                      <p className="text-xl font-bold text-amber-400">
                        ${importDependency.total_import_value}M
                      </p>
                    </div>
                  )}
                  {importDependency.dependency_ratio && (
                    <div className="p-4 bg-muted/30 rounded-lg text-center">
                      <p className="text-[13px] text-muted-foreground mb-1">Dependency Ratio</p>
                      <p className="text-xl font-bold text-violet-400">
                        {importDependency.dependency_ratio}%
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Recommendations */}
              {importDependency.recommendations && importDependency.recommendations.length > 0 && (
                <div className="p-4 bg-emerald-500/[0.04] border border-emerald-500/15 rounded-lg">
                  <h5 className="text-[14px] font-semibold text-emerald-400 mb-2">
                    Recommendations
                  </h5>
                  <ul className="space-y-1.5">
                    {importDependency.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-[14px] text-foreground">
                        <span className="text-emerald-400 mt-1">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

      {/* ── 7. SOURCING STRATEGY RECOMMENDATIONS ── */}
      {sourcingInsights &&
        (sourcingInsights.primary_sources ||
          sourcingInsights.description ||
          sourcingInsights.diversification_recommendation) && (
          <div>
            <SectionHeader title="Sourcing Strategy" color="violet" />
            <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-4">
              {/* Description */}
              {sourcingInsights.description && (
                <p className="text-[15px] text-muted-foreground leading-relaxed">
                  {sourcingInsights.description}
                </p>
              )}

              {/* Primary Sources Table */}
              {sourcingInsights.primary_sources && sourcingInsights.primary_sources.length > 0 && (
                <div>
                  <h4 className="text-[15px] font-semibold text-foreground mb-3 flex items-center gap-2">
                    <Package size={16} className="text-violet-400" />
                    Primary Sources
                  </h4>
                  <DataTable
                    headers={["Country", "Share", "Quality", "Risk Level"]}
                    rows={sourcingInsights.primary_sources.map((src) => [
                      src.country || "N/A",
                      <span key="share" className="text-sky-400 font-medium">
                        {src.share_percent}%
                      </span>,
                      <span
                        key="quality"
                        className={`font-medium ${src.quality_rating === "High" ? "text-emerald-400" : "text-amber-400"}`}
                      >
                        {src.quality_rating || "N/A"}
                      </span>,
                      <span
                        key="risk"
                        className={`font-medium px-2.5 py-1 rounded-full text-[13px] ${
                          src.risk_level === "High"
                            ? "bg-red-500/15 text-red-400"
                            : src.risk_level === "Medium"
                              ? "bg-amber-500/15 text-amber-400"
                              : "bg-emerald-500/15 text-emerald-400"
                        }`}
                      >
                        {src.risk_level || "N/A"}
                      </span>,
                    ])}
                    color="violet"
                  />
                </div>
              )}

              {/* Concentration & HHI Metrics */}
              {(sourcingInsights.supply_concentration || sourcingInsights.hhi_index) && (
                <div className="grid grid-cols-2 gap-3">
                  {sourcingInsights.supply_concentration && (
                    <div className="p-4 bg-muted/30 rounded-lg text-center">
                      <p className="text-[13px] text-muted-foreground mb-1">Supply Concentration</p>
                      <p className="text-xl font-bold text-violet-400">
                        {sourcingInsights.supply_concentration}
                      </p>
                    </div>
                  )}
                  {sourcingInsights.hhi_index && (
                    <div className="p-4 bg-muted/30 rounded-lg text-center">
                      <p className="text-[13px] text-muted-foreground mb-1">HHI Index</p>
                      <p className="text-xl font-bold text-sky-400">{sourcingInsights.hhi_index}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Diversification Recommendation */}
              {sourcingInsights.diversification_recommendation && (
                <div className="p-4 bg-violet-500/[0.06] border border-violet-500/20 rounded-lg">
                  <div className="flex items-start gap-3">
                    <TrendingUp size={18} className="text-violet-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h5 className="text-[14px] font-semibold text-violet-400 mb-1">
                        Diversification Strategy
                      </h5>
                      <p className="text-[14px] text-foreground leading-relaxed">
                        {sourcingInsights.diversification_recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      {/* ── 8. TRADE DATA TABLE WITH EXPAND ── */}
      {allTrades.length > 0 && (
        <div>
          <SectionHeader
            title="Trading Partners"
            badge={`${allTrades.length} countries`}
            color="teal"
          />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-4">
            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const csv = [
                    ["Country", currentYearCol, previousYearCol, "% Growth", "% Share"],
                    ...allTrades.map((t) => [
                      t.Country || t.country || "",
                      t[currentYearCol] || t.current_value || "",
                      t[previousYearCol] || t.previous_value || "",
                      t["%Growth"] || t.growth || "",
                      t["%Share"] || t.share || "",
                    ]),
                  ]
                    .map((row) => row.map((cell) => `"${cell}"`).join(","))
                    .join("\n");

                  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                  const link = document.createElement("a");
                  const url = URL.createObjectURL(blob);
                  link.setAttribute("href", url);
                  link.setAttribute("download", "trade_data.csv");
                  link.style.visibility = "hidden";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 hover:border-emerald-400/50 hover:bg-emerald-500/15 transition-all text-emerald-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download CSV
              </button>
              <button
                onClick={() => setExpandView(!expandView)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-500/10 border border-teal-500/30 hover:border-teal-400/50 hover:bg-teal-500/15 transition-all text-teal-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Expand View
              </button>
            </div>

            <DataTable
              headers={["Country", currentYearCol, previousYearCol, "Growth", "Share"]}
              rows={paginatedTrades.map((trade) => [
                trade.Country || trade.country || trade.name || "N/A",
                trade[currentYearCol] || trade.current_value || "N/A",
                trade[previousYearCol] || trade.previous_value || "N/A",
                <span
                  key="growth"
                  className={`font-medium ${parseFloat(trade["%Growth"] || trade.growth || 0) > 0 ? "text-emerald-400" : "text-red-400"}`}
                >
                  {trade["%Growth"] || trade.growth || "N/A"}%
                </span>,
                <span key="share" className="text-sky-400 font-medium">
                  {trade["%Share"] || trade.share || "N/A"}%
                </span>,
              ])}
              color="teal"
            />

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
                <span className="text-[14px] text-muted-foreground">
                  Showing {startIdx + 1}–{Math.min(endIdx, allTrades.length)} of {allTrades.length}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTradePage(Math.max(0, tradePage - 1))}
                    disabled={tradePage === 0}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    ← Previous
                  </button>
                  <span className="text-[14px] font-medium text-foreground px-3 py-1.5 rounded-lg bg-white/[0.05]">
                    {tradePage + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setTradePage(Math.min(totalPages - 1, tradePage + 1))}
                    disabled={tradePage === totalPages - 1}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Expanded View Modal */}
      <AnimatePresence>
        {expandView && (
          <motion.div
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setExpandView(false);
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-800/95 border border-slate-700/50 rounded-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
            >
              {/* Modal Header */}
              <div className="bg-slate-700/40 border-b border-slate-600/50 p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                    <div className="p-2 bg-teal-500/10 rounded-lg">
                      <svg
                        className="w-6 h-6 text-teal-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                    Trade Data — All Partners
                  </h3>
                </div>
                <div className="flex items-center gap-3">
                  <motion.button
                    onClick={() => {
                      const csv = [
                        ["Country", currentYearCol, previousYearCol, "% Growth", "% Share"],
                        ...allTrades.map((t) => [
                          t.Country || t.country || "",
                          t[currentYearCol] || t.current_value || "",
                          t[previousYearCol] || t.previous_value || "",
                          t["%Growth"] || t.growth || "",
                          t["%Share"] || t.share || "",
                        ]),
                      ]
                        .map((row) => row.map((cell) => `"${cell}"`).join(","))
                        .join("\n");

                      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                      const link = document.createElement("a");
                      const url = URL.createObjectURL(blob);
                      link.setAttribute("href", url);
                      link.setAttribute("download", "trade_data_full.csv");
                      link.style.visibility = "hidden";
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 px-4 py-2 bg-teal-500/20 border border-teal-400/30 hover:border-teal-300/50 hover:bg-teal-500/30 text-teal-300 rounded-lg transition-colors font-medium"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Download
                  </motion.button>
                  <motion.button
                    onClick={() => setExpandView(false)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 hover:bg-slate-600/50 text-red-400 hover:text-red-300 rounded-lg transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </motion.button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-8 max-h-[calc(90vh-140px)]">
                <div className="bg-slate-800/60 border border-slate-700/30 rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-700/50 border-b border-slate-600/30">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Country
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          {currentYearCol}
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          {previousYearCol}
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Growth
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Share
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {allTrades.map((trade, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors"
                        >
                          <td className="px-6 py-4 text-sm text-slate-100 font-medium">
                            {trade.Country || trade.country || trade.name || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-200">
                            ${trade[currentYearCol] || trade.current_value || "N/A"}M
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-200">
                            ${trade[previousYearCol] || trade.previous_value || "N/A"}M
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <span
                              className={`font-medium ${parseFloat(trade["%Growth"] || trade.growth || 0) > 0 ? "text-emerald-400" : "text-red-400"}`}
                            >
                              {trade["%Growth"] || trade.growth || "N/A"}%
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-sky-400 font-medium">
                            {trade["%Share"] || trade.share || "N/A"}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="p-6 border-t border-slate-600/50 bg-slate-700/30 flex items-center justify-center">
                <p className="text-sm text-slate-300">
                  Showing all{" "}
                  <span className="font-semibold text-slate-100">{allTrades.length}</span> trading
                  partners
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AgentDisplayShell>
  );
}

// ============================================================================
// PATENT AGENT DISPLAY — IP Intelligence
// Layout: Summary → Metrics → Filing Heatmap → Key Patent → IP Opportunities → AUD Focus
// ============================================================================

export function PatentDataDisplay({ data, isFirstPrompt, onPromptClick }) {
  const [patentPage, setPatentPage] = React.useState(0);
  const [expandView, setExpandView] = React.useState(false);

  // Handle escape key for modal
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape" && expandView) {
        setExpandView(false);
      }
    };
    if (expandView) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [expandView]);

  const PATENTS_PER_PAGE = 10;

  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Patent" icon={Shield} color="amber" />;
  }

  // Handle error responses
  if (data.status === "error" && data.message) {
    return (
      <AgentDisplayShell
        icon={Shield}
        title="Patent Landscape"
        subtitle="FTO analysis & lifecycle strategy"
        color="amber"
      >
        <div className="flex items-center gap-3 p-4 bg-red-500/[0.06] border border-red-500/20 rounded-xl">
          <AlertTriangle className="text-red-400 flex-shrink-0" size={20} />
          <p className="text-[15px] text-red-300">{data.message}</p>
        </div>
      </AgentDisplayShell>
    );
  }

  // Unwrap nested data — orchestrator wraps as {timestamp, query, data: {status, data: {...}, visualizations}}
  const outerData = data.data || data;
  const actualData = outerData.data || outerData;

  // Extract banner summary from outer level (it's at the same level as "status")
  const bannerSummary = outerData.bannerSummary || data.bannerSummary || actualData.bannerSummary;

  // Core FTO fields
  const ftoStatus = actualData.ftoStatus || data.ftoStatus || "CLEAR";
  const ftoDate = actualData.ftoDate || data.ftoDate;
  const patentsFound = actualData.patentsFound ?? data.patentsFound ?? 0;
  const normalizedRisk = actualData.normalizedRiskInternal ?? data.normalizedRiskInternal ?? 0;

  // Summary layers
  const summaryLayers = actualData.summaryLayers || data.summaryLayers || {};
  // Fallback: if no executive summary in layers, use the top-level summary string
  const executiveSummary = summaryLayers.executive || outerData.summary || data.summary || "";

  // Patent lists
  const blockingPatents = actualData.blockingPatents || data.blockingPatents || [];
  const blockingPatentsSummary =
    actualData.blockingPatentsSummary || data.blockingPatentsSummary || {};
  const expandedResults = actualData.expandedResults || data.expandedResults || {};
  const nonBlockingPatents = expandedResults.nonBlockingPatents || [];
  const expiredPatents = expandedResults.expiredPatents || [];
  const uncertainPatents = expandedResults.uncertainPatents || [];

  // All patents combined for the table
  const allPatents = [
    ...blockingPatents.map((p) => ({ ...p, _category: "Blocking" })),
    ...uncertainPatents.map((p) => ({ ...p, _category: "Uncertain" })),
    ...nonBlockingPatents.map((p) => ({ ...p, _category: "Non-Blocking" })),
    ...expiredPatents.map((p) => ({ ...p, _category: "Expired" })),
  ];

  // Recommended actions
  const recommendedActions = actualData.recommendedActions || data.recommendedActions || [];
  const disclaimer = actualData.disclaimer || data.disclaimer;

  // Pagination
  const totalPages = Math.ceil(allPatents.length / PATENTS_PER_PAGE);
  const startIdx = patentPage * PATENTS_PER_PAGE;
  const endIdx = startIdx + PATENTS_PER_PAGE;
  const paginatedPatents = allPatents.slice(startIdx, endIdx);

  // FTO status styling
  const ftoStatusConfig = {
    CLEAR: {
      label: "Clear",
      color: "emerald",
      icon: CheckCircle,
      badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    },
    NEEDS_MONITORING: {
      label: "Monitor",
      color: "amber",
      icon: AlertTriangle,
      badge: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    },
    AT_RISK: {
      label: "At Risk",
      color: "amber",
      icon: AlertTriangle,
      badge: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    },
    BLOCKED: {
      label: "Blocked",
      color: "red",
      icon: Shield,
      badge: "bg-red-500/20 text-red-400 border-red-500/30",
    },
  };
  const statusConfig = ftoStatusConfig[ftoStatus] || ftoStatusConfig.CLEAR;

  // Build pie chart data from patent categories
  const pieData = [];
  if (blockingPatents.length > 0)
    pieData.push({ label: "Blocking", value: blockingPatents.length });
  if (uncertainPatents.length > 0)
    pieData.push({ label: "Uncertain", value: uncertainPatents.length });
  if (nonBlockingPatents.length > 0)
    pieData.push({ label: "Non-Blocking", value: nonBlockingPatents.length });
  if (expiredPatents.length > 0) pieData.push({ label: "Expired", value: expiredPatents.length });

  // Build claim type distribution from blockingPatentsSummary
  const claimTypeCounts = blockingPatentsSummary.claimTypeCounts || {};
  const claimTypeData = Object.entries(claimTypeCounts).map(([type, count]) => ({
    label: type,
    value: count,
  }));

  return (
    <AgentDisplayShell
      icon={Shield}
      title="Patent Landscape"
      subtitle="FTO analysis & lifecycle strategy"
      tag={patentsFound > 0 ? `${patentsFound} patents` : null}
      color="amber"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {bannerSummary && bannerSummary.researcherQuestion && (
        <SummaryBanner summary={bannerSummary} color="amber" />
      )}

      {/* ── 2. LANDSCAPE OVERVIEW ── */}
      {executiveSummary && (
        <div>
          <SectionHeader title="Patent Landscape" color="amber" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <p className="text-[15px] text-foreground leading-relaxed">{executiveSummary}</p>
          </div>
        </div>
      )}

      {/* ── 3. KEY METRICS ── */}
      <div>
        <SectionHeader title="Key Metrics" color="amber" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="FTO Status"
            value={statusConfig.label}
            color={ftoStatus === "CLEAR" ? "emerald" : ftoStatus === "BLOCKED" ? "red" : "amber"}
            icon={statusConfig.icon}
            delay={0}
          />
          <MetricCard
            label="Patents Found"
            value={patentsFound}
            color="sky"
            icon={FileText}
            delay={1}
          />
          <MetricCard
            label="Blocking Patents"
            value={blockingPatentsSummary.count ?? blockingPatents.length}
            color={blockingPatents.length > 0 ? "red" : "emerald"}
            icon={Shield}
            delay={2}
          />
          {ftoDate ? (
            <MetricCard label="FTO Date" value={ftoDate} color="violet" icon={Calendar} delay={3} />
          ) : (
            <MetricCard
              label="Risk Index"
              value={normalizedRisk}
              unit="/100"
              color={normalizedRisk > 60 ? "red" : normalizedRisk > 30 ? "amber" : "emerald"}
              icon={Activity}
              delay={3}
            />
          )}
        </div>
      </div>

      {/* ── 4. CHART — Patent Breakdown Pie ── */}
      {pieData.length > 0 &&
        (() => {
          const PIE_COLORS = {
            Blocking: "#ef4444",
            Uncertain: "#f59e0b",
            "Non-Blocking": "#10b981",
            Expired: "#6b7280",
          };
          const pieTotal = pieData.reduce((s, d) => s + d.value, 0);

          return (
            <div>
              <SectionHeader title="Patent Classification" color="amber" />
              <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={110}
                          paddingAngle={3}
                          dataKey="value"
                          nameKey="label"
                          labelLine={false}
                          label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
                            if (percent < 0.04) return null;
                            const RADIAN = Math.PI / 180;
                            const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                            const x = cx + radius * Math.cos(-midAngle * RADIAN);
                            const y = cy + radius * Math.sin(-midAngle * RADIAN);
                            return (
                              <text
                                x={x}
                                y={y}
                                fill="white"
                                textAnchor="middle"
                                dominantBaseline="central"
                                fontSize={15}
                                fontWeight={700}
                              >
                                {`${(percent * 100).toFixed(0)}%`}
                              </text>
                            );
                          }}
                          animationDuration={800}
                          animationEasing="ease-out"
                        >
                          {pieData.map((entry, idx) => (
                            <Cell
                              key={`cell-${idx}`}
                              fill={PIE_COLORS[entry.label] || "#8b5cf6"}
                              stroke="var(--background)"
                              strokeWidth={3}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "rgba(10, 15, 26, 0.95)",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "8px",
                            color: "#ffffff",
                          }}
                          formatter={(value, name) => {
                            const pct = pieTotal > 0 ? ((value / pieTotal) * 100).toFixed(1) : 0;
                            return [`${pct}% (${value})`, name];
                          }}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2.5">
                    {pieData.map((item, idx) => {
                      const pct = pieTotal > 0 ? ((item.value / pieTotal) * 100).toFixed(1) : 0;
                      return (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                        >
                          <div className="flex items-center gap-2.5">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: PIE_COLORS[item.label] || "#8b5cf6" }}
                            />
                            <span className="text-[15px] text-foreground">{item.label}</span>
                          </div>
                          <span
                            className="text-[15px] font-semibold"
                            style={{ color: PIE_COLORS[item.label] || "#8b5cf6" }}
                          >
                            {pct}% ({item.value})
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

      {/* ── 5. CHART — Claim Type Distribution Bar Chart ── */}
      {claimTypeData.length > 0 && (
        <div>
          <SectionHeader title="Blocking Patent Claim Types" color="amber" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <ResponsiveContainer width="100%" height={250}>
              <RechartsBarChart data={claimTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#ffffff", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.2)"
                />
                <YAxis
                  tick={{ fill: "#ffffff", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.2)"
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "transparent",
                    border: "none",
                    color: "#ffffff",
                  }}
                  labelStyle={{ color: "#ffffff" }}
                  itemStyle={{ color: "#ffffff" }}
                  cursor={false}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {claimTypeData.map((_, index) => {
                    const colors = [
                      "#f59e0b",
                      "#ef4444",
                      "#8b5cf6",
                      "#0ea5e9",
                      "#10b981",
                      "#ec4899",
                    ];
                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                  })}
                </Bar>
              </RechartsBarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── 6. TABLE — Recommended Actions ── */}
      {recommendedActions.length > 0 && (
        <div>
          <SectionHeader
            title="Recommended Actions"
            badge={`${recommendedActions.length} actions`}
            color="emerald"
          />
          <div className="space-y-2.5">
            {recommendedActions.map((action, idx) => {
              const feasColor = {
                HIGH: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30",
                MEDIUM: "text-amber-400 bg-amber-500/15 border-amber-500/30",
                LOW: "text-red-400 bg-red-500/15 border-red-500/30",
              };
              const fc = feasColor[action.feasibility] || feasColor.MEDIUM;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-4 bg-card/60 border border-white/[0.06] rounded-xl backdrop-blur-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <Zap size={15} className="text-amber-400 flex-shrink-0" />
                        <p className="text-[15px] font-semibold text-foreground">{action.action}</p>
                      </div>
                      {action.reason && (
                        <p className="text-sm text-muted-foreground ml-[23px]">{action.reason}</p>
                      )}
                      {action.nextStep && (
                        <p className="text-sm text-sky-400 mt-1.5 ml-[23px]">→ {action.nextStep}</p>
                      )}
                    </div>
                    {action.feasibility && (
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-full border whitespace-nowrap ${fc}`}
                      >
                        {action.feasibility}
                      </span>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 7. TABLE — All Patents with Pagination ── */}
      {paginatedPatents.length > 0 && (
        <div>
          <SectionHeader title="Patent Details" color="amber" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-4">
            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const csv = [
                    [
                      "Patent Number",
                      "Category",
                      "Claim Type",
                      "Assignee",
                      "Expiry",
                      "Risk Band",
                      "Reason",
                    ],
                    ...allPatents.map((p) => [
                      p.patentNumber || p.patent || "",
                      p._category || "",
                      p.claimType || "",
                      p.assignee || "",
                      p.expiry || p.expectedExpiry || "",
                      p.riskBand || "",
                      p.reason || "",
                    ]),
                  ]
                    .map((row) => row.map((cell) => `"${cell}"`).join(","))
                    .join("\n");
                  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                  const link = document.createElement("a");
                  link.href = URL.createObjectURL(blob);
                  link.download = "patent_analysis.csv";
                  link.style.visibility = "hidden";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500/10 border border-amber-500/30 hover:border-amber-400/50 hover:bg-amber-500/15 transition-all text-amber-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download CSV
              </button>
              <button
                onClick={() => setExpandView(!expandView)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-500/10 border border-teal-500/30 hover:border-teal-400/50 hover:bg-teal-500/15 transition-all text-teal-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Expand View
              </button>
            </div>

            <DataTable
              headers={["Patent", "Category", "Claim Type", "Expiry", "Risk"]}
              rows={paginatedPatents.map((p) => {
                const catColors = {
                  Blocking: "text-red-400",
                  Uncertain: "text-amber-400",
                  "Non-Blocking": "text-emerald-400",
                  Expired: "text-gray-400",
                };
                const riskColors = {
                  HIGH: "text-red-400",
                  MEDIUM: "text-amber-400",
                  LOW: "text-emerald-400",
                  CLEAR: "text-emerald-400",
                };
                const patentNum = p.patentNumber || p.patent || "N/A";
                const googlePatentsUrl =
                  patentNum !== "N/A"
                    ? `https://patents.google.com/patent/${patentNum.replace(/\s+/g, "")}/en`
                    : null;
                return [
                  googlePatentsUrl ? (
                    <a
                      key="pn"
                      href={googlePatentsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sky-400 hover:text-sky-300 underline underline-offset-2 decoration-sky-400/40 hover:decoration-sky-300/60 transition-colors"
                      title={`View ${patentNum} on Google Patents`}
                    >
                      {patentNum}
                    </a>
                  ) : (
                    <span key="pn" className="font-medium">
                      {patentNum}
                    </span>
                  ),
                  <span
                    key="cat"
                    className={`font-medium ${catColors[p._category] || "text-foreground"}`}
                  >
                    {p._category}
                  </span>,
                  p.claimType || "N/A",
                  p.expiry || p.expectedExpiry || "N/A",
                  <span
                    key="risk"
                    className={`font-medium ${riskColors[p.riskBand] || "text-foreground"}`}
                  >
                    {p.riskBand || p.status || "N/A"}
                  </span>,
                ];
              })}
              color="amber"
            />

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
                <span className="text-[14px] text-muted-foreground">
                  Showing {startIdx + 1}–{Math.min(endIdx, allPatents.length)} of{" "}
                  {allPatents.length}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPatentPage(Math.max(0, patentPage - 1))}
                    disabled={patentPage === 0}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    ← Previous
                  </button>
                  <span className="text-[14px] font-medium text-foreground px-3 py-1.5 rounded-lg bg-white/[0.05]">
                    {patentPage + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPatentPage(Math.min(totalPages - 1, patentPage + 1))}
                    disabled={patentPage === totalPages - 1}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── BUSINESS & LEGAL INSIGHTS ── */}
      {(summaryLayers.business || summaryLayers.legal) && (
        <div>
          <SectionHeader title="Expert Insights" color="violet" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {summaryLayers.business && (
              <div className="p-4 bg-card/60 border border-white/[0.06] rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Building size={15} className="text-sky-400" />
                  <h4 className="text-sm font-semibold text-sky-400 uppercase tracking-wider">
                    Business
                  </h4>
                </div>
                <p className="text-[15px] text-muted-foreground leading-relaxed">
                  {summaryLayers.business}
                </p>
              </div>
            )}
            {summaryLayers.legal && (
              <div className="p-4 bg-card/60 border border-white/[0.06] rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Scale size={15} className="text-violet-400" />
                  <h4 className="text-sm font-semibold text-violet-400 uppercase tracking-wider">
                    Legal
                  </h4>
                </div>
                <p className="text-[15px] text-muted-foreground leading-relaxed whitespace-pre-line">
                  {summaryLayers.legal}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── No Patents Found Info ── */}
      {patentsFound === 0 && !allPatents.length && (
        <div className="flex items-start gap-3 p-4 bg-emerald-500/[0.04] border border-emerald-500/15 rounded-xl">
          <CheckCircle className="text-emerald-400 flex-shrink-0 mt-0.5" size={18} />
          <div>
            <p className="text-[15px] text-foreground font-medium">No Blocking Patents Found</p>
            <p className="text-sm text-muted-foreground mt-1">
              The FTO analysis did not identify any blocking patents. Freedom to operate appears
              clear, but manual verification with patent counsel is recommended.
            </p>
          </div>
        </div>
      )}

      {/* ── Disclaimer ── */}
      {disclaimer && <p className="text-xs text-muted-foreground/60 italic px-1">{disclaimer}</p>}

      {/* ── Expanded View Modal ── */}
      <AnimatePresence>
        {expandView && (
          <motion.div
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setExpandView(false);
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-800/95 border border-slate-700/50 rounded-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
            >
              {/* Modal Header */}
              <div className="bg-slate-700/40 border-b border-slate-600/50 p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                    <div className="p-2 bg-amber-500/10 rounded-lg">
                      <Shield className="w-6 h-6 text-amber-400" />
                    </div>
                    Patent Analysis Details
                  </h3>
                </div>
                <div className="flex items-center gap-3">
                  <motion.button
                    onClick={() => {
                      const csv = [
                        [
                          "Patent Number",
                          "Category",
                          "Title",
                          "Assignee",
                          "Claim Type",
                          "Expiry",
                          "Risk Band",
                          "Reason",
                          "Status",
                        ],
                        ...allPatents.map((p) => [
                          p.patentNumber || p.patent || "",
                          p._category || "",
                          p.title || "",
                          p.assignee || "",
                          p.claimType || "",
                          p.expiry || p.expectedExpiry || "",
                          p.riskBand || "",
                          p.reason || "",
                          p.status || "",
                        ]),
                      ]
                        .map((row) => row.map((cell) => `"${cell}"`).join(","))
                        .join("\n");
                      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                      const link = document.createElement("a");
                      link.href = URL.createObjectURL(blob);
                      link.download = "patent_analysis_full.csv";
                      link.style.visibility = "hidden";
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 px-4 py-2 bg-teal-500/20 border border-teal-400/30 hover:border-teal-300/50 hover:bg-teal-500/30 text-teal-300 rounded-lg transition-colors font-medium"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Download
                  </motion.button>
                  <motion.button
                    onClick={() => setExpandView(false)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 hover:bg-slate-600/50 text-red-400 hover:text-red-300 rounded-lg transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </motion.button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-8 max-h-[calc(90vh-140px)]">
                <div className="bg-slate-800/60 border border-slate-700/30 rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-700/50 border-b border-slate-600/30">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Patent Number
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Category
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Title
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Assignee
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Claim Type
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Expiry
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Risk
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {allPatents.map((p, idx) => {
                        const catColors = {
                          Blocking: "text-red-400",
                          Uncertain: "text-amber-400",
                          "Non-Blocking": "text-emerald-400",
                          Expired: "text-gray-400",
                        };
                        const riskColors = {
                          HIGH: "text-red-400",
                          MEDIUM: "text-amber-400",
                          LOW: "text-emerald-400",
                          CLEAR: "text-emerald-400",
                        };
                        const patentNum = p.patentNumber || p.patent || "N/A";
                        const googlePatentsUrl =
                          patentNum !== "N/A"
                            ? `https://patents.google.com/patent/${patentNum.replace(/\s+/g, "")}/en`
                            : null;
                        return (
                          <tr
                            key={idx}
                            className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors"
                          >
                            <td className="px-6 py-4 text-sm font-medium">
                              {googlePatentsUrl ? (
                                <a
                                  href={googlePatentsUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sky-400 hover:text-sky-300 underline underline-offset-2 decoration-sky-400/40 hover:decoration-sky-300/60 transition-colors"
                                  title={`View ${patentNum} on Google Patents`}
                                >
                                  {patentNum}
                                </a>
                              ) : (
                                <span className="text-slate-100">{patentNum}</span>
                              )}
                            </td>
                            <td
                              className={`px-6 py-4 text-sm font-medium ${catColors[p._category] || "text-slate-200"}`}
                            >
                              {p._category}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-200 max-w-xs truncate">
                              {p.title || "N/A"}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-200">
                              {p.assignee || "N/A"}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-200">
                              {p.claimType || "N/A"}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-200">
                              {p.expiry || p.expectedExpiry || "N/A"}
                            </td>
                            <td
                              className={`px-6 py-4 text-sm font-medium ${riskColors[p.riskBand] || "text-slate-200"}`}
                            >
                              {p.riskBand || p.status || "N/A"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AgentDisplayShell>
  );
}

// ============================================================================
// CLINICAL AGENT DISPLAY — Trial Intelligence
// Layout: Summary → Landscape → Key Metrics → Phase Distribution Chart → Sponsor Table → Key Trials Table
// ============================================================================

export function ClinicalDataDisplay({ data, isFirstPrompt, onPromptClick }) {
  const [trialsPage, setTrialsPage] = React.useState(0);
  const [expandView, setExpandView] = React.useState(false);

  // Handle escape key for modal
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape" && expandView) {
        setExpandView(false);
      }
    };

    if (expandView) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [expandView]);
  const TRIALS_PER_PAGE = 20;

  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Clinical" icon={Activity} color="emerald" />;
  }

  const actualData = data.data || data;

  // Clinical agent returns: { trials: {...}, analysis: {...}, summary: {...}, visualizations: [...] }
  const trials = actualData.trials || data.trials || {};
  const analysis = actualData.analysis || data.analysis || {};
  const bannerSummary = actualData.summary || data.summary;
  const visualizations = actualData.visualizations || data.visualizations || [];

  // Extract key metrics from trials/analysis
  const totalTrials = trials.total_trials || 0;
  const medianEnrollment = trials.enrollment_summary?.median_enrollment || 0;
  const maturityScore = analysis.maturity_score ? Math.round(analysis.maturity_score * 100) : 0;

  // Find phase distribution bar chart from visualizations
  const phaseDistributionViz = visualizations.find((v) => v.id === "phase_distribution");
  const phaseDistributionData = phaseDistributionViz?.data || [];

  // Find status distribution pie chart from visualizations
  const statusDistributionViz = visualizations.find((v) => v.id === "status_distribution");
  const statusDistributionData = statusDistributionViz?.data || [];

  // Build landscape overview
  const landscapeOverview = {
    title: "Clinical Landscape",
    description: `Analysis of ${totalTrials} clinical trials across multiple phases and sponsors.`,
  };

  // Build sponsor profile from trials data
  const sponsorProfile = trials.top_sponsors
    ? {
        title: "Sponsor Profile",
        data: trials.top_sponsors.map((s) => ({
          sponsor: s.name,
          trial_count: s.count,
          focus: s.focus || "N/A",
        })),
      }
    : null;

  // Build key trials table with pagination
  const allTrials = trials.trials || [];
  const totalPages = Math.ceil(allTrials.length / TRIALS_PER_PAGE);
  const startIdx = trialsPage * TRIALS_PER_PAGE;
  const endIdx = startIdx + TRIALS_PER_PAGE;
  const paginatedTrials = allTrials.slice(startIdx, endIdx);

  return (
    <AgentDisplayShell
      icon={Activity}
      title="Clinical Trials"
      subtitle="MoA mapping & pipeline analysis"
      tag={totalTrials ? `${totalTrials} trials` : null}
      color="emerald"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {bannerSummary && bannerSummary.researcherQuestion && (
        <SummaryBanner summary={bannerSummary} color="emerald" />
      )}

      {/* ── 2. CONTENT — Landscape Overview ── */}
      {landscapeOverview && (
        <div>
          <SectionHeader title={landscapeOverview.title || "Clinical Landscape"} color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <p className="text-[15px] text-foreground leading-relaxed">
              {landscapeOverview.description}
            </p>
          </div>
        </div>
      )}

      {/* ── 3. METRICS — Key Metrics ── */}
      <div>
        <SectionHeader title="Key Metrics" color="emerald" />
        <div className="grid grid-cols-3 gap-3">
          <MetricCard
            label="Total Trials"
            value={totalTrials}
            color="emerald"
            icon={Activity}
            delay={0}
          />
          <MetricCard
            label="Median Enrollment"
            value={medianEnrollment}
            color="teal"
            icon={Users}
            delay={1}
          />
          <MetricCard
            label="Maturity Score"
            value={maturityScore}
            unit="%"
            color="sky"
            icon={TrendingUp}
            delay={2}
          />
        </div>
      </div>

      {/* ── 4. CHART — Phase Distribution Bar Chart ── */}
      {phaseDistributionData.length > 0 && (
        <div>
          <SectionHeader title="Trial Phase Distribution" color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <ResponsiveContainer width="100%" height={300}>
              <RechartsBarChart data={phaseDistributionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="phase"
                  tick={{ fill: "#ffffff", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.2)"
                />
                <YAxis tick={{ fill: "#ffffff", fontSize: 13 }} stroke="rgba(255,255,255,0.2)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "transparent",
                    border: "none",
                    color: "#ffffff",
                  }}
                  labelStyle={{ color: "#ffffff" }}
                  itemStyle={{ color: "#ffffff" }}
                  cursor={false}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {phaseDistributionData.map((entry, index) => {
                    const colors = [
                      "#0ea5e9",
                      "#10b981",
                      "#f59e0b",
                      "#8b5cf6",
                      "#ec4899",
                      "#14b8a6",
                    ];
                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                  })}
                </Bar>
              </RechartsBarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── 5. CHART — Trial Status Breakdown Pie Chart ── */}
      {statusDistributionData.length > 0 && (
        <div>
          <SectionHeader title="Trial Status Breakdown" color="teal" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
              {/* Pie Chart — left side */}
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={statusDistributionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={110}
                      paddingAngle={3}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="label"
                      labelLine={false}
                      label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
                        if (percent < 0.04) return null;
                        const RADIAN = Math.PI / 180;
                        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                        const x = cx + radius * Math.cos(-midAngle * RADIAN);
                        const y = cy + radius * Math.sin(-midAngle * RADIAN);
                        return (
                          <text
                            x={x}
                            y={y}
                            fill="white"
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize={15}
                            fontWeight={700}
                          >
                            {`${(percent * 100).toFixed(0)}%`}
                          </text>
                        );
                      }}
                      animationDuration={800}
                      animationEasing="ease-out"
                    >
                      {statusDistributionData.map((entry, index) => {
                        const colors = [
                          "#0ea5e9",
                          "#10b981",
                          "#f59e0b",
                          "#8b5cf6",
                          "#ec4899",
                          "#14b8a6",
                        ];
                        return (
                          <Cell
                            key={`cell-${index}`}
                            fill={colors[index % colors.length]}
                            stroke="var(--background)"
                            strokeWidth={3}
                          />
                        );
                      })}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(10, 15, 26, 0.95)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                        color: "#ffffff",
                      }}
                      labelStyle={{ color: "#ffffff" }}
                      itemStyle={{ color: "#ffffff" }}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend — right side */}
              <div className="space-y-2.5">
                {statusDistributionData.map((item, idx) => {
                  const colors = ["#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"];
                  const totalValue = statusDistributionData.reduce(
                    (sum, d) => sum + (d.value || 0),
                    0,
                  );
                  const percentage =
                    totalValue > 0 ? ((item.value / totalValue) * 100).toFixed(1) : 0;
                  const statusName = item.label || item.name || item.status || "Unknown";

                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: colors[idx % colors.length] }}
                        />
                        <span className="text-[15px] text-foreground">{statusName}</span>
                      </div>
                      <span
                        className="text-[15px] font-semibold"
                        style={{ color: colors[idx % colors.length] }}
                      >
                        {percentage}% ({item.value})
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── 6. TABLE — Sponsor Profile ── */}
      {sponsorProfile && sponsorProfile.data && (
        <div>
          <SectionHeader title={sponsorProfile.title || "Sponsor Profile"} color="teal" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <DataTable
              headers={["Sponsor", "Trials", "Focus"]}
              rows={sponsorProfile.data.map((item, idx) => [
                item.sponsor,
                <span
                  key="count"
                  className={
                    idx === 0
                      ? "text-sky-400 font-medium"
                      : idx === 1
                        ? "text-emerald-400 font-medium"
                        : "text-amber-400 font-medium"
                  }
                >
                  ~{item.trial_count}
                </span>,
                item.focus,
              ])}
              color="teal"
            />
          </div>
        </div>
      )}

      {/* ── 7. TABLE — Key Trials with Pagination ── */}
      {paginatedTrials.length > 0 && (
        <div>
          <SectionHeader title="Key Trials" color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-4">
            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const csv = [
                    ["Trial ID", "Phase", "Status", "Sponsor"],
                    ...paginatedTrials.map((t) => [
                      t.nct_id || t.trial_id || "",
                      t.phase || "",
                      t.status || "",
                      t.sponsor || "",
                    ]),
                  ]
                    .map((row) => row.map((cell) => `"${cell}"`).join(","))
                    .join("\n");

                  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                  const link = document.createElement("a");
                  const url = URL.createObjectURL(blob);
                  link.setAttribute("href", url);
                  link.setAttribute("download", "clinical_trials.csv");
                  link.style.visibility = "hidden";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 hover:border-emerald-400/50 hover:bg-emerald-500/15 transition-all text-emerald-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download CSV
              </button>
              <button
                onClick={() => setExpandView(!expandView)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-500/10 border border-teal-500/30 hover:border-teal-400/50 hover:bg-teal-500/15 transition-all text-teal-400 font-medium text-[14px]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Expand View
              </button>
            </div>

            <DataTable
              headers={["Trial ID", "Phase", "Status", "Sponsor"]}
              rows={paginatedTrials.map((trial) => [
                trial.nct_id || trial.trial_id || "N/A",
                trial.phase || "N/A",
                trial.status || "N/A",
                trial.sponsor || "N/A",
              ])}
              color="emerald"
            />

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
                <span className="text-[14px] text-muted-foreground">
                  Showing {startIdx + 1}–{Math.min(endIdx, allTrials.length)} of {allTrials.length}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTrialsPage(Math.max(0, trialsPage - 1))}
                    disabled={trialsPage === 0}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    ← Previous
                  </button>
                  <span className="text-[14px] font-medium text-foreground px-3 py-1.5 rounded-lg bg-white/[0.05]">
                    {trialsPage + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setTrialsPage(Math.min(totalPages - 1, trialsPage + 1))}
                    disabled={trialsPage === totalPages - 1}
                    className="px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[14px] text-foreground"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Expanded View Modal */}
      <AnimatePresence>
        {expandView && (
          <motion.div
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setExpandView(false);
              }
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-800/95 border border-slate-700/50 rounded-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
            >
              {/* Modal Header */}
              <div className="bg-slate-700/40 border-b border-slate-600/50 p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/10 rounded-lg">
                      <svg
                        className="w-6 h-6 text-emerald-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h2a2 2 0 002-2z"
                        />
                      </svg>
                    </div>
                    Clinical Trials Details
                  </h3>
                </div>
                <div className="flex items-center gap-3">
                  <motion.button
                    onClick={() => {
                      const csv = [
                        ["Trial ID", "Phase", "Status", "Sponsor"],
                        ...allTrials.map((t) => [
                          t.nct_id || t.trial_id || "",
                          t.phase || "",
                          t.status || "",
                          t.sponsor || "",
                        ]),
                      ]
                        .map((row) => row.map((cell) => `"${cell}"`).join(","))
                        .join("\n");

                      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                      const link = document.createElement("a");
                      const url = URL.createObjectURL(blob);
                      link.setAttribute("href", url);
                      link.setAttribute("download", "clinical_trials_full.csv");
                      link.style.visibility = "hidden";
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 px-4 py-2 bg-teal-500/20 border border-teal-400/30 hover:border-teal-300/50 hover:bg-teal-500/30 text-teal-300 rounded-lg transition-colors font-medium"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Download
                  </motion.button>
                  <motion.button
                    onClick={() => setExpandView(false)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 hover:bg-slate-600/50 text-red-400 hover:text-red-300 rounded-lg transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </motion.button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-8 max-h-[calc(90vh-140px)]">
                <div className="bg-slate-800/60 border border-slate-700/30 rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-700/50 border-b border-slate-600/30">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Trial ID
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Phase
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Status
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-slate-200">
                          Sponsor
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {allTrials.map((trial, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors"
                        >
                          <td className="px-6 py-4 text-sm text-slate-100 font-medium">
                            {trial.nct_id || trial.trial_id || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-200">
                            {trial.phase || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-200">
                            {trial.status || "N/A"}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-200">
                            {trial.sponsor || "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="p-6 border-t border-slate-600/50 bg-slate-700/30 flex items-center justify-center">
                <p className="text-sm text-slate-300">
                  Showing all{" "}
                  <span className="font-semibold text-slate-100">{allTrials.length}</span> rows
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AgentDisplayShell>
  );
}

// ============================================================================
// INTERNAL KNOWLEDGE AGENT DISPLAY — Company Intelligence
// Layout: Summary → Overview → Metrics → Key Findings → Strategy → Recommendations → Research → Refs → Docs
// ============================================================================

export function InternalKnowledgeDisplay({ data, onPromptClick }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Internal Knowledge" icon={BookOpen} color="cyan" />;
  }

  const actualData = data.data || data;

  const pastResearch = actualData.past_research || data.past_research;
  const companyMemory = actualData.company_memory || data.company_memory;
  const documents = actualData.documents || data.documents;
  const bannerSummary = actualData.summary || data.summary;

  const overview = actualData.overview || data.overview;
  const keyFindings = actualData.key_findings || data.key_findings || [];
  const recommendations = actualData.recommendations || data.recommendations || [];
  const strategicImplications = actualData.strategic_implications || data.strategic_implications;
  const internalRefs = actualData.internal_references || data.internal_references || [];
  const confidence = actualData.confidence || data.confidence;
  const source = actualData.source || data.source;
  const filename = actualData.filename || data.filename;

  const docCount = documents?.length || 0;
  const studyCount = pastResearch?.studies?.length || 0;
  const findingsCount = keyFindings.length;

  return (
    <AgentDisplayShell
      icon={BookOpen}
      title="Internal Knowledge"
      subtitle={
        source === "uploaded_document" && filename
          ? `Analyzing: ${filename}`
          : "Company data & previous research"
      }
      tag={
        findingsCount
          ? `${findingsCount} findings`
          : docCount
            ? `${docCount} docs`
            : studyCount
              ? `${studyCount} studies`
              : null
      }
      color="cyan"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {bannerSummary && bannerSummary.researcherQuestion && (
        <SummaryBanner summary={bannerSummary} color="cyan" />
      )}

      {/* ── 2. CONTENT — Overview ── */}
      {overview && (
        <div>
          <SectionHeader title="Overview" color="cyan" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <p className="text-[15px] text-foreground leading-relaxed">{overview}</p>
          </div>
        </div>
      )}

      {/* ── 3. METRICS — Company Memory ── */}
      {companyMemory && (
        <div>
          <SectionHeader title={companyMemory.title || "Company Knowledge"} color="cyan" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {companyMemory.items?.map((item, idx) => (
              <MetricCard
                key={idx}
                label={item.label}
                value={item.value}
                color={idx === 0 ? "cyan" : idx === 1 ? "teal" : idx === 2 ? "sky" : "violet"}
                icon={idx === 0 ? BookOpen : idx === 1 ? FileText : Microscope}
                delay={idx}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── 4. CONTENT — Key Findings ── */}
      {keyFindings.length > 0 && (
        <div>
          <SectionHeader
            title="Key Findings"
            badge={`${keyFindings.length} findings`}
            color="cyan"
          />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-2.5">
            {keyFindings.map((finding, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.08 }}
                className="flex items-start gap-3 p-3 bg-cyan-500/[0.04] border border-cyan-500/15 rounded-lg"
              >
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 font-semibold text-xs mt-0.5">
                  {idx + 1}
                </div>
                <p className="text-[15px] text-foreground flex-1">{finding}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 5. CONTENT — Strategic Implications ── */}
      {strategicImplications && (
        <div>
          <SectionHeader title="Strategic Implications" color="teal" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm">
            <p className="text-[15px] text-foreground leading-relaxed">{strategicImplications}</p>
          </div>
        </div>
      )}

      {/* ── 6. CONTENT — Recommended Actions ── */}
      {recommendations.length > 0 && (
        <div>
          <SectionHeader title="Recommended Actions" color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-2.5">
            {recommendations.map((rec, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-start gap-3 p-3 bg-emerald-500/[0.04] border border-emerald-500/15 rounded-lg"
              >
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-semibold text-xs mt-0.5">
                  {idx + 1}
                </div>
                <p className="text-[15px] text-foreground flex-1">{rec}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 7. DETAILS — Past Research ── */}
      {pastResearch && pastResearch.studies && (
        <div>
          <SectionHeader
            title={pastResearch.title || "Past Research"}
            badge={`${pastResearch.studies.length} studies`}
            color="cyan"
          />
          <div className="space-y-3">
            {pastResearch.studies.map((study, idx) => (
              <div
                key={idx}
                className="bg-card/60 border border-white/[0.06] rounded-xl p-5 backdrop-blur-sm"
              >
                <h4 className="text-[15px] font-semibold text-foreground mb-2 flex items-center gap-2">
                  <Microscope size={16} className="text-cyan-400" />
                  {study.title}
                </h4>
                {(study.summary || study.findings) && (
                  <p className="text-[15px] text-muted-foreground leading-relaxed">
                    {study.summary || study.findings}
                  </p>
                )}
                {study.key_findings && study.key_findings.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    {study.key_findings.map((f, fi) => (
                      <div key={fi} className="flex items-start gap-2 text-[15px] text-foreground">
                        <span className="text-cyan-400 mt-1">•</span>
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 8. CONTENT — Internal References ── */}
      {internalRefs.length > 0 && (
        <div>
          <SectionHeader
            title="Internal References"
            badge={`${internalRefs.length} sources`}
            color="cyan"
          />
          <div className="space-y-2">
            {internalRefs.map((ref, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-3 p-3.5 rounded-xl bg-cyan-500/[0.04] border border-cyan-500/15"
              >
                <FileText className="text-cyan-400 flex-shrink-0" size={16} />
                <p className="text-[15px] text-foreground">
                  {typeof ref === "string" ? ref : ref.title || ref.name || JSON.stringify(ref)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 9. CONTENT — Documents ── */}
      {documents && documents.length > 0 && (
        <div>
          <SectionHeader
            title="Related Documents"
            badge={`${documents.length} found`}
            color="cyan"
          />
          <div className="space-y-2">
            {documents.slice(0, 5).map((doc, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-3 p-3.5 rounded-xl bg-cyan-500/[0.04] border border-cyan-500/15"
              >
                <FileText className="text-cyan-400 flex-shrink-0" size={16} />
                <div className="flex-1 min-w-0">
                  <p className="text-[15px] font-medium text-foreground truncate">{doc.title}</p>
                  <p className="text-xs text-muted-foreground">{doc.date || doc.type}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 10. Confidence Level ── */}
      {confidence && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-card/60 border border-white/[0.06] backdrop-blur-sm">
          <span className="text-[15px] text-muted-foreground">Analysis Confidence</span>
          <span
            className={`text-xs font-semibold px-3 py-1 rounded-full ${
              confidence === "high" || confidence === "HIGH"
                ? "bg-emerald-500/20 text-emerald-400"
                : confidence === "low" || confidence === "LOW"
                  ? "bg-orange-500/20 text-orange-400"
                  : "bg-yellow-500/20 text-yellow-400"
            }`}
          >
            {typeof confidence === "string" ? confidence.toUpperCase() : confidence}
          </span>
        </div>
      )}
    </AgentDisplayShell>
  );
}

// ============================================================================
// WEB INTELLIGENCE AGENT DISPLAY — Real-time Signals
// Layout: Summary → Sentiment Metrics → News Articles → Forum Discussions → Recommendations → Confidence
// ============================================================================

export function WebIntelDisplay({ data, onPromptClick }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Web Intelligence" icon={Globe} color="indigo" />;
  }

  const actualData = data.data || data;

  const newsArticles =
    actualData.news_articles || actualData.news || data.news_articles || data.news || [];
  const forumQuotes =
    actualData.forum_quotes || actualData.forums || data.forum_quotes || data.forums || [];
  const recommendedActions =
    actualData.recommended_actions ||
    actualData.recommendations ||
    data.recommended_actions ||
    data.recommendations ||
    [];
  const confidence = actualData.confidence || data.confidence;
  const sentimentSummary = actualData.sentiment_summary || data.sentiment_summary;
  const bannerSummary = actualData.summary || data.summary;

  const hasContent =
    newsArticles.length > 0 ||
    forumQuotes.length > 0 ||
    recommendedActions.length > 0 ||
    sentimentSummary;
  const sourceCount = newsArticles.length + forumQuotes.length;

  return (
    <AgentDisplayShell
      icon={Globe}
      title="Web Intelligence"
      subtitle="Real-time web signals & market sentiment"
      tag={sourceCount ? `${sourceCount} sources` : null}
      color="indigo"
    >
      {/* ── 1. SUMMARY BANNER ── */}
      {bannerSummary && bannerSummary.researcherQuestion && (
        <SummaryBanner summary={bannerSummary} color="indigo" />
      )}

      {/* ── 2. METRICS — Sentiment Analysis ── */}
      {sentimentSummary && (
        <div>
          <SectionHeader title="Sentiment Analysis" color="indigo" />
          <div className="grid grid-cols-3 gap-3">
            <MetricCard
              label="Positive"
              value={sentimentSummary.positive || 0}
              unit="%"
              color="emerald"
              icon={TrendingUp}
              delay={0}
            />
            <MetricCard
              label="Neutral"
              value={sentimentSummary.neutral || 0}
              unit="%"
              color="teal"
              icon={Activity}
              delay={1}
            />
            <MetricCard
              label="Negative"
              value={sentimentSummary.negative || 0}
              unit="%"
              color="amber"
              icon={AlertTriangle}
              delay={2}
            />
          </div>
        </div>
      )}

      {/* ── 3. CONTENT — News Articles ── */}
      {newsArticles.length > 0 && (
        <div>
          <SectionHeader
            title="Recent News"
            badge={`${newsArticles.length} articles`}
            color="indigo"
          />
          <div className="space-y-2">
            {newsArticles.map((article, idx) => (
              <motion.a
                key={idx}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group block p-4 rounded-xl bg-indigo-500/[0.04] border border-indigo-500/15 hover:border-indigo-400/30 transition-all duration-200"
              >
                <p className="text-[15px] font-medium text-foreground line-clamp-2 group-hover:text-indigo-400 transition-colors">
                  {article.title}
                </p>
                {article.snippet && (
                  <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2">
                    {article.snippet}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-2.5 text-[13px] text-muted-foreground">
                  {article.source && (
                    <span className="text-indigo-400 font-medium">{article.source}</span>
                  )}
                  {article.publishedAt && (
                    <>
                      <span>•</span>
                      <span>{new Date(article.publishedAt).toLocaleDateString()}</span>
                    </>
                  )}
                  {article.sentiment && <SentimentBadge sentiment={article.sentiment} />}
                  <ExternalLink size={13} className="ml-auto opacity-50 group-hover:opacity-100" />
                </div>
              </motion.a>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. CONTENT — Forum Discussions ── */}
      {forumQuotes.length > 0 && (
        <div>
          <SectionHeader
            title="Community Discussions"
            badge={`${forumQuotes.length} posts`}
            color="amber"
          />
          <div className="space-y-2">
            {forumQuotes.map((forum, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="p-4 rounded-xl bg-amber-500/[0.04] border border-amber-500/15"
              >
                <p className="text-[15px] text-muted-foreground italic leading-relaxed">
                  "{forum.quote}"
                </p>
                <div className="flex items-center gap-2 mt-2.5">
                  {forum.site && (
                    <span className="text-xs font-medium text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">
                      {forum.site}
                    </span>
                  )}
                  {forum.sentiment && <SentimentBadge sentiment={forum.sentiment} />}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 5. CONTENT — Recommended Actions ── */}
      {recommendedActions.length > 0 && (
        <div>
          <SectionHeader title="Recommended Actions" color="emerald" />
          <div className="bg-card/60 border border-white/[0.06] rounded-xl p-6 backdrop-blur-sm space-y-2.5">
            {recommendedActions.map((action, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-start gap-3 p-3 bg-emerald-500/[0.04] border border-emerald-500/15 rounded-lg"
              >
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-semibold text-xs mt-0.5">
                  {idx + 1}
                </div>
                <p className="text-[15px] text-foreground flex-1">
                  {typeof action === "string"
                    ? action
                    : action.action || action.description || JSON.stringify(action)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── 6. Confidence Level ── */}
      {confidence && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-card/60 border border-white/[0.06] backdrop-blur-sm">
          <span className="text-[15px] text-muted-foreground">Analysis Confidence</span>
          <ConfidenceBadge level={confidence} />
        </div>
      )}

      {/* Fallback if no content */}
      {!hasContent && !bannerSummary && (
        <div className="p-5 rounded-xl bg-indigo-500/[0.04] border border-indigo-500/15 text-center">
          <Globe className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
          <p className="text-[15px] text-muted-foreground">
            Web intelligence analysis complete. No specific articles or discussions found for this
            query.
          </p>
        </div>
      )}
    </AgentDisplayShell>
  );
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

function RiskBadge({ level }) {
  const styles = {
    High: "bg-red-500/20 text-red-400",
    Medium: "bg-yellow-500/20 text-yellow-400",
    Low: "bg-emerald-500/20 text-emerald-400",
  };

  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${styles[level] || styles.Medium}`}>
      {level}
    </span>
  );
}

function SentimentBadge({ sentiment }) {
  const styles = {
    POS: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Positive" },
    NEG: { bg: "bg-red-500/10", text: "text-red-400", label: "Negative" },
    NEU: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Neutral" },
  };

  const style = styles[sentiment] || styles.NEU;

  return (
    <span className={`text-xs font-medium ${style.bg} ${style.text} px-2 py-0.5 rounded`}>
      {style.label}
    </span>
  );
}

function ConfidenceBadge({ level }) {
  const styles = {
    HIGH: "bg-emerald-500/20 text-emerald-400",
    MEDIUM: "bg-yellow-500/20 text-yellow-400",
    LOW: "bg-orange-500/20 text-orange-400",
  };

  return (
    <span
      className={`text-xs font-semibold px-3 py-1 rounded-full ${styles[level] || styles.MEDIUM}`}
    >
      {level}
    </span>
  );
}

function FallbackDisplay({ agentName, icon: Icon = Shield, color = "sky" }) {
  const colorStyles = {
    sky: "text-sky-400 bg-sky-500/10 border-sky-500/15",
    teal: "text-teal-400 bg-teal-500/10 border-teal-500/15",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/15",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/15",
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/15",
    indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/15",
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-12 px-6"
    >
      <div
        className={`w-16 h-16 rounded-2xl ${colorStyles[color] || colorStyles.sky} border flex items-center justify-center mb-4`}
      >
        <Icon size={28} />
      </div>
      <h3 className="text-foreground font-semibold text-lg mb-2 font-[family-name:var(--font-heading)]">
        No Data Available
      </h3>
      <p className="text-muted-foreground text-[15px] text-center max-w-md">
        The {agentName} agent hasn't returned any data yet.
      </p>
    </motion.div>
  );
}

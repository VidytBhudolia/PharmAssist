import { motion } from "framer-motion";
import { Shield, Sparkles } from "lucide-react";

/**
 * Agent Summary Banner Component
 * Displays a 2-3 line executive summary at the top of each agent output panel
 */
export function AgentSummaryBanner({ icon, title, lines, colorClass = "blue", question }) {
  const colorStyles = {
    blue: {
      gradient: "from-blue-500/10 via-blue-500/5 to-transparent",
      border: "border-blue-400/25",
      iconBg: "bg-blue-500/10 border border-blue-400/20",
      iconColor: "text-blue-400",
      titleColor: "text-blue-300",
      glowColor: "rgba(59, 130, 246, 0.15)",
      questionBg: "bg-blue-500/8",
      accentLine: "from-blue-400/50 via-blue-500/25 to-transparent",
    },
    teal: {
      gradient: "from-teal-500/10 via-teal-500/5 to-transparent",
      border: "border-teal-400/25",
      iconBg: "bg-teal-500/10 border border-teal-400/20",
      iconColor: "text-teal-400",
      titleColor: "text-teal-300",
      glowColor: "rgba(20, 184, 166, 0.15)",
      questionBg: "bg-teal-500/8",
      accentLine: "from-teal-400/50 via-teal-500/25 to-transparent",
    },
    amber: {
      gradient: "from-amber-500/10 via-amber-500/5 to-transparent",
      border: "border-amber-400/25",
      iconBg: "bg-amber-500/10 border border-amber-400/20",
      iconColor: "text-amber-400",
      titleColor: "text-amber-300",
      glowColor: "rgba(245, 158, 11, 0.15)",
      questionBg: "bg-amber-500/8",
      accentLine: "from-amber-400/50 via-amber-500/25 to-transparent",
    },
    emerald: {
      gradient: "from-emerald-500/10 via-emerald-500/5 to-transparent",
      border: "border-emerald-400/25",
      iconBg: "bg-emerald-500/10 border border-emerald-400/20",
      iconColor: "text-emerald-400",
      titleColor: "text-emerald-300",
      glowColor: "rgba(16, 185, 129, 0.15)",
      questionBg: "bg-emerald-500/8",
      accentLine: "from-emerald-400/50 via-emerald-500/25 to-transparent",
    },
    pink: {
      gradient: "from-pink-500/10 via-pink-500/5 to-transparent",
      border: "border-pink-400/25",
      iconBg: "bg-pink-500/10 border border-pink-400/20",
      iconColor: "text-pink-400",
      titleColor: "text-pink-300",
      glowColor: "rgba(236, 72, 153, 0.15)",
      questionBg: "bg-pink-500/8",
      accentLine: "from-pink-400/50 via-pink-500/25 to-transparent",
    },
    violet: {
      gradient: "from-violet-500/10 via-violet-500/5 to-transparent",
      border: "border-violet-400/25",
      iconBg: "bg-violet-500/10 border border-violet-400/20",
      iconColor: "text-violet-400",
      titleColor: "text-violet-300",
      glowColor: "rgba(139, 92, 246, 0.15)",
      questionBg: "bg-violet-500/8",
      accentLine: "from-violet-400/50 via-violet-500/25 to-transparent",
    },
    cyan: {
      gradient: "from-cyan-500/10 via-cyan-500/5 to-transparent",
      border: "border-cyan-400/25",
      iconBg: "bg-cyan-500/10 border border-cyan-400/20",
      iconColor: "text-cyan-400",
      titleColor: "text-cyan-300",
      glowColor: "rgba(6, 182, 212, 0.15)",
      questionBg: "bg-cyan-500/8",
      accentLine: "from-cyan-400/50 via-cyan-500/25 to-transparent",
    },
  };

  const styles = colorStyles[colorClass] || colorStyles.blue;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={`relative mb-6 rounded-xl overflow-hidden border ${styles.border} bg-gradient-to-br ${styles.gradient} backdrop-blur-sm`}
      style={{
        boxShadow: `0 4px 24px -4px ${styles.glowColor}, 0 0 0 1px ${styles.glowColor}`,
      }}
    >
      {/* Animated glow effect on hover */}
      <motion.div
        className="absolute inset-0 opacity-0 transition-opacity duration-500"
        style={{
          background: `radial-gradient(ellipse at 50% 0%, ${styles.glowColor} 0%, transparent 70%)`,
        }}
        whileHover={{ opacity: 1 }}
      />

      {/* Top accent line - elegant animated gradient */}
      <motion.div
        className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r ${styles.accentLine}`}
        initial={{ scaleX: 0, originX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      />

      <div className="p-4 pr-8 relative">
        {/* Header with icon and title */}
        <div className="flex items-center gap-3 mb-2">
          <motion.div
            className={`p-2 rounded-lg ${styles.iconBg}`}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <span className="text-lg">{icon}</span>
          </motion.div>
          <div className="flex-1">
            <motion.h4
              className={`text-sm font-semibold tracking-wide ${styles.titleColor}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.15 }}
            >
              {title}
            </motion.h4>
            {question && (
              <motion.p
                className={`text-xs ${styles.titleColor} opacity-60 mt-0.5 italic`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.6 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                {question}
              </motion.p>
            )}
          </div>
        </div>

        {/* Summary lines */}
        <div className="space-y-1.5 pl-1 mt-3">
          {lines.map((line, idx) => {
            // Ensure line is a string - if it's an object, try to extract text or skip
            let displayText = "";
            if (typeof line === "string") {
              displayText = line;
            } else if (line && typeof line === "object") {
              // Try to extract text from common object shapes
              displayText =
                line.text ||
                line.value ||
                line.answer ||
                (line.explainers && Array.isArray(line.explainers)
                  ? line.explainers.join(". ")
                  : "") ||
                JSON.stringify(line);
            }

            // Skip empty lines
            if (!displayText) return null;

            return (
              <motion.p
                key={idx}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.25 + idx * 0.08, ease: [0.22, 1, 0.36, 1] }}
                className={`text-sm leading-relaxed ${idx === lines.length - 1 ? "text-foreground font-medium" : "text-foreground/75"}`}
              >
                {displayText}
              </motion.p>
            );
          })}
        </div>
      </div>

      {/* Bottom accent line - subtle gradient fade */}
      <motion.div
        className={`h-[1px] w-full bg-gradient-to-r ${styles.accentLine}`}
        initial={{ scaleX: 0, originX: 1 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.6, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
      />
    </motion.div>
  );
}

/**
 * Agent-specific summary generators - DYNAMIC based on actual data
 */
const AGENT_SUMMARIES = {
  iqvia: {
    icon: "🧠",
    title: "IQVIA Insights Agent — Market & Competition",
    color: "blue",
    question: "Is this worth exploring commercially?",
    getLines: (data) => {
      const lines = [];

      // Get data from either top level or nested .data
      const actualData = data?.data || data;

      // Extract market forecast data
      const marketForecast = actualData?.market_forecast;
      const competitiveShare = actualData?.competitive_share;
      const cagrAnalysis = actualData?.cagr_analysis;
      const infographics = actualData?.infographics || [];
      const marketSizeUSD = actualData?.marketSizeUSD;
      const cagrPercent = actualData?.cagrPercent;
      const marketLeader = actualData?.marketLeader;
      const totalGrowthPercent = actualData?.totalGrowthPercent;

      // Check if we have any data
      const hasAnyData =
        marketForecast ||
        competitiveShare ||
        cagrAnalysis ||
        marketSizeUSD ||
        infographics.length > 0;

      // Calculate market growth
      let marketTrend = "stable";
      let growthRate = cagrPercent || null;

      if (!growthRate && cagrAnalysis?.cagr_percent) {
        growthRate = parseFloat(cagrAnalysis.cagr_percent);
      }

      if (!growthRate && marketForecast?.data?.length >= 2) {
        const values = marketForecast.data;
        const startVal = values[0]?.value;
        const endVal = values[values.length - 1]?.value;
        if (startVal && endVal) {
          const totalGrowth = ((endVal - startVal) / startVal) * 100;
          growthRate = totalGrowth / (values.length - 1);
        }
      }

      if (growthRate) {
        marketTrend =
          growthRate > 15
            ? "rapid growth"
            : growthRate > 10
              ? "high growth"
              : growthRate > 5
                ? "moderate growth"
                : growthRate > 0
                  ? "stable"
                  : "declining";
      }

      // Parse competitive intensity
      const parseShareValue = (share) => {
        if (!share) return 0;
        if (typeof share === "number") return share;
        const cleaned = String(share).replace(/[~%]/g, "").trim();
        return parseFloat(cleaned) || 0;
      };

      let competitiveIntensity = "moderate";
      let leaderInfo = "";
      if (marketLeader) {
        const leaderShare = marketLeader.shareValue || parseShareValue(marketLeader.share);
        competitiveIntensity =
          leaderShare > 50
            ? "highly concentrated"
            : leaderShare > 30
              ? "moderately concentrated"
              : "fragmented";
        leaderInfo = ` (${marketLeader.therapy}: ${marketLeader.share})`;
      } else if (competitiveShare?.data?.length > 0) {
        const topShare = parseShareValue(competitiveShare.data[0]?.share);
        competitiveIntensity =
          topShare > 50
            ? "highly concentrated"
            : topShare > 30
              ? "moderately concentrated"
              : "fragmented";
      }

      // Build insight lines
      if (hasAnyData) {
        // Line 1: Market overview
        if (marketSizeUSD && growthRate) {
          const sizeStr =
            typeof marketSizeUSD === "number"
              ? `$${marketSizeUSD.toFixed(1)}B`
              : `$${marketSizeUSD}B`;
          lines.push(
            `${sizeStr} market with ${marketTrend} trajectory (${growthRate.toFixed(1)}% CAGR). ${competitiveIntensity} competitive landscape${leaderInfo}.`,
          );
        } else if (marketSizeUSD) {
          const sizeStr =
            typeof marketSizeUSD === "number"
              ? `$${marketSizeUSD.toFixed(1)}B`
              : `$${marketSizeUSD}B`;
          lines.push(
            `${sizeStr} market identified with ${competitiveIntensity} competitive dynamics.`,
          );
        } else if (growthRate !== null) {
          lines.push(
            `Market shows ${marketTrend} trajectory (~${growthRate.toFixed(1)}% CAGR) with ${competitiveIntensity} competitive landscape.`,
          );
        } else if (infographics.length > 0) {
          lines.push(
            `Market analysis indicates ${competitiveIntensity} competitive intensity. ${infographics.length} research reports available.`,
          );
        } else {
          lines.push(`Market data available for commercial viability assessment.`);
        }

        // Line 2: Commercial viability assessment
        const isHighGrowth = growthRate && growthRate > 5;
        const hasGoodSize =
          marketSizeUSD && (typeof marketSizeUSD === "number" ? marketSizeUSD > 5 : true);
        const isViable = isHighGrowth || hasGoodSize || infographics.length >= 2;

        if (isViable) {
          lines.push(
            `Researcher takeaway: ✓ Worth exploring commercially — ${isHighGrowth ? "strong growth potential" : "established market"}.`,
          );
        } else {
          lines.push(`Researcher takeaway: △ Requires deeper validation — limited growth signals.`);
        }
      } else {
        // Fallback when no specific market data is available
        lines.push(`Market intelligence analysis in progress for commercial assessment.`);
        lines.push(`Researcher takeaway: △ Awaiting data — potential worth exploring.`);
      }

      return lines;
    },
  },
  exim: {
    icon: "🌍",
    title: "Export–Import Trade Agent — Supply Chain Feasibility",
    color: "teal",
    question: "Can we manufacture this reliably?",
    getLines: (data) => {
      const lines = [];

      // Check if EXIMDataDisplay would actually show content
      // New format: has visualizations array
      const visualizations = data?.visualizations || [];
      if (visualizations.length > 0) {
        // This has visualizations, content will be rendered by VizList
        const tradeTable = visualizations.find(
          (v) => v.title?.includes("Trade") || v.id?.includes("trade"),
        );
        if (tradeTable?.data?.rows) {
          const topCountries = tradeTable.data.rows
            .slice(0, 3)
            .map((r) => r.partner || r.country || r.reporter);
          lines.push(`Primary sourcing from ${topCountries.join(", ")}.`);
        } else {
          lines.push(
            `Trade flow analysis completed — ${visualizations.length} data visualization(s) generated.`,
          );
        }

        lines.push(
          `Researcher takeaway: △ Supply chain complexity moderate — diversification recommended.`,
        );
        return lines;
      }

      // Legacy format: check for trade_volume, price_trend, import_dependency
      const tradeVolume = data?.trade_volume || data?.data?.trade_volume;
      const priceTrend = data?.price_trend || data?.price_trends || data?.data?.price_trends;
      const importRisks = data?.import_risks || data?.data?.import_risks;
      const importDependency = data?.import_dependency || data?.data?.import_dependency;

      // Check if we have any trade-related data
      const hasAnyData = tradeVolume || priceTrend || importDependency || importRisks;

      // Always provide analysis - either specific or fallback
      if (hasAnyData) {
        // Analyze supply chain from legacy data
        let topCountries = [];
        let totalVolume = 0;
        let riskLevel = "moderate";

        if (tradeVolume?.data?.length > 0) {
          topCountries = tradeVolume.data.slice(0, 3).map((d) => d.country);
          totalVolume = tradeVolume.data.reduce((sum, d) => sum + (d.q3_2024 || d.value || 0), 0);
        }

        // Determine risk level
        if (
          importDependency?.data?.some((d) => d.risk_level === "High") ||
          importRisks?.details?.toLowerCase().includes("high")
        ) {
          riskLevel = "high";
        } else if (topCountries.some((c) => ["China", "India"].includes(c))) {
          riskLevel = "elevated";
        }

        // Build insight lines
        if (topCountries.length > 0) {
          lines.push(
            `Primary sourcing from ${topCountries.join(", ")}${totalVolume ? ` with ${totalVolume.toLocaleString()} units traded` : ""}.`,
          );
        } else {
          lines.push(`Supply chain analysis completed — trade data evaluated.`);
        }

        const riskEmoji = riskLevel === "high" ? "⚠" : riskLevel === "elevated" ? "△" : "✓";
        lines.push(
          `Researcher takeaway: ${riskEmoji} Supply chain risk is ${riskLevel} — ${riskLevel === "high" ? "consider alternative sourcing or local manufacturing." : "manageable with proper supplier diversification."}`,
        );
      } else {
        // Fallback when no specific trade data is available - show for running agents
        lines.push(`Export-import trade analysis in progress for supply chain assessment.`);
        lines.push(
          `Researcher takeaway: △ Supply chain evaluation pending — diversification strategy recommended.`,
        );
      }

      return lines;
    },
  },
  patent: {
    icon: "🧬",
    title: "Patent Landscape Agent — Intellectual Property Risk",
    color: "amber",
    question: "Will intellectual property block us?",
    getLines: (data) => {
      const lines = [];

      // Extract patent data
      const ftoStatus = data?.fto_status || data?.data?.fto_status;
      const blockingPatents = data?.blocking_patents || data?.data?.blocking_patents || [];
      const freedomDate = data?.earliest_freedom_date || data?.data?.earliest_freedom_date;
      const confidence = data?.confidence || data?.data?.confidence;
      const visualizations = data?.visualizations || [];

      // Check for FTO summary visualization
      const ftoSummary = visualizations.find(
        (v) => v.id === "fto_summary" || v.title?.includes("FTO"),
      );
      const patentTable = visualizations.find(
        (v) => v.id === "blocking_patents" || v.title?.includes("Patent"),
      );

      let status = ftoStatus || ftoSummary?.data?.value || "MODERATE_RISK";
      let patentCount = blockingPatents.length || patentTable?.data?.rows?.length || 0;

      // Normalize status
      const statusLower = String(status).toLowerCase();
      let riskLevel = "moderate";
      let riskEmoji = "△";

      if (statusLower.includes("clear") || statusLower.includes("low")) {
        riskLevel = "low";
        riskEmoji = "✓";
      } else if (statusLower.includes("high")) {
        riskLevel = "high";
        riskEmoji = "⚠";
      }

      // Build insight lines
      if (freedomDate) {
        lines.push(
          `FTO Status: ${status.replace(/_/g, " ")}${patentCount > 0 ? ` — ${patentCount} potentially blocking patent(s) identified` : ""}.`,
        );
        lines.push(
          `Researcher takeaway: ${riskEmoji} IP risk is ${riskLevel}. Earliest freedom date: ${freedomDate}.`,
        );
      } else if (patentCount > 0) {
        lines.push(`${patentCount} relevant patent(s) identified in the landscape analysis.`);
        lines.push(
          `Researcher takeaway: ${riskEmoji} IP risk is ${riskLevel} — ${riskLevel === "low" ? "freedom to operate appears clear." : "requires detailed FTO opinion before proceeding."}`,
        );
      } else {
        lines.push(`Patent landscape analysis indicates ${riskLevel} intellectual property risk.`);
        lines.push(
          `Researcher takeaway: ${riskEmoji} Freedom to operate appears ${riskLevel === "low" ? "clear" : "manageable"} for further development.`,
        );
      }

      return lines;
    },
  },
  clinical: {
    icon: "🧪",
    title: "Clinical Trials Agent — Development Landscape",
    color: "emerald",
    question: "Is the development space already crowded?",
    getLines: (data) => {
      const lines = [];

      // Extract clinical data from actual structure
      const landscapeOverview = data?.landscape_overview;
      const phaseDistribution = data?.phase_distribution;
      const sponsorProfile = data?.sponsor_profile;
      const keyTrials = data?.key_trials;
      const audFocus = data?.aud_focus;
      const visualizations = data?.visualizations || [];

      // Check if we have any clinical-related data
      const hasAnyData =
        landscapeOverview ||
        phaseDistribution ||
        sponsorProfile ||
        keyTrials ||
        audFocus ||
        visualizations.length > 0;

      // Extract trial counts from phase distribution
      let totalTrials = 0;
      let phase3Count = 0;
      let phase2Count = 0;

      if (phaseDistribution?.data && Array.isArray(phaseDistribution.data)) {
        totalTrials = phaseDistribution.data.reduce((sum, phase) => sum + (phase.count || 0), 0);
        phase3Count =
          phaseDistribution.data.find((p) => p.phase?.includes("III") || p.phase?.includes("3"))
            ?.count || 0;
        phase2Count =
          phaseDistribution.data.find((p) => p.phase?.includes("II") || p.phase?.includes("2"))
            ?.count || 0;
      }

      // Extract sponsor count
      let sponsorCount = 0;
      if (sponsorProfile?.data && Array.isArray(sponsorProfile.data)) {
        sponsorCount = sponsorProfile.data.length;
      }

      // Determine competitive intensity
      let intensity = "limited";
      let spaceStatus = "open";

      if (totalTrials > 50 || phase3Count > 5) {
        intensity = "high";
        spaceStatus = "crowded";
      } else if (totalTrials > 20 || phase3Count > 2) {
        intensity = "moderate";
        spaceStatus = "competitive";
      }

      // Build insight lines - always provide analysis
      if (hasAnyData) {
        if (totalTrials > 0) {
          lines.push(
            `${totalTrials} clinical trial(s) identified${phase3Count > 0 ? ` — ${phase3Count} in late-stage (Phase 3)` : phase2Count > 0 ? ` — mostly early to mid-stage` : ""}.`,
          );
        } else if (landscapeOverview || audFocus) {
          lines.push(
            `Clinical development landscape analyzed — ${audFocus ? "focused on AUD indications" : "comprehensive overview"}.`,
          );
        } else if (visualizations.length > 0) {
          lines.push(`Clinical trial database searched — limited activity found.`);
        } else {
          lines.push(`Clinical development landscape analyzed.`);
        }

        const emoji = intensity === "high" ? "⚠" : intensity === "moderate" ? "△" : "✓";
        lines.push(
          `Researcher takeaway: ${emoji} Development space is ${spaceStatus}${sponsorCount > 0 ? ` (${sponsorCount} active sponsors)` : ""} — ${intensity === "high" ? "differentiation strategy critical." : "opportunity for competitive positioning."}`,
        );
      } else {
        // Fallback when no specific clinical data is available
        lines.push(`Clinical trials landscape analysis completed for development assessment.`);
        lines.push(
          `Researcher takeaway: ✓ Development space appears open — good opportunity for entry.`,
        );
      }

      return lines;
    },
  },
  internal: {
    icon: "📄",
    title: "Internal Knowledge Agent — Strategic Alignment",
    color: "pink",
    question: "Does this fit our company strategy?",
    getLines: (data) => {
      const lines = [];

      // Extract internal knowledge data
      const strategicSynthesis = data?.strategic_synthesis || data?.data?.strategic_synthesis;
      const audFocus = data?.aud_focus || data?.data?.aud_focus;
      const insights = strategicSynthesis?.insights || audFocus?.insights || [];
      const summaryObj = data?.summary || data?.data?.summary;
      const visualizations = data?.visualizations || [];

      // Handle summary - can be string or object with {researcherQuestion, answer, explainers}
      let summaryText = null;
      if (summaryObj && typeof summaryObj === "string") {
        summaryText = summaryObj;
      } else if (summaryObj && typeof summaryObj === "object" && summaryObj.explainers) {
        // Extract text from explainers array
        summaryText = Array.isArray(summaryObj.explainers)
          ? summaryObj.explainers.join(". ")
          : null;
      }

      // Check if we have any internal knowledge data
      const hasAnyData =
        strategicSynthesis ||
        audFocus ||
        insights.length > 0 ||
        summaryText ||
        visualizations.length > 0;

      // Check for summary visualization
      const summaryViz = visualizations.find(
        (v) => v.id?.includes("summary") || v.title?.includes("Summary"),
      );

      // Determine strategic fit
      let alignment = "moderate";
      let hasCapabilities = false;
      let hasPriority = false;

      if (insights.length > 0) {
        const insightText = insights
          .map((i) => i.value || i.label || "")
          .join(" ")
          .toLowerCase();
        hasCapabilities =
          insightText.includes("capability") ||
          insightText.includes("expertise") ||
          insightText.includes("strength");
        hasPriority =
          insightText.includes("priority") ||
          insightText.includes("strategic") ||
          insightText.includes("focus");
        alignment =
          hasCapabilities && hasPriority
            ? "strong"
            : hasCapabilities || hasPriority
              ? "moderate"
              : "limited";
      }

      // Build insight lines - always provide analysis
      if (hasAnyData) {
        if (summaryText && typeof summaryText === "string") {
          lines.push(
            summaryText.length > 100 ? summaryText.substring(0, 100) + "..." : summaryText,
          );
        } else if (insights.length > 0) {
          lines.push(`${insights.length} strategic insight(s) identified from internal documents.`);
        } else if (visualizations.length > 0) {
          lines.push(
            `Internal knowledge base queried — ${visualizations.length} relevant finding(s).`,
          );
        } else {
          lines.push(`Internal documents analyzed for strategic relevance.`);
        }

        const emoji = alignment === "strong" ? "✓" : alignment === "moderate" ? "△" : "⚠";
        lines.push(
          `Researcher takeaway: ${emoji} Strategic alignment is ${alignment} — ${alignment === "strong" ? "aligns with existing capabilities and priorities." : "may require additional strategic review."}`,
        );
      } else {
        // Fallback when no specific internal data is available
        lines.push(`Internal knowledge analysis completed for strategic alignment assessment.`);
        lines.push(
          `Researcher takeaway: △ Strategic fit evaluation shows moderate alignment — review recommended.`,
        );
      }

      return lines;
    },
  },
  web: {
    icon: "🌐",
    title: "Web Intelligence Agent — Real-Time Market Signals",
    color: "cyan",
    question: "Is there real unmet need?",
    getLines: (data) => {
      const lines = [];

      // Web intelligence returns: news_articles, forum_quotes, sentiment_summary, top_signal, etc.
      const news = data?.news_articles || data?.top_headlines || data?.news || [];
      const forums = data?.forum_quotes || data?.forums || [];
      const sentiment = data?.sentiment_summary || data?.sentiment;
      const topSignal = data?.top_signal;
      const confidence = data?.confidence;
      const summaryObj = data?.summary || data?.data?.summary;

      // Handle summary - can be string or object with {researcherQuestion, answer, explainers}
      let summaryText = null;
      if (summaryObj && typeof summaryObj === "string") {
        summaryText = summaryObj;
      } else if (summaryObj && typeof summaryObj === "object" && summaryObj.explainers) {
        // Extract text from explainers array
        summaryText = Array.isArray(summaryObj.explainers)
          ? summaryObj.explainers.join(". ")
          : null;
      }

      const hasAnyData =
        news.length > 0 || forums.length > 0 || sentiment || topSignal || summaryText;

      if (hasAnyData) {
        // Add signal summary if available
        if (topSignal?.text && typeof topSignal.text === "string") {
          lines.push(
            topSignal.text.length > 120 ? topSignal.text.substring(0, 120) + "..." : topSignal.text,
          );
        } else if (summaryText) {
          lines.push(
            summaryText.length > 120 ? summaryText.substring(0, 120) + "..." : summaryText,
          );
        }

        // Add data summary line
        const parts = [];
        if (news.length > 0)
          parts.push(`${news.length} news article${news.length !== 1 ? "s" : ""}`);
        if (forums.length > 0)
          parts.push(`${forums.length} forum post${forums.length !== 1 ? "s" : ""}`);
        if (parts.length > 0) {
          lines.push(`Analyzed ${parts.join(" and ")}.`);
        }

        // Add sentiment insight if available
        if (sentiment && (sentiment.positive || sentiment.negative)) {
          const positivePct = sentiment.positive || 0;
          const negativePct = sentiment.negative || 0;
          if (positivePct > 50) {
            lines.push(`✓ Sentiment: ${positivePct}% positive — favorable market reception.`);
          } else if (negativePct > 40) {
            lines.push(`⚠ Sentiment: ${negativePct}% negative — caution advised.`);
          } else {
            lines.push(`△ Sentiment: Mixed — further monitoring recommended.`);
          }
        }
      } else {
        lines.push(`Web intelligence scan completed for real-time market signals.`);
        lines.push(`△ Limited data available — expand search parameters or retry.`);
      }

      return lines;
    },
  },
  report: {
    icon: "📊",
    title: "Report Generator — Comprehensive Analysis",
    color: "violet",
    question: "What's the bottom line?",
    getLines: (data) => {
      const lines = [];

      // Extract report data
      const sections = data?.sections || data?.data?.sections || [];
      const title = data?.title || data?.data?.title;
      const status = sections.find((s) => s.status === "Finalizing") ? "ready" : "processing";

      // Count completed sections
      const completedSections = sections.filter((s) => s.status === "Complete").length;

      if (completedSections > 0 || sections.length > 0) {
        lines.push(
          `${completedSections || sections.length} analysis section(s) synthesized from all agents.`,
        );
      } else {
        lines.push(`Comprehensive analysis compiled from all agent outputs.`);
      }

      const emoji = status === "ready" ? "✓" : "⏳";
      lines.push(
        `${emoji} Report ${status === "ready" ? "ready for download" : "being finalized"} — includes strategic recommendations.`,
      );

      return lines;
    },
  },
};

/**
 * Get summary component for a specific agent
 */
export function getAgentSummary(agentKey, data) {
  const summaryConfig = AGENT_SUMMARIES[agentKey];
  if (!summaryConfig) {
    console.log(`[getAgentSummary] No config found for agent: ${agentKey}`);
    return null;
  }

  // Basic validation - check if there's any meaningful data
  if (!data || (typeof data === "object" && Object.keys(data).length === 0)) {
    console.log(`[getAgentSummary] No data for agent: ${agentKey}`);
    return null;
  }

  // Special check for patent agent - ensure PatentDataDisplay would actually show content
  if (agentKey === "patent") {
    // Check if this has visualizations (new format) - banner ok if visualizations exist
    const visualizations = data?.visualizations || data?.data?.visualizations || [];
    if (visualizations.length > 0) {
      console.log(`[getAgentSummary] Patent agent has ${visualizations.length} visualizations`);
      // This is fine - visualizations will be rendered
    } else {
      // Legacy format - check if PatentDataDisplay will show content
      const hasLegacyContent =
        data?.landscape_overview ||
        data?.repurposing_strategy ||
        data?.filing_heatmap ||
        data?.key_patent_extract ||
        data?.ip_opportunities;
      if (!hasLegacyContent) {
        console.log(`[getAgentSummary] Patent agent has no renderable content`);
        return null;
      }
    }
  }

  try {
    const rawLines = summaryConfig.getLines(data);
    console.log(
      `[getAgentSummary] Generated ${rawLines?.length || 0} raw lines for ${agentKey}:`,
      rawLines,
    );

    // Filter and sanitize lines - ensure all are strings
    const lines = (rawLines || []).filter((line) => {
      if (typeof line === "string" && line.trim()) return true;
      // Log any non-string items for debugging
      if (line && typeof line === "object") {
        console.warn(`[getAgentSummary] Non-string line detected for ${agentKey}:`, line);
      }
      return false;
    });

    // Only render if we have valid summary lines
    if (!lines || !Array.isArray(lines) || lines.length === 0) {
      console.log(`[getAgentSummary] No valid lines generated for agent: ${agentKey}`);
      return null;
    }

    return (
      <AgentSummaryBanner
        icon={summaryConfig.icon}
        title={summaryConfig.title}
        lines={lines}
        colorClass={summaryConfig.color}
        question={summaryConfig.question}
      />
    );
  } catch (error) {
    console.warn(`[getAgentSummary] Error generating summary for ${agentKey}:`, error);
    return null;
  }
}

/**
 * IQVIA Agent Data Renderer - Comprehensive Market Intelligence Display
 */
export function IQVIADataDisplay({ data, isFirstPrompt }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="IQVIA" />;
  }

  // Extract data - could be at top level or nested in .data
  const actualData = data.data || data;

  const marketForecast = actualData.market_forecast || data.market_forecast;
  const competitiveShare = actualData.competitive_share || data.competitive_share;
  const marketOverview = actualData.market_overview;
  const cagrAnalysis = actualData.cagr_analysis;
  const marketSizeUSD = actualData.marketSizeUSD;
  const cagrPercent = actualData.cagrPercent;
  const totalGrowthPercent = actualData.totalGrowthPercent;
  const marketLeader = actualData.marketLeader;
  const topTherapies = actualData.topTherapies || [];
  const topArticles = actualData.topArticles || [];
  const infographics = actualData.infographics || [];
  const dataAvailability = actualData.dataAvailability || {};
  const existingTherapies = actualData.existing_therapies;
  const audSignal = actualData.aud_signal;
  const commercialScenario = actualData.commercial_scenario;

  // Parse share value helper
  const parseShareValue = (share) => {
    if (!share) return 0;
    if (typeof share === "number") return share;
    const cleaned = String(share).replace(/[~%]/g, "").trim();
    return parseFloat(cleaned) || 0;
  };

  // Calculate market growth if we have forecast data
  let marketGrowth = null;
  if (marketForecast?.data?.length >= 2) {
    const startVal = marketForecast.data[0]?.value || 0;
    const endVal = marketForecast.data[marketForecast.data.length - 1]?.value || 0;
    if (startVal > 0) {
      marketGrowth = (((endVal - startVal) / startVal) * 100).toFixed(1);
    }
  }

  return (
    <div className="space-y-6">
      {/* ===== KEY METRICS SECTION ===== */}
      {(marketSizeUSD || cagrPercent || marketLeader) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-blue-400 font-semibold mb-4 text-lg flex items-center gap-2">
            <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
            Market Overview
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Market Size */}
            {marketSizeUSD && (
              <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/30 rounded-xl p-4 hover:border-blue-400/50 transition-colors">
                <p className="text-xs text-blue-300/70 uppercase tracking-wide mb-1">Market Size</p>
                <p className="text-2xl font-bold text-blue-400">
                  ${typeof marketSizeUSD === "number" ? marketSizeUSD.toFixed(1) : marketSizeUSD}B
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {marketForecast?.data?.[marketForecast.data.length - 1]?.year || "Latest"}
                </p>
              </div>
            )}

            {/* CAGR */}
            {cagrPercent && (
              <div className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/30 rounded-xl p-4 hover:border-emerald-400/50 transition-colors">
                <p className="text-xs text-emerald-300/70 uppercase tracking-wide mb-1">CAGR</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {typeof cagrPercent === "number" ? cagrPercent.toFixed(1) : cagrPercent}%
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {cagrPercent > 10
                    ? "🔥 High Growth"
                    : cagrPercent > 5
                      ? "📈 Moderate"
                      : "📊 Stable"}
                </p>
              </div>
            )}

            {/* Total Growth */}
            {(totalGrowthPercent || marketGrowth) && (
              <div className="bg-gradient-to-br from-teal-500/10 to-teal-600/5 border border-teal-500/30 rounded-xl p-4 hover:border-teal-400/50 transition-colors">
                <p className="text-xs text-teal-300/70 uppercase tracking-wide mb-1">
                  Total Growth
                </p>
                <p className="text-2xl font-bold text-teal-400">
                  {totalGrowthPercent
                    ? typeof totalGrowthPercent === "number"
                      ? totalGrowthPercent.toFixed(1)
                      : totalGrowthPercent
                    : marketGrowth}
                  %
                </p>
                <p className="text-xs text-muted-foreground mt-1">Over forecast period</p>
              </div>
            )}

            {/* Market Leader */}
            {marketLeader && (
              <div className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border border-violet-500/30 rounded-xl p-4 hover:border-violet-400/50 transition-colors">
                <p className="text-xs text-violet-300/70 uppercase tracking-wide mb-1">
                  Market Leader
                </p>
                <p className="text-lg font-bold text-violet-400 truncate">{marketLeader.therapy}</p>
                <p className="text-sm text-violet-300 mt-1">{marketLeader.share}</p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* ===== MARKET FORECAST LINE CHART ===== */}
      {marketForecast?.data && marketForecast.data.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-blue-400 font-semibold mb-4 text-lg flex items-center gap-2">
            <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
            {marketForecast.title || "Market Growth Trajectory"}
          </h3>

          <div className="bg-card/50 border border-border rounded-xl p-6">
            {/* SVG Line Chart */}
            <div className="relative h-64 w-full">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 bottom-8 w-14 flex flex-col justify-between text-xs text-muted-foreground">
                {[...Array(5)].map((_, i) => {
                  const maxVal = Math.max(...marketForecast.data.map((d) => d.value || 0));
                  const val = maxVal - (maxVal / 4) * i;
                  return <span key={i}>${val.toFixed(0)}B</span>;
                })}
              </div>

              {/* Chart Area */}
              <div className="ml-16 h-full relative">
                <svg
                  className="w-full h-[calc(100%-2rem)]"
                  viewBox="0 0 400 200"
                  preserveAspectRatio="none"
                >
                  <defs>
                    <linearGradient id="iqviaGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
                    </linearGradient>
                  </defs>

                  {/* Grid lines */}
                  {[...Array(5)].map((_, i) => (
                    <line
                      key={i}
                      x1="0"
                      y1={i * 50}
                      x2="400"
                      y2={i * 50}
                      stroke="currentColor"
                      strokeOpacity="0.1"
                      strokeDasharray="4 4"
                    />
                  ))}

                  {/* Area fill */}
                  {(() => {
                    const maxVal = Math.max(...marketForecast.data.map((d) => d.value || 0));
                    const points = marketForecast.data.map((d, i) => {
                      const x = (i / (marketForecast.data.length - 1)) * 400;
                      const y = 200 - ((d.value || 0) / maxVal) * 180;
                      return `${x},${y}`;
                    });
                    const areaPath = `M 0,200 L ${points.join(" L ")} L 400,200 Z`;
                    const linePath = `M ${points.join(" L ")}`;

                    return (
                      <>
                        <path d={areaPath} fill="url(#iqviaGradient)" />
                        <path
                          d={linePath}
                          fill="none"
                          stroke="#3b82f6"
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                        {/* Data points */}
                        {marketForecast.data.map((d, i) => {
                          const x = (i / (marketForecast.data.length - 1)) * 400;
                          const y = 200 - ((d.value || 0) / maxVal) * 180;
                          return (
                            <circle
                              key={i}
                              cx={x}
                              cy={y}
                              r="6"
                              fill="#3b82f6"
                              stroke="white"
                              strokeWidth="2"
                            />
                          );
                        })}
                      </>
                    );
                  })()}
                </svg>

                {/* X-axis labels */}
                <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                  {marketForecast.data.map((d, i) => (
                    <div key={i} className="text-center">
                      <div className="font-medium text-foreground">{d.year}</div>
                      <div className="text-blue-400">${d.value}B</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {marketForecast.description && (
              <p className="text-sm text-muted-foreground mt-4 border-t border-border pt-4">
                {marketForecast.description}
              </p>
            )}
          </div>
        </motion.div>
      )}

      {/* ===== COMPETITIVE MARKET SHARE ===== */}
      {competitiveShare?.data && competitiveShare.data.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-emerald-400 font-semibold mb-4 text-lg flex items-center gap-2">
            <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
            {competitiveShare.title || "Competitive Landscape"}
          </h3>

          <div className="bg-card/50 border border-border rounded-xl p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart Visualization */}
              <div className="flex items-center justify-center">
                <div className="relative w-48 h-48">
                  <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                    {(() => {
                      let currentAngle = 0;
                      const colors = [
                        "#3b82f6",
                        "#10b981",
                        "#8b5cf6",
                        "#f59e0b",
                        "#ec4899",
                        "#6366f1",
                      ];
                      return competitiveShare.data.map((item, idx) => {
                        const share = parseShareValue(item.share);
                        const angle = (share / 100) * 360;
                        const startAngle = currentAngle;
                        currentAngle += angle;

                        // Calculate SVG arc path
                        const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
                        const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
                        const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180);
                        const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180);
                        const largeArc = angle > 180 ? 1 : 0;

                        return (
                          <path
                            key={idx}
                            d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                            fill={colors[idx % colors.length]}
                            stroke="var(--background)"
                            strokeWidth="1"
                            className="hover:opacity-80 transition-opacity cursor-pointer"
                          />
                        );
                      });
                    })()}
                    {/* Center circle for donut effect */}
                    <circle cx="50" cy="50" r="25" fill="var(--card)" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Total</p>
                      <p className="text-lg font-bold text-foreground">100%</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Legend and Details */}
              <div className="space-y-3">
                {competitiveShare.data.map((item, idx) => {
                  const colors = [
                    "bg-blue-500",
                    "bg-emerald-500",
                    "bg-violet-500",
                    "bg-amber-500",
                    "bg-pink-500",
                    "bg-indigo-500",
                  ];
                  const textColors = [
                    "text-blue-400",
                    "text-emerald-400",
                    "text-violet-400",
                    "text-amber-400",
                    "text-pink-400",
                    "text-indigo-400",
                  ];
                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-3 h-3 rounded-full ${colors[idx % colors.length]}`}
                        ></div>
                        <span className="text-sm font-medium text-foreground">{item.company}</span>
                      </div>
                      <span className={`text-sm font-bold ${textColors[idx % textColors.length]}`}>
                        {item.share}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {competitiveShare.description && (
              <p className="text-sm text-muted-foreground mt-4 border-t border-border pt-4">
                {competitiveShare.description}
              </p>
            )}
          </div>
        </motion.div>
      )}

      {/* ===== MARKET INTELLIGENCE / TOP ARTICLES ===== */}
      {(topArticles.length > 0 || infographics.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h3 className="text-cyan-400 font-semibold mb-4 text-lg flex items-center gap-2">
            <span className="w-2 h-2 bg-cyan-400 rounded-full"></span>
            Market Research & Insights
            <span className="ml-2 text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full">
              {topArticles.length || infographics.length} sources
            </span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(topArticles.length > 0 ? topArticles : infographics).slice(0, 6).map((item, idx) => (
              <motion.a
                key={idx}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + idx * 0.05 }}
                className="group block p-4 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 border border-cyan-500/20 rounded-xl hover:border-cyan-400/40 hover:shadow-lg hover:shadow-cyan-500/5 transition-all"
              >
                <div className="flex gap-3">
                  {/* Thumbnail if available */}
                  {item.imageUrl && (
                    <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-muted">
                      <img
                        src={item.imageUrl}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={(e) => (e.target.style.display = "none")}
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground line-clamp-2 group-hover:text-cyan-400 transition-colors">
                      {item.title}
                    </p>
                    {(item.snippet || item.subtitle) && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {item.snippet || item.subtitle}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <span className="text-cyan-400 font-medium">{item.source || "Statista"}</span>
                      {item.premium && (
                        <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[10px]">
                          Premium
                        </span>
                      )}
                      <span className="ml-auto group-hover:text-cyan-400 transition-colors">
                        View →
                      </span>
                    </div>
                  </div>
                </div>
              </motion.a>
            ))}
          </div>
        </motion.div>
      )}

      {/* ===== LEGACY AUD SPECIFIC DATA ===== */}
      {/* AUD Market Overview */}
      {marketOverview && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h3 className="text-teal-500 font-semibold mb-3 text-lg">{marketOverview.title}</h3>
          <div className="bg-muted rounded-lg p-6 grid grid-cols-4 gap-4 text-sm">
            {marketOverview.metrics?.map((metric, idx) => (
              <div key={idx} className="bg-card border border-primary/20 rounded-lg p-4">
                <p className="text-muted-foreground text-xs">{metric.label}</p>
                <p className="text-teal-400 font-semibold mt-1">{metric.value}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Existing Therapies Table */}
      {existingTherapies && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-violet-500 font-semibold mb-3 text-lg">{existingTherapies.title}</h3>
          <div className="bg-muted rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3">Drug</th>
                  <th className="text-center p-3">Mechanism</th>
                  <th className="text-center p-3">Efficacy</th>
                  <th className="text-left p-3">Limitations</th>
                </tr>
              </thead>
              <tbody>
                {existingTherapies.data?.map((therapy, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className="p-3">{therapy.drug}</td>
                    <td className="text-center p-3">{therapy.mechanism}</td>
                    <td
                      className={`text-center p-3 ${therapy.efficacy === "Low" ? "text-red-400" : "text-yellow-400"}`}
                    >
                      {therapy.efficacy}
                    </td>
                    <td className="p-3">{therapy.limitations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* AUD Signal */}
      {audSignal && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="text-emerald-400 font-semibold mb-3 text-lg">{audSignal.title}</h3>
          <div className="bg-muted rounded-lg p-6 text-sm space-y-3">
            <div className="bg-card border border-emerald-500/20 rounded-lg p-4">
              <p className="text-muted-foreground text-xs">Observed Effects</p>
              <p className="text-emerald-300 font-semibold mt-1">{audSignal.observed_effects}</p>
            </div>
            <ul className="list-disc list-inside text-muted-foreground">
              {audSignal.key_points?.map((point, idx) => (
                <li key={idx}>{point}</li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Commercial Scenario */}
      {commercialScenario && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <h3 className="text-amber-500 font-semibold mb-3 text-lg">{commercialScenario.title}</h3>
          <div className="bg-muted rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                {commercialScenario.data?.map((item, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className={`p-3 ${item.highlight ? "font-semibold" : ""}`}>
                      {item.metric}
                    </td>
                    <td
                      className={`p-3 text-right ${item.highlight ? "text-emerald-400 font-semibold" : ""}`}
                    >
                      {item.value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}

/**
 * EXIM Agent Data Renderer
 */
export function EXIMDataDisplay({ data, showChart }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="EXIM" />;
  }

  // Check if this is new structured data with visualizations array
  if (data.visualizations && Array.isArray(data.visualizations)) {
    // New format - visualizations will be rendered by the main visualization system
    return null;
  }

  // Legacy format support
  const tradeVolume = data.trade_volume;
  const priceTrend = data.price_trend;
  const importDependency = data.import_dependency;

  return (
    <>
      {/* Trade Volume */}
      {tradeVolume && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-teal-500 font-semibold mb-3 text-lg">{tradeVolume.title}</h3>

          <div className="bg-muted rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 text-foreground font-semibold">Source Country</th>
                  <th className="text-right p-3 text-foreground font-semibold">Q2 2024 (kg)</th>
                  <th className="text-right p-3 text-foreground font-semibold">Q3 2024 (kg)</th>
                  <th className="text-right p-3 text-foreground font-semibold">QoQ Growth</th>
                </tr>
              </thead>
              <tbody>
                {tradeVolume.data?.map((item, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className="p-3 text-zinc-200 font-medium">{item.country}</td>
                    <td className="text-right p-3 text-foreground">{item.q2_2024}</td>
                    <td className="text-right p-3 text-foreground">{item.q3_2024}</td>
                    <td className="text-right p-3">
                      <span className="text-emerald-500 font-semibold">{item.qoq_growth}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-sm text-muted-foreground">{tradeVolume.description}</p>
        </motion.div>
      )}

      {/* Price Trend Chart */}
      {showChart && priceTrend && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h3 className="text-violet-500 font-semibold mb-3 text-lg">{priceTrend.title}</h3>

          <div className="bg-muted rounded-lg p-6">
            <div className="space-y-4">
              <div className="flex items-end justify-between h-48">
                <div className="flex flex-col justify-between h-full text-xs text-muted-foreground pr-2">
                  <span>$6.0</span>
                  <span>$5.5</span>
                  <span>$5.0</span>
                  <span>$4.5</span>
                  <span>$4.0</span>
                </div>

                <div className="flex-1 relative h-full">
                  <div className="absolute inset-0 flex flex-col justify-between">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="border-t border-border" />
                    ))}
                  </div>

                  <svg
                    className="absolute inset-0 w-full h-full"
                    viewBox="0 0 300 192"
                    preserveAspectRatio="none"
                  >
                    <defs>
                      <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#a855f7" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
                      </linearGradient>
                    </defs>

                    <path
                      d="M 50 38.4 L 150 76.8 L 250 134.4 L 250 192 L 50 192 Z"
                      fill="url(#priceGradient)"
                    />
                    <path
                      d="M 50 38.4 L 150 76.8 L 250 134.4"
                      stroke="#a855f7"
                      strokeWidth="3"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />

                    {[50, 150, 250].map((x, i) => (
                      <circle
                        key={i}
                        cx={x}
                        cy={[38.4, 76.8, 134.4][i]}
                        r="5"
                        fill="#a855f7"
                        stroke="#18181b"
                        strokeWidth="2"
                      />
                    ))}
                  </svg>
                </div>
              </div>

              <div className="flex justify-around text-xs text-muted-foreground pt-2 border-t border-border">
                {priceTrend.data?.map((item, idx) => (
                  <div key={idx} className="text-center">
                    <div className="text-foreground font-medium">{item.quarter}</div>
                    <div className="text-violet-500 font-semibold">${item.price}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <p className="mt-3 text-sm text-muted-foreground">{priceTrend.description}</p>
        </motion.div>
      )}

      {/* Import Dependency */}
      {importDependency && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h3 className="text-orange-400 font-semibold mb-3 text-lg">{importDependency.title}</h3>

          <div className="bg-muted rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 text-foreground font-semibold">Region</th>
                  <th className="text-center p-3 text-foreground font-semibold">Dependency %</th>
                  <th className="text-left p-3 text-foreground font-semibold">Primary Sources</th>
                  <th className="text-center p-3 text-foreground font-semibold">Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {importDependency.data?.map((item, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className="p-3 text-zinc-200 font-medium">{item.region}</td>
                    <td className="text-center p-3 text-foreground">{item.dependency_percent}</td>
                    <td className="p-3 text-foreground">{item.primary_sources}</td>
                    <td className="text-center p-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          item.risk_level === "High"
                            ? "bg-red-500/20 text-red-400"
                            : "bg-yellow-500/20 text-yellow-400"
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-sm text-muted-foreground">{importDependency.description}</p>
        </motion.div>
      )}
    </>
  );
}

/**
 * Patent Agent Data Renderer
 */
export function PatentDataDisplay({ data, isFirstPrompt }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Patent" />;
  }

  // NEW: Check if this is real patent agent data (has visualizations array)
  if (data.visualizations && Array.isArray(data.visualizations)) {
    // This is real patent FTO data - it will be rendered by the main visualization system
    // Return null here since visualizations are rendered separately
    return null;
  }

  // LEGACY: Old mock data structure for backwards compatibility
  if (isFirstPrompt) {
    const landscapeOverview = data.landscape_overview;
    const repurposingStrategy = data.repurposing_strategy;
    const filingHeatmap = data.filing_heatmap;
    const keyPatentExtract = data.key_patent_extract;
    const ipOpportunities = data.ip_opportunities;

    return (
      <>
        {/* Landscape Overview */}
        {landscapeOverview && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-amber-500 font-semibold mb-3 text-lg">{landscapeOverview.title}</h3>

            <div className="bg-muted rounded-lg p-6 space-y-4">
              <div className="space-y-3">
                {landscapeOverview.sections?.map((section, idx) => (
                  <div key={idx} className="bg-card border border-amber-500/20 rounded-lg p-4">
                    <p className="text-muted-foreground text-sm">{section.label}</p>
                    <p className="text-amber-300 font-semibold mt-1">{section.value}</p>
                  </div>
                ))}
              </div>

              <p className="text-sm text-muted-foreground">{landscapeOverview.description}</p>
            </div>
          </motion.div>
        )}

        {/* Repurposing Strategy */}
        {repurposingStrategy && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h3 className="text-blue-500 font-semibold mb-3 text-lg">
              {repurposingStrategy.title}
            </h3>

            <div className="bg-muted rounded-lg p-6 space-y-3 text-sm">
              <p className="text-muted-foreground">
                <span className="text-white font-semibold">High-confidence targets:</span>{" "}
                {repurposingStrategy.high_confidence_targets}
              </p>
              <p className="text-muted-foreground">
                <span className="text-white font-semibold">Medium-risk exploratory areas:</span>{" "}
                {repurposingStrategy.medium_risk_areas}
              </p>
            </div>
          </motion.div>
        )}

        {/* Filing Heatmap */}
        {filingHeatmap && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-emerald-400 font-semibold mb-3 text-lg">{filingHeatmap.title}</h3>

            <div className="bg-muted rounded-lg p-6">
              <div className="grid grid-cols-4 gap-3">
                {filingHeatmap.data?.map((item, idx) => (
                  <div key={idx} className="text-center">
                    <div
                      className={`bg-${item.color}-500/20 border border-${item.color}-500/30 rounded-lg p-4`}
                    >
                      <div className={`text-2xl font-bold text-${item.color}-400`}>
                        {item.count}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">{item.region}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <p className="mt-3 text-sm text-muted-foreground">{filingHeatmap.description}</p>
          </motion.div>
        )}

        {/* Key Patent Extract */}
        {keyPatentExtract && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <h3 className="text-violet-400 font-semibold mb-3 text-lg">{keyPatentExtract.title}</h3>

            <div className="bg-muted rounded-lg p-4 border-l-4 border-violet-500">
              <div className="flex items-start gap-3">
                <Shield className="text-violet-400 mt-1" size={20} />
                <div>
                  <div className="text-xs text-violet-400 font-mono mb-2">
                    {keyPatentExtract.patent_number}
                  </div>
                  <p className="text-sm text-foreground italic">"{keyPatentExtract.description}"</p>
                  <p className="text-xs text-zinc-500 mt-2">
                    <span className="text-amber-500 font-semibold">⚠ Risk:</span>{" "}
                    {keyPatentExtract.risk_note}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* IP Opportunities */}
        {ipOpportunities && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
          >
            <h3 className="text-violet-500 font-semibold mb-3 text-lg">{ipOpportunities.title}</h3>

            <div className="bg-muted rounded-lg p-6 space-y-3 text-sm">
              <div className="bg-card border border-violet-500/20 rounded-lg p-4">
                <p className="text-muted-foreground text-xs">High-Value Claims</p>
                <p className="text-violet-300 font-semibold mt-1">
                  {ipOpportunities.high_value_claims}
                </p>
              </div>
              <p className="text-muted-foreground text-xs">{ipOpportunities.note}</p>
            </div>
          </motion.div>
        )}
      </>
    );
  }

  // AUD-specific patent data
  const audFocus = data.aud_focus;

  return (
    <>
      {audFocus && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-amber-500 font-semibold mb-3 text-lg">{audFocus.title}</h3>

          <div className="bg-muted rounded-lg p-6 space-y-4">
            <div className="space-y-3">
              {audFocus.sections?.map((section, idx) => (
                <div key={idx} className="bg-card border border-amber-500/20 rounded-lg p-4">
                  <p className="text-muted-foreground text-sm">{section.label}</p>
                  <p className="text-amber-300 font-semibold mt-1">{section.value}</p>
                </div>
              ))}
            </div>

            <p className="text-sm text-muted-foreground">{audFocus.description}</p>
          </div>
        </motion.div>
      )}
    </>
  );
}

/**
 * Clinical Agent Data Renderer
 */
export function ClinicalDataDisplay({ data, isFirstPrompt }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Clinical" />;
  }

  if (isFirstPrompt) {
    const landscapeOverview = data.landscape_overview;
    const phaseDistribution = data.phase_distribution;
    const sponsorProfile = data.sponsor_profile;

    return (
      <>
        {/* Landscape Overview */}
        {landscapeOverview && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-emerald-500 font-semibold mb-3 text-lg">
              {landscapeOverview.title}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">{landscapeOverview.description}</p>
          </motion.div>
        )}

        {/* Phase Distribution */}
        {phaseDistribution && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h3 className="text-indigo-400 font-semibold mb-3 text-lg">
              {phaseDistribution.title}
            </h3>

            <div className="bg-muted rounded-lg p-6">
              <div className="flex items-center justify-center gap-8">
                <div className="relative w-40 h-40">
                  <svg viewBox="0 0 200 200" className="transform -rotate-90">
                    <circle
                      cx="100"
                      cy="100"
                      r="70"
                      fill="none"
                      stroke="#27272a"
                      strokeWidth="30"
                    />
                    <circle
                      cx="100"
                      cy="100"
                      r="70"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="30"
                      strokeDasharray="70 439.82"
                    />
                    <circle
                      cx="100"
                      cy="100"
                      r="70"
                      fill="none"
                      stroke="#10b981"
                      strokeWidth="30"
                      strokeDasharray="140 439.82"
                      strokeDashoffset="-70"
                    />
                    <circle
                      cx="100"
                      cy="100"
                      r="70"
                      fill="none"
                      stroke="#f59e0b"
                      strokeWidth="30"
                      strokeDasharray="229.82 439.82"
                      strokeDashoffset="-210"
                    />
                  </svg>
                </div>

                <div className="flex flex-col gap-3 text-sm">
                  {phaseDistribution.data?.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div className={`w-4 h-4 rounded bg-${item.color}-500`}></div>
                      <span className="text-foreground">{item.phase}</span>
                      <span className={`text-${item.color}-400 font-semibold`}>
                        ~{item.count} trials
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <p className="mt-3 text-sm text-muted-foreground">{phaseDistribution.description}</p>
          </motion.div>
        )}

        {/* Sponsor Profile */}
        {sponsorProfile && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-teal-400 font-semibold mb-3 text-lg">{sponsorProfile.title}</h3>

            <div className="bg-muted rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-3 text-foreground font-semibold">Sponsor</th>
                    <th className="text-center p-3 text-foreground font-semibold">Trial Count</th>
                    <th className="text-left p-3 text-foreground font-semibold">Primary Focus</th>
                  </tr>
                </thead>
                <tbody>
                  {sponsorProfile.data?.map((item, idx) => (
                    <tr key={idx} className="border-t border-border">
                      <td className="p-3 text-zinc-200 font-medium">{item.sponsor}</td>
                      <td
                        className={`text-center p-3 font-semibold ${idx === 0 ? "text-blue-500" : idx === 1 ? "text-emerald-500" : "text-amber-500"}`}
                      >
                        ~{item.trial_count}
                      </td>
                      <td className="p-3 text-foreground">{item.focus}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-3 text-sm text-muted-foreground">{sponsorProfile.description}</p>
          </motion.div>
        )}
      </>
    );
  }

  // AUD-specific clinical data
  const audFocus = data.aud_focus;
  const keyTrials = data.key_trials;
  const signalInterpretation = data.signal_interpretation;
  const developmentGaps = data.development_gaps;

  return (
    <>
      {audFocus && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-emerald-500 font-semibold mb-3 text-lg">{audFocus.title}</h3>
          <p className="text-sm text-muted-foreground mb-4">{audFocus.description}</p>
        </motion.div>
      )}

      {keyTrials && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-indigo-400 font-semibold mb-3 text-lg">{keyTrials.title}</h3>

          <div className="bg-muted rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 text-foreground font-semibold">Trial ID</th>
                  <th className="text-center p-3 text-foreground font-semibold">Phase</th>
                  <th className="text-left p-3 text-foreground font-semibold">Primary Endpoints</th>
                  <th className="text-left p-3 text-foreground font-semibold">Sponsor</th>
                </tr>
              </thead>
              <tbody>
                {keyTrials.data?.map((trial, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className="p-3 text-zinc-200 font-mono">{trial.trial_id}</td>
                    <td className="text-center p-3 text-emerald-500 font-semibold">
                      {trial.phase}
                    </td>
                    <td className="p-3 text-foreground">{trial.primary_endpoints}</td>
                    <td className="p-3 text-foreground">{trial.sponsor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-sm text-muted-foreground">{keyTrials.description}</p>
        </motion.div>
      )}

      {signalInterpretation && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h3 className="text-emerald-400 font-semibold mb-3 text-lg">
            {signalInterpretation.title}
          </h3>

          <div className="bg-muted rounded-lg p-6 space-y-3 text-sm">
            <div className="bg-card border border-emerald-500/20 rounded-lg p-4">
              <p className="text-muted-foreground text-xs">Observed Trends</p>
              <p className="text-emerald-300 font-semibold mt-1">
                {signalInterpretation.observed_trends}
              </p>
            </div>

            <p className="text-muted-foreground">{signalInterpretation.description}</p>
          </div>
        </motion.div>
      )}

      {developmentGaps && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="text-amber-500 font-semibold mb-3 text-lg">{developmentGaps.title}</h3>

          <div className="bg-muted rounded-lg p-6 text-sm space-y-2">
            {developmentGaps.gaps?.map((gap, idx) => (
              <p key={idx} className="text-muted-foreground">
                • {gap}
              </p>
            ))}
          </div>
        </motion.div>
      )}
    </>
  );
}

/**
 * Internal Knowledge Agent Data Renderer
 */
export function InternalKnowledgeDataDisplay({ data, isFirstPrompt }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Internal Knowledge" />;
  }

  if (isFirstPrompt) {
    const strategicSynthesis = data.strategic_synthesis;
    const crossIndicationComparison = data.cross_indication_comparison;

    return (
      <>
        {strategicSynthesis && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-pink-500 font-semibold mb-3 text-lg">{strategicSynthesis.title}</h3>

            <div className="bg-muted rounded-lg p-6 text-sm space-y-4">
              {strategicSynthesis.insights?.map((insight, idx) => (
                <div key={idx} className="bg-card border border-pink-500/30 rounded-lg p-4">
                  <p className="text-muted-foreground text-xs">{insight.label}</p>
                  <p className="text-pink-200 font-semibold mt-1">{insight.value}</p>
                </div>
              ))}

              <p className="text-muted-foreground">{strategicSynthesis.description}</p>
            </div>
          </motion.div>
        )}

        {crossIndicationComparison && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h3 className="text-fuchsia-400 font-semibold mb-3 text-lg">
              {crossIndicationComparison.title}
            </h3>

            <div className="bg-muted rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-3 text-foreground font-semibold">Dimension</th>
                    <th className="text-center p-3 text-foreground font-semibold">
                      Current Indication
                    </th>
                    <th className="text-center p-3 text-foreground font-semibold">
                      New Indication
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {crossIndicationComparison.dimensions?.map((dim, idx) => (
                    <tr key={idx} className="border-t border-border">
                      <td className="p-3 text-zinc-200 font-medium">{dim.dimension}</td>
                      <td className="text-center p-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            (dim.current_level || dim.diabetes_obesity_level) === "green"
                              ? "bg-green-500/20 text-emerald-500"
                              : (dim.current_level || dim.diabetes_obesity_level) === "red"
                                ? "bg-red-500/20 text-red-400"
                                : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {dim.current || dim.diabetes_obesity}
                        </span>
                      </td>
                      <td className="text-center p-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            (dim.new_level || dim.emerging_cns_level) === "green"
                              ? "bg-green-500/20 text-emerald-500"
                              : (dim.new_level || dim.emerging_cns_level) === "red"
                                ? "bg-red-500/20 text-red-400"
                                : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {dim.new || dim.emerging_cns}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-3 text-sm text-muted-foreground">
              {crossIndicationComparison.description}
            </p>
          </motion.div>
        )}
      </>
    );
  }

  // AUD-specific internal knowledge data
  const audFocus = data.aud_focus;
  const riskFlags = data.risk_flags;

  return (
    <>
      {audFocus && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-pink-500 font-semibold mb-3 text-lg">{audFocus.title}</h3>

          <div className="bg-muted rounded-lg p-6 text-sm space-y-4">
            {audFocus.insights?.map((insight, idx) => (
              <div key={idx} className="bg-card border border-pink-500/30 rounded-lg p-4">
                <p className="text-muted-foreground text-xs">{insight.label}</p>
                <p className="text-pink-200 font-semibold mt-1">{insight.value}</p>
              </div>
            ))}

            <p className="text-muted-foreground">{audFocus.description}</p>
          </div>
        </motion.div>
      )}

      {riskFlags && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-fuchsia-400 font-semibold mb-3 text-lg">{riskFlags.title}</h3>

          <div className="bg-muted rounded-lg p-6 text-sm space-y-2">
            {riskFlags.flags?.map((flag, idx) => (
              <p key={idx} className="text-muted-foreground">
                • {flag}
              </p>
            ))}
          </div>

          <p className="mt-3 text-sm text-muted-foreground">{riskFlags.description}</p>
        </motion.div>
      )}
    </>
  );
}

/**
 * Report Generator Data Renderer
 */
export function ReportGeneratorDataDisplay({ data, isFirstPrompt, onDownload }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Report Generator" />;
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h3 className="text-violet-500 font-semibold mb-2 text-lg">{data.title}</h3>
        <p className="mb-3">{data.description}</p>
      </motion.div>

      {data.sections?.map((section, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + idx * 0.2 }}
        >
          <h3 className={`text-${section.color}-400 font-semibold mb-2 text-lg`}>
            {section.title}
          </h3>
          {section.description && <p className="mb-3">{section.description}</p>}

          {section.status === "Finalizing" ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col gap-3 mt-4"
            >
              <div className="text-violet-500 text-sm">⏳ Finalizing report for viewing</div>
              <motion.button
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                onClick={onDownload}
                className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-all duration-200 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                View Report
              </motion.button>
            </motion.div>
          ) : (
            <div className={`text-${section.status === "Complete" ? "green" : "blue"}-400 text-sm`}>
              {section.status === "Complete" ? "✓" : "○"}{" "}
              {section.status === "Complete" ? `${section.title} - Complete` : "In Progress"}
            </div>
          )}
        </motion.div>
      ))}
    </>
  );
}

/**
 * Web Intelligence Agent Data Renderer
 */
export function WebIntelligenceDataDisplay({ data, isFirstPrompt }) {
  if (!data || Object.keys(data).length === 0) {
    return <FallbackDisplay agentName="Web Intelligence" />;
  }

  // Unwrap nested data structure: web intelligence agent returns {status: "success", data: {...}}
  const actualData = data.status === "success" && data.data ? data.data : data;

  // Extract main sections from the structured output
  const header = actualData.header || {};
  const topSignal = actualData.top_signal || {};
  const topHeadlines = actualData.top_headlines || [];
  const forumQuotes = actualData.forum_quotes || [];
  const sentiment = actualData.sentiment || {};
  const recommendedActions = actualData.recommended_actions || [];
  const confidence = actualData.confidence || "MEDIUM";

  return (
    <>
      {/* Top Signal / Summary */}
      {topSignal.text && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-cyan-500 font-semibold mb-3 text-lg">Signal Summary</h3>
          <div className="bg-muted rounded-lg p-5 border border-cyan-500/30">
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <p className="text-muted-foreground leading-relaxed mb-2">{topSignal.text}</p>
                {topSignal.score !== undefined && (
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-xs text-muted-foreground">Signal Score:</span>
                    <div className="flex-1 max-w-xs bg-card rounded h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full"
                        style={{ width: `${Math.min((topSignal.score / 100) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-cyan-400">
                      {topSignal.score?.toFixed(1) || "0"}
                    </span>
                  </div>
                )}
                {topSignal.label && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Alert Level:{" "}
                    <span className="text-cyan-400 font-semibold">{topSignal.label}</span>
                  </p>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Sentiment Breakdown */}
      {sentiment.total > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <h3 className="text-emerald-500 font-semibold mb-3 text-lg">Sentiment Analysis</h3>
          <div className="bg-muted rounded-lg p-4 grid grid-cols-3 gap-3">
            <div className="bg-card border border-emerald-500/20 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">Positive</p>
              <p className="text-emerald-400 font-bold text-lg mt-1">{sentiment.positive || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {sentiment.total > 0
                  ? ((sentiment.positive / sentiment.total) * 100).toFixed(0)
                  : 0}
                %
              </p>
            </div>
            <div className="bg-card border border-yellow-500/20 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">Neutral</p>
              <p className="text-yellow-400 font-bold text-lg mt-1">{sentiment.neutral || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {sentiment.total > 0 ? ((sentiment.neutral / sentiment.total) * 100).toFixed(0) : 0}
                %
              </p>
            </div>
            <div className="bg-card border border-red-500/20 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">Negative</p>
              <p className="text-red-400 font-bold text-lg mt-1">{sentiment.negative || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {sentiment.total > 0
                  ? ((sentiment.negative / sentiment.total) * 100).toFixed(0)
                  : 0}
                %
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Top Headlines */}
      {topHeadlines.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-blue-500 font-semibold mb-3 text-lg">Latest News & Headlines</h3>
          <div className="space-y-3">
            {topHeadlines.slice(0, 6).map((article, idx) => (
              <div
                key={idx}
                className="bg-card border border-blue-500/20 rounded-lg p-4 hover:border-blue-500/40 transition-all"
              >
                <p className="font-medium text-foreground text-sm leading-snug">{article.title}</p>
                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                  {article.source && (
                    <span className="font-semibold text-blue-400">{article.source}</span>
                  )}
                  {article.publishedAt && (
                    <>
                      <span>•</span>
                      <span>{new Date(article.publishedAt).toLocaleDateString()}</span>
                    </>
                  )}
                </div>
                {article.snippet && (
                  <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                    {article.snippet}
                  </p>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Forum Discussions */}
      {forumQuotes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h3 className="text-amber-500 font-semibold mb-3 text-lg">Community Discussions</h3>
          <div className="space-y-3">
            {forumQuotes.slice(0, 5).map((forum, idx) => (
              <div
                key={idx}
                className="bg-card border border-amber-500/20 rounded-lg p-4 hover:border-amber-500/40 transition-all"
              >
                <p className="text-sm text-muted-foreground italic">"{forum.quote}"</p>
                <div className="flex items-center gap-2 mt-2">
                  {forum.site && (
                    <span className="text-xs font-semibold text-amber-400 bg-amber-500/10 px-2 py-1 rounded">
                      {forum.site}
                    </span>
                  )}
                  {forum.sentiment && (
                    <span
                      className={`text-xs font-semibold px-2 py-1 rounded ${
                        forum.sentiment === "POS"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : forum.sentiment === "NEG"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-yellow-500/10 text-yellow-400"
                      }`}
                    >
                      {forum.sentiment === "POS"
                        ? "Positive"
                        : forum.sentiment === "NEG"
                          ? "Negative"
                          : "Neutral"}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recommended Actions */}
      {recommendedActions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-violet-500 font-semibold mb-3 text-lg">Recommended Actions</h3>
          <div className="bg-muted rounded-lg p-4 space-y-2">
            {recommendedActions.map((action, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <div className="flex-shrink-0 text-violet-400 font-bold">→</div>
                <p className="text-sm text-muted-foreground">{action}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Confidence Level */}
      {confidence && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <div className="bg-muted rounded-lg p-4 flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Analysis Confidence:</span>
            <span
              className={`text-sm font-semibold px-3 py-1 rounded-full ${
                confidence === "HIGH"
                  ? "bg-emerald-500/20 text-emerald-400"
                  : confidence === "MEDIUM"
                    ? "bg-yellow-500/20 text-yellow-400"
                    : "bg-orange-500/20 text-orange-400"
              }`}
            >
              {confidence}
            </span>
          </div>
        </motion.div>
      )}
    </>
  );
}

/**
 * Fallback display when no data is available
 */
function FallbackDisplay({ agentName }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="flex flex-col items-center justify-center py-12 px-6"
    >
      <div className="w-16 h-16 rounded-2xl bg-muted/50 border border-border flex items-center justify-center mb-4">
        <Shield className="text-muted-foreground" size={28} />
      </div>
      <h3 className="text-foreground font-semibold text-lg mb-2">No Data Available</h3>
      <p className="text-muted-foreground text-sm text-center max-w-md">
        The {agentName} agent hasn&apos;t returned any data yet. This may be because the analysis is
        still processing or the data source is temporarily unavailable.
      </p>
    </motion.div>
  );
}

/**
 * MetricCard - Unified metric card component for consistent agent outputs
 *
 * All cards have fixed dimensions for visual consistency across all agents
 */

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

// Fixed card dimensions for consistency
const CARD_HEIGHT = "h-[120px]";
const CARD_MIN_HEIGHT = "min-h-[120px]";

// Color themes — Teal + Deep Navy palette
const colorThemes = {
  sky: {
    bg: "bg-sky-500/6",
    border: "border-sky-500/20",
    accent: "text-sky-400",
    gradient: "from-sky-500/8 to-transparent",
  },
  blue: {
    bg: "bg-sky-500/6",
    border: "border-sky-500/20",
    accent: "text-sky-400",
    gradient: "from-sky-500/8 to-transparent",
  },
  teal: {
    bg: "bg-teal-500/6",
    border: "border-teal-500/20",
    accent: "text-teal-400",
    gradient: "from-teal-500/8 to-transparent",
  },
  amber: {
    bg: "bg-amber-500/6",
    border: "border-amber-500/20",
    accent: "text-amber-400",
    gradient: "from-amber-500/8 to-transparent",
  },
  emerald: {
    bg: "bg-emerald-500/6",
    border: "border-emerald-500/20",
    accent: "text-emerald-400",
    gradient: "from-emerald-500/8 to-transparent",
  },
  violet: {
    bg: "bg-violet-500/6",
    border: "border-violet-500/20",
    accent: "text-violet-400",
    gradient: "from-violet-500/8 to-transparent",
  },
  pink: {
    bg: "bg-cyan-500/6",
    border: "border-cyan-500/20",
    accent: "text-cyan-400",
    gradient: "from-cyan-500/8 to-transparent",
  },
  cyan: {
    bg: "bg-cyan-500/6",
    border: "border-cyan-500/20",
    accent: "text-cyan-400",
    gradient: "from-cyan-500/8 to-transparent",
  },
  indigo: {
    bg: "bg-indigo-500/6",
    border: "border-indigo-500/20",
    accent: "text-indigo-400",
    gradient: "from-indigo-500/8 to-transparent",
  },
};

/**
 * MetricCard - Display a single metric with optional trend indicator
 */
export function MetricCard({
  label,
  value,
  unit = "",
  trend,
  trendValue,
  color = "blue",
  icon: Icon,
  delay = 0,
  compact = false,
}) {
  const theme = colorThemes[color] || colorThemes.blue;

  // Determine trend direction
  const trendDirection =
    trend === "up" || (typeof trendValue === "number" && trendValue > 0)
      ? "up"
      : trend === "down" || (typeof trendValue === "number" && trendValue < 0)
        ? "down"
        : null;

  const TrendIcon =
    trendDirection === "up" ? TrendingUp : trendDirection === "down" ? TrendingDown : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.05, duration: 0.3 }}
      className={`
        relative overflow-hidden rounded-2xl border ${theme.border} ${theme.bg}
        ${compact ? "p-3" : "p-4"}
        ${compact ? "min-h-[80px]" : CARD_MIN_HEIGHT}
        bg-gradient-to-br ${theme.gradient}
        hover:border-opacity-50 transition-all duration-300 backdrop-blur-sm
        flex flex-col justify-between
      `}
    >
      {/* Label */}
      <div className="flex items-start justify-between gap-2">
        <p
          className={`text-muted-foreground font-medium ${compact ? "text-xs" : "text-[13px]"} uppercase tracking-wider leading-tight`}
        >
          {label}
        </p>
        {Icon && (
          <Icon className={`${theme.accent} flex-shrink-0 opacity-60`} size={compact ? 16 : 18} />
        )}
      </div>

      {/* Value */}
      <div className="flex items-end justify-between gap-2 mt-auto">
        <div className="flex items-baseline gap-1.5 min-w-0">
          <span
            className={`font-bold ${theme.accent} ${compact ? "text-2xl" : "text-3xl"} truncate leading-none`}
          >
            {value ?? "—"}
          </span>
          {unit && (
            <span
              className={`text-muted-foreground ${compact ? "text-xs" : "text-sm"} font-medium`}
            >
              {unit}
            </span>
          )}
        </div>

        {/* Trend Indicator - Simple text only, no box */}
        {trendValue !== undefined && trendValue !== null && (
          <div
            className={`flex items-center gap-1 text-xs font-medium flex-shrink-0
            ${trendDirection === "up" ? "text-emerald-400" : trendDirection === "down" ? "text-red-400" : "text-muted-foreground"}
          `}
          >
            {TrendIcon && <TrendIcon size={12} />}
            <span>
              {typeof trendValue === "number"
                ? `${trendValue > 0 ? "+" : ""}${trendValue}%`
                : trendValue}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * MetricGrid - Container for metric cards with consistent grid layout
 */
export function MetricGrid({ children, columns = 3, className = "" }) {
  return <div className={`grid grid-cols-${columns} gap-3 ${className}`}>{children}</div>;
}

/**
 * DataTable - Compact table component for tabular data
 */
export function DataTable({ headers = [], rows = [], color = "blue", compact = false }) {
  const theme = colorThemes[color] || colorThemes.blue;

  if (!rows.length) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`rounded-2xl border ${theme.border} overflow-hidden backdrop-blur-sm`}
    >
      <table className="w-full text-[15px]">
        <thead className="bg-muted/50">
          <tr>
            {headers.map((header, idx) => (
              <th
                key={idx}
                className={`text-left ${compact ? "px-3 py-2" : "px-4 py-2.5"} text-foreground font-semibold text-[13px] uppercase tracking-wider`}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="border-t border-border/50 hover:bg-muted/30 transition-colors"
            >
              {row.map((cell, cellIdx) => (
                <td
                  key={cellIdx}
                  className={`${compact ? "px-3 py-2" : "px-4 py-2.5"} text-muted-foreground`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}

/**
 * InfoCard - Card for text-based information
 */
export function InfoCard({ title, content, items = [], color = "blue", icon: Icon, delay = 0 }) {
  const theme = colorThemes[color] || colorThemes.blue;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.05, duration: 0.3 }}
      className={`
        rounded-2xl border ${theme.border} ${theme.bg}
        bg-gradient-to-br ${theme.gradient}
        p-5 space-y-3 backdrop-blur-sm
      `}
    >
      {title && (
        <div className="flex items-center gap-2.5">
          {Icon && <Icon className={theme.accent} size={18} />}
          <h4 className="font-semibold text-foreground text-base">{title}</h4>
        </div>
      )}

      {content && (
        <div className="text-muted-foreground text-[15px] leading-relaxed space-y-1.5">
          {content.split("\n").map((line, idx) => {
            const trimmed = line.trim();
            if (!trimmed) return null;
            const numberedMatch = trimmed.match(/^(\d+)[\.\)]\s+(.*)/);
            if (numberedMatch) {
              return (
                <div key={idx} className="flex items-start gap-2">
                  <span className={`${theme.accent} font-semibold min-w-[1.25rem] text-right`}>{numberedMatch[1]}.</span>
                  <span>{numberedMatch[2]}</span>
                </div>
              );
            }
            return <p key={idx}>{trimmed}</p>;
          })}
        </div>
      )}

      {items.length > 0 && (
        <ul className="space-y-2">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2.5 text-[15px] text-muted-foreground">
              <span className={`${theme.accent} mt-1.5`}>•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}

/**
 * SectionHeader - Section title with optional badge and accent line
 */
export function SectionHeader({ title, badge, color = "blue" }) {
  const theme = colorThemes[color] || colorThemes.blue;

  return (
    <div className="flex items-center gap-2.5 mb-3">
      <div className={`w-1 h-5 rounded-full opacity-60 ${theme.accent.replace('text-', 'bg-')}`} />
      <h3 className={`font-semibold ${theme.accent} text-sm uppercase tracking-wider font-[family-name:var(--font-heading)]`}>{title}</h3>
      {badge && (
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full ${theme.bg} ${theme.accent} font-semibold`}
        >
          {badge}
        </span>
      )}
    </div>
  );
}

/**
 * SummaryBanner - Canonical summary banner for all agents
 * 
 * Displays researcher question, answer badge, and explainer chips.
 * Designed as a subtle "key finding" strip at the top of each agent section.
 */
export function SummaryBanner({ summary, color = "blue", delay = 0 }) {
  if (!summary || !summary.researcherQuestion) {
    return null;
  }

  const theme = colorThemes[color] || colorThemes.blue;
  
  const questionText = typeof summary.researcherQuestion === 'string'
    ? summary.researcherQuestion
    : (summary.researcherQuestion?.text || String(summary.researcherQuestion));
  
  const rawAnswer = summary.answer || "Unknown";
  const answer = typeof rawAnswer === 'string' ? rawAnswer : (rawAnswer?.text || String(rawAnswer));
  const answerLower = answer.toLowerCase();
  
  let badgeStyle = "";
  if (answerLower === "yes" || answerLower === "positive" || answerLower === "clear") {
    badgeStyle = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  } else if (answerLower === "no" || answerLower === "blocked" || answerLower === "caution") {
    badgeStyle = "bg-red-500/20 text-red-400 border-red-500/30";
  } else if (answerLower === "risky" || answerLower === "unclear" || answerLower === "mixed" || answerLower === "developing" || answerLower === "stable") {
    badgeStyle = "bg-amber-500/20 text-amber-400 border-amber-500/30";
  } else {
    badgeStyle = `${theme.bg} ${theme.accent} ${theme.border}`;
  }

  const explainers = summary.explainers || [];
  
  // ── Feasibility Score ──
  const fs = summary.feasibilityScore;
  const scoreValue = fs?.score ?? null;
  const scoreLabel = fs?.label || "";
  const isCritical = fs?.isCritical === true;
  
  // Score ring colour
  let scoreRingColor = "stroke-muted-foreground/40";
  let scoreTextColor = "text-muted-foreground";
  if (scoreValue !== null) {
    if (scoreValue === 0) {
      scoreRingColor = "stroke-red-500";
      scoreTextColor = "text-red-400";
    } else if (scoreValue <= 20) {
      scoreRingColor = "stroke-red-400";
      scoreTextColor = "text-red-400";
    } else if (scoreValue <= 40) {
      scoreRingColor = "stroke-orange-400";
      scoreTextColor = "text-orange-400";
    } else if (scoreValue <= 60) {
      scoreRingColor = "stroke-amber-400";
      scoreTextColor = "text-amber-400";
    } else if (scoreValue <= 80) {
      scoreRingColor = "stroke-emerald-400";
      scoreTextColor = "text-emerald-400";
    } else {
      scoreRingColor = "stroke-teal-400";
      scoreTextColor = "text-teal-400";
    }
  }
  
  // SVG ring math (r=18, circumference ≈ 113.1)
  const circumference = 2 * Math.PI * 18;
  const scorePct = scoreValue !== null ? Math.max(0, Math.min(100, scoreValue)) : 0;
  const dashOffset = circumference - (scorePct / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.05, duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={`
        relative overflow-hidden rounded-xl border ${theme.border}
        p-4 bg-gradient-to-r ${theme.gradient} backdrop-blur-sm
      `}
    >
      {/* Question, Answer & Score Row */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <p className="text-[15px] text-foreground/80 font-medium leading-snug flex-1">
          {questionText}
        </p>
        <div className="flex items-center gap-2.5 flex-shrink-0">
          <span className={`text-xs font-bold px-3.5 py-1.5 rounded-full border whitespace-nowrap ${badgeStyle}`}>
            {answer}
          </span>
          {scoreValue !== null && (
            <div className="relative flex items-center justify-center" title={`Feasibility: ${scoreValue}/100 — ${scoreLabel}${isCritical ? " (CRITICAL BLOCKER)" : ""}`}>
              <svg width="44" height="44" viewBox="0 0 44 44" className="-rotate-90">
                <circle cx="22" cy="22" r="18" fill="none" strokeWidth="3" className="stroke-white/[0.06]" />
                <motion.circle
                  cx="22" cy="22" r="18" fill="none" strokeWidth="3"
                  className={scoreRingColor}
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: dashOffset }}
                  transition={{ delay: (delay * 0.05) + 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                />
              </svg>
              <span className={`absolute text-[11px] font-bold ${scoreTextColor}`}>
                {scoreValue}
              </span>
            </div>
          )}
        </div>
      </div>
      
      {/* Critical blocker banner */}
      {isCritical && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-red-500/[0.12] border border-red-500/30 rounded-lg">
          <span className="text-red-400 text-xs font-bold uppercase tracking-wider">Critical Blocker</span>
          <span className="text-red-300/80 text-xs">{fs?.criticalReason || "This factor critically blocks feasibility"}</span>
        </div>
      )}
      
      {/* Explainers + score label */}
      {(explainers.length > 0 || scoreLabel) && (
        <div className="flex flex-wrap gap-2 items-center">
          {explainers.slice(0, 3).map((explainer, idx) => {
            const explainerText = typeof explainer === 'string' 
              ? explainer 
              : (explainer && typeof explainer === 'object' 
                  ? (explainer.text || explainer.value || JSON.stringify(explainer)) 
                  : String(explainer));
            
            return (
              <span
                key={idx}
                className="text-[13px] px-3 py-1.5 rounded-lg bg-white/[0.04] text-muted-foreground border border-white/[0.06]"
              >
                {explainerText}
              </span>
            );
          })}
          {scoreValue !== null && (
            <span className={`text-[11px] px-2.5 py-1 rounded-lg border border-white/[0.06] font-medium ${scoreTextColor} bg-white/[0.03]`}>
              Score: {scoreValue}/100
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

/**
 * SuggestedPrompts - Display suggested next prompts
 */
export function SuggestedPrompts({ prompts, onPromptClick, color = "blue" }) {
  if (!prompts || prompts.length === 0) {
    return null;
  }

  const theme = colorThemes[color] || colorThemes.blue;

  return (
    <div className="mt-6 pt-5 border-t border-white/[0.04]">
      <p className="text-xs text-muted-foreground mb-3 uppercase tracking-wider font-semibold">Suggested follow-ups</p>
      <div className="flex flex-wrap gap-2">
        {prompts.slice(0, 3).map((item, idx) => (
          <motion.button
            key={idx}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onPromptClick?.(item.prompt)}
            className={`
              text-sm px-4 py-2.5 rounded-xl
              bg-white/[0.04] text-muted-foreground border border-white/[0.08]
              hover:bg-white/[0.07] hover:text-foreground hover:border-white/[0.12]
              transition-all duration-200 cursor-pointer
            `}
          >
            {item.prompt}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

export default MetricCard;

/**
 * Modular Visualization System
 *
 * A highly modular, agent-agnostic visualization system that:
 * - Renders beautiful charts using Recharts
 * - Handles missing/null data gracefully
 * - Formats column names intelligently
 * - Supports bar, pie, line, area, table, and metric card types
 * - Provides consistent styling across all visualizations
 */

import React, { useMemo, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
  LineChart as RechartsLineChart,
  Line,
  AreaChart as RechartsAreaChart,
  Area,
} from "recharts";
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Table as TableIcon,
  BarChart3,
  PieChart as PieChartIcon,
  Download,
  Maximize2,
  X,
} from "lucide-react";
import {
  PRIMARY_PALETTE,
  EXTENDED_PALETTE,
  COLD_TO_HOT,
  NAVY_SCALE,
  BLUE_SCALE,
  PURPLE_SCALE,
  CORAL_SCALE,
  ORANGE_SCALE,
  getColor,
  getAlternatingColors,
  getPaletteForChartType,
  lightenColor,
} from "../../lib/colorPalette.js";

// ============================================================================
// COLOR PALETTE - Professional & Subtle Colors
// ============================================================================
export const CHART_COLORS = PRIMARY_PALETTE;

export const GRADIENT_COLORS = PRIMARY_PALETTE.map((color, idx) => {
  const nextColor = PRIMARY_PALETTE[(idx + 1) % PRIMARY_PALETTE.length];
  return {
    start: color,
    end: lightenColor(nextColor, 15),
  };
});

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Convert field keys to human-readable labels
 */
export const formatLabel = (key) => {
  if (!key) return "";

  // Special cases for uppercase acronyms
  const specialLabels = {
    nct_id: "NCT ID",
    id: "ID",
    url: "URL",
    api: "API",
    cagr: "CAGR",
    roi: "ROI",
    usd: "USD",
    eur: "EUR",
    gbp: "GBP",
    fda: "FDA",
    eua: "EUA",
  };

  const lower = String(key).toLowerCase();
  if (specialLabels[lower]) return specialLabels[lower];

  // Handle phase labels specifically for natural ordering
  if (lower.includes("phase")) {
    const phaseMatch = String(key).match(/phase[_\s]*(\d+|i+|iv?|one|two|three|four)/i);
    if (phaseMatch) {
      const phaseNum = phaseMatch[1];
      // Convert roman numerals or text to numbers
      const numMap = { i: 1, ii: 2, iii: 3, iv: 4, one: 1, two: 2, three: 3, four: 4 };
      const normalizedNum = numMap[phaseNum.toLowerCase()] || phaseNum;
      return `Phase ${normalizedNum}`;
    }
  }

  // Known concatenated phrases in pharmaceutical data (status fields, etc.)
  const knownPhrases = {
    activenotrecruiting: "Active, not recruiting",
    notyetrecruiting: "Not yet recruiting",
    enrollingbyinvitation: "Enrolling by invitation",
    activelycompleted: "Actively completed",
    temporarilynotavailable: "Temporarily not available",
    notavailable: "Not available",
    approvedformarketing: "Approved for marketing",
    notyetapproved: "Not yet approved",
    notyetactive: "Not yet active",
    withheldunknown: "Withheld / unknown",
    notapplicable: "Not applicable",
  };

  const lowerKey = String(key).toLowerCase().replace(/[\s_-]/g, "");
  if (knownPhrases[lowerKey]) return knownPhrases[lowerKey];

  let raw = String(key);

  // If the string is ALL CAPS (or nearly), just title-case it instead of
  // inserting a space before every letter.
  const upperRatio = (raw.match(/[A-Z]/g) || []).length / raw.replace(/[^a-zA-Z]/g, "").length;
  if (upperRatio > 0.6) {
    // ALL-CAPS input like "COMPLETED" or "NOT_YET_RECRUITING"
    raw = raw
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase()); // Title Case each word
    // Return as-is (already nicely formatted)
    return raw;
  }

  // Convert snake_case and camelCase to Sentence case (only first word capitalized)
  let formatted = raw
    .replace(/_/g, " ") // Replace underscores with spaces
    .replace(/([A-Z])/g, " $1") // Add space before capital letters (camelCase)
    .trim();

  // Capitalize only the first letter, lowercase the rest
  formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1).toLowerCase();

  return formatted;
};

/**
 * Format numeric values with appropriate precision and units
 */
export const formatValue = (value, type = "number") => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (type === "currency") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  if (type === "percent") {
    return `${Number(value).toFixed(1)}%`;
  }

  if (typeof value === "number") {
    if (value >= 1_000_000_000) {
      return `${(value / 1_000_000_000).toFixed(1)}B`;
    }
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(1)}M`;
    }
    if (value >= 1_000) {
      return `${(value / 1_000).toFixed(1)}K`;
    }
    if (Number.isInteger(value)) {
      return value.toLocaleString();
    }
    return value.toFixed(2);
  }

  return String(value);
};

/**
 * Sanitize data - handle missing values, normalize structure
 */
export const sanitizeData = (data, fields = []) => {
  if (!Array.isArray(data)) return [];

  return data.map((item, idx) => {
    const sanitized = { ...item, _index: idx };
    fields.forEach((field) => {
      if (sanitized[field] === null || sanitized[field] === undefined) {
        sanitized[field] = 0;
      }
    });
    return sanitized;
  });
};

// ============================================================================
// BASE CARD COMPONENT - Enhanced with vibrant styling
// ============================================================================

const VizCard = ({ title, description, icon: Icon, children, className = "" }) => {
  // Safely convert description to string if it's an object
  const safeDescription = typeof description === 'string' 
    ? description 
    : (description && typeof description === 'object' 
        ? (description.text || description.value || description.answer || '') 
        : '');
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      className={`bg-gradient-to-br from-card via-card/95 to-card/90 border border-white/[0.06] rounded-2xl p-6 shadow-xl hover:shadow-2xl hover:border-primary/20 transition-all duration-300 backdrop-blur-sm ${className}`}
    >
      {title && (
        <div className="flex items-start justify-between mb-5 pb-4 border-b border-white/[0.06]">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-foreground flex items-center gap-3 font-[family-name:var(--font-heading)] tracking-tight">
              {Icon && (
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/15 via-primary/10 to-primary/5 border border-primary/20">
                  <Icon size={20} className="text-primary" />
                </div>
              )}
              <span>{title}</span>
            </h3>
            {safeDescription && (
              <div className="text-sm text-muted-foreground mt-2 leading-relaxed space-y-1.5">
                {safeDescription.split("\n").map((line, idx) => {
                  const trimmed = line.trim();
                  if (!trimmed) return null;
                  const numberedMatch = trimmed.match(/^(\d+)[\.\)]\s+(.*)/);
                  if (numberedMatch) {
                    return (
                      <div key={idx} className="flex items-start gap-2">
                        <span className="text-primary font-semibold min-w-[1.25rem] text-right">{numberedMatch[1]}.</span>
                        <span>{numberedMatch[2]}</span>
                      </div>
                    );
                  }
                  if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                    return (
                      <div key={idx} className="flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>{trimmed.replace(/^[•\-]\s*/, "")}</span>
                      </div>
                    );
                  }
                  return <p key={idx}>{trimmed}</p>;
                })}
              </div>
            )}
          </div>
        </div>
      )}
      {children}
    </motion.div>
  );
};

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

const CustomTooltip = ({ active, payload, label, labelFormatter }) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
      <p className="text-sm font-medium text-foreground mb-2">
        {labelFormatter ? labelFormatter(label) : label}
      </p>
      {payload.map((entry, idx) => (
        <div key={idx} className="flex items-center justify-between gap-4 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-muted-foreground">{formatLabel(entry.dataKey)}</span>
          </span>
          <span className="font-medium text-foreground">{formatValue(entry.value)}</span>
        </div>
      ))}
    </div>
  );
};

// ============================================================================
// BAR CHART COMPONENT - Supports both vertical and horizontal orientations
// ============================================================================

export const BarChartViz = ({ viz }) => {
  const { data = [], config = {}, title, description } = viz;
  const xField = config.xField || "label";
  const yField = config.yField || "value";
  const orientation = config.orientation || "vertical";

  const sanitizedData = useMemo(() => sanitizeData(data, [yField]), [data, yField]);

  if (!sanitizedData.length) {
    return (
      <VizCard title={title} description={description} icon={BarChart3}>
        <EmptyState message="No data available for chart" />
      </VizCard>
    );
  }

  // In Recharts: layout="vertical" means bars go horizontally (left to right)
  // layout="horizontal" (default) means bars go vertically (bottom to top)
  const isHorizontal = orientation === "horizontal";

  return (
    <VizCard title={title} description={description} icon={BarChart3}>
      <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart
            data={sanitizedData}
            layout={isHorizontal ? "vertical" : "horizontal"}
            margin={{
              top: 20,
              right: 50,
              left: isHorizontal ? 20 : 40,
              bottom: isHorizontal ? 20 : 70,
            }}
          >
            <defs>
              {sanitizedData.map((_, idx) => {
                const color = getAlternatingColors(sanitizedData.length, PRIMARY_PALETTE)[idx];
                const nextColor = lightenColor(color, 12);
                return (
                  <linearGradient
                    key={`barGrad${idx}`}
                    id={`barGrad${idx}`}
                    x1="0"
                    y1="0"
                    x2={isHorizontal ? "1" : "0"}
                    y2={isHorizontal ? "0" : "1"}
                  >
                    <stop offset="0%" stopColor={color} stopOpacity={0.95} />
                    <stop offset="100%" stopColor={nextColor} stopOpacity={0.75} />
                  </linearGradient>
                );
              })}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.25} />
            {isHorizontal ? (
              <>
                <XAxis
                  type="number"
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
                  tickLine={{ stroke: "hsl(var(--border))" }}
                  axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
                  tickFormatter={formatValue}
                />
                <YAxis
                  dataKey={xField}
                  type="category"
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
                  tickLine={{ stroke: "hsl(var(--border))" }}
                  axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
                  width={180}
                  tickFormatter={(v) => (v?.length > 25 ? v.slice(0, 25) + "…" : v)}
                />
              </>
            ) : (
              <>
                <XAxis
                  dataKey={xField}
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                  tickLine={{ stroke: "hsl(var(--border))" }}
                  axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
                  tickFormatter={(v) => (v?.length > 10 ? v.slice(0, 10) + "…" : v)}
                  angle={-45}
                  textAnchor="end"
                  height={70}
                  interval={0}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
                  tickLine={{ stroke: "hsl(var(--border))" }}
                  axisLine={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
                  tickFormatter={formatValue}
                />
              </>
            )}
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "hsl(var(--muted))", opacity: 0.15 }}
            />
            <Bar
              dataKey={yField}
              radius={isHorizontal ? [0, 6, 6, 0] : [6, 6, 0, 0]}
              maxBarSize={55}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {sanitizedData.map((entry, idx) => {
                const color = getAlternatingColors(sanitizedData.length, PRIMARY_PALETTE)[idx];
                const nextColor = lightenColor(color, 12);
                return <Cell key={`cell-${idx}`} fill={`url(#barGrad${idx})`} />;
              })}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </VizCard>
  );
};

// ============================================================================
// PIE CHART COMPONENT
// ============================================================================

export const PieChartViz = ({ viz }) => {
  const { data = [], config = {}, title, description } = viz;
  const labelField = config.labelField || "label";
  const valueField = config.valueField || "value";

  const sanitizedData = useMemo(() => {
    const filtered = data.filter(
      (d) => d[valueField] !== null && d[valueField] !== undefined && d[valueField] > 0,
    );
    return filtered.map((d, idx) => ({
      ...d,
      name: d[labelField] || `Item ${idx + 1}`,
      value: Number(d[valueField]) || 0,
    }));
  }, [data, labelField, valueField]);

  const total = useMemo(() => sanitizedData.reduce((sum, d) => sum + d.value, 0), [sanitizedData]);

  if (!sanitizedData.length || total === 0) {
    return (
      <VizCard title={title} description={description} icon={PieChartIcon}>
        <EmptyState message="No data available for chart" />
      </VizCard>
    );
  }

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null; // Hide labels for small slices
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
        fontSize={14}
        fontWeight={700}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  // Custom legend formatter to show percentages for all slices
  const renderLegendText = (value, entry) => {
    // Get the actual data value from the entry payload
    const dataValue = entry?.payload?.value || entry?.value || 0;
    const percent = total > 0 ? ((dataValue / total) * 100).toFixed(1) : "0.0";
    return (
      <span className="text-sm text-foreground" style={{ letterSpacing: 'normal', wordSpacing: 'normal', textTransform: 'none' }}>
        {formatLabel(value)} <span className="text-muted-foreground">({percent}%)</span>
      </span>
    );
  };

  return (
    <VizCard title={title} description={description} icon={PieChartIcon}>
      <div className="h-[450px] w-full flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsPieChart>
            <defs>
              {sanitizedData.map((_, idx) => {
                const color = getAlternatingColors(sanitizedData.length, EXTENDED_PALETTE)[idx];
                return (
                  <linearGradient key={idx} id={`pieGradient${idx}`} x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={1} />
                    <stop offset="100%" stopColor={color} stopOpacity={0.75} />
                  </linearGradient>
                );
              })}
            </defs>
            <Pie
              data={sanitizedData}
              cx="50%"
              cy="45%"
              innerRadius={80}
              outerRadius={140}
              paddingAngle={3}
              dataKey="value"
              labelLine={false}
              label={renderCustomLabel}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              {sanitizedData.map((entry, idx) => {
                const color = getAlternatingColors(sanitizedData.length, EXTENDED_PALETTE)[idx];
                return (
                  <Cell
                    key={`cell-${idx}`}
                    fill={color}
                    stroke="var(--background)"
                    strokeWidth={3}
                  />
                );
              })}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={100}
              iconType="circle"
              iconSize={12}
              wrapperStyle={{ paddingTop: "20px", letterSpacing: "normal", textTransform: "none" }}
              formatter={(value, entry) => {
                const dataValue = entry?.payload?.value || 0;
                const percent = total > 0 ? ((dataValue / total) * 100).toFixed(1) : "0.0";
                return (
                  <span className="text-sm font-medium text-foreground" style={{ letterSpacing: 'normal', wordSpacing: 'normal', textTransform: 'none' }}>
                    {formatLabel(value)} <span className="text-muted-foreground">({percent}%)</span>
                  </span>
                );
              }}
            />
          </RechartsPieChart>
        </ResponsiveContainer>
      </div>
    </VizCard>
  );
};

// ============================================================================
// LINE CHART COMPONENT
// ============================================================================

export const LineChartViz = ({ viz }) => {
  const { data = [], config = {}, title, description } = viz;
  const xField = config.xField || "label";
  const yField = config.yField || "value";
  const yFields = config.yFields || [yField];

  const sanitizedData = useMemo(() => sanitizeData(data, yFields), [data, yFields]);

  if (!sanitizedData.length) {
    return (
      <VizCard title={title} description={description}>
        <EmptyState message="No data available for chart" />
      </VizCard>
    );
  }

  return (
    <VizCard title={title} description={description}>
      <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsLineChart
            data={sanitizedData}
            margin={{ top: 10, right: 30, left: 0, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.25} />
            <XAxis
              dataKey={xField}
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "var(--border)", strokeWidth: 1 }}
            />
            <YAxis
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "var(--border)", strokeWidth: 1 }}
              tickFormatter={formatValue}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {yFields.map((field, idx) => {
              const color = getAlternatingColors(yFields.length, PRIMARY_PALETTE)[idx];
              return (
                <Line
                  key={field}
                  type="monotone"
                  dataKey={field}
                  stroke={color}
                  strokeWidth={3}
                  dot={{ fill: color, r: 5, strokeWidth: 2, stroke: "var(--background)" }}
                  activeDot={{ r: 7, strokeWidth: 2, stroke: color }}
                  animationDuration={800}
                />
              );
            })}
          </RechartsLineChart>
        </ResponsiveContainer>
      </div>
    </VizCard>
  );
};

// ============================================================================
// AREA CHART COMPONENT
// ============================================================================

export const AreaChartViz = ({ viz }) => {
  const { data = [], config = {}, title, description } = viz;
  const xField = config.xField || "label";
  const yField = config.yField || "value";

  const sanitizedData = useMemo(() => sanitizeData(data, [yField]), [data, yField]);

  if (!sanitizedData.length) {
    return (
      <VizCard title={title} description={description}>
        <EmptyState message="No data available for chart" />
      </VizCard>
    );
  }

  return (
    <VizCard title={title} description={description}>
      <div className="h-[450px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsAreaChart
            data={sanitizedData}
            margin={{ top: 25, right: 50, left: 60, bottom: 60 }}
          >
            <defs>
              {PRIMARY_PALETTE.map((color, idx) => (
                <linearGradient
                  key={`areaGrad${idx}`}
                  id={`areaGradient${idx}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="5%" stopColor={color} stopOpacity={0.35} />
                  <stop offset="50%" stopColor={color} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={color} stopOpacity={0.02} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.2} />
            <XAxis
              dataKey={xField}
              stroke="var(--muted-foreground)"
              fontSize={13}
              tickLine={{ stroke: "var(--border)" }}
              axisLine={{ stroke: "var(--border)", strokeWidth: 1 }}
              angle={-45}
              textAnchor="end"
              height={80}
              tickFormatter={formatLabel}
            />
            <YAxis
              stroke="var(--muted-foreground)"
              fontSize={13}
              tickLine={{ stroke: "var(--border)" }}
              axisLine={{ stroke: "var(--border)", strokeWidth: 1 }}
              width={70}
              tickFormatter={formatValue}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: "var(--muted)", strokeWidth: 1, strokeDasharray: "5 5" }}
            />
            <Area
              type="monotone"
              dataKey={yField}
              stroke={PRIMARY_PALETTE[0]}
              strokeWidth={3}
              fill={`url(#areaGradient0)`}
              animationDuration={1200}
              animationEasing="ease-in-out"
              dot={{ fill: "var(--background)", stroke: PRIMARY_PALETTE[0], strokeWidth: 2, r: 5 }}
              activeDot={{ r: 8, strokeWidth: 3 }}
            />
          </RechartsAreaChart>
        </ResponsiveContainer>
      </div>
    </VizCard>
  );
};

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

export const MetricCardViz = ({ viz, index = 0 }) => {
  const { data = {}, title, description } = viz;
  const { value, delta, unit } = data;

  // Teal + Deep Navy metric card accent colors
  const brightColors = [
    { color: "#0ea5e9", light: "#38bdf8" }, // Sky
    { color: "#14b8a6", light: "#2dd4bf" }, // Teal
    { color: "#6366f1", light: "#818cf8" }, // Indigo
    { color: "#f59e0b", light: "#fbbf24" }, // Amber
    { color: "#10b981", light: "#34d399" }, // Emerald
    { color: "#8b5cf6", light: "#a78bfa" }, // Violet
    { color: "#06b6d4", light: "#22d3ee" }, // Cyan
    { color: "#0e7490", light: "#0891b2" }, // Deep Teal
  ];
  const selectedColor = brightColors[index % brightColors.length];

  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (typeof value === "number") {
      const duration = 1500;
      const steps = 70;
      const increment = value / steps;
      let current = 0;
      const interval = setInterval(() => {
        current += increment;
        if (current >= value) {
          setDisplayValue(value);
          clearInterval(interval);
        } else {
          setDisplayValue(Math.round(current * 10) / 10);
        }
      }, duration / steps);
      return () => clearInterval(interval);
    } else {
      setDisplayValue(value ?? "—");
    }
  }, [value]);

  const TrendIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const trendColor =
    delta > 0 ? "text-emerald-500" : delta < 0 ? "text-red-500" : "text-muted-foreground";

  // Determine if value is text (non-numeric) for responsive font sizing
  const isTextValue = typeof displayValue === "string" && isNaN(Number(displayValue));
  const isLongText = isTextValue && String(displayValue).length > 8;

  return (
    <VizCard title={title} description={description}>
      <div className="flex items-end justify-between py-4 overflow-hidden">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.2 }}
          className="flex items-baseline gap-2 min-w-0 flex-1"
        >
          <span
            className={`font-bold truncate ${
              isLongText 
                ? "text-2xl sm:text-3xl" 
                : isTextValue 
                  ? "text-3xl sm:text-4xl" 
                  : "text-4xl sm:text-5xl"
            }`}
            style={{
              background: `linear-gradient(135deg, ${selectedColor.color}, ${selectedColor.light})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
            title={String(displayValue)}
          >
            {formatValue(displayValue)}
          </span>
          {unit && <span className="text-lg sm:text-xl font-semibold text-muted-foreground flex-shrink-0">{unit}</span>}
        </motion.div>

        {typeof delta === "number" && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.3 }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${
              delta > 0
                ? "bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 border-2 border-emerald-500/40"
                : delta < 0
                  ? "bg-gradient-to-r from-red-500/20 to-red-600/20 border-2 border-red-500/40"
                  : "bg-muted/50"
            } shadow-lg ${trendColor}`}
          >
            <TrendIcon size={20} />
            <span className="text-base font-semibold">
              {delta > 0 ? "+" : ""}
              {delta}%
            </span>
          </motion.div>
        )}
      </div>
    </VizCard>
  );
};

// ============================================================================
// DATA TABLE COMPONENT
// ============================================================================

export const DataTableViz = ({ viz }) => {
  const { data = {}, title, description, config = {} } = viz;
  const columns = data.columns || [];
  const rows = data.rows || [];
  const pageSize = config.pageSize || 20;

  const [page, setPage] = useState(0);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });
  const [isExpanded, setIsExpanded] = useState(false);

  // Download CSV function
  const downloadCSV = () => {
    const csvContent = [
      // Header row
      normalizedColumns.map((col) => `"${col.label}"`).join(","),
      // Data rows
      ...sortedRows.map((row) =>
        normalizedColumns
          .map((col) => {
            const value = row[col.key];
            const displayValue = Array.isArray(value) ? value.join("; ") : (value ?? "");
            return `"${String(displayValue).replace(/"/g, '""')}"`;
          })
          .join(","),
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `${title || "data"}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const normalizedColumns = useMemo(() => {
    return columns
      .map((col) => {
        if (typeof col === "string") {
          return { key: col, label: formatLabel(col) };
        }
        return {
          key: col.key || col.field || col.name,
          label: col.label || formatLabel(col.key || col.field || col.name),
          type: col.type,
        };
      })
      .filter((c) => c.key);
  }, [columns]);

  const sortedRows = useMemo(() => {
    if (!sortConfig.key) return rows;

    return [...rows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      // Special handling for phase labels
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();

      if (aStr.includes("phase") && bStr.includes("phase")) {
        const aPhaseMatch = aStr.match(/phase[\s_-]*(\d+|i+|iv?)/);
        const bPhaseMatch = bStr.match(/phase[\s_-]*(\d+|i+|iv?)/);

        if (aPhaseMatch && bPhaseMatch) {
          const numMap = { i: 1, ii: 2, iii: 3, iv: 4 };
          const aNum = numMap[aPhaseMatch[1]] || parseInt(aPhaseMatch[1]) || 0;
          const bNum = numMap[bPhaseMatch[1]] || parseInt(bPhaseMatch[1]) || 0;
          return sortConfig.direction === "asc" ? aNum - bNum : bNum - aNum;
        }
      }

      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortConfig.direction === "asc" ? aVal - bVal : bVal - aVal;
      }

      const comparison = String(aVal).localeCompare(String(bVal));
      return sortConfig.direction === "asc" ? comparison : -comparison;
    });
  }, [rows, sortConfig.key, sortConfig.direction]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const currentRows = sortedRows.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  if (!normalizedColumns.length || !rows.length) {
    return (
      <VizCard title={title} description={description} icon={TableIcon}>
        <EmptyState message="No data available for table" />
      </VizCard>
    );
  }

  return (
    <>
      <VizCard title={title} description={description} icon={TableIcon} className="overflow-hidden">
        {/* Action Buttons */}
        <div className="flex gap-2 mb-4 -mt-2">
          <motion.button
            onClick={downloadCSV}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors text-sm font-medium"
          >
            <Download size={16} />
            Download CSV
          </motion.button>
          <motion.button
            onClick={() => setIsExpanded(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors text-sm font-medium"
          >
            <Maximize2 size={16} />
            Expand View
          </motion.button>
        </div>

        <div className="overflow-x-auto -mx-5 px-5 shadow-inner bg-gradient-to-b from-muted/20 to-transparent rounded-xl">
          <table className="w-full text-sm border-separate border-spacing-0">
            <thead>
              <tr className="bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10">
                {normalizedColumns.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="text-left p-4 text-foreground font-bold whitespace-nowrap cursor-pointer hover:bg-primary/15 transition-all select-none first:rounded-tl-xl last:rounded-tr-xl border-b border-primary/20 backdrop-blur-sm"
                  >
                    <span className="flex items-center gap-2">
                      {col.label}
                      {sortConfig.key === col.key && (
                        <span className="text-base font-bold text-primary">
                          {sortConfig.direction === "asc" ? "↑" : "↓"}
                        </span>
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence mode="popLayout">
                {currentRows.map((row, rowIdx) => (
                  <motion.tr
                    key={`${page}-${rowIdx}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: rowIdx * 0.03, duration: 0.3 }}
                    className={`border-b border-border/30 hover:bg-primary/10 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] ${
                      rowIdx % 2 === 0 ? "bg-muted/20" : "bg-transparent"
                    }`}
                  >
                    {normalizedColumns.map((col, colIdx) => {
                      const cellValue = row[col.key];
                      const displayValue = Array.isArray(cellValue)
                        ? cellValue.join(", ")
                        : (cellValue ?? "—");

                    // Special handling for patent numbers - make them clickable links
                    if (col.key === "patent" && row.patentUrl) {
                      return (
                        <td
                          key={col.key}
                          className="p-4 text-foreground font-medium align-top max-w-[400px]"
                        >
                          <a
                            href={row.patentUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:text-primary/80 underline font-semibold transition-colors"
                            title={`View ${displayValue} on Google Patents`}
                          >
                            {displayValue}
                          </a>
                        </td>
                      );
                    }

                      // Columns that should wrap text instead of truncating
                      const wrapColumns = ['reason', 'nextStep', 'nextSteps', 'rationale', 'description', 'summary'];
                      const shouldWrap = wrapColumns.includes(col.key);

                      return (
                        <td
                          key={col.key}
                          className={`p-4 text-foreground font-medium align-top ${
                            shouldWrap ? "max-w-[300px]" : "max-w-[400px]"
                          } ${colIdx === 0 ? "font-semibold text-primary" : ""}`}
                          title={String(displayValue)}
                        >
                          <div className={shouldWrap ? "whitespace-normal break-words" : "truncate"}>
                            {displayValue}
                          </div>
                        </td>
                      );
                    })}
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-6 pt-5 border-t border-border/30">
            <span className="text-sm font-medium text-muted-foreground">
              Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, rows.length)} of{" "}
              <span className="text-foreground font-bold">{rows.length}</span>
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-2.5 rounded-xl border border-border hover:bg-primary/10 hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-sm font-bold text-foreground px-3 py-1 bg-muted/50 rounded-lg">
                {page + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-2.5 rounded-xl border border-border hover:bg-primary/10 hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </VizCard>

      {/* Expanded Modal View */}
      {isExpanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          onClick={() => setIsExpanded(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-background rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden border border-primary/20"
          >
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-primary/20 via-primary/10 to-primary/20 p-6 border-b border-primary/20 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-foreground flex items-center gap-3">
                  <TableIcon className="text-primary" size={28} />
                  {title || "Data Table"}
                </h3>
                {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
              </div>
              <div className="flex gap-2">
                <motion.button
                  onClick={downloadCSV}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
                >
                  <Download size={18} />
                  Download
                </motion.button>
                <motion.button
                  onClick={() => setIsExpanded(false)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg transition-colors"
                >
                  <X size={24} />
                </motion.button>
              </div>
            </div>

            {/* Modal Content - Scrollable Table */}
            <div className="overflow-auto p-6 max-h-[calc(90vh-180px)]">
              <table className="w-full text-sm border-separate border-spacing-0">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-gradient-to-r from-primary/15 via-primary/10 to-primary/15 backdrop-blur-lg">
                    {normalizedColumns.map((col) => (
                      <th
                        key={col.key}
                        onClick={() => handleSort(col.key)}
                        className="text-left p-4 text-foreground font-bold whitespace-nowrap cursor-pointer hover:bg-primary/20 transition-all border-b border-primary/20"
                      >
                        <span className="flex items-center gap-2">
                          {col.label}
                          {sortConfig.key === col.key && (
                            <span className="text-lg font-bold text-primary">
                              {sortConfig.direction === "asc" ? "↑" : "↓"}
                            </span>
                          )}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row, rowIdx) => (
                    <tr
                      key={rowIdx}
                      className={`border-b border-border/30 hover:bg-primary/10 transition-all ${
                        rowIdx % 2 === 0 ? "bg-muted/20" : "bg-transparent"
                      }`}
                    >
                      {normalizedColumns.map((col, colIdx) => {
                        const cellValue = row[col.key];
                        const displayValue = Array.isArray(cellValue)
                          ? cellValue.join(", ")
                          : (cellValue ?? "—");

                        return (
                          <td
                            key={col.key}
                            className={`p-4 text-foreground font-medium align-top ${
                              colIdx === 0 ? "font-semibold text-primary" : ""
                            }`}
                            title={String(displayValue)}
                          >
                            {displayValue}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Modal Footer */}
            <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10 p-4 border-t border-primary/20">
              <p className="text-sm text-muted-foreground text-center">
                Showing all <span className="font-bold text-foreground">{sortedRows.length}</span>{" "}
                rows
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </>
  );
};

// ============================================================================
// EMPTY STATE COMPONENT
// ============================================================================

const EmptyState = ({ message = "No data available" }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <AlertCircle size={32} className="text-muted-foreground mb-3" />
    <p className="text-sm text-muted-foreground">{message}</p>
  </div>
);

// ============================================================================
// IMAGE VISUALIZATION - Renders images with captions (Enhanced for Statista)
// ============================================================================

const ImageViz = ({ viz }) => {
  const { data, title, description } = viz;
  const imageUrl = data?.imageUrl || data?.content;
  const caption = data?.caption || description;
  const sourceUrl = data?.sourceUrl;
  const source = data?.source || "Statista";
  const premium = data?.premium;
  const [imageLoaded, setImageLoaded] = React.useState(false);
  const [imageError, setImageError] = React.useState(false);

  if (!imageUrl) {
    return (
      <VizCard title={title || "Image"}>
        <EmptyState message="No image URL provided" />
      </VizCard>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-card via-card/95 to-card/90 border border-white/[0.06] rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl hover:border-primary/20 transition-all duration-300"
    >
      {/* Header */}
      <div className="p-4 border-b border-border/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-foreground line-clamp-2">
              {title || "Market Research"}
            </h3>
            {caption && caption !== title && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{caption}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {premium && (
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full font-medium">
                Premium
              </span>
            )}
            <span className="text-[10px] px-2 py-0.5 bg-primary/20 text-primary rounded-full font-medium">
              {source}
            </span>
          </div>
        </div>
      </div>
      
      {/* Image Container */}
      <div className="relative bg-white">
        {/* Loading skeleton */}
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 bg-muted animate-pulse flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin mx-auto mb-2"></div>
              <p className="text-xs text-muted-foreground">Loading infographic...</p>
            </div>
          </div>
        )}
        
        <img
          src={imageUrl}
          alt={title || "Market Infographic"}
          className={`w-full h-auto transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => {
            setImageError(true);
            setImageLoaded(true);
          }}
        />
        
        {/* Error state */}
        {imageError && (
          <div className="flex flex-col items-center justify-center py-16 bg-muted">
            <AlertCircle size={40} className="text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-2">Unable to load infographic</p>
            {sourceUrl && (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline"
              >
                View on {source} →
              </a>
            )}
          </div>
        )}
      </div>
      
      {/* Footer */}
      {sourceUrl && !imageError && (
        <div className="p-3 bg-muted/30 border-t border-border/30 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Source: {source}
          </span>
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline inline-flex items-center gap-1 font-medium"
          >
            View Full Report →
          </a>
        </div>
      )}
    </motion.div>
  );
};

// ============================================================================
// TEXT VISUALIZATION - Beautiful text-only display
// ============================================================================

const TextViz = ({ viz }) => {
  const { title, description, data } = viz;
  
  // Content can be at viz.content or viz.data.content
  const content = viz.content || data?.content;

  // Parse content - can be a string or structured data
  const renderContent = () => {
    // If no content but we have description, just show description (it's already displayed in VizCard)
    if (!content) {
      // Just return null - description is already shown in VizCard header
      return null;
    }

    // If content is a string, render as paragraphs
    if (typeof content === "string") {
      // Split by double newline for paragraphs, or single newline for bullet points
      const lines = content.split("\n");
      const hasBullets = lines.some(line => line.trim().startsWith("•") || line.trim().startsWith("-"));
      const hasNumbered = lines.some(line => /^\d+[\.\)]\s/.test(line.trim()));
      
      if (hasBullets || hasNumbered) {
        return (
          <div className="space-y-2">
            {lines.map((line, idx) => {
              const trimmed = line.trim();
              if (!trimmed) return null;
              
              // Handle bullet points
              if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                const bulletText = trimmed.replace(/^[•\-]\s*/, "");
                return (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span className="text-foreground/90 leading-relaxed">{bulletText}</span>
                  </div>
                );
              }

              // Handle numbered items (e.g., "1. ...", "2) ...")
              const numberedMatch = trimmed.match(/^(\d+)[\.\)]\s+(.*)/);
              if (numberedMatch) {
                return (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="text-primary font-semibold min-w-[1.5rem] text-right">{numberedMatch[1]}.</span>
                    <span className="text-foreground/90 leading-relaxed">{numberedMatch[2]}</span>
                  </div>
                );
              }
              
              // Regular text
              return (
                <p key={idx} className="text-foreground/90 leading-relaxed">
                  {trimmed}
                </p>
              );
            })}
          </div>
        );
      }
      
      // Standard paragraph rendering
      return (
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {content.split("\n\n").map((paragraph, idx) => (
            <p key={idx} className="text-foreground/90 leading-relaxed mb-4 last:mb-0">
              {paragraph}
            </p>
          ))}
        </div>
      );
    }

    // If content is an array of sections/paragraphs
    if (Array.isArray(content)) {
      return (
        <div className="space-y-4">
          {content.map((item, idx) => {
            // Handle string items
            if (typeof item === "string") {
              return (
                <p key={idx} className="text-foreground/90 leading-relaxed">
                  {item}
                </p>
              );
            }

            // Handle object items with heading and text
            if (typeof item === "object" && item !== null) {
              return (
                <div key={idx} className="space-y-2">
                  {item.heading && (
                    <h4 className="font-semibold text-foreground">{item.heading}</h4>
                  )}
                  {item.text && (
                    <p className="text-foreground/90 leading-relaxed">{item.text}</p>
                  )}
                  {item.bullets && Array.isArray(item.bullets) && (
                    <ul className="list-disc list-inside space-y-1 text-foreground/80 ml-4">
                      {item.bullets.map((bullet, bIdx) => (
                        <li key={bIdx}>{bullet}</li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            }

            return null;
          })}
        </div>
      );
    }

    // If content is an object with sections
    if (typeof content === "object" && content !== null) {
      return (
        <div className="space-y-6">
          {Object.entries(content).map(([key, value], idx) => (
            <div key={idx} className="space-y-2">
              <h4 className="font-semibold text-foreground capitalize">
                {formatLabel(key)}
              </h4>
              {typeof value === "string" ? (
                <p className="text-foreground/90 leading-relaxed">{value}</p>
              ) : Array.isArray(value) ? (
                <ul className="list-disc list-inside space-y-1 text-foreground/80 ml-4">
                  {value.map((item, vIdx) => (
                    <li key={vIdx}>{typeof item === "string" ? item : JSON.stringify(item)}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-foreground/90 leading-relaxed">{JSON.stringify(value)}</p>
              )}
            </div>
          ))}
        </div>
      );
    }

    return null;
  };

  // Get the rendered content
  const renderedContent = renderContent();

  return (
    <VizCard title={title} description={!renderedContent ? description : undefined}>
      <div className="bg-gradient-to-br from-muted/30 to-muted/15 rounded-xl p-6 border border-white/[0.04]">
        {/* If we have rendered content, show it. Otherwise show description here */}
        {renderedContent || (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {description && description.split("\n").map((line, idx) => {
              const trimmed = line.trim();
              if (!trimmed) return null;
              
              if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                const bulletText = trimmed.replace(/^[•\-]\s*/, "");
                return (
                  <div key={idx} className="flex items-start gap-2 mb-2">
                    <span className="text-primary mt-0.5">•</span>
                    <span className="text-foreground/90 leading-relaxed">{bulletText}</span>
                  </div>
                );
              }

              // Handle numbered items (e.g., "1. ...", "2) ...")
              const numberedMatch = trimmed.match(/^(\d+)[\.\)]\s+(.*)/);
              if (numberedMatch) {
                return (
                  <div key={idx} className="flex items-start gap-3 mb-2">
                    <span className="text-primary font-semibold min-w-[1.5rem] text-right">{numberedMatch[1]}.</span>
                    <span className="text-foreground/90 leading-relaxed">{numberedMatch[2]}</span>
                  </div>
                );
              }
              
              return (
                <p key={idx} className="text-foreground/90 leading-relaxed mb-2 last:mb-0">
                  {trimmed}
                </p>
              );
            })}
          </div>
        )}
      </div>
    </VizCard>
  );
};

// ============================================================================
// VISUALIZATION RENDERER - Routes to correct component
// ============================================================================

export const VizRenderer = ({ viz }) => {
  if (!viz || !viz.vizType) {
    return <EmptyState message="Invalid visualization configuration" />;
  }

  const type = viz.vizType.toLowerCase();

  switch (type) {
    case "bar":
      return <BarChartViz viz={viz} />;
    case "pie":
      return <PieChartViz viz={viz} />;
    case "line":
      return <LineChartViz viz={viz} />;
    case "area":
      return <AreaChartViz viz={viz} />;
    case "table":
      return <DataTableViz viz={viz} />;
    case "card":
      return <MetricCardViz viz={viz} index={viz.index || 0} />;
    case "image":
      return <ImageViz viz={viz} />;
    case "text":
      return <TextViz viz={viz} />;
    default:
      return (
        <VizCard title={viz.title || "Unsupported Chart"}>
          <EmptyState message={`Chart type "${viz.vizType}" is not supported`} />
        </VizCard>
      );
  }
};

// ============================================================================
// VISUALIZATION LIST - Renders array of visualizations in logical vertical order
// ============================================================================

export const VizList = ({ visualizations = [], agentName, className = "" }) => {
  if (!visualizations?.length) return null;

  // Group visualizations by type for logical ordering
  const metricCards = visualizations.filter((v) => v.vizType?.toLowerCase() === "card");
  const textBlocks = visualizations.filter((v) => v.vizType?.toLowerCase() === "text");
  const images = visualizations.filter((v) => v.vizType?.toLowerCase() === "image");
  const barCharts = visualizations.filter((v) => v.vizType?.toLowerCase() === "bar");
  const pieCharts = visualizations.filter((v) => v.vizType?.toLowerCase() === "pie");
  const lineCharts = visualizations.filter((v) => v.vizType?.toLowerCase() === "line");
  const areaCharts = visualizations.filter((v) => v.vizType?.toLowerCase() === "area");
  const tables = visualizations.filter((v) => v.vizType?.toLowerCase() === "table");

  // Logical order: Cards → Text → Charts (Bar, Pie, Line, Area) → Images → Tables
  const orderedSections = [
    { type: "cards", items: metricCards, cols: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" },
    { type: "text", items: textBlocks, cols: "grid-cols-1" },
    { type: "bar", items: barCharts, cols: "grid-cols-1" },
    { type: "pie", items: pieCharts, cols: "grid-cols-1" },
    { type: "line", items: lineCharts, cols: "grid-cols-1" },
    { type: "area", items: areaCharts, cols: "grid-cols-1" },
    { type: "images", items: images, cols: "grid-cols-1 lg:grid-cols-2" },
    { type: "tables", items: tables, cols: "grid-cols-1" },
  ];

  return (
    <div className={`space-y-8 ${className}`}>
      {orderedSections.map(({ type, items, cols }, sectionIdx) => {
        if (!items.length) return null;

        return (
          <div key={type} className="space-y-6">
            <div className={`grid ${cols} gap-6`}>
              {items.map((viz, idx) => (
                <motion.div
                  key={viz.id || `${type}-${idx}`}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    delay: sectionIdx * 0.1 + idx * 0.05,
                    duration: 0.5,
                    ease: [0.4, 0, 0.2, 1],
                  }}
                  className="w-full"
                >
                  <VizRenderer viz={{ ...viz, index: idx }} />
                </motion.div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default VizList;

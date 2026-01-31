/**
 * Chart color palettes and utilities for consistent visualization
 */

// Severity color palette (matching Tailwind design tokens)
export const severityColors = {
  critical: {
    fill: "#dc2626", // red-600
    stroke: "#b91c1c", // red-700
    bg: "#fef2f2", // red-50
    text: "#991b1b", // red-800
  },
  high: {
    fill: "#ea580c", // orange-600
    stroke: "#c2410c", // orange-700
    bg: "#fff7ed", // orange-50
    text: "#9a3412", // orange-800
  },
  medium: {
    fill: "#ca8a04", // yellow-600
    stroke: "#a16207", // yellow-700
    bg: "#fefce8", // yellow-50
    text: "#854d0e", // yellow-800
  },
  low: {
    fill: "#16a34a", // green-600
    stroke: "#15803d", // green-700
    bg: "#f0fdf4", // green-50
    text: "#166534", // green-800
  },
  info: {
    fill: "#2563eb", // blue-600
    stroke: "#1d4ed8", // blue-700
    bg: "#eff6ff", // blue-50
    text: "#1e40af", // blue-800
  },
};

// Status color palette
export const statusColors = {
  open: "#3b82f6", // blue-500
  in_progress: "#f59e0b", // amber-500
  resolved: "#22c55e", // green-500
  closed: "#6b7280", // gray-500
  draft: "#94a3b8", // slate-400
  active: "#10b981", // emerald-500
  mitigated: "#8b5cf6", // violet-500
  accepted: "#06b6d4", // cyan-500
};

// Trend line colors
export const trendColors = {
  primary: "#3b82f6", // blue-500
  secondary: "#8b5cf6", // violet-500
  success: "#22c55e", // green-500
  warning: "#f59e0b", // amber-500
  danger: "#ef4444", // red-500
  neutral: "#6b7280", // gray-500
};

// Chart color sequences for multi-series charts
export const chartColorSequence = [
  "#3b82f6", // blue-500
  "#8b5cf6", // violet-500
  "#ec4899", // pink-500
  "#f59e0b", // amber-500
  "#10b981", // emerald-500
  "#06b6d4", // cyan-500
  "#ef4444", // red-500
  "#84cc16", // lime-500
];

// Gradient definitions for area charts
export const gradients = {
  blue: {
    start: "rgba(59, 130, 246, 0.3)",
    end: "rgba(59, 130, 246, 0.0)",
  },
  green: {
    start: "rgba(34, 197, 94, 0.3)",
    end: "rgba(34, 197, 94, 0.0)",
  },
  red: {
    start: "rgba(239, 68, 68, 0.3)",
    end: "rgba(239, 68, 68, 0.0)",
  },
  purple: {
    start: "rgba(139, 92, 246, 0.3)",
    end: "rgba(139, 92, 246, 0.0)",
  },
};

// Risk heatmap colors (5x5 matrix)
export const riskHeatmapColors = {
  1: "#22c55e", // green-500 (low)
  2: "#84cc16", // lime-500
  3: "#f59e0b", // amber-500
  4: "#f97316", // orange-500
  5: "#ef4444", // red-500 (critical)
};

// Calculate risk level from impact/likelihood (both 1-5)
export function getRiskLevel(impact: number, likelihood: number): number {
  const score = impact * likelihood;
  if (score <= 4) return 1;
  if (score <= 8) return 2;
  if (score <= 12) return 3;
  if (score <= 16) return 4;
  return 5;
}

// Get color for risk score
export function getRiskColor(impact: number, likelihood: number): string {
  const level = getRiskLevel(impact, likelihood);
  return riskHeatmapColors[level as keyof typeof riskHeatmapColors];
}

// Security score colors (gauge)
export const scoreColors = {
  excellent: "#22c55e", // 80-100
  good: "#84cc16", // 60-79
  fair: "#f59e0b", // 40-59
  poor: "#f97316", // 20-39
  critical: "#ef4444", // 0-19
};

export function getScoreColor(score: number): string {
  if (score >= 80) return scoreColors.excellent;
  if (score >= 60) return scoreColors.good;
  if (score >= 40) return scoreColors.fair;
  if (score >= 20) return scoreColors.poor;
  return scoreColors.critical;
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  if (score >= 20) return "Poor";
  return "Critical";
}

// SLA status colors
export const slaColors = {
  onTrack: "#22c55e", // green
  warning: "#f59e0b", // amber (75-100% time used)
  breached: "#ef4444", // red
};

// Analyst workload colors
export const workloadColors = {
  underloaded: "#3b82f6", // blue
  optimal: "#22c55e", // green
  heavy: "#f59e0b", // amber
  overloaded: "#ef4444", // red
};

export function getWorkloadColor(
  current: number,
  capacity: number
): string {
  const ratio = current / capacity;
  if (ratio < 0.5) return workloadColors.underloaded;
  if (ratio < 0.8) return workloadColors.optimal;
  if (ratio < 1.0) return workloadColors.heavy;
  return workloadColors.overloaded;
}

// Format helpers
export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)}m`;
  if (minutes < 1440) return `${(minutes / 60).toFixed(1)}h`;
  return `${(minutes / 1440).toFixed(1)}d`;
}

export function formatNumber(value: number): string {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toString();
}

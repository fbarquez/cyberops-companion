"use client";

import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import { trendColors } from "@/lib/chart-colors";
import { cn } from "@/lib/utils";

export interface SparkLineDataPoint {
  value: number;
}

interface SparkLineProps {
  data: SparkLineDataPoint[];
  color?: string;
  width?: number;
  height?: number;
  showTrend?: boolean;
  className?: string;
}

export function SparkLine({
  data,
  color = trendColors.primary,
  width = 100,
  height = 32,
  showTrend = true,
  className,
}: SparkLineProps) {
  if (!data || data.length < 2) {
    return (
      <div
        style={{ width, height }}
        className={cn("flex items-center justify-center", className)}
      >
        <span className="text-xs text-gray-400">No data</span>
      </div>
    );
  }

  // Calculate trend
  const firstValue = data[0].value;
  const lastValue = data[data.length - 1].value;
  const trend = lastValue - firstValue;
  const trendPercent = firstValue !== 0 ? ((trend / firstValue) * 100).toFixed(1) : "0";
  const isPositive = trend > 0;
  const isNeutral = trend === 0;

  // Dynamic color based on trend
  const lineColor = showTrend
    ? isNeutral
      ? trendColors.neutral
      : isPositive
      ? trendColors.success
      : trendColors.danger
    : color;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <ResponsiveContainer width={width} height={height}>
        <LineChart data={data}>
          <YAxis domain={["dataMin", "dataMax"]} hide />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      {showTrend && (
        <div
          className={cn(
            "text-xs font-medium whitespace-nowrap",
            isNeutral && "text-gray-500",
            isPositive && "text-green-600 dark:text-green-400",
            !isPositive && !isNeutral && "text-red-600 dark:text-red-400"
          )}
        >
          {isPositive ? "+" : ""}
          {trendPercent}%
        </div>
      )}
    </div>
  );
}

// Trend indicator without chart
export function TrendIndicator({
  current,
  previous,
  format = (v) => v.toString(),
  inverse = false, // For metrics where decrease is good
}: {
  current: number;
  previous: number;
  format?: (value: number) => string;
  inverse?: boolean;
}) {
  const diff = current - previous;
  const percent = previous !== 0 ? ((diff / previous) * 100).toFixed(1) : "0";
  const isPositive = inverse ? diff < 0 : diff > 0;
  const isNeutral = diff === 0;

  return (
    <div className="flex items-center gap-2">
      <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {format(current)}
      </span>
      <div
        className={cn(
          "flex items-center text-sm font-medium",
          isNeutral && "text-gray-500",
          isPositive && "text-green-600 dark:text-green-400",
          !isPositive && !isNeutral && "text-red-600 dark:text-red-400"
        )}
      >
        <svg
          className={cn(
            "w-4 h-4 mr-0.5",
            !isNeutral && (diff > 0 ? "" : "rotate-180")
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          {isNeutral ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 12h14"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 15l7-7 7 7"
            />
          )}
        </svg>
        {Math.abs(parseFloat(percent))}%
      </div>
    </div>
  );
}

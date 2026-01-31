"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SparkLine, TrendIndicator } from "../charts";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface TrendCardProps {
  title: string;
  value: number;
  previousValue?: number;
  sparklineData?: Array<{ value: number }>;
  format?: (value: number) => string;
  inverse?: boolean; // For metrics where decrease is good (e.g., incidents)
  icon?: LucideIcon;
  iconColor?: string;
  description?: string;
  className?: string;
}

export function TrendCard({
  title,
  value,
  previousValue,
  sparklineData,
  format = (v) => v.toString(),
  inverse = false,
  icon: Icon,
  iconColor = "text-blue-500",
  description,
  className,
}: TrendCardProps) {
  const hasTrend = previousValue !== undefined;
  const hasSparkline = sparklineData && sparklineData.length > 0;

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </CardTitle>
        {Icon && (
          <Icon className={cn("h-5 w-5", iconColor)} />
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div className="flex flex-col">
            {hasTrend ? (
              <TrendIndicator
                current={value}
                previous={previousValue!}
                format={format}
                inverse={inverse}
              />
            ) : (
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {format(value)}
              </span>
            )}
            {description && (
              <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {description}
              </span>
            )}
          </div>
          {hasSparkline && (
            <SparkLine
              data={sparklineData}
              showTrend={false}
              width={80}
              height={32}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Compact version for dashboard grids
export function TrendCardCompact({
  title,
  value,
  trend,
  trendLabel,
  icon: Icon,
  iconColor = "text-blue-500",
  className,
}: {
  title: string;
  value: string | number;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  icon?: LucideIcon;
  iconColor?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 p-4 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
        className
      )}
    >
      {Icon && (
        <div
          className={cn(
            "flex items-center justify-center w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700",
            iconColor
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
          {title}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {value}
          </span>
          {trend && trendLabel && (
            <span
              className={cn(
                "text-xs font-medium",
                trend === "up" && "text-green-600",
                trend === "down" && "text-red-600",
                trend === "neutral" && "text-gray-500"
              )}
            >
              {trendLabel}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

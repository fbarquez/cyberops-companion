"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChartCardProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  actions?: React.ReactNode;
  loading?: boolean;
  onRefresh?: () => void;
  className?: string;
  contentClassName?: string;
}

export function ChartCard({
  title,
  description,
  icon: Icon,
  children,
  actions,
  loading = false,
  onRefresh,
  className,
  contentClassName,
}: ChartCardProps) {
  return (
    <Card className={cn("relative", className)}>
      <CardHeader className="flex flex-col sm:flex-row sm:items-start sm:justify-between pb-2 gap-2">
        <div className="flex items-center gap-2">
          {Icon && (
            <Icon className="h-4 w-4 md:h-5 md:w-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
          )}
          <div>
            <CardTitle className="text-sm md:text-base font-semibold">
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-xs md:text-sm text-gray-500 dark:text-gray-400">
                {description}
              </CardDescription>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {actions}
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
              className="h-8 w-8 p-0"
            >
              <RefreshCw
                className={cn("h-4 w-4", loading && "animate-spin")}
              />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className={cn("relative", contentClassName)}>
        {loading ? (
          <div className="flex items-center justify-center h-48 md:h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}

// Security Score Gauge Card
export function ScoreGaugeCard({
  title,
  score,
  maxScore = 100,
  label,
  description,
  trend,
  className,
}: {
  title: string;
  score: number;
  maxScore?: number;
  label: string;
  description?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}) {
  const percentage = (score / maxScore) * 100;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getScoreColor = (pct: number) => {
    if (pct >= 80) return "#22c55e"; // green
    if (pct >= 60) return "#84cc16"; // lime
    if (pct >= 40) return "#f59e0b"; // amber
    if (pct >= 20) return "#f97316"; // orange
    return "#ef4444"; // red
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        {description && (
          <CardDescription>{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90">
              {/* Background circle */}
              <circle
                cx="64"
                cy="64"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="10"
                className="text-gray-200 dark:text-gray-700"
              />
              {/* Progress circle */}
              <circle
                cx="64"
                cy="64"
                r="45"
                fill="none"
                stroke={getScoreColor(percentage)}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-500 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {Math.round(score)}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {label}
              </span>
            </div>
          </div>
        </div>
        {trend && (
          <div className="flex justify-center mt-2">
            <span
              className={cn(
                "text-sm font-medium flex items-center gap-1",
                trend === "up" && "text-green-600",
                trend === "down" && "text-red-600",
                trend === "neutral" && "text-gray-500"
              )}
            >
              {trend === "up" && "↑ Improving"}
              {trend === "down" && "↓ Declining"}
              {trend === "neutral" && "→ Stable"}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// SLA Status Card
export function SLAStatusCard({
  title,
  compliant,
  total,
  breached,
  atRisk,
  className,
}: {
  title: string;
  compliant: number;
  total: number;
  breached: number;
  atRisk: number;
  className?: string;
}) {
  const complianceRate = total > 0 ? (compliant / total) * 100 : 0;

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {complianceRate.toFixed(1)}%
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Compliance Rate
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
          <div
            className={cn(
              "h-2 rounded-full transition-all",
              complianceRate >= 95 && "bg-green-500",
              complianceRate >= 80 && complianceRate < 95 && "bg-lime-500",
              complianceRate >= 60 && complianceRate < 80 && "bg-amber-500",
              complianceRate < 60 && "bg-red-500"
            )}
            style={{ width: `${complianceRate}%` }}
          />
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-green-600">
              {compliant}
            </div>
            <div className="text-xs text-gray-500">Compliant</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-amber-600">
              {atRisk}
            </div>
            <div className="text-xs text-gray-500">At Risk</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-red-600">
              {breached}
            </div>
            <div className="text-xs text-gray-500">Breached</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

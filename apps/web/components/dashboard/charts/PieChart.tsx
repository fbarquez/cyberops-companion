"use client";

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import {
  severityColors,
  statusColors,
  chartColorSequence,
  formatNumber,
  formatPercentage,
} from "@/lib/chart-colors";

export interface PieDataPoint {
  name: string;
  value: number;
  color?: string;
}

interface PieChartProps {
  data: PieDataPoint[];
  colorScheme?: "severity" | "status" | "auto" | "custom";
  showLegend?: boolean;
  showLabels?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  height?: number;
  formatValue?: (value: number) => string;
}

function getColorForName(name: string, scheme: string): string {
  const lowerName = name.toLowerCase();

  if (scheme === "severity") {
    if (lowerName.includes("critical")) return severityColors.critical.fill;
    if (lowerName.includes("high")) return severityColors.high.fill;
    if (lowerName.includes("medium")) return severityColors.medium.fill;
    if (lowerName.includes("low")) return severityColors.low.fill;
    if (lowerName.includes("info")) return severityColors.info.fill;
  }

  if (scheme === "status") {
    if (lowerName.includes("open")) return statusColors.open;
    if (lowerName.includes("progress") || lowerName.includes("active"))
      return statusColors.in_progress;
    if (lowerName.includes("resolved") || lowerName.includes("closed"))
      return statusColors.resolved;
    if (lowerName.includes("draft")) return statusColors.draft;
    if (lowerName.includes("mitigated")) return statusColors.mitigated;
    if (lowerName.includes("accepted")) return statusColors.accepted;
  }

  return chartColorSequence[0];
}

export function PieChart({
  data,
  colorScheme = "auto",
  showLegend = true,
  showLabels = false,
  innerRadius = 0,
  outerRadius = 80,
  height = 300,
  formatValue = formatNumber,
}: PieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  const enrichedData = data.map((item, index) => ({
    ...item,
    fill:
      item.color ||
      (colorScheme === "custom" || colorScheme === "auto"
        ? chartColorSequence[index % chartColorSequence.length]
        : getColorForName(item.name, colorScheme)),
    percentage: total > 0 ? (item.value / total) * 100 : 0,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;

    const item = payload[0].payload;
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {item.name}
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {formatValue(item.value)} ({formatPercentage(item.percentage)})
        </p>
      </div>
    );
  };

  const renderLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    name,
  }: any) => {
    if (percent < 0.05) return null; // Don't show labels for small slices

    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 1.2;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="currentColor"
        textAnchor={x > cx ? "start" : "end"}
        dominantBaseline="central"
        className="text-xs fill-gray-600 dark:fill-gray-400"
      >
        {name} ({formatPercentage(percent * 100)})
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={enrichedData}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={2}
          dataKey="value"
          label={showLabels ? renderLabel : undefined}
          labelLine={showLabels}
        >
          {enrichedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        {showLegend && (
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            formatter={(value, entry: any) => (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {value} ({formatValue(entry.payload.value)})
              </span>
            )}
          />
        )}
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}

// Donut chart variant
export function DonutChart(props: Omit<PieChartProps, "innerRadius">) {
  return <PieChart {...props} innerRadius={60} />;
}

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import {
  severityColors,
  statusColors,
  chartColorSequence,
  formatNumber,
} from "@/lib/chart-colors";

export interface DistributionDataPoint {
  name: string;
  value: number;
  color?: string;
}

interface DistributionChartProps {
  data: DistributionDataPoint[];
  colorScheme?: "severity" | "status" | "auto" | "custom";
  orientation?: "horizontal" | "vertical";
  showGrid?: boolean;
  showLegend?: boolean;
  height?: number;
  barSize?: number;
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

export function DistributionChart({
  data,
  colorScheme = "auto",
  orientation = "vertical",
  showGrid = true,
  showLegend = false,
  height = 300,
  barSize = 32,
  formatValue = formatNumber,
}: DistributionChartProps) {
  const enrichedData = data.map((item, index) => ({
    ...item,
    fill:
      item.color ||
      (colorScheme === "custom"
        ? chartColorSequence[index % chartColorSequence.length]
        : colorScheme === "auto"
        ? chartColorSequence[index % chartColorSequence.length]
        : getColorForName(item.name, colorScheme)),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;

    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {label || payload[0].payload.name}
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {formatValue(payload[0].value)}
        </p>
      </div>
    );
  };

  if (orientation === "horizontal") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={enrichedData} layout="vertical">
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={true}
              vertical={false}
              className="stroke-gray-200 dark:stroke-gray-700"
            />
          )}
          <XAxis
            type="number"
            tickFormatter={formatValue}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            width={100}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          <Bar dataKey="value" barSize={barSize} radius={[0, 4, 4, 0]}>
            {enrichedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={enrichedData}>
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={true}
            vertical={false}
            className="stroke-gray-200 dark:stroke-gray-700"
          />
        )}
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={formatValue}
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend />}
        <Bar dataKey="value" barSize={barSize} radius={[4, 4, 0, 0]}>
          {enrichedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  Legend,
} from "recharts";
import { trendColors, gradients, formatNumber } from "@/lib/chart-colors";

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendSeries {
  key: string;
  name: string;
  color?: string;
  data: TrendDataPoint[];
}

interface TrendLineChartProps {
  data: TrendDataPoint[];
  series?: TrendSeries[];
  xKey?: string;
  yKey?: string;
  color?: string;
  showArea?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  height?: number;
  formatYAxis?: (value: number) => string;
  formatTooltip?: (value: number) => string;
}

export function TrendLineChart({
  data,
  series,
  xKey = "date",
  yKey = "value",
  color = trendColors.primary,
  showArea = true,
  showGrid = true,
  showLegend = false,
  height = 300,
  formatYAxis = formatNumber,
  formatTooltip,
}: TrendLineChartProps) {
  const isSingleSeries = !series || series.length === 0;

  // For single series, transform data
  const chartData = isSingleSeries
    ? data
    : data.map((point) => {
        const result: Record<string, unknown> = { [xKey]: point.date };
        series?.forEach((s) => {
          const seriesPoint = s.data.find((d) => d.date === point.date);
          result[s.key] = seriesPoint?.value ?? 0;
        });
        return result;
      });

  // Build unique dates for multi-series
  const uniqueDates = isSingleSeries
    ? []
    : Array.from(
        new Set(series?.flatMap((s) => s.data.map((d) => d.date)) ?? [])
      ).sort();

  const multiSeriesData = isSingleSeries
    ? chartData
    : uniqueDates.map((date) => {
        const result: Record<string, unknown> = { date };
        series?.forEach((s) => {
          const point = s.data.find((d) => d.date === date);
          result[s.key] = point?.value ?? 0;
        });
        return result;
      });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;

    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
          {label}
        </p>
        {payload.map((entry: any, index: number) => (
          <p
            key={index}
            className="text-sm"
            style={{ color: entry.color }}
          >
            {entry.name}: {formatTooltip ? formatTooltip(entry.value) : formatNumber(entry.value)}
          </p>
        ))}
      </div>
    );
  };

  if (showArea && isSingleSeries) {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          )}
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            className="text-gray-500"
          />
          <YAxis
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            className="text-gray-500"
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={yKey}
            stroke={color}
            strokeWidth={2}
            fill={`url(#gradient-${color.replace('#', '')})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={isSingleSeries ? chartData : multiSeriesData}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        )}
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          className="text-gray-500"
        />
        <YAxis
          tickFormatter={formatYAxis}
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          className="text-gray-500"
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend />}
        {isSingleSeries ? (
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ) : (
          series?.map((s, index) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color ?? Object.values(trendColors)[index % Object.values(trendColors).length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

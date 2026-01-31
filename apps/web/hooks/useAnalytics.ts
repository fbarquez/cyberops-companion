"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";

// ============== Types ==============

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendResponse {
  entity: string;
  metric: string;
  period_days: number;
  aggregation: string;
  data: TrendDataPoint[];
  total?: number;
  average?: number;
  change_percentage?: number;
}

export interface DistributionDataPoint {
  name: string;
  value: number;
  percentage?: number;
  color?: string;
}

export interface DistributionResponse {
  entity: string;
  group_by: string;
  total: number;
  data: DistributionDataPoint[];
}

export interface HeatmapCell {
  x: number;
  y: number;
  value: number;
}

export interface RiskHeatmapResponse {
  type: string;
  total_risks: number;
  cells: HeatmapCell[];
  x_labels: string[];
  y_labels: string[];
}

export interface SecurityScoreComponent {
  name: string;
  weight: number;
  score: number;
  weighted_score: number;
  status: string;
  details?: Record<string, unknown>;
}

export interface SecurityScoreResponse {
  overall_score: number;
  grade: string;
  trend: string;
  components: SecurityScoreComponent[];
  calculated_at: string;
  recommendations?: string[];
}

export interface SLAMetric {
  severity: string;
  target_minutes: number;
  average_minutes: number;
  compliant_count: number;
  breached_count: number;
  at_risk_count: number;
  compliance_rate: number;
}

export interface SLAComplianceResponse {
  type: string;
  period_days: number;
  overall_compliance_rate: number;
  metrics: SLAMetric[];
  total_items: number;
  compliant_items: number;
  breached_items: number;
  at_risk_items: number;
}

export interface AnalystMetrics {
  analyst_id: string;
  analyst_name: string;
  alerts_assigned: number;
  alerts_resolved: number;
  cases_assigned: number;
  cases_closed: number;
  avg_response_time_minutes: number;
  avg_resolution_time_hours: number;
  false_positive_rate: number;
  workload_score: number;
  efficiency_score: number;
}

export interface AnalystMetricsResponse {
  period_days: number;
  total_analysts: number;
  analysts: AnalystMetrics[];
  team_averages: Record<string, number>;
  workload_distribution: DistributionDataPoint[];
}

export interface AgingBucket {
  bucket: string;
  count: number;
  by_severity: Record<string, number>;
}

export interface VulnerabilityAgingResponse {
  total_open: number;
  total_overdue: number;
  aging_buckets: AgingBucket[];
  overdue_by_severity: Record<string, number>;
  average_age_days: number;
  oldest_vulnerability_days: number;
}

export interface RiskTrendPoint {
  date: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  average_score: number;
}

export interface RiskTrendsResponse {
  period_days: number;
  current_totals: Record<string, number>;
  trend_data: RiskTrendPoint[];
  risk_velocity: number;
  mitigation_rate: number;
}

// ============== Hooks ==============

export function useTrend(
  entity: string,
  metric: string,
  periodDays: number = 30,
  aggregation: string = "daily"
) {
  const { token } = useAuthStore();

  return useQuery<TrendResponse>({
    queryKey: ["analytics", "trend", entity, metric, periodDays, aggregation],
    queryFn: () =>
      analyticsAPI.getTrend(token!, entity, metric, periodDays, aggregation) as Promise<TrendResponse>,
    enabled: !!token,
    staleTime: 60000, // 1 minute
  });
}

export function useDistribution(entity: string, groupBy: string) {
  const { token } = useAuthStore();

  return useQuery<DistributionResponse>({
    queryKey: ["analytics", "distribution", entity, groupBy],
    queryFn: () => analyticsAPI.getDistribution(token!, entity, groupBy) as Promise<DistributionResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useHeatmap(type: string) {
  const { token } = useAuthStore();

  return useQuery<RiskHeatmapResponse>({
    queryKey: ["analytics", "heatmap", type],
    queryFn: () => analyticsAPI.getHeatmap(token!, type) as Promise<RiskHeatmapResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useSecurityScore() {
  const { token } = useAuthStore();

  return useQuery<SecurityScoreResponse>({
    queryKey: ["analytics", "security-score"],
    queryFn: () => analyticsAPI.getSecurityScore(token!) as Promise<SecurityScoreResponse>,
    enabled: !!token,
    staleTime: 60000,
    refetchInterval: 300000, // 5 minutes
  });
}

export function useSecurityScoreHistory(periodDays: number = 30) {
  const { token } = useAuthStore();

  return useQuery({
    queryKey: ["analytics", "security-score-history", periodDays],
    queryFn: () => analyticsAPI.getSecurityScoreHistory(token!, periodDays),
    enabled: !!token,
    staleTime: 300000,
  });
}

export function useSLACompliance(type: string, periodDays: number = 30) {
  const { token } = useAuthStore();

  return useQuery<SLAComplianceResponse>({
    queryKey: ["analytics", "sla", type, periodDays],
    queryFn: () => analyticsAPI.getSLACompliance(token!, type, periodDays) as Promise<SLAComplianceResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useSLABreaches(periodDays: number = 30) {
  const { token } = useAuthStore();

  return useQuery({
    queryKey: ["analytics", "sla-breaches", periodDays],
    queryFn: () => analyticsAPI.getSLABreaches(token!, periodDays),
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useAnalystMetrics(periodDays: number = 30) {
  const { token } = useAuthStore();

  return useQuery<AnalystMetricsResponse>({
    queryKey: ["analytics", "analyst-metrics", periodDays],
    queryFn: () => analyticsAPI.getAnalystMetrics(token!, periodDays) as Promise<AnalystMetricsResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useVulnerabilityAging() {
  const { token } = useAuthStore();

  return useQuery<VulnerabilityAgingResponse>({
    queryKey: ["analytics", "vulnerability-aging"],
    queryFn: () => analyticsAPI.getVulnerabilityAging(token!) as Promise<VulnerabilityAgingResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

export function useRiskTrends(periodDays: number = 30) {
  const { token } = useAuthStore();

  return useQuery<RiskTrendsResponse>({
    queryKey: ["analytics", "risk-trends", periodDays],
    queryFn: () => analyticsAPI.getRiskTrends(token!, periodDays) as Promise<RiskTrendsResponse>,
    enabled: !!token,
    staleTime: 60000,
  });
}

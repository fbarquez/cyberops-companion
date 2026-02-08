"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  TrendingUp,
  FileText,
  Shield,
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  ArrowRight,
  Landmark,
  Users,
  TestTube,
  Share2,
  ShieldAlert,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";

interface DashboardStats {
  total_assessments: number;
  completed_assessments: number;
  in_progress_assessments: number;
  draft_assessments: number;
  average_score: number;
  total_gaps: number;
  critical_gaps: number;
  by_entity_type: Record<string, number>;
  pillar_scores: Record<string, number>;
  recent_assessments: Array<{
    id: string;
    name: string;
    status: string;
    entity_type: string | null;
    overall_score: number;
    created_at: string | null;
  }>;
  compliance_trend: Array<{
    date: string | null;
    score: number;
    name: string;
  }>;
}

const STATUS_CONFIG = {
  draft: { label: "Draft", color: "bg-gray-100 text-gray-800", icon: FileText },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-800", icon: Clock },
  completed: { label: "Completed", color: "bg-green-100 text-green-800", icon: CheckCircle },
  archived: { label: "Archived", color: "bg-gray-100 text-gray-600", icon: FileText },
};

const PILLAR_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  ict_risk_management: { label: "ICT Risk Management", icon: ShieldCheck, color: "text-blue-600" },
  incident_reporting: { label: "Incident Reporting", icon: AlertTriangle, color: "text-orange-600" },
  resilience_testing: { label: "Resilience Testing", icon: TestTube, color: "text-purple-600" },
  third_party_risk: { label: "Third-Party Risk", icon: Users, color: "text-green-600" },
  information_sharing: { label: "Information Sharing", icon: Share2, color: "text-cyan-600" },
};

const ENTITY_TYPE_LABELS: Record<string, string> = {
  credit_institution: "Credit Institution",
  investment_firm: "Investment Firm",
  payment_institution: "Payment Institution",
  e_money_institution: "E-Money Institution",
  insurance_undertaking: "Insurance Undertaking",
  reinsurance_undertaking: "Reinsurance Undertaking",
  ucits_manager: "UCITS Manager",
  aifm: "AIFM",
  ccp: "Central Counterparty",
  csd: "Central Securities Depository",
  trading_venue: "Trading Venue",
  casp: "Crypto-Asset Service Provider",
  crowdfunding: "Crowdfunding Provider",
  cra: "Credit Rating Agency",
  pension_fund: "Pension Fund",
  ict_provider: "ICT Service Provider",
};

export function DORADashboard() {
  const { token } = useAuthStore();

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["dora-dashboard"],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/dora/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch dashboard stats");
      return response.json();
    },
    enabled: !!token,
  });

  const exportReport = (format: "json" | "csv") => {
    if (!stats) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === "json") {
      content = JSON.stringify(stats, null, 2);
      filename = `dora-dashboard-${new Date().toISOString().split("T")[0]}.json`;
      mimeType = "application/json";
    } else {
      const headers = ["Pillar", "Average Score"];
      const rows = Object.entries(stats.pillar_scores).map(([pillar, score]) => [
        PILLAR_CONFIG[pillar]?.label || pillar,
        score,
      ]);
      content = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      filename = `dora-dashboard-${new Date().toISOString().split("T")[0]}.csv`;
      mimeType = "text/csv";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-muted rounded-lg" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-green-600";
    if (score >= 70) return "text-lime-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBadge = (score: number) => {
    if (score >= 85) return { label: "Fully Compliant", color: "bg-green-100 text-green-800" };
    if (score >= 70) return { label: "Largely Compliant", color: "bg-lime-100 text-lime-800" };
    if (score >= 50) return { label: "Partially Compliant", color: "bg-yellow-100 text-yellow-800" };
    return { label: "Non-Compliant", color: "bg-red-100 text-red-800" };
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <TrendingUp className={`h-4 w-4 ${getScoreColor(stats.average_score)}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${getScoreColor(stats.average_score)}`}>
              {stats.average_score}%
            </div>
            <Progress value={stats.average_score} className="mt-2 h-2" />
            {stats.average_score > 0 && (
              <Badge className={`mt-2 ${getScoreBadge(stats.average_score).color}`}>
                {getScoreBadge(stats.average_score).label}
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Assessments</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_assessments}</div>
            <p className="text-xs text-muted-foreground">
              {stats.completed_assessments} completed, {stats.in_progress_assessments} in progress
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Gaps</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.total_gaps}</div>
            <p className="text-xs text-muted-foreground">
              {stats.critical_gaps} critical priority
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Gaps</CardTitle>
            <ShieldAlert className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.critical_gaps}</div>
            <p className="text-xs text-muted-foreground">
              require immediate attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Entity Types</CardTitle>
            <Landmark className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600">
              {Object.keys(stats.by_entity_type).length}
            </div>
            <p className="text-xs text-muted-foreground">
              covered in assessments
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Export Buttons */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={() => exportReport("csv")}>
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
        <Button variant="outline" size="sm" onClick={() => exportReport("json")}>
          <FileText className="h-4 w-4 mr-2" />
          Export JSON
        </Button>
      </div>

      {/* Pillar Scores */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance by Pillar</CardTitle>
          <CardDescription>Average scores across DORA&apos;s 5 pillars</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            {Object.entries(PILLAR_CONFIG).map(([key, config]) => {
              const score = stats.pillar_scores[key] || 0;
              const Icon = config.icon;
              return (
                <div key={key} className="text-center p-4 rounded-lg border">
                  <Icon className={`h-8 w-8 mx-auto mb-2 ${config.color}`} />
                  <p className="text-xs font-medium mb-1">{config.label}</p>
                  <p className={`text-2xl font-bold ${getScoreColor(score)}`}>
                    {score}%
                  </p>
                  <Progress value={score} className="mt-2 h-1" />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Assessment Status</CardTitle>
            <CardDescription>Distribution of assessments by status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { key: "draft", value: stats.draft_assessments },
                { key: "in_progress", value: stats.in_progress_assessments },
                { key: "completed", value: stats.completed_assessments },
              ].map(({ key, value }) => {
                const config = STATUS_CONFIG[key as keyof typeof STATUS_CONFIG];
                const percentage = stats.total_assessments > 0
                  ? (value / stats.total_assessments) * 100
                  : 0;

                return (
                  <div key={key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={config.color}>{config.label}</Badge>
                      </div>
                      <span className="text-sm font-medium">
                        {value} ({percentage.toFixed(0)}%)
                      </span>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Entity Type Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Entity Types</CardTitle>
            <CardDescription>Financial entities assessed under DORA</CardDescription>
          </CardHeader>
          <CardContent>
            {Object.keys(stats.by_entity_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(stats.by_entity_type).slice(0, 6).map(([type, count]) => {
                  const percentage = stats.total_assessments > 0
                    ? (count / stats.total_assessments) * 100
                    : 0;

                  return (
                    <div key={type} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {ENTITY_TYPE_LABELS[type] || type.replace(/_/g, " ")}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {count} ({percentage.toFixed(0)}%)
                        </span>
                      </div>
                      <Progress value={percentage} className="h-1" />
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No entity types recorded yet. Complete assessments to see distribution.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Assessments */}
      {stats.recent_assessments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Assessments</CardTitle>
            <CardDescription>Latest DORA compliance assessments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_assessments.map((assessment) => {
                const statusConfig = STATUS_CONFIG[assessment.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.draft;

                return (
                  <div
                    key={assessment.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="space-y-1">
                        <p className="font-medium text-sm">{assessment.name}</p>
                        <div className="flex items-center gap-2">
                          <Badge className={statusConfig.color} variant="secondary">
                            {statusConfig.label}
                          </Badge>
                          {assessment.entity_type && (
                            <Badge variant="outline">
                              {ENTITY_TYPE_LABELS[assessment.entity_type] || assessment.entity_type}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {assessment.overall_score > 0 && (
                        <span className={`text-lg font-bold ${getScoreColor(assessment.overall_score)}`}>
                          {assessment.overall_score}%
                        </span>
                      )}
                      <Link href={`/compliance/regulatory/dora/${assessment.id}`}>
                        <Button variant="ghost" size="sm">
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Compliance Trend */}
      {stats.compliance_trend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Compliance Trend</CardTitle>
            <CardDescription>Scores from completed assessments over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.compliance_trend.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 rounded border">
                  <div className="flex items-center gap-3">
                    <CheckCircle className={`h-4 w-4 ${getScoreColor(item.score)}`} />
                    <div>
                      <p className="text-sm font-medium">{item.name}</p>
                      <p className="text-xs text-muted-foreground">{item.date}</p>
                    </div>
                  </div>
                  <span className={`text-lg font-bold ${getScoreColor(item.score)}`}>
                    {item.score}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* DORA Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">About DORA (EU 2022/2554)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-blue-600">5 Pillars</span>
              <p className="text-muted-foreground text-xs">
                ICT Risk, Incident Reporting, Testing, Third-Party, Information Sharing
              </p>
            </div>
            <div>
              <span className="font-medium text-green-600">28 Requirements</span>
              <p className="text-muted-foreground text-xs">
                Covering Articles 5-45 of the regulation
              </p>
            </div>
            <div>
              <span className="font-medium text-purple-600">20+ Entity Types</span>
              <p className="text-muted-foreground text-xs">
                From credit institutions to crypto-asset providers
              </p>
            </div>
            <div>
              <span className="font-medium text-red-600">Deadline</span>
              <p className="text-muted-foreground text-xs">
                Application date: January 17, 2025
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

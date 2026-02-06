"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  TrendingUp,
  FileText,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  ArrowRight,
  Building2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";

interface DashboardStats {
  total_assessments: number;
  completed_assessments: number;
  average_score: number;
  total_gaps: number;
  critical_gaps: number;
  by_status: {
    draft: number;
    in_progress: number;
    completed: number;
    archived: number;
  };
  by_entity_type: {
    essential: number;
    important: number;
    out_of_scope: number;
  };
  by_sector: Array<{
    sector: string;
    count: number;
    avg_score: number;
  }>;
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

const ENTITY_TYPE_CONFIG = {
  essential: { label: "Essential", color: "text-red-600", bgColor: "bg-red-100" },
  important: { label: "Important", color: "text-yellow-600", bgColor: "bg-yellow-100" },
  out_of_scope: { label: "Out of Scope", color: "text-gray-500", bgColor: "bg-gray-100" },
};

export function NIS2Dashboard() {
  const { token } = useAuthStore();

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["nis2-dashboard"],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/nis2/dashboard`, {
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
      filename = `nis2-dashboard-${new Date().toISOString().split("T")[0]}.json`;
      mimeType = "application/json";
    } else {
      const headers = ["Sector", "Assessment Count", "Average Score"];
      const rows = stats.by_sector.map((s) => [s.sector, s.count, s.avg_score]);
      content = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      filename = `nis2-dashboard-${new Date().toISOString().split("T")[0]}.csv`;
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
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    if (score >= 40) return "text-orange-600";
    return "text-red-600";
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
              {stats.completed_assessments} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Essential</CardTitle>
            <ShieldAlert className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.by_entity_type.essential}</div>
            <p className="text-xs text-muted-foreground">
              entities classified
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
              {stats.critical_gaps} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Important</CardTitle>
            <Shield className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.by_entity_type.important}</div>
            <p className="text-xs text-muted-foreground">
              entities classified
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

      <div className="grid gap-6 md:grid-cols-2">
        {/* Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Assessment Status</CardTitle>
            <CardDescription>Distribution of assessments by status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.by_status).map(([status, count]) => {
                const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG];
                const percentage = stats.total_assessments > 0
                  ? (count / stats.total_assessments) * 100
                  : 0;

                return (
                  <div key={status} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={config.color}>{config.label}</Badge>
                      </div>
                      <span className="text-sm font-medium">
                        {count} ({percentage.toFixed(0)}%)
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
            <CardTitle>Entity Classification</CardTitle>
            <CardDescription>Distribution by NIS2 entity type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.by_entity_type).map(([type, count]) => {
                const config = ENTITY_TYPE_CONFIG[type as keyof typeof ENTITY_TYPE_CONFIG];
                const percentage = stats.total_assessments > 0
                  ? (count / stats.total_assessments) * 100
                  : 0;

                return (
                  <div key={type} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${config.bgColor}`} />
                        <span className={`font-medium ${config.color}`}>{config.label}</span>
                      </div>
                      <span className="text-sm font-medium">
                        {count} ({percentage.toFixed(0)}%)
                      </span>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sector Breakdown */}
      {stats.by_sector.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Assessments by Sector</CardTitle>
            <CardDescription>Breakdown of assessments across NIS2 sectors</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.by_sector.map((sector) => (
                <div key={sector.sector} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium text-sm">
                        {sector.sector.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-muted-foreground">
                        {sector.count} assessment{sector.count !== 1 ? "s" : ""}
                      </span>
                      <span className={`font-bold ${getScoreColor(sector.avg_score)}`}>
                        {sector.avg_score}%
                      </span>
                    </div>
                  </div>
                  <Progress value={sector.avg_score} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Assessments */}
      {stats.recent_assessments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Assessments</CardTitle>
            <CardDescription>Latest NIS2 assessments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_assessments.map((assessment) => {
                const statusConfig = STATUS_CONFIG[assessment.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.draft;
                const entityConfig = assessment.entity_type
                  ? ENTITY_TYPE_CONFIG[assessment.entity_type as keyof typeof ENTITY_TYPE_CONFIG]
                  : null;

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
                          {entityConfig && (
                            <Badge variant="outline" className={entityConfig.color}>
                              {entityConfig.label}
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
                      <Link href={`/compliance/nis2/${assessment.id}`}>
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

      {/* NIS2 Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">About NIS2 Directive</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-red-600">Essential Entities</span>
              <p className="text-muted-foreground text-xs">
                Annex I sectors: Energy, Transport, Banking, Health, Digital Infrastructure, etc.
              </p>
            </div>
            <div>
              <span className="font-medium text-yellow-600">Important Entities</span>
              <p className="text-muted-foreground text-xs">
                Annex II sectors: Postal, Waste, Food, Manufacturing, Digital Providers, etc.
              </p>
            </div>
            <div>
              <span className="font-medium">Deadline</span>
              <p className="text-muted-foreground text-xs">
                Member states must transpose NIS2 by October 17, 2024
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

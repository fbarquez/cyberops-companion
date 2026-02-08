"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  TrendingUp,
  Link2,
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
  Activity,
  FileWarning,
  Zap,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/stores/auth-store";

interface ControlSummary {
  control_id: string;
  control_name: string;
  effectiveness_score: number;
  effectiveness_level: string;
  effectiveness_color: string;
  evidence_count: number;
  last_activity_date: string | null;
  trend: string | null;
}

interface FrameworkSummary {
  framework: string;
  name: string;
  overall_score: number;
  overall_level: string;
  controls_assessed: number;
  controls_total: number;
  controls_meeting_baseline: number;
}

interface EvidenceLink {
  id: string;
  control_framework: string;
  control_id: string;
  control_name: string | null;
  activity_type: string;
  activity_id: string;
  activity_title: string | null;
  evidence_strength: string;
  linked_at: string;
}

interface DashboardData {
  total_evidence_links: number;
  links_last_24h: number;
  links_last_7d: number;
  links_last_30d: number;
  frameworks: FrameworkSummary[];
  activities_linked: Record<string, number>;
  top_controls: ControlSummary[];
  controls_needing_attention: ControlSummary[];
  recent_evidence: EvidenceLink[];
  effectiveness_trend: Array<{
    date: string;
    score: number;
  }>;
}

const FRAMEWORK_COLORS: Record<string, string> = {
  iso27001: "from-blue-500 to-blue-600",
  dora: "from-purple-500 to-purple-600",
  nis2: "from-orange-500 to-orange-600",
  bsi_grundschutz: "from-green-500 to-green-600",
  gdpr: "from-red-500 to-red-600",
  tisax: "from-cyan-500 to-cyan-600",
};

const EFFECTIVENESS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  fully_effective: { bg: "bg-green-100", text: "text-green-700", border: "border-green-300" },
  largely_effective: { bg: "bg-blue-100", text: "text-blue-700", border: "border-blue-300" },
  partially_effective: { bg: "bg-yellow-100", text: "text-yellow-700", border: "border-yellow-300" },
  ineffective: { bg: "bg-red-100", text: "text-red-700", border: "border-red-300" },
  not_assessed: { bg: "bg-gray-100", text: "text-gray-700", border: "border-gray-300" },
};

const ACTIVITY_ICONS: Record<string, React.ReactNode> = {
  incident: <AlertTriangle className="h-4 w-4" />,
  alert: <Zap className="h-4 w-4" />,
  vulnerability_scan: <Shield className="h-4 w-4" />,
  playbook_execution: <Activity className="h-4 w-4" />,
  training_completion: <CheckCircle className="h-4 w-4" />,
  document_approval: <FileWarning className="h-4 w-4" />,
};

export function EvidenceBridgeDashboard() {
  const { token } = useAuthStore();

  const { data: dashboard, isLoading, refetch } = useQuery<DashboardData>({
    queryKey: ["evidence-bridge-dashboard"],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/evidence-bridge/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch dashboard");
      return response.json();
    },
    enabled: !!token,
  });

  const getScoreColor = (score: number) => {
    if (score >= 76) return "text-green-600";
    if (score >= 51) return "text-blue-600";
    if (score >= 26) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreLabel = (level: string) => {
    const labels: Record<string, string> = {
      fully_effective: "Fully Effective",
      largely_effective: "Largely Effective",
      partially_effective: "Partially Effective",
      ineffective: "Ineffective",
      not_assessed: "Not Assessed",
    };
    return labels[level] || level;
  };

  const formatActivityType = (type: string) => {
    return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
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

  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Evidence Links</CardTitle>
            <Link2 className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard.total_evidence_links}</div>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline" className="text-xs">
                +{dashboard.links_last_24h} today
              </Badge>
              <Badge variant="outline" className="text-xs">
                +{dashboard.links_last_7d} week
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Frameworks</CardTitle>
            <Shield className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard.frameworks.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active compliance frameworks
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Effectiveness</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {dashboard.frameworks.length > 0 ? (
              <>
                <div className={`text-3xl font-bold ${getScoreColor(
                  dashboard.frameworks.reduce((sum, f) => sum + f.overall_score, 0) / dashboard.frameworks.length
                )}`}>
                  {Math.round(
                    dashboard.frameworks.reduce((sum, f) => sum + f.overall_score, 0) / dashboard.frameworks.length
                  )}%
                </div>
                <Progress
                  value={dashboard.frameworks.reduce((sum, f) => sum + f.overall_score, 0) / dashboard.frameworks.length}
                  className="mt-2 h-2"
                />
              </>
            ) : (
              <div className="text-3xl font-bold text-muted-foreground">-</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Needs Attention</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {dashboard.controls_needing_attention.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Controls below baseline
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Refresh Button */}
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Framework Effectiveness Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Framework Effectiveness</CardTitle>
          <CardDescription>
            Control effectiveness across compliance frameworks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {dashboard.frameworks.map((fw) => (
              <Link
                key={fw.framework}
                href={`/compliance/assurance/bridge/${fw.framework}`}
              >
                <Card className="hover:shadow-md transition-all cursor-pointer">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg bg-gradient-to-br ${FRAMEWORK_COLORS[fw.framework] || "from-gray-500 to-gray-600"} text-white`}>
                          <Shield className="h-4 w-4" />
                        </div>
                        <span className="font-medium">{fw.name}</span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Score</span>
                        <span className={`text-lg font-bold ${getScoreColor(fw.overall_score)}`}>
                          {Math.round(fw.overall_score)}%
                        </span>
                      </div>
                      <Progress value={fw.overall_score} className="h-2" />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>{fw.controls_meeting_baseline}/{fw.controls_assessed} meeting baseline</span>
                        <Badge variant="outline" className="text-xs">
                          {getScoreLabel(fw.overall_level)}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Activities Linked */}
        <Card>
          <CardHeader>
            <CardTitle>Activities Linked</CardTitle>
            <CardDescription>Evidence by activity type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(dashboard.activities_linked)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 8)
                .map(([type, count]) => {
                  const total = Object.values(dashboard.activities_linked).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? (count / total) * 100 : 0;

                  return (
                    <div key={type} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {ACTIVITY_ICONS[type] || <Activity className="h-4 w-4" />}
                          <span className="text-sm">{formatActivityType(type)}</span>
                        </div>
                        <span className="text-sm font-medium">{count}</span>
                      </div>
                      <Progress value={percentage} className="h-1.5" />
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>

        {/* Controls Needing Attention */}
        <Card>
          <CardHeader>
            <CardTitle>Controls Needing Attention</CardTitle>
            <CardDescription>Controls with low effectiveness scores</CardDescription>
          </CardHeader>
          <CardContent>
            {dashboard.controls_needing_attention.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <ShieldCheck className="h-12 w-12 mb-2 text-green-500" />
                <p>All controls meeting baseline</p>
              </div>
            ) : (
              <div className="space-y-3">
                {dashboard.controls_needing_attention.slice(0, 5).map((control) => {
                  const levelConfig = EFFECTIVENESS_COLORS[control.effectiveness_level] || EFFECTIVENESS_COLORS.not_assessed;

                  return (
                    <div
                      key={`${control.control_id}`}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="h-4 w-4 text-yellow-600" />
                          <span className="font-medium text-sm">{control.control_id}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">{control.control_name}</p>
                      </div>
                      <div className="text-right">
                        <span className={`text-lg font-bold ${getScoreColor(control.effectiveness_score)}`}>
                          {Math.round(control.effectiveness_score)}%
                        </span>
                        <div className={`text-xs px-2 py-0.5 rounded ${levelConfig.bg} ${levelConfig.text}`}>
                          {getScoreLabel(control.effectiveness_level)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Top Performing Controls</CardTitle>
          <CardDescription>Controls with highest evidence coverage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {dashboard.top_controls.slice(0, 6).map((control) => {
              const levelConfig = EFFECTIVENESS_COLORS[control.effectiveness_level] || EFFECTIVENESS_COLORS.not_assessed;

              return (
                <div
                  key={`${control.control_id}`}
                  className={`p-4 rounded-lg border ${levelConfig.border} ${levelConfig.bg}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline">{control.control_id}</Badge>
                    <span className={`text-lg font-bold ${levelConfig.text}`}>
                      {Math.round(control.effectiveness_score)}%
                    </span>
                  </div>
                  <p className="text-sm font-medium truncate">{control.control_name}</p>
                  <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                    <span>{control.evidence_count} evidence items</span>
                    {control.trend && (
                      <Badge variant="outline" className="text-xs">
                        {control.trend}
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Evidence */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Evidence Links</CardTitle>
          <CardDescription>Latest activities linked to controls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dashboard.recent_evidence.slice(0, 10).map((link) => (
              <div
                key={link.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-muted">
                    {ACTIVITY_ICONS[link.activity_type] || <Activity className="h-4 w-4" />}
                  </div>
                  <div>
                    <p className="font-medium text-sm">
                      {link.activity_title || `${formatActivityType(link.activity_type)} ${link.activity_id.slice(0, 8)}`}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {link.control_framework.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {link.control_id}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      link.evidence_strength === "strong" ? "default" :
                      link.evidence_strength === "moderate" ? "secondary" : "outline"
                    }
                    className="text-xs"
                  >
                    {link.evidence_strength}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(link.linked_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200 dark:border-blue-800">
        <CardContent className="py-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Link2 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                ISMS ↔ SOC Evidence Bridge
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                This bridge automatically links operational activities (incidents, alerts, scans, etc.)
                to compliance controls. Control effectiveness is calculated from real operational evidence,
                enabling auditors to verify compliance through actual security operations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

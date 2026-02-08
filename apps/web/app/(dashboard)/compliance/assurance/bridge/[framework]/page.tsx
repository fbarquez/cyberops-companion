"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  ExternalLink,
  FileText,
  Activity,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

interface ControlEffectiveness {
  control_id: string;
  control_name: string;
  effectiveness_score: number;
  effectiveness_level: string;
  effectiveness_color: string;
  evidence_count: number;
  last_activity_date: string | null;
  trend: string | null;
}

interface FrameworkEffectiveness {
  framework: string;
  framework_name: string;
  overall_score: number;
  overall_level: string;
  controls_assessed: number;
  controls_total: number;
  controls_meeting_baseline: number;
  by_level: Record<string, number>;
  controls: ControlEffectiveness[];
  top_gaps: Array<{
    control_id: string;
    control_name: string;
    score: number;
    gap_type: string;
  }>;
}

const FRAMEWORK_NAMES: Record<string, string> = {
  iso27001: "ISO 27001:2022",
  dora: "DORA",
  nis2: "NIS2",
  bsi_grundschutz: "BSI IT-Grundschutz",
  gdpr: "GDPR",
  tisax: "TISAX",
};

const LEVEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  fully_effective: { bg: "bg-green-100 dark:bg-green-900", text: "text-green-700 dark:text-green-300", border: "border-green-300" },
  largely_effective: { bg: "bg-blue-100 dark:bg-blue-900", text: "text-blue-700 dark:text-blue-300", border: "border-blue-300" },
  partially_effective: { bg: "bg-yellow-100 dark:bg-yellow-900", text: "text-yellow-700 dark:text-yellow-300", border: "border-yellow-300" },
  ineffective: { bg: "bg-red-100 dark:bg-red-900", text: "text-red-700 dark:text-red-300", border: "border-red-300" },
  not_assessed: { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-700 dark:text-gray-300", border: "border-gray-300" },
};

export default function FrameworkEffectivenessPage() {
  const params = useParams();
  const framework = params.framework as string;
  const { token } = useAuthStore();

  const { data: effectiveness, isLoading, refetch } = useQuery<FrameworkEffectiveness>({
    queryKey: ["framework-effectiveness", framework],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/evidence-bridge/frameworks/${framework}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch framework effectiveness");
      return response.json();
    },
    enabled: !!token && !!framework,
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

  const getTrendIcon = (trend: string | null) => {
    if (!trend) return <Minus className="h-4 w-4 text-muted-foreground" />;
    if (trend === "improving") return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend === "declining") return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <Header title={`${FRAMEWORK_NAMES[framework] || framework} Effectiveness`}>
          <Link href="/compliance/assurance/bridge">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Bridge
            </Button>
          </Link>
        </Header>
        <div className="flex-1 p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-32 bg-muted rounded-lg" />
            <div className="grid gap-4 md:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-muted rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!effectiveness) return null;

  const controlsByLevel = {
    fully_effective: effectiveness.controls.filter((c) => c.effectiveness_level === "fully_effective"),
    largely_effective: effectiveness.controls.filter((c) => c.effectiveness_level === "largely_effective"),
    partially_effective: effectiveness.controls.filter((c) => c.effectiveness_level === "partially_effective"),
    ineffective: effectiveness.controls.filter((c) => c.effectiveness_level === "ineffective"),
    not_assessed: effectiveness.controls.filter((c) => c.effectiveness_level === "not_assessed"),
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={`${effectiveness.framework_name} Effectiveness`}>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Link href="/compliance/assurance/bridge">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Bridge
            </Button>
          </Link>
        </div>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {/* Overall Score Card */}
        <Card className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
          <CardContent className="py-6">
            <div className="grid gap-6 md:grid-cols-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Overall Score</p>
                <div className={`text-5xl font-bold ${getScoreColor(effectiveness.overall_score)}`}>
                  {Math.round(effectiveness.overall_score)}%
                </div>
                <Badge className="mt-2" variant="outline">
                  {getScoreLabel(effectiveness.overall_level)}
                </Badge>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Controls Assessed</p>
                <div className="text-3xl font-bold">
                  {effectiveness.controls_assessed}/{effectiveness.controls_total}
                </div>
                <Progress
                  value={(effectiveness.controls_assessed / effectiveness.controls_total) * 100}
                  className="mt-2 h-2"
                />
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Meeting Baseline</p>
                <div className="text-3xl font-bold text-green-600">
                  {effectiveness.controls_meeting_baseline}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  of {effectiveness.controls_assessed} assessed
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Below Baseline</p>
                <div className="text-3xl font-bold text-yellow-600">
                  {effectiveness.controls_assessed - effectiveness.controls_meeting_baseline}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  need attention
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Level Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Effectiveness Distribution</CardTitle>
            <CardDescription>Controls by effectiveness level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-5">
              {Object.entries(LEVEL_COLORS).map(([level, colors]) => {
                const count = effectiveness.by_level[level] || 0;
                const percentage = effectiveness.controls_total > 0
                  ? (count / effectiveness.controls_total) * 100
                  : 0;

                return (
                  <div
                    key={level}
                    className={`p-4 rounded-lg ${colors.bg} ${colors.border} border`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-2xl font-bold ${colors.text}`}>{count}</span>
                      <span className="text-sm text-muted-foreground">{percentage.toFixed(0)}%</span>
                    </div>
                    <p className={`text-sm font-medium ${colors.text}`}>
                      {getScoreLabel(level)}
                    </p>
                    <Progress value={percentage} className="mt-2 h-1" />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Top Gaps */}
        {effectiveness.top_gaps.length > 0 && (
          <Card className="border-yellow-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                Top Gaps to Address
              </CardTitle>
              <CardDescription>Controls requiring immediate attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {effectiveness.top_gaps.map((gap) => (
                  <div
                    key={gap.control_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800"
                  >
                    <div className="flex items-center gap-3">
                      <ShieldAlert className="h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="font-medium">{gap.control_id}</p>
                        <p className="text-sm text-muted-foreground">{gap.control_name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-lg font-bold ${getScoreColor(gap.score)}`}>
                        {Math.round(gap.score)}%
                      </span>
                      <Badge variant="outline" className="ml-2 text-xs">
                        {gap.gap_type}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Controls by Level */}
        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">All Controls ({effectiveness.controls.length})</TabsTrigger>
            <TabsTrigger value="fully_effective" className="text-green-600">
              Fully Effective ({controlsByLevel.fully_effective.length})
            </TabsTrigger>
            <TabsTrigger value="largely_effective" className="text-blue-600">
              Largely ({controlsByLevel.largely_effective.length})
            </TabsTrigger>
            <TabsTrigger value="needs_attention" className="text-yellow-600">
              Needs Attention ({controlsByLevel.partially_effective.length + controlsByLevel.ineffective.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <ControlsGrid controls={effectiveness.controls} getScoreColor={getScoreColor} getTrendIcon={getTrendIcon} />
          </TabsContent>

          <TabsContent value="fully_effective">
            <ControlsGrid controls={controlsByLevel.fully_effective} getScoreColor={getScoreColor} getTrendIcon={getTrendIcon} />
          </TabsContent>

          <TabsContent value="largely_effective">
            <ControlsGrid controls={controlsByLevel.largely_effective} getScoreColor={getScoreColor} getTrendIcon={getTrendIcon} />
          </TabsContent>

          <TabsContent value="needs_attention">
            <ControlsGrid
              controls={[...controlsByLevel.partially_effective, ...controlsByLevel.ineffective]}
              getScoreColor={getScoreColor}
              getTrendIcon={getTrendIcon}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function ControlsGrid({
  controls,
  getScoreColor,
  getTrendIcon,
}: {
  controls: ControlEffectiveness[];
  getScoreColor: (score: number) => string;
  getTrendIcon: (trend: string | null) => React.ReactNode;
}) {
  if (controls.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No controls in this category</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {controls.map((control) => {
        const levelConfig = LEVEL_COLORS[control.effectiveness_level] || LEVEL_COLORS.not_assessed;

        return (
          <Card key={control.control_id} className={`${levelConfig.border} border`}>
            <CardContent className="pt-4">
              <div className="flex items-start justify-between mb-3">
                <Badge variant="outline">{control.control_id}</Badge>
                <div className="flex items-center gap-2">
                  {getTrendIcon(control.trend)}
                  <span className={`text-xl font-bold ${getScoreColor(control.effectiveness_score)}`}>
                    {Math.round(control.effectiveness_score)}%
                  </span>
                </div>
              </div>
              <p className="text-sm font-medium mb-3 line-clamp-2">{control.control_name}</p>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  <span>{control.evidence_count} evidence</span>
                </div>
                {control.last_activity_date && (
                  <span>
                    Last: {new Date(control.last_activity_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              <Progress value={control.effectiveness_score} className="mt-3 h-1.5" />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronRight,
  Download,
  RefreshCw,
  FileText,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { complianceAPI, incidentsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface ValidationResult {
  framework_id: string;
  framework_name: string;
  phase: string;
  is_compliant: boolean;
  score: number;
  checks: ComplianceCheck[];
  gaps: string[];
  recommendations: string[];
  timestamp: string;
}

interface ComplianceCheck {
  control_id: string;
  control_name: string;
  status: "passed" | "failed" | "partial" | "not_applicable";
  evidence: string[];
  notes: string;
}

interface UnifiedControl {
  id: string;
  name: string;
  description: string;
  phase: string;
  mappings: {
    bsi?: string[];
    nist?: string[];
    iso27001?: string[];
    owasp?: string[];
  };
}

export default function CompliancePage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([
    "bsi",
    "nist",
    "iso27001",
  ]);
  const [activePhase, setActivePhase] = useState<string>("detection");

  // Fetch frameworks
  const { data: frameworks, isLoading: frameworksLoading } = useQuery({
    queryKey: ["compliance-frameworks"],
    queryFn: () => complianceAPI.getFrameworks(token!),
    enabled: !!token,
  });

  // Fetch incident to get current phase
  const { data: incident } = useQuery({
    queryKey: ["incident", incidentId],
    queryFn: () => incidentsAPI.get(token!, incidentId),
    enabled: !!token && !!incidentId,
  });

  // Fetch validation results for selected frameworks
  const { data: validationResults, isLoading: validationLoading, refetch: refetchValidation } = useQuery({
    queryKey: ["compliance-validation", incidentId, selectedFrameworks],
    queryFn: () => complianceAPI.validateIncident(token!, incidentId, selectedFrameworks),
    enabled: !!token && !!incidentId && selectedFrameworks.length > 0,
  });

  // Fetch cross-framework mapping
  const { data: crossMapping } = useQuery({
    queryKey: ["compliance-cross-mapping"],
    queryFn: () => complianceAPI.getCrossMapping(token!),
    enabled: !!token,
  });

  // Export report mutation
  const exportMutation = useMutation({
    mutationFn: (format: string) => complianceAPI.exportReport(token!, incidentId, selectedFrameworks, format),
    onSuccess: (data: any) => {
      // Download the report
      const blob = new Blob([data.content || data], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compliance-report-${incidentId}.md`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Report exported successfully");
    },
    onError: () => {
      toast.error("Failed to export report");
    },
  });

  const frameworkList = (frameworks as any[]) || [];
  const results = (validationResults as Record<string, Record<string, ValidationResult>>) || {};
  const mappings = (crossMapping as { unified_controls: UnifiedControl[] }) || { unified_controls: [] };

  // Calculate overall compliance score
  const overallScore = useMemo(() => {
    if (!results || Object.keys(results).length === 0) return null;

    let totalScore = 0;
    let count = 0;

    Object.values(results).forEach((phaseResults: any) => {
      Object.values(phaseResults).forEach((result: any) => {
        if (result?.score !== undefined) {
          totalScore += result.score;
          count++;
        }
      });
    });

    return count > 0 ? Math.round(totalScore / count) : null;
  }, [results]);

  // Calculate per-framework scores
  const frameworkScores = useMemo(() => {
    if (!results || Object.keys(results).length === 0) return {};

    const scores: Record<string, { score: number; count: number }> = {};

    Object.values(results).forEach((phaseResults: any) => {
      Object.entries(phaseResults).forEach(([frameworkId, result]: [string, any]) => {
        if (result?.score !== undefined) {
          if (!scores[frameworkId]) {
            scores[frameworkId] = { score: 0, count: 0 };
          }
          scores[frameworkId].score += result.score;
          scores[frameworkId].count++;
        }
      });
    });

    const avgScores: Record<string, number> = {};
    Object.entries(scores).forEach(([frameworkId, { score, count }]) => {
      avgScores[frameworkId] = Math.round(score / count);
    });

    return avgScores;
  }, [results]);

  // Extract all gaps from validation results
  const allGaps = useMemo(() => {
    if (!results || Object.keys(results).length === 0) return [];

    const gaps: Array<{
      title: string;
      description: string;
      severity: "high" | "medium" | "low";
      frameworks: string[];
      phase: string;
    }> = [];

    Object.entries(results).forEach(([phase, phaseResults]: [string, any]) => {
      Object.entries(phaseResults).forEach(([frameworkId, result]: [string, any]) => {
        if (result?.gaps) {
          result.gaps.forEach((gap: string) => {
            const existingGap = gaps.find((g) => g.title === gap);
            if (existingGap) {
              if (!existingGap.frameworks.includes(frameworkId)) {
                existingGap.frameworks.push(frameworkId);
              }
            } else {
              gaps.push({
                title: gap,
                description: result.recommendations?.find((r: string) => r.toLowerCase().includes(gap.toLowerCase().split(" ")[0])) || "Address this compliance gap",
                severity: result.score < 50 ? "high" : result.score < 75 ? "medium" : "low",
                frameworks: [frameworkId],
                phase,
              });
            }
          });
        }
      });
    });

    return gaps.sort((a, b) => {
      const severityOrder = { high: 0, medium: 1, low: 2 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  }, [results]);

  if (frameworksLoading) return <PageLoading />;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return "Excellent";
    if (score >= 80) return "Good";
    if (score >= 60) return "Needs Improvement";
    return "Critical";
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={t("compliance.title")}
        backHref={`/incidents/${incidentId}`}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchValidation()}
              disabled={validationLoading}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", validationLoading && "animate-spin")} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportMutation.mutate("markdown")}
              disabled={exportMutation.isPending}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Framework Selection */}
        <Card>
          <CardHeader>
            <CardTitle>{t("compliance.frameworks")}</CardTitle>
            <CardDescription>
              Select compliance frameworks to validate against
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {frameworkList.map((framework: any) => (
                <FrameworkCard
                  key={framework.id}
                  framework={framework}
                  isSelected={selectedFrameworks.includes(framework.id)}
                  score={frameworkScores[framework.id]}
                  onToggle={() => {
                    setSelectedFrameworks((prev) =>
                      prev.includes(framework.id)
                        ? prev.filter((f) => f !== framework.id)
                        : [...prev, framework.id]
                    );
                  }}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Compliance Overview */}
        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="details">Phase Details</TabsTrigger>
            <TabsTrigger value="gaps">Gaps ({allGaps.length})</TabsTrigger>
            <TabsTrigger value="mapping">Control Mapping</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-4">
            {validationLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">Validating compliance...</p>
                </CardContent>
              </Card>
            ) : overallScore !== null ? (
              <>
                <div className="grid md:grid-cols-3 gap-4">
                  {selectedFrameworks.map((frameworkId) => {
                    const framework = frameworkList.find((f: any) => f.id === frameworkId);
                    const score = frameworkScores[frameworkId] ?? 0;
                    return (
                      <ComplianceScoreCard
                        key={frameworkId}
                        framework={framework}
                        score={score}
                      />
                    );
                  })}
                </div>

                {/* Overall Score */}
                <Card>
                  <CardHeader>
                    <CardTitle>Overall Compliance Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-6">
                      <div className="relative h-32 w-32">
                        <svg className="h-32 w-32 -rotate-90">
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            className="fill-none stroke-muted stroke-[8]"
                          />
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            className={cn(
                              "fill-none stroke-[8]",
                              overallScore >= 80 ? "stroke-green-500" :
                              overallScore >= 60 ? "stroke-yellow-500" : "stroke-red-500"
                            )}
                            strokeDasharray={`${overallScore * 3.52} 352`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className={cn("text-3xl font-bold", getScoreColor(overallScore))}>
                            {overallScore}%
                          </span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-lg font-medium">{getScoreLabel(overallScore)} Compliance</p>
                        <p className="text-muted-foreground">
                          {overallScore >= 80
                            ? "Your incident response process meets most compliance requirements across selected frameworks."
                            : overallScore >= 60
                            ? "Some compliance gaps need attention. Review the gaps tab for specific recommendations."
                            : "Significant compliance gaps detected. Immediate action recommended."}
                        </p>
                        {allGaps.length > 0 && (
                          <p className="text-sm text-muted-foreground">
                            {allGaps.filter(g => g.severity === "high").length} critical gaps,{" "}
                            {allGaps.filter(g => g.severity === "medium").length} moderate gaps
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">
                    Select frameworks and validate to see compliance scores
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="details" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Phase-by-Phase Compliance</CardTitle>
                <CardDescription>
                  Detailed compliance status for each IR phase
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {["detection", "analysis", "containment", "eradication", "recovery", "post_incident"].map((phase) => {
                    const phaseResults = results[phase];
                    if (!phaseResults) {
                      return (
                        <PhaseComplianceRow
                          key={phase}
                          phase={phase}
                          results={null}
                          selectedFrameworks={selectedFrameworks}
                        />
                      );
                    }
                    return (
                      <PhaseComplianceRow
                        key={phase}
                        phase={phase}
                        results={phaseResults}
                        selectedFrameworks={selectedFrameworks}
                      />
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="gaps" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Compliance Gaps</CardTitle>
                <CardDescription>
                  Areas requiring attention for full compliance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {allGaps.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                    <p className="text-muted-foreground">
                      No compliance gaps detected. Great job!
                    </p>
                  </div>
                ) : (
                  allGaps.map((gap, idx) => (
                    <GapItem
                      key={idx}
                      title={gap.title}
                      description={gap.description}
                      severity={gap.severity}
                      frameworks={gap.frameworks}
                      phase={gap.phase}
                    />
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mapping" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Cross-Framework Control Mapping</CardTitle>
                <CardDescription>
                  How controls map across different compliance frameworks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mappings.unified_controls?.length > 0 ? (
                    mappings.unified_controls
                      .filter((uc: UnifiedControl) =>
                        selectedFrameworks.some(f => uc.mappings[f as keyof typeof uc.mappings])
                      )
                      .slice(0, 10)
                      .map((control: UnifiedControl) => (
                        <ControlMappingCard
                          key={control.id}
                          control={control}
                          selectedFrameworks={selectedFrameworks}
                        />
                      ))
                  ) : (
                    <div className="text-center py-8">
                      <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        Cross-framework mappings will appear here
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function FrameworkCard({
  framework,
  isSelected,
  score,
  onToggle,
}: {
  framework: any;
  isSelected: boolean;
  score?: number;
  onToggle: () => void;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-colors",
        isSelected && "border-primary bg-primary/5"
      )}
      onClick={onToggle}
    >
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="font-medium">{framework.name}</p>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {framework.description}
            </p>
          </div>
          <div
            className={cn(
              "h-5 w-5 rounded-full border-2 flex items-center justify-center",
              isSelected
                ? "border-primary bg-primary"
                : "border-muted-foreground"
            )}
          >
            {isSelected && <CheckCircle className="h-3 w-3 text-white" />}
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">{framework.version}</Badge>
            <span>{framework.controls_count} controls</span>
          </div>
          {score !== undefined && isSelected && (
            <Badge variant={score >= 80 ? "default" : score >= 60 ? "secondary" : "destructive"}>
              {score}%
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ComplianceScoreCard({
  framework,
  score,
}: {
  framework: any;
  score: number;
}) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">{framework?.name}</p>
            <p className="text-sm text-muted-foreground">
              {framework?.version}
            </p>
          </div>
          <span className={cn("text-3xl font-bold", getScoreColor(score))}>
            {score}%
          </span>
        </div>
        <Progress
          value={score}
          className="mt-4"
        />
      </CardContent>
    </Card>
  );
}

function PhaseComplianceRow({
  phase,
  results,
  selectedFrameworks,
}: {
  phase: string;
  results: Record<string, ValidationResult> | null;
  selectedFrameworks: string[];
}) {
  const phaseLabels: Record<string, string> = {
    detection: "Detection",
    analysis: "Analysis",
    containment: "Containment",
    eradication: "Eradication",
    recovery: "Recovery",
    post_incident: "Post-Incident",
  };

  return (
    <div className="p-4 bg-muted rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <p className="font-medium">{phaseLabels[phase]}</p>
        {!results && (
          <Badge variant="outline">No data</Badge>
        )}
      </div>
      {results && (
        <div className="grid grid-cols-3 gap-2">
          {selectedFrameworks.map((frameworkId) => {
            const result = results[frameworkId];
            return (
              <div
                key={frameworkId}
                className="flex items-center gap-2 text-sm"
              >
                {result ? (
                  <>
                    {result.is_compliant ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : result.score >= 60 ? (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span>{frameworkId.toUpperCase()}</span>
                    <span className="text-muted-foreground">{result.score}%</span>
                  </>
                ) : (
                  <>
                    <div className="h-4 w-4 rounded-full border border-muted-foreground" />
                    <span className="text-muted-foreground">{frameworkId.toUpperCase()}</span>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function GapItem({
  title,
  description,
  severity,
  frameworks,
  phase,
}: {
  title: string;
  description: string;
  severity: "high" | "medium" | "low";
  frameworks: string[];
  phase: string;
}) {
  const severityColors = {
    high: "text-red-500",
    medium: "text-yellow-500",
    low: "text-blue-500",
  };

  const severityIcons = {
    high: XCircle,
    medium: AlertTriangle,
    low: CheckCircle,
  };

  const phaseLabels: Record<string, string> = {
    detection: "Detection",
    analysis: "Analysis",
    containment: "Containment",
    eradication: "Eradication",
    recovery: "Recovery",
    post_incident: "Post-Incident",
  };

  const Icon = severityIcons[severity];

  return (
    <div className="flex items-start gap-4 p-4 bg-muted rounded-lg">
      <Icon className={cn("h-5 w-5 mt-0.5", severityColors[severity])} />
      <div className="flex-1">
        <p className="font-medium">{title}</p>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge variant="outline">{phaseLabels[phase] || phase}</Badge>
          {frameworks.map((f) => (
            <Badge key={f} variant="secondary">
              {f.toUpperCase()}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}

function ControlMappingCard({
  control,
  selectedFrameworks,
}: {
  control: UnifiedControl;
  selectedFrameworks: string[];
}) {
  const frameworkLabels: Record<string, string> = {
    bsi: "BSI",
    nist: "NIST",
    iso27001: "ISO 27001",
    owasp: "OWASP",
  };

  return (
    <div className="p-4 bg-muted rounded-lg">
      <p className="font-medium">{control.name}</p>
      <p className="text-sm text-muted-foreground mt-1">{control.description}</p>
      <div className="flex flex-wrap gap-4 mt-3">
        {selectedFrameworks.map((frameworkId) => {
          const mapping = control.mappings[frameworkId as keyof typeof control.mappings];
          if (!mapping || mapping.length === 0) return null;
          return (
            <div key={frameworkId} className="flex items-center gap-2 text-sm">
              <Badge variant="secondary">{frameworkLabels[frameworkId] || frameworkId}</Badge>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <div className="flex gap-1">
                {mapping.map((controlId: string) => (
                  <code key={controlId} className="bg-background px-2 py-0.5 rounded text-xs">
                    {controlId}
                  </code>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

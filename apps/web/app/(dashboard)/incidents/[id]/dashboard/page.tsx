"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Clock,
  Server,
  FileText,
  CheckSquare,
  GitBranch,
  TrendingUp,
  AlertTriangle,
  Shield,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { incidentsAPI } from "@/lib/api-client";
import { formatDate, formatDuration, getPhaseIndex } from "@/lib/utils";

const phases = [
  "detection",
  "analysis",
  "containment",
  "eradication",
  "recovery",
  "post_incident",
];

export default function DashboardPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();

  const { data: summary, isLoading } = useQuery({
    queryKey: ["incident-summary", incidentId],
    queryFn: () => incidentsAPI.getSummary(token!, incidentId),
    enabled: !!token && !!incidentId,
  });

  if (isLoading) return <PageLoading />;

  const data = summary as any;
  const incident = data?.incident;
  const progress = data?.progress;
  const timeline = data?.timeline;

  if (!incident) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        Failed to load dashboard
      </div>
    );
  }

  const currentPhaseIndex = getPhaseIndex(incident.current_phase);

  return (
    <div className="flex flex-col h-full">
      <Header title={t("incidents.dashboard")} backHref={`/incidents/${incidentId}`} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            icon={Clock}
            label="Time in Current Phase"
            value={
              progress?.total_duration_seconds
                ? formatDuration(progress.total_duration_seconds)
                : "N/A"
            }
          />
          <MetricCard
            icon={Server}
            label="Affected Systems"
            value={incident.affected_systems?.length || 0}
          />
          <MetricCard
            icon={FileText}
            label="Evidence Entries"
            value={progress?.evidence_count || 0}
          />
          <MetricCard
            icon={GitBranch}
            label="Decisions Made"
            value={progress?.decisions_made || 0}
          />
        </div>

        {/* Phase Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Phase Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {phases.map((phase, idx) => {
                const isCompleted = idx < currentPhaseIndex;
                const isCurrent = idx === currentPhaseIndex;
                const phaseData = timeline?.timeline?.find(
                  (t: any) => t.phase === phase
                );

                return (
                  <div key={phase} className="flex items-center gap-4">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center text-sm font-medium ${
                        isCompleted
                          ? "bg-green-500 text-white"
                          : isCurrent
                          ? `bg-phase-${phase} text-white`
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p
                          className={`font-medium ${
                            isCurrent ? "text-foreground" : "text-muted-foreground"
                          }`}
                        >
                          {t(`phases.${phase}`)}
                        </p>
                        {isCompleted && (
                          <Badge variant="default">Completed</Badge>
                        )}
                        {isCurrent && (
                          <Badge variant="secondary">In Progress</Badge>
                        )}
                      </div>
                      {(isCompleted || isCurrent) && phaseData && (
                        <p className="text-sm text-muted-foreground">
                          {phaseData.started_at &&
                            `Started: ${formatDate(phaseData.started_at)}`}
                          {phaseData.duration_seconds &&
                            ` | Duration: ${formatDuration(
                              phaseData.duration_seconds
                            )}`}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Key Metrics */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Checklist Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckSquare className="h-5 w-5" />
                Checklist Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Overall Progress</span>
                <span className="font-semibold">
                  {Math.round(progress?.checklist_progress || 0)}%
                </span>
              </div>
              <Progress value={progress?.checklist_progress || 0} />

              <div className="grid grid-cols-2 gap-4 pt-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">
                    {progress?.checklist_completed || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Completed</p>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">
                    {progress?.mandatory_remaining || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Mandatory Remaining
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Severity & Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Incident Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Severity</span>
                <Badge variant={incident.severity}>
                  {t(`severity.${incident.severity}`)}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Status</span>
                <Badge variant="outline">{t(`status.${incident.status}`)}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Current Phase</span>
                <Badge variant={incident.current_phase}>
                  {t(`phases.${incident.current_phase}`)}
                </Badge>
              </div>

              {incident.detected_at && (
                <div className="pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Time since detection
                  </p>
                  <p className="text-xl font-semibold">
                    {formatDuration(
                      Math.floor(
                        (Date.now() - new Date(incident.detected_at).getTime()) /
                          1000
                      )
                    )}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Affected Systems Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Affected Systems
            </CardTitle>
          </CardHeader>
          <CardContent>
            {incident.affected_systems?.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {incident.affected_systems.map((system: any) => (
                  <div
                    key={system.id}
                    className="p-3 bg-muted rounded-lg space-y-1"
                  >
                    <p className="font-medium">{system.hostname}</p>
                    <p className="text-sm text-muted-foreground">
                      {system.ip_address}
                    </p>
                    <Badge variant="outline" className="mt-2">
                      {system.criticality}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-4">
                No affected systems recorded
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-3">
          <Icon className="h-8 w-8 text-primary" />
          <div>
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ClipboardList,
  GitBranch,
  FileText,
  Shield,
  BarChart3,
  Download,
  ArrowRight,
  Clock,
  Users,
  Server,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useIncidentStore } from "@/stores/incident-store";
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

export default function IncidentOverviewPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { setIncident } = useIncidentStore();

  const { data: incident, isLoading, error } = useQuery({
    queryKey: ["incident", incidentId],
    queryFn: () => incidentsAPI.get(token!, incidentId),
    enabled: !!token && !!incidentId,
  });

  useEffect(() => {
    if (incident) {
      setIncident(incident as any);
    }
  }, [incident, setIncident]);

  if (isLoading) return <PageLoading />;
  if (error || !incident) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">{t("common.error")}</p>
      </div>
    );
  }

  const inc = incident as any;
  const currentPhaseIndex = getPhaseIndex(inc.current_phase);

  return (
    <div className="flex flex-col h-full">
      <Header title={inc.title}>
        <div className="flex gap-2">
          <Badge variant={inc.severity}>{t(`severity.${inc.severity}`)}</Badge>
          <Badge variant={inc.current_phase}>
            {t(`phases.${inc.current_phase}`)}
          </Badge>
        </div>
      </Header>

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Phase Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Phase Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                {phases.map((phase, idx) => (
                  <div key={phase} className="flex-1 space-y-2">
                    <div
                      className={`h-3 rounded-full transition-colors ${
                        idx < currentPhaseIndex
                          ? "bg-green-500"
                          : idx === currentPhaseIndex
                          ? `bg-phase-${phase}`
                          : "bg-muted"
                      }`}
                    />
                    <p
                      className={`text-xs text-center ${
                        idx === currentPhaseIndex
                          ? "font-semibold"
                          : "text-muted-foreground"
                      }`}
                    >
                      {t(`phases.${phase}`)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <QuickActionCard
            href={`/incidents/${incidentId}/checklist`}
            icon={ClipboardList}
            title={t("incidents.checklist")}
            description="Complete phase tasks"
          />
          <QuickActionCard
            href={`/incidents/${incidentId}/decisions`}
            icon={GitBranch}
            title={t("incidents.decisions")}
            description="Navigate decision trees"
          />
          <QuickActionCard
            href={`/incidents/${incidentId}/evidence`}
            icon={FileText}
            title={t("incidents.evidence")}
            description="Forensic evidence chain"
          />
          <QuickActionCard
            href={`/incidents/${incidentId}/compliance`}
            icon={Shield}
            title={t("incidents.compliance")}
            description="Framework validation"
          />
          <QuickActionCard
            href={`/incidents/${incidentId}/dashboard`}
            icon={BarChart3}
            title={t("incidents.dashboard")}
            description="Executive summary"
          />
          <QuickActionCard
            href={`/incidents/${incidentId}/export`}
            icon={Download}
            title={t("incidents.export")}
            description="Generate reports"
          />
        </div>

        {/* Details Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Incident Info */}
          <Card>
            <CardHeader>
              <CardTitle>Incident Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {inc.description && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Description
                  </p>
                  <p className="mt-1">{inc.description}</p>
                </div>
              )}
              {inc.initial_indicator && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Initial Indicator
                  </p>
                  <p className="mt-1 font-mono text-sm bg-muted p-2 rounded">
                    {inc.initial_indicator}
                  </p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Status
                  </p>
                  <p className="mt-1">{t(`status.${inc.status}`)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Detection Source
                  </p>
                  <p className="mt-1">{inc.detection_source || "-"}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <TimelineItem
                label="Created"
                date={inc.created_at}
                isActive
              />
              {inc.detected_at && (
                <TimelineItem label="Detected" date={inc.detected_at} isActive />
              )}
              {inc.contained_at && (
                <TimelineItem label="Contained" date={inc.contained_at} isActive />
              )}
              {inc.eradicated_at && (
                <TimelineItem
                  label="Eradicated"
                  date={inc.eradicated_at}
                  isActive
                />
              )}
              {inc.closed_at && (
                <TimelineItem label="Closed" date={inc.closed_at} isActive />
              )}
            </CardContent>
          </Card>

          {/* Affected Systems */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Affected Systems
              </CardTitle>
            </CardHeader>
            <CardContent>
              {inc.affected_systems?.length > 0 ? (
                <div className="space-y-2">
                  {inc.affected_systems.map((system: any) => (
                    <div
                      key={system.id}
                      className="flex items-center justify-between p-2 bg-muted rounded"
                    >
                      <div>
                        <p className="font-medium">{system.hostname}</p>
                        <p className="text-sm text-muted-foreground">
                          {system.ip_address} - {system.os_type}
                        </p>
                      </div>
                      <Badge variant="outline">{system.criticality}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No affected systems recorded
                </p>
              )}
            </CardContent>
          </Card>

          {/* Analyst Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Personnel
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Analyst
                </p>
                <p className="mt-1">
                  {inc.analyst_name || "-"}
                  {inc.analyst_email && (
                    <span className="text-muted-foreground ml-2">
                      ({inc.analyst_email})
                    </span>
                  )}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function QuickActionCard({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <Link href={href}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardContent className="pt-6 text-center space-y-2">
          <Icon className="h-8 w-8 mx-auto text-primary" />
          <p className="font-medium">{title}</p>
          <p className="text-xs text-muted-foreground">{description}</p>
        </CardContent>
      </Card>
    </Link>
  );
}

function TimelineItem({
  label,
  date,
  isActive,
}: {
  label: string;
  date: string;
  isActive: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`h-2 w-2 rounded-full ${
          isActive ? "bg-green-500" : "bg-muted"
        }`}
      />
      <div className="flex-1 flex items-center justify-between">
        <span className="text-sm">{label}</span>
        <span className="text-sm text-muted-foreground">{formatDate(date)}</span>
      </div>
    </div>
  );
}

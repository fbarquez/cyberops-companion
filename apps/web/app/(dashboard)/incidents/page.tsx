"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, Search, Filter } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { incidentsAPI } from "@/lib/api-client";
import { formatDate, getPhaseIndex } from "@/lib/utils";
import { Incident, IncidentStatus, IncidentSeverity } from "@/types";

export default function IncidentsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["incidents", statusFilter],
    queryFn: () =>
      incidentsAPI.list(token!, {
        status: statusFilter !== "all" ? statusFilter : undefined,
      }),
    enabled: !!token,
  });

  const incidents = (data as any)?.items || [];

  const filteredIncidents = incidents.filter((incident: Incident) =>
    incident.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <Header title={t("incidents.title")}>
        <Link href="/incidents/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            {t("incidents.new")}
          </Button>
        </Link>
      </Header>

      <div className="p-6 space-y-6">
        {/* Filters */}
        <div className="flex gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t("common.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder={t("common.filter")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("incidents.all")}</SelectItem>
              <SelectItem value="active">{t("status.active")}</SelectItem>
              <SelectItem value="contained">{t("status.contained")}</SelectItem>
              <SelectItem value="closed">{t("status.closed")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Incident List */}
        {isLoading ? (
          <PageLoading />
        ) : error ? (
          <div className="text-center text-destructive p-8">
            {t("common.error")}
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="text-center text-muted-foreground p-8">
            {t("incidents.noIncidents")}
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredIncidents.map((incident: Incident) => (
              <IncidentCard key={incident.id} incident={incident} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function IncidentCard({ incident }: { incident: Incident }) {
  const { t } = useTranslations();

  return (
    <Link href={`/incidents/${incident.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg">{incident.title}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {incident.description?.slice(0, 100)}
                {(incident.description?.length || 0) > 100 ? "..." : ""}
              </p>
            </div>
            <div className="flex gap-2">
              <Badge variant={incident.severity as any}>
                {t(`severity.${incident.severity}`)}
              </Badge>
              <Badge variant={incident.current_phase as any}>
                {t(`phases.${incident.current_phase}`)}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex gap-4">
              <span>
                {t("status." + incident.status)}
              </span>
              <span>
                {incident.affected_systems?.length || 0} {t("incidents.systems")}
              </span>
            </div>
            <span>{formatDate(incident.created_at)}</span>
          </div>

          {/* Phase Progress */}
          <div className="mt-4 flex gap-1">
            {["detection", "analysis", "containment", "eradication", "recovery", "post_incident"].map(
              (phase, idx) => (
                <div
                  key={phase}
                  className={`h-2 flex-1 rounded-full ${
                    idx <= getPhaseIndex(incident.current_phase)
                      ? `bg-phase-${phase}`
                      : "bg-muted"
                  }`}
                />
              )
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, X, AlertTriangle, Lock, HelpCircle } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useIncidentStore } from "@/stores/incident-store";
import { useTranslations } from "@/hooks/use-translations";
import { checklistsAPI, incidentsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const phases = [
  "detection",
  "analysis",
  "containment",
  "eradication",
  "recovery",
  "post_incident",
];

export default function ChecklistPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { currentIncident, setIncident } = useIncidentStore();
  const queryClient = useQueryClient();

  const currentPhase = currentIncident?.current_phase || "detection";

  const { data: checklist, isLoading } = useQuery({
    queryKey: ["checklist", incidentId, currentPhase],
    queryFn: () => checklistsAPI.get(token!, incidentId, currentPhase),
    enabled: !!token && !!incidentId,
  });

  const completeMutation = useMutation({
    mutationFn: ({ itemId }: { itemId: string }) =>
      checklistsAPI.complete(token!, incidentId, currentPhase, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checklist", incidentId] });
    },
  });

  const advanceMutation = useMutation({
    mutationFn: () => incidentsAPI.advancePhase(token!, incidentId),
    onSuccess: async (data: any) => {
      // Update the incident store with new phase
      if (data && currentIncident) {
        setIncident({ ...currentIncident, current_phase: data.current_phase });
      }
      queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      queryClient.invalidateQueries({ queryKey: ["checklist", incidentId] });
    },
  });

  if (isLoading) return <PageLoading />;

  const checklistData = checklist as any;
  const items = checklistData?.items || [];

  return (
    <div className="flex flex-col h-full">
      <Header title={t("checklist.title")} backHref={`/incidents/${incidentId}`} />

      <div className="p-6 space-y-6">
        {/* Progress Overview */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold">{t(`phases.${currentPhase}`)}</h3>
                <p className="text-sm text-muted-foreground">
                  {checklistData?.completed_items || 0} / {checklistData?.total_items || 0} completed
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">
                  {Math.round(checklistData?.progress_percent || 0)}%
                </p>
                {checklistData?.can_advance && (
                  <Badge variant="default" className="mt-1">
                    {t("checklist.canAdvance")}
                  </Badge>
                )}
              </div>
            </div>
            <Progress value={checklistData?.progress_percent || 0} />

            {checklistData?.can_advance && (
              <div className="mt-4 flex justify-end">
                <Button
                  onClick={() => advanceMutation.mutate()}
                  disabled={advanceMutation.isPending}
                >
                  Advance to Next Phase
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Phase Tabs */}
        <Tabs defaultValue={currentPhase}>
          <TabsList className="w-full justify-start overflow-x-auto">
            {phases.map((phase) => (
              <TabsTrigger
                key={phase}
                value={phase}
                disabled={phase !== currentPhase}
              >
                {t(`phases.${phase}`)}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value={currentPhase} className="mt-4 space-y-3">
            {items.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No checklist items for this phase
              </p>
            ) : (
              items.map((item: any) => (
                <ChecklistItemCard
                  key={item.id}
                  item={item}
                  onComplete={() =>
                    completeMutation.mutate({ itemId: item.item_id })
                  }
                  isCompleting={completeMutation.isPending}
                />
              ))
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function ChecklistItemCard({
  item,
  onComplete,
  isCompleting,
}: {
  item: any;
  onComplete: () => void;
  isCompleting: boolean;
}) {
  const { t } = useTranslations();
  const isCompleted = item.status === "completed" || item.status === "skipped";
  const isBlocked = item.is_blocked;

  return (
    <Card
      className={cn(
        "transition-colors",
        isCompleted && "bg-muted/50",
        isBlocked && "opacity-60"
      )}
    >
      <CardContent className="pt-4">
        <div className="flex items-start gap-4">
          {/* Status Icon */}
          <div className="mt-1">
            {isCompleted ? (
              <div className="h-6 w-6 rounded-full bg-green-500 flex items-center justify-center">
                <Check className="h-4 w-4 text-white" />
              </div>
            ) : isBlocked ? (
              <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center">
                <Lock className="h-4 w-4 text-muted-foreground" />
              </div>
            ) : (
              <div className="h-6 w-6 rounded-full border-2 border-primary" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p
                  className={cn(
                    "font-medium",
                    isCompleted && "line-through text-muted-foreground"
                  )}
                >
                  {item.text}
                </p>
                {item.help_text && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {item.help_text}
                  </p>
                )}
              </div>

              <div className="flex gap-2 flex-shrink-0">
                {item.mandatory && (
                  <Badge variant="destructive">{t("checklist.mandatory")}</Badge>
                )}
                {item.forensic_critical && (
                  <Badge variant="outline" className="border-orange-500 text-orange-500">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    {t("checklist.forensicCritical")}
                  </Badge>
                )}
              </div>
            </div>

            {/* Warning */}
            {item.warning && (
              <div className="flex items-start gap-2 p-2 bg-orange-50 dark:bg-orange-950 rounded text-sm">
                <AlertTriangle className="h-4 w-4 text-orange-500 flex-shrink-0 mt-0.5" />
                <p className="text-orange-700 dark:text-orange-300">{item.warning}</p>
              </div>
            )}

            {/* Blocked message */}
            {isBlocked && (
              <p className="text-sm text-muted-foreground">
                {t("checklist.blocked")}: {item.blockers?.join(", ")}
              </p>
            )}

            {/* Actions */}
            {!isCompleted && !isBlocked && (
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  onClick={onComplete}
                  disabled={isCompleting}
                >
                  <Check className="h-4 w-4 mr-1" />
                  {t("checklist.complete")}
                </Button>
                {!item.mandatory && (
                  <Button size="sm" variant="outline">
                    <X className="h-4 w-4 mr-1" />
                    {t("checklist.skip")}
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

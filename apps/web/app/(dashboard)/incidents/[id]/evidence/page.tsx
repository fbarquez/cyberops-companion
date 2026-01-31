"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import {
  Plus,
  CheckCircle,
  XCircle,
  X,
  Download,
  Hash,
  Clock,
  User,
  Tag,
  FileText,
  Paperclip,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { FileUpload } from "@/components/shared/file-upload";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/stores/auth-store";
import { useIncidentStore } from "@/stores/incident-store";
import { useTranslations } from "@/hooks/use-translations";
import { evidenceAPI } from "@/lib/api-client";
import { formatDate, truncateHash } from "@/lib/utils";

export default function EvidencePage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { currentIncident } = useIncidentStore();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);

  const { data: chain, isLoading, error } = useQuery({
    queryKey: ["evidence-chain", incidentId],
    queryFn: () => evidenceAPI.getChain(token!, incidentId),
    enabled: !!token && !!incidentId,
  });

  const verifyMutation = useMutation({
    mutationFn: () => evidenceAPI.verify(token!, incidentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evidence-chain", incidentId] });
    },
  });

  if (isLoading) return <PageLoading />;

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <Header title={t("evidence.title")} backHref={`/incidents/${incidentId}`} />
        <div className="p-6">
          <Card>
            <CardContent className="py-8 text-center text-destructive">
              Error loading evidence: {(error as Error).message}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const chainData = chain as any;
  const entries = chainData?.entries || [];

  return (
    <div className="flex flex-col h-full">
      <Header title={t("evidence.title")} backHref={`/incidents/${incidentId}`}>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => verifyMutation.mutate()}
            disabled={verifyMutation.isPending}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            {t("evidence.verify")}
          </Button>
          <Button onClick={() => setShowAddForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t("evidence.add")}
          </Button>
        </div>
      </Header>

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Add Evidence Form Modal */}
        {showAddForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
              className="fixed inset-0 bg-black/50"
              onClick={() => setShowAddForm(false)}
            />
            <div className="relative bg-background rounded-lg shadow-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{t("evidence.add")}</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowAddForm(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <AddEvidenceForm
                incidentId={incidentId}
                currentPhase={currentIncident?.current_phase || "detection"}
                onSuccess={() => {
                  setShowAddForm(false);
                  queryClient.invalidateQueries({
                    queryKey: ["evidence-chain", incidentId],
                  });
                }}
              />
            </div>
          </div>
        )}

        <Tabs defaultValue="chain" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="chain" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {t("evidence.chain")}
            </TabsTrigger>
            <TabsTrigger value="attachments" className="flex items-center gap-2">
              <Paperclip className="h-4 w-4" />
              {t("evidence.attachments")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chain" className="space-y-6 mt-6">
            {/* Chain Status */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {chainData?.chain_valid !== false ? (
                      <>
                        <CheckCircle className="h-8 w-8 text-green-500" />
                        <div>
                          <p className="font-semibold text-green-700 dark:text-green-400">
                            {t("evidence.chainValid")}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {chainData?.total_entries || 0} entries
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-8 w-8 text-red-500" />
                        <div>
                          <p className="font-semibold text-red-700 dark:text-red-400">
                            {t("evidence.chainInvalid")}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Chain integrity compromised
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    {t("evidence.export")}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Evidence Timeline */}
            <div className="space-y-4">
              {entries.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center text-muted-foreground">
                    No evidence entries yet. Click "Add Evidence" to create the first entry.
                  </CardContent>
                </Card>
              ) : (
                entries.map((entry: any, index: number) => (
                  <EvidenceEntryCard
                    key={entry.id}
                    entry={entry}
                    isFirst={index === 0}
                    isLast={index === entries.length - 1}
                  />
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="attachments" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Paperclip className="h-5 w-5" />
                  {t("evidence.fileAttachments")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <FileUpload
                  entityType="incident"
                  entityId={incidentId}
                  showList={true}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function EvidenceEntryCard({
  entry,
  isFirst,
  isLast,
}: {
  entry: any;
  isFirst: boolean;
  isLast: boolean;
}) {
  const { t } = useTranslations();

  const typeColors: Record<string, string> = {
    observation: "bg-blue-500",
    action: "bg-green-500",
    decision: "bg-purple-500",
    artifact: "bg-orange-500",
    note: "bg-gray-500",
    system: "bg-cyan-500",
  };

  return (
    <div className="flex gap-4">
      {/* Timeline Line */}
      <div className="flex flex-col items-center">
        <div
          className={`h-3 w-3 rounded-full ${typeColors[entry.entry_type] || "bg-gray-500"}`}
        />
        {!isLast && <div className="w-0.5 flex-1 bg-border" />}
      </div>

      {/* Content */}
      <Card className="flex-1 mb-4">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {t(`evidence.type.${entry.entry_type}`)}
                </Badge>
                <Badge variant="secondary">{entry.phase}</Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  #{entry.sequence_number}
                </span>
              </div>
              <p className="font-medium">{entry.description}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Metadata */}
          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <User className="h-4 w-4" />
              {entry.operator || "System"}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {formatDate(entry.timestamp)}
            </div>
            {entry.tags?.length > 0 && (
              <div className="flex items-center gap-1">
                <Tag className="h-4 w-4" />
                {entry.tags.join(", ")}
              </div>
            )}
          </div>

          {/* Hash */}
          <div className="flex items-center gap-2 font-mono text-xs bg-muted p-2 rounded">
            <Hash className="h-4 w-4" />
            <span className="text-muted-foreground">Hash:</span>
            <span>{truncateHash(entry.entry_hash, 12)}</span>
            {entry.previous_hash && (
              <>
                <span className="text-muted-foreground ml-4">Prev:</span>
                <span>{truncateHash(entry.previous_hash, 12)}</span>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AddEvidenceForm({
  incidentId,
  currentPhase,
  onSuccess,
}: {
  incidentId: string;
  currentPhase: string;
  onSuccess: () => void;
}) {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { register, handleSubmit, setValue, watch } = useForm({
    defaultValues: {
      entry_type: "observation",
      phase: currentPhase,
      description: "",
      tags: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => evidenceAPI.create(token!, incidentId, data),
    onSuccess,
  });

  const onSubmit = (data: any) => {
    createMutation.mutate({
      ...data,
      tags: data.tags ? data.tags.split(",").map((t: string) => t.trim()) : [],
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label>Type</Label>
        <Select
          value={watch("entry_type")}
          onValueChange={(v) => setValue("entry_type", v)}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="observation">{t("evidence.type.observation")}</SelectItem>
            <SelectItem value="action">{t("evidence.type.action")}</SelectItem>
            <SelectItem value="note">{t("evidence.type.note")}</SelectItem>
            <SelectItem value="artifact">{t("evidence.type.artifact")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea {...register("description")} rows={3} required />
      </div>

      <div className="space-y-2">
        <Label>Tags (comma-separated)</Label>
        <Input {...register("tags")} placeholder="ioc, malware, network" />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? t("common.loading") : t("evidence.add")}
        </Button>
      </div>
    </form>
  );
}

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  GitBranch,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  ThumbsUp,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useIncidentStore } from "@/stores/incident-store";
import { useUIStore } from "@/stores/ui-store";
import { useTranslations } from "@/hooks/use-translations";
import { decisionsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function DecisionsPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { currentIncident } = useIncidentStore();
  const { language } = useUIStore();
  const queryClient = useQueryClient();

  const currentPhase = currentIncident?.current_phase || "detection";

  const { data: trees, isLoading } = useQuery({
    queryKey: ["decision-trees", incidentId, currentPhase, language],
    queryFn: () => decisionsAPI.getTrees(token!, incidentId, currentPhase, language),
    enabled: !!token && !!incidentId,
  });

  const [selectedTree, setSelectedTree] = useState<string | null>(null);

  if (isLoading) return <PageLoading />;

  const treeList = (trees as any[]) || [];

  return (
    <div className="flex flex-col h-full">
      <Header title={t("decisions.title")} backHref={`/incidents/${incidentId}`} />

      <div className="p-6 space-y-6">
        {/* Tree Selection */}
        {!selectedTree && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {treeList.length === 0 ? (
              <Card className="col-span-full">
                <CardContent className="py-8 text-center text-muted-foreground">
                  No decision trees available for this phase
                </CardContent>
              </Card>
            ) : (
              treeList.map((tree: any) => (
                <Card
                  key={tree.tree_id}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => setSelectedTree(tree.tree_id)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <GitBranch className="h-8 w-8 text-primary" />
                      {tree.completed && (
                        <Badge variant="default">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="mt-2">{tree.name}</CardTitle>
                    <CardDescription>{tree.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {tree.completed_nodes} / {tree.total_nodes} decisions
                      </span>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Active Decision Tree */}
        {selectedTree && (
          <DecisionTreeView
            incidentId={incidentId}
            treeId={selectedTree}
            onBack={() => setSelectedTree(null)}
          />
        )}
      </div>
    </div>
  );
}

function DecisionTreeView({
  incidentId,
  treeId,
  onBack,
}: {
  incidentId: string;
  treeId: string;
  onBack: () => void;
}) {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { language } = useUIStore();
  const queryClient = useQueryClient();
  const [rationale, setRationale] = useState("");
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const { data: currentNode, isLoading } = useQuery({
    queryKey: ["decision-node", incidentId, treeId, language],
    queryFn: () => decisionsAPI.getCurrentNode(token!, incidentId, treeId, language),
    enabled: !!token && !!incidentId && !!treeId,
  });

  const decideMutation = useMutation({
    mutationFn: ({ optionId, rationale }: { optionId: string; rationale?: string }) =>
      decisionsAPI.decide(token!, incidentId, treeId, optionId, rationale),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["decision-node", incidentId, treeId] });
      queryClient.invalidateQueries({ queryKey: ["decision-trees", incidentId] });
      setRationale("");
      setSelectedOption(null);
    },
  });

  if (isLoading) return <PageLoading />;

  const node = currentNode as any;

  if (!node) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <p className="text-lg font-medium">Decision Tree Completed</p>
          <Button variant="outline" onClick={onBack} className="mt-4">
            Back to Trees
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={onBack}>
        ← Back to Trees
      </Button>

      {/* Current Decision Node */}
      <Card>
        <CardHeader>
          <CardTitle>{node.title}</CardTitle>
          <CardDescription>{node.question}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Context */}
          {node.context && (
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm">{node.context}</p>
            </div>
          )}

          {/* Help Text */}
          {node.help_text && (
            <div className="flex items-start gap-2 text-sm text-muted-foreground">
              <HelpCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <p>{node.help_text}</p>
            </div>
          )}

          {/* Blocked Warning */}
          {!node.is_available && (
            <div className="bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-orange-700 dark:text-orange-300">
                <AlertTriangle className="h-5 w-5" />
                <p className="font-medium">Prerequisites Required</p>
              </div>
              <ul className="mt-2 text-sm text-orange-600 dark:text-orange-400 list-disc list-inside">
                {node.blocked_by?.map((item: string) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Options */}
          {node.is_available && (
            <div className="space-y-3">
              <Label className="text-base font-medium">Select an Option</Label>
              {node.options?.map((option: any) => (
                <div
                  key={option.id}
                  className={cn(
                    "border rounded-lg p-4 cursor-pointer transition-colors",
                    selectedOption === option.id
                      ? "border-primary bg-primary/5"
                      : "hover:border-primary/50"
                  )}
                  onClick={() => setSelectedOption(option.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{option.label}</p>
                        {option.recommended && (
                          <Badge variant="default">
                            <ThumbsUp className="h-3 w-3 mr-1" />
                            {t("decisions.recommended")}
                          </Badge>
                        )}
                        {option.confidence && (
                          <Badge variant="secondary">
                            {option.confidence} confidence
                          </Badge>
                        )}
                      </div>
                      {option.description && (
                        <p className="text-sm text-muted-foreground">
                          {option.description}
                        </p>
                      )}
                    </div>
                    <div
                      className={cn(
                        "h-5 w-5 rounded-full border-2 flex-shrink-0",
                        selectedOption === option.id
                          ? "border-primary bg-primary"
                          : "border-muted-foreground"
                      )}
                    >
                      {selectedOption === option.id && (
                        <CheckCircle className="h-4 w-4 text-primary-foreground" />
                      )}
                    </div>
                  </div>

                  {/* Warning */}
                  {option.warning && (
                    <div className="mt-2 flex items-start gap-2 text-sm text-orange-600">
                      <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                      <p>{option.warning}</p>
                    </div>
                  )}

                  {/* Evidence warning */}
                  {option.modifies_evidence && (
                    <div className="mt-2 text-sm text-red-600">
                      ⚠️ This action may modify forensic evidence
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Rationale */}
          {selectedOption && (
            <div className="space-y-2">
              <Label htmlFor="rationale">{t("decisions.rationale")} (optional)</Label>
              <Textarea
                id="rationale"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Explain your reasoning..."
                rows={3}
              />
            </div>
          )}

          {/* Submit */}
          {selectedOption && (
            <div className="flex justify-end">
              <Button
                onClick={() =>
                  decideMutation.mutate({
                    optionId: selectedOption,
                    rationale: rationale || undefined,
                  })
                }
                disabled={decideMutation.isPending}
              >
                {decideMutation.isPending ? "Processing..." : t("decisions.make")}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

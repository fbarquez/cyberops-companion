"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  PlayCircle,
  Award,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  ChevronRight,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { toolsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface Scenario {
  id: string;
  name: string;
  description: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  estimated_duration: string;
  objectives: string[];
  background?: string;
  initial_situation?: string;
  hints?: string[];
  expected_findings?: string[];
}

interface SimulationSession {
  session_id: string;
  scenario_id: string;
  started_at: string;
  status: string;
  current_phase: string;
  scenario: {
    name: string;
    background: string;
    initial_situation: string;
    objectives: string[];
  };
  artifacts: {
    ransom_note?: { filename: string; content: string };
    encrypted_files?: Array<{ original_name: string; encrypted_name: string; size: number }>;
    suspicious_processes?: Array<{ name: string; pid: number; command_line: string }>;
  };
}

export default function SimulationPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [difficultyFilter, setDifficultyFilter] = useState<string>("all");
  const [activeSession, setActiveSession] = useState<SimulationSession | null>(null);
  const [showSessionDialog, setShowSessionDialog] = useState(false);

  const { data: scenarios, isLoading, refetch } = useQuery({
    queryKey: ["simulation-scenarios", difficultyFilter],
    queryFn: () =>
      toolsAPI.getSimulationScenarios(
        token!,
        difficultyFilter !== "all" ? difficultyFilter : undefined
      ),
    enabled: !!token,
  });

  const startMutation = useMutation<SimulationSession, Error, string>({
    mutationFn: async (scenarioId: string) => {
      const result = await toolsAPI.startSimulation(token!, scenarioId);
      return result as SimulationSession;
    },
    onSuccess: (data) => {
      setActiveSession(data);
      setShowSessionDialog(true);
      toast.success("Simulation started!");
    },
    onError: () => {
      toast.error("Failed to start simulation");
    },
  });

  const completeMutation = useMutation({
    mutationFn: (sessionId: string) => toolsAPI.completeSimulation(token!, sessionId),
    onSuccess: (data: any) => {
      toast.success(`Simulation completed! Score: ${data.score}%`);
      setShowSessionDialog(false);
      setActiveSession(null);
    },
    onError: () => {
      toast.error("Failed to complete simulation");
    },
  });

  if (isLoading) return <PageLoading />;

  const scenarioList: Scenario[] = (scenarios as any)?.scenarios || [];

  const difficultyColors = {
    beginner: "bg-green-500",
    intermediate: "bg-yellow-500",
    advanced: "bg-red-500",
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={t("nav.simulation")} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Introduction */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlayCircle className="h-5 w-5 text-primary" />
              Training Simulations
            </CardTitle>
            <CardDescription>
              Practice incident response procedures with realistic scenarios in a safe
              environment. All actions are logged but marked as simulations and do not
              affect production systems.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground">Filter by difficulty:</span>
              </div>
              <Select value={difficultyFilter} onValueChange={setDifficultyFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Scenarios */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenarioList.map((scenario) => (
            <ScenarioCard
              key={scenario.id}
              scenario={scenario}
              difficultyColors={difficultyColors}
              onStart={() => startMutation.mutate(scenario.id)}
              isStarting={startMutation.isPending}
            />
          ))}
        </div>

        {scenarioList.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <PlayCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">
                No scenarios available for the selected difficulty level.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Active Session Dialog */}
      <Dialog open={showSessionDialog} onOpenChange={setShowSessionDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {activeSession && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <PlayCircle className="h-5 w-5 text-primary" />
                  {activeSession.scenario.name}
                </DialogTitle>
                <DialogDescription>
                  Phase: {activeSession.current_phase} | Status: {activeSession.status}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6">
                {/* Background */}
                <div>
                  <h3 className="font-semibold mb-2">Background</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">
                    {activeSession.scenario.background}
                  </p>
                </div>

                {/* Initial Situation */}
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    Current Situation
                  </h3>
                  <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-line">
                    {activeSession.scenario.initial_situation}
                  </div>
                </div>

                {/* Objectives */}
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Objectives
                  </h3>
                  <ul className="space-y-2">
                    {activeSession.scenario.objectives.map((obj, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        {obj}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Artifacts */}
                {activeSession.artifacts && Object.keys(activeSession.artifacts).length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Available Artifacts</h3>
                    <div className="space-y-4">
                      {activeSession.artifacts.ransom_note && (
                        <div className="bg-destructive/10 border border-destructive/20 p-4 rounded-lg">
                          <h4 className="font-medium text-destructive mb-2">
                            Ransom Note: {activeSession.artifacts.ransom_note.filename}
                          </h4>
                          <pre className="text-xs whitespace-pre-wrap bg-background p-2 rounded">
                            {activeSession.artifacts.ransom_note.content}
                          </pre>
                        </div>
                      )}

                      {activeSession.artifacts.encrypted_files &&
                        activeSession.artifacts.encrypted_files.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">Encrypted Files Found:</h4>
                            <div className="grid grid-cols-2 gap-2">
                              {activeSession.artifacts.encrypted_files.map((file, i) => (
                                <div
                                  key={i}
                                  className="text-xs bg-muted p-2 rounded font-mono"
                                >
                                  {file.encrypted_name}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {activeSession.artifacts.suspicious_processes &&
                        activeSession.artifacts.suspicious_processes.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">Suspicious Processes:</h4>
                            <div className="space-y-1">
                              {activeSession.artifacts.suspicious_processes.map((proc, i) => (
                                <div
                                  key={i}
                                  className="text-xs bg-muted p-2 rounded font-mono"
                                >
                                  PID {proc.pid}: {proc.command_line}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowSessionDialog(false);
                      setActiveSession(null);
                    }}
                  >
                    Abandon Simulation
                  </Button>
                  <Button
                    onClick={() => completeMutation.mutate(activeSession.session_id)}
                    disabled={completeMutation.isPending}
                  >
                    <Award className="h-4 w-4 mr-2" />
                    Complete Simulation
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ScenarioCard({
  scenario,
  difficultyColors,
  onStart,
  isStarting,
}: {
  scenario: Scenario;
  difficultyColors: Record<string, string>;
  onStart: () => void;
  isStarting: boolean;
}) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between">
          <PlayCircle className="h-10 w-10 text-primary" />
          <Badge className={cn(difficultyColors[scenario.difficulty], "text-white")}>
            {scenario.difficulty}
          </Badge>
        </div>
        <CardTitle className="mt-4">{scenario.name}</CardTitle>
        <CardDescription>{scenario.description}</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-end space-y-4">
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {scenario.estimated_duration}
          </div>
          <div className="flex items-center gap-1">
            <Target className="h-4 w-4" />
            {scenario.objectives.length} objectives
          </div>
        </div>

        {/* Expandable Objectives */}
        <div>
          <button
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            onClick={() => setShowDetails(!showDetails)}
          >
            <ChevronRight
              className={cn("h-4 w-4 transition-transform", showDetails && "rotate-90")}
            />
            View objectives
          </button>
          {showDetails && (
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground pl-5">
              {scenario.objectives.map((obj, i) => (
                <li key={i} className="list-disc">
                  {obj}
                </li>
              ))}
            </ul>
          )}
        </div>

        <Button className="w-full" onClick={onStart} disabled={isStarting}>
          <PlayCircle className="h-4 w-4 mr-2" />
          {isStarting ? "Starting..." : "Start Simulation"}
        </Button>
      </CardContent>
    </Card>
  );
}

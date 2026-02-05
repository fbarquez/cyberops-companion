"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Save,
  AlertCircle,
  Calendar,
  Clock,
  Users,
  Target,
  CheckCircle2,
  XCircle,
  Plus,
  Trash2,
  FileText,
  Play,
  Check,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuthStore } from "@/stores/auth-store";
import { bcmAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";

// Types
interface Exercise {
  id: string;
  exercise_id: string;
  name: string;
  description: string;
  exercise_type: string;
  scenario_id: string | null;
  plan_id: string | null;
  objectives: Array<{ objective: string; met: boolean | null }>;
  scope: string;
  participants: string[];
  planned_date: string;
  planned_duration_hours: number;
  actual_date: string | null;
  actual_duration_hours: number | null;
  status: string;
  results_summary: string | null;
  objectives_met: Record<string, boolean>;
  issues_identified: Array<{ issue: string; severity: string; resolution: string }>;
  lessons_learned: string | null;
  action_items: Array<{ action: string; owner: string; due_date: string; status: string }>;
  conducted_by: string | null;
}

interface Scenario {
  id: string;
  scenario_id: string;
  name: string;
}

interface Plan {
  id: string;
  plan_id: string;
  name: string;
}

const EXERCISE_TYPE_LABELS: Record<string, string> = {
  tabletop: "Tabletop Exercise",
  walkthrough: "Walkthrough",
  simulation: "Simulation",
  parallel_test: "Parallel Test",
  full_interruption: "Full Interruption Test",
};

const EXERCISE_TYPE_DESCRIPTIONS: Record<string, string> = {
  tabletop: "Discussion-based exercise to review plans and procedures",
  walkthrough: "Step-by-step review of procedures without actual execution",
  simulation: "Simulated scenario with active response but no actual disruption",
  parallel_test: "Partial activation of backup systems alongside production",
  full_interruption: "Complete activation of recovery procedures",
};

export default function ExerciseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const exerciseId = params.id as string;
  const isNewExercise = exerciseId === "new";

  const [activeTab, setActiveTab] = useState("details");
  const [isCompleteDialogOpen, setIsCompleteDialogOpen] = useState(false);

  // Form state
  const [exerciseForm, setExerciseForm] = useState({
    exercise_id: "",
    name: "",
    description: "",
    exercise_type: "tabletop",
    scenario_id: null as string | null,
    plan_id: null as string | null,
    objectives: [] as Array<{ objective: string; met: boolean | null }>,
    scope: "",
    participants: [] as string[],
    planned_date: new Date().toISOString().split("T")[0],
    planned_duration_hours: 2,
    actual_date: null as string | null,
    actual_duration_hours: null as number | null,
    results_summary: "",
    issues_identified: [] as Array<{ issue: string; severity: string; resolution: string }>,
    lessons_learned: "",
    action_items: [] as Array<{ action: string; owner: string; due_date: string; status: string }>,
    conducted_by: "",
  });

  // Query for existing exercise
  const { data: exercise, isLoading: exerciseLoading } = useQuery<Exercise>({
    queryKey: ["bcm", "exercise", exerciseId],
    queryFn: () => bcmAPI.getExercise(token!, exerciseId) as Promise<Exercise>,
    enabled: !!token && !!exerciseId && !isNewExercise,
  });

  // Query for scenarios and plans for dropdowns
  const { data: scenariosData } = useQuery<{ scenarios: Scenario[] }>({
    queryKey: ["bcm", "scenarios"],
    queryFn: () => bcmAPI.listScenarios(token!) as Promise<{ scenarios: Scenario[] }>,
    enabled: !!token,
  });

  const { data: plansData } = useQuery<{ plans: Plan[] }>({
    queryKey: ["bcm", "plans"],
    queryFn: () => bcmAPI.listPlans(token!) as Promise<{ plans: Plan[] }>,
    enabled: !!token,
  });

  // Initialize form from exercise
  useEffect(() => {
    if (exercise) {
      setExerciseForm({
        exercise_id: exercise.exercise_id,
        name: exercise.name,
        description: exercise.description,
        exercise_type: exercise.exercise_type,
        scenario_id: exercise.scenario_id,
        plan_id: exercise.plan_id,
        objectives: exercise.objectives || [],
        scope: exercise.scope,
        participants: exercise.participants || [],
        planned_date: exercise.planned_date,
        planned_duration_hours: exercise.planned_duration_hours,
        actual_date: exercise.actual_date,
        actual_duration_hours: exercise.actual_duration_hours,
        results_summary: exercise.results_summary || "",
        issues_identified: exercise.issues_identified || [],
        lessons_learned: exercise.lessons_learned || "",
        action_items: exercise.action_items || [],
        conducted_by: exercise.conducted_by || "",
      });
    }
  }, [exercise]);

  // Mutations
  const saveExerciseMutation = useMutation({
    mutationFn: (data: typeof exerciseForm) =>
      isNewExercise
        ? bcmAPI.createExercise(token!, data)
        : bcmAPI.updateExercise(token!, exerciseId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
      if (isNewExercise && data?.id) {
        router.push(`/bcm/exercises/${data.id}`);
      }
    },
  });

  const completeExerciseMutation = useMutation({
    mutationFn: (data: {
      results_summary: string;
      objectives_met: Record<string, boolean>;
      issues_identified: Array<{ issue: string; severity: string; resolution: string }>;
      lessons_learned: string;
      action_items: Array<{ action: string; owner: string; due_date: string; status: string }>;
      actual_date: string;
      actual_duration_hours: number;
      conducted_by: string;
    }) => bcmAPI.completeExercise(token!, exerciseId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
      setIsCompleteDialogOpen(false);
      router.push("/bcm");
    },
  });

  // Helper functions
  const addObjective = () => {
    setExerciseForm({
      ...exerciseForm,
      objectives: [...exerciseForm.objectives, { objective: "", met: null }],
    });
  };

  const removeObjective = (index: number) => {
    setExerciseForm({
      ...exerciseForm,
      objectives: exerciseForm.objectives.filter((_, i) => i !== index),
    });
  };

  const updateObjective = (index: number, field: string, value: string | boolean | null) => {
    const objectives = [...exerciseForm.objectives];
    objectives[index] = { ...objectives[index], [field]: value };
    setExerciseForm({ ...exerciseForm, objectives });
  };

  const addIssue = () => {
    setExerciseForm({
      ...exerciseForm,
      issues_identified: [
        ...exerciseForm.issues_identified,
        { issue: "", severity: "medium", resolution: "" },
      ],
    });
  };

  const removeIssue = (index: number) => {
    setExerciseForm({
      ...exerciseForm,
      issues_identified: exerciseForm.issues_identified.filter((_, i) => i !== index),
    });
  };

  const updateIssue = (index: number, field: string, value: string) => {
    const issues = [...exerciseForm.issues_identified];
    issues[index] = { ...issues[index], [field]: value };
    setExerciseForm({ ...exerciseForm, issues_identified: issues });
  };

  const addActionItem = () => {
    setExerciseForm({
      ...exerciseForm,
      action_items: [
        ...exerciseForm.action_items,
        { action: "", owner: "", due_date: "", status: "pending" },
      ],
    });
  };

  const removeActionItem = (index: number) => {
    setExerciseForm({
      ...exerciseForm,
      action_items: exerciseForm.action_items.filter((_, i) => i !== index),
    });
  };

  const updateActionItem = (index: number, field: string, value: string) => {
    const items = [...exerciseForm.action_items];
    items[index] = { ...items[index], [field]: value };
    setExerciseForm({ ...exerciseForm, action_items: items });
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      planned: { variant: "outline", label: "Planned" },
      in_progress: { variant: "default", label: "In Progress" },
      completed: { variant: "default", label: "Completed" },
      cancelled: { variant: "secondary", label: "Cancelled" },
    };
    const statusConfig = config[status] || { variant: "secondary", label: status };
    return <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>;
  };

  const handleComplete = () => {
    const objectivesMet: Record<string, boolean> = {};
    exerciseForm.objectives.forEach((obj, idx) => {
      objectivesMet[`objective_${idx}`] = obj.met === true;
    });

    completeExerciseMutation.mutate({
      results_summary: exerciseForm.results_summary,
      objectives_met: objectivesMet,
      issues_identified: exerciseForm.issues_identified,
      lessons_learned: exerciseForm.lessons_learned,
      action_items: exerciseForm.action_items,
      actual_date: exerciseForm.actual_date || new Date().toISOString().split("T")[0],
      actual_duration_hours: exerciseForm.actual_duration_hours || exerciseForm.planned_duration_hours,
      conducted_by: exerciseForm.conducted_by,
    });
  };

  if (exerciseLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading exercise...</div>
      </div>
    );
  }

  if (!isNewExercise && !exercise) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Exercise not found</p>
        <Button onClick={() => router.push("/bcm")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to BCM
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header
        title={isNewExercise ? "Schedule Exercise" : exerciseForm.name}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/bcm")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            {!isNewExercise && exercise?.status === "planned" && (
              <Button variant="outline" onClick={() => setIsCompleteDialogOpen(true)}>
                <Check className="h-4 w-4 mr-2" />
                Complete Exercise
              </Button>
            )}
            <Button
              onClick={() => saveExerciseMutation.mutate(exerciseForm)}
              disabled={saveExerciseMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {saveExerciseMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        {!isNewExercise && exercise && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm font-mono text-muted-foreground">{exercise.exercise_id}</span>
            {getStatusBadge(exercise.status)}
            <Badge variant="outline">
              {EXERCISE_TYPE_LABELS[exercise.exercise_type] || exercise.exercise_type}
            </Badge>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="objectives">Objectives</TabsTrigger>
            {(!isNewExercise && exercise?.status === "completed") && (
              <TabsTrigger value="results">Results</TabsTrigger>
            )}
            <TabsTrigger value="actions">Action Items</TabsTrigger>
          </TabsList>

          {/* Details Tab */}
          <TabsContent value="details" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Exercise Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Exercise ID</Label>
                      <Input
                        value={exerciseForm.exercise_id}
                        onChange={(e) =>
                          setExerciseForm({ ...exerciseForm, exercise_id: e.target.value })
                        }
                        placeholder="e.g., EX-2024-001"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Exercise Type</Label>
                      <Select
                        value={exerciseForm.exercise_type}
                        onValueChange={(value) =>
                          setExerciseForm({ ...exerciseForm, exercise_type: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(EXERCISE_TYPE_LABELS).map(([value, label]) => (
                            <SelectItem key={value} value={value}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {EXERCISE_TYPE_DESCRIPTIONS[exerciseForm.exercise_type]}
                  </p>

                  <div className="space-y-2">
                    <Label>Exercise Name</Label>
                    <Input
                      value={exerciseForm.name}
                      onChange={(e) => setExerciseForm({ ...exerciseForm, name: e.target.value })}
                      placeholder="Enter exercise name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={exerciseForm.description}
                      onChange={(e) =>
                        setExerciseForm({ ...exerciseForm, description: e.target.value })
                      }
                      placeholder="Describe the exercise scenario and goals"
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Scope</Label>
                    <Textarea
                      value={exerciseForm.scope}
                      onChange={(e) => setExerciseForm({ ...exerciseForm, scope: e.target.value })}
                      placeholder="What is included/excluded from this exercise"
                      rows={2}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Scheduling</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Planned Date</Label>
                      <Input
                        type="date"
                        value={exerciseForm.planned_date}
                        onChange={(e) =>
                          setExerciseForm({ ...exerciseForm, planned_date: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Planned Duration (hours)</Label>
                      <Input
                        type="number"
                        min="1"
                        value={exerciseForm.planned_duration_hours}
                        onChange={(e) =>
                          setExerciseForm({
                            ...exerciseForm,
                            planned_duration_hours: parseInt(e.target.value) || 1,
                          })
                        }
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Related Scenario</Label>
                    <Select
                      value={exerciseForm.scenario_id || "none"}
                      onValueChange={(value) =>
                        setExerciseForm({
                          ...exerciseForm,
                          scenario_id: value === "none" ? null : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a scenario" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No scenario</SelectItem>
                        {scenariosData?.scenarios?.map((scenario) => (
                          <SelectItem key={scenario.id} value={scenario.id}>
                            {scenario.scenario_id} - {scenario.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Related Plan</Label>
                    <Select
                      value={exerciseForm.plan_id || "none"}
                      onValueChange={(value) =>
                        setExerciseForm({
                          ...exerciseForm,
                          plan_id: value === "none" ? null : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a plan" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No plan</SelectItem>
                        {plansData?.plans?.map((plan) => (
                          <SelectItem key={plan.id} value={plan.id}>
                            {plan.plan_id} - {plan.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Participants</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add participant..."
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && e.currentTarget.value) {
                            setExerciseForm({
                              ...exerciseForm,
                              participants: [...exerciseForm.participants, e.currentTarget.value],
                            });
                            e.currentTarget.value = "";
                          }
                        }}
                      />
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {exerciseForm.participants.map((participant, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="cursor-pointer"
                          onClick={() =>
                            setExerciseForm({
                              ...exerciseForm,
                              participants: exerciseForm.participants.filter((_, i) => i !== idx),
                            })
                          }
                        >
                          <Users className="h-3 w-3 mr-1" />
                          {participant} &times;
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Objectives Tab */}
          <TabsContent value="objectives" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Exercise Objectives</CardTitle>
                  <CardDescription>What do you want to test or achieve?</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={addObjective}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Objective
                </Button>
              </CardHeader>
              <CardContent>
                {exerciseForm.objectives.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No objectives defined</p>
                ) : (
                  <div className="space-y-4">
                    {exerciseForm.objectives.map((obj, idx) => (
                      <div key={idx} className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-bold">
                          {idx + 1}
                        </div>
                        <div className="flex-1 space-y-2">
                          <Input
                            value={obj.objective}
                            onChange={(e) => updateObjective(idx, "objective", e.target.value)}
                            placeholder="Describe the objective"
                          />
                          {!isNewExercise && exercise?.status === "completed" && (
                            <div className="flex items-center gap-4">
                              <Label className="text-sm">Met?</Label>
                              <div className="flex items-center gap-2">
                                <Checkbox
                                  checked={obj.met === true}
                                  onCheckedChange={(checked) =>
                                    updateObjective(idx, "met", checked ? true : false)
                                  }
                                />
                                <span className="text-sm">Yes</span>
                              </div>
                            </div>
                          )}
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => removeObjective(idx)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Results Tab */}
          {(!isNewExercise && exercise?.status === "completed") && (
            <TabsContent value="results" className="space-y-6 mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Exercise Results</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Actual Date</Label>
                      <Input type="date" value={exerciseForm.actual_date || ""} readOnly />
                    </div>
                    <div className="space-y-2">
                      <Label>Actual Duration (hours)</Label>
                      <Input
                        type="number"
                        value={exerciseForm.actual_duration_hours || ""}
                        readOnly
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Conducted By</Label>
                    <Input value={exerciseForm.conducted_by} readOnly />
                  </div>

                  <div className="space-y-2">
                    <Label>Results Summary</Label>
                    <Textarea value={exerciseForm.results_summary} rows={4} readOnly />
                  </div>

                  <div className="space-y-2">
                    <Label>Lessons Learned</Label>
                    <Textarea value={exerciseForm.lessons_learned} rows={4} readOnly />
                  </div>
                </CardContent>
              </Card>

              {/* Issues Identified */}
              <Card>
                <CardHeader>
                  <CardTitle>Issues Identified</CardTitle>
                </CardHeader>
                <CardContent>
                  {exerciseForm.issues_identified.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No issues identified</p>
                  ) : (
                    <div className="space-y-4">
                      {exerciseForm.issues_identified.map((issue, idx) => (
                        <Card key={idx}>
                          <CardContent className="pt-4">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{issue.issue}</span>
                                  <Badge
                                    variant={
                                      issue.severity === "high"
                                        ? "destructive"
                                        : issue.severity === "medium"
                                        ? "default"
                                        : "secondary"
                                    }
                                  >
                                    {issue.severity}
                                  </Badge>
                                </div>
                                {issue.resolution && (
                                  <p className="text-sm text-muted-foreground mt-1">
                                    Resolution: {issue.resolution}
                                  </p>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Action Items Tab */}
          <TabsContent value="actions" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Action Items</CardTitle>
                  <CardDescription>Follow-up actions from this exercise</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={addActionItem}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Action
                </Button>
              </CardHeader>
              <CardContent>
                {exerciseForm.action_items.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No action items</p>
                ) : (
                  <div className="space-y-4">
                    {exerciseForm.action_items.map((item, idx) => (
                      <Card key={idx}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-4">
                            <Target className="h-5 w-5 text-muted-foreground mt-2" />
                            <div className="flex-1 space-y-4">
                              <div className="space-y-2">
                                <Label>Action</Label>
                                <Input
                                  value={item.action}
                                  onChange={(e) => updateActionItem(idx, "action", e.target.value)}
                                  placeholder="What needs to be done"
                                />
                              </div>
                              <div className="grid grid-cols-3 gap-4">
                                <div className="space-y-2">
                                  <Label>Owner</Label>
                                  <Input
                                    value={item.owner}
                                    onChange={(e) => updateActionItem(idx, "owner", e.target.value)}
                                    placeholder="Who is responsible"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label>Due Date</Label>
                                  <Input
                                    type="date"
                                    value={item.due_date}
                                    onChange={(e) =>
                                      updateActionItem(idx, "due_date", e.target.value)
                                    }
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label>Status</Label>
                                  <Select
                                    value={item.status}
                                    onValueChange={(value) => updateActionItem(idx, "status", value)}
                                  >
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="pending">Pending</SelectItem>
                                      <SelectItem value="in_progress">In Progress</SelectItem>
                                      <SelectItem value="completed">Completed</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeActionItem(idx)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Complete Exercise Dialog */}
      <Dialog open={isCompleteDialogOpen} onOpenChange={setIsCompleteDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Complete Exercise</DialogTitle>
            <DialogDescription>
              Record the results and outcomes of the exercise.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Actual Date</Label>
                <Input
                  type="date"
                  value={exerciseForm.actual_date || new Date().toISOString().split("T")[0]}
                  onChange={(e) =>
                    setExerciseForm({ ...exerciseForm, actual_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Actual Duration (hours)</Label>
                <Input
                  type="number"
                  min="0"
                  value={exerciseForm.actual_duration_hours || exerciseForm.planned_duration_hours}
                  onChange={(e) =>
                    setExerciseForm({
                      ...exerciseForm,
                      actual_duration_hours: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Conducted By</Label>
              <Input
                value={exerciseForm.conducted_by}
                onChange={(e) => setExerciseForm({ ...exerciseForm, conducted_by: e.target.value })}
                placeholder="Name of exercise facilitator"
              />
            </div>

            <div className="space-y-2">
              <Label>Results Summary</Label>
              <Textarea
                value={exerciseForm.results_summary}
                onChange={(e) =>
                  setExerciseForm({ ...exerciseForm, results_summary: e.target.value })
                }
                placeholder="Summarize the exercise results..."
                rows={3}
              />
            </div>

            {/* Objectives Met */}
            <div className="space-y-2">
              <Label>Objectives Met</Label>
              <div className="space-y-2">
                {exerciseForm.objectives.map((obj, idx) => (
                  <div key={idx} className="flex items-center gap-4 p-2 bg-muted rounded">
                    <Checkbox
                      checked={obj.met === true}
                      onCheckedChange={(checked) => updateObjective(idx, "met", checked ? true : false)}
                    />
                    <span className="flex-1 text-sm">{obj.objective || `Objective ${idx + 1}`}</span>
                    {obj.met === true ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : obj.met === false ? (
                      <XCircle className="h-4 w-4 text-red-500" />
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            {/* Issues Identified */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Issues Identified</Label>
                <Button variant="outline" size="sm" onClick={addIssue}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Issue
                </Button>
              </div>
              {exerciseForm.issues_identified.map((issue, idx) => (
                <div key={idx} className="flex gap-2 items-start">
                  <Input
                    value={issue.issue}
                    onChange={(e) => updateIssue(idx, "issue", e.target.value)}
                    placeholder="Describe the issue"
                    className="flex-1"
                  />
                  <Select
                    value={issue.severity}
                    onValueChange={(value) => updateIssue(idx, "severity", value)}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" onClick={() => removeIssue(idx)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Label>Lessons Learned</Label>
              <Textarea
                value={exerciseForm.lessons_learned}
                onChange={(e) =>
                  setExerciseForm({ ...exerciseForm, lessons_learned: e.target.value })
                }
                placeholder="What was learned from this exercise..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCompleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleComplete}
              disabled={completeExerciseMutation.isPending}
            >
              {completeExerciseMutation.isPending ? "Completing..." : "Complete Exercise"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Save,
  AlertCircle,
  FileText,
  Plus,
  Trash2,
  Check,
  Phone,
  Users,
  Clock,
  CheckSquare,
  Download,
  Shield,
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useAuthStore } from "@/stores/auth-store";
import { bcmAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";

// Types
interface Plan {
  id: string;
  plan_id: string;
  name: string;
  description: string | null;
  plan_type: string;
  scope_description: string;
  affected_processes: string[];
  affected_locations: string[];
  activation_criteria: Array<{ condition: string; threshold: string }>;
  response_phases: Array<{
    phase: string;
    duration: string;
    activities: string[];
    responsible: string;
  }>;
  procedures: Array<{ step: number; action: string; responsible: string; notes: string }>;
  roles_responsibilities: Array<{ role: string; responsibilities: string[]; contact: string }>;
  communication_tree: Array<{ level: number; role: string; contacts: string[] }>;
  contact_list: Array<{ name: string; role: string; phone: string; email: string }>;
  resources_required: Array<{ resource: string; quantity: string; source: string }>;
  activation_checklist: Array<{ item: string; completed: boolean }>;
  recovery_checklist: Array<{ item: string; completed: boolean }>;
  version: string;
  effective_date: string;
  review_date: string;
  status: string;
  approved_by: string | null;
  approved_at: string | null;
}

const PLAN_TYPE_LABELS: Record<string, string> = {
  crisis_management: "Crisis Management",
  emergency_response: "Emergency Response",
  business_recovery: "Business Recovery",
  it_disaster_recovery: "IT Disaster Recovery",
  communication: "Communication",
  evacuation: "Evacuation",
};

export default function PlanEditorPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const planId = params.id as string;
  const isNewPlan = planId === "new";

  const [activeTab, setActiveTab] = useState("overview");
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);

  // Form state
  const [planForm, setPlanForm] = useState({
    plan_id: "",
    name: "",
    description: "",
    plan_type: "emergency_response",
    scope_description: "",
    affected_processes: [] as string[],
    affected_locations: [] as string[],
    activation_criteria: [] as Array<{ condition: string; threshold: string }>,
    response_phases: [] as Array<{
      phase: string;
      duration: string;
      activities: string[];
      responsible: string;
    }>,
    procedures: [] as Array<{ step: number; action: string; responsible: string; notes: string }>,
    roles_responsibilities: [] as Array<{ role: string; responsibilities: string[]; contact: string }>,
    communication_tree: [] as Array<{ level: number; role: string; contacts: string[] }>,
    contact_list: [] as Array<{ name: string; role: string; phone: string; email: string }>,
    resources_required: [] as Array<{ resource: string; quantity: string; source: string }>,
    activation_checklist: [] as Array<{ item: string; completed: boolean }>,
    recovery_checklist: [] as Array<{ item: string; completed: boolean }>,
    version: "1.0",
    effective_date: new Date().toISOString().split("T")[0],
    review_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
  });

  // Query for existing plan
  const { data: plan, isLoading: planLoading } = useQuery<Plan>({
    queryKey: ["bcm", "plan", planId],
    queryFn: () => bcmAPI.getPlan(token!, planId) as Promise<Plan>,
    enabled: !!token && !!planId && !isNewPlan,
  });

  // Initialize form from plan
  useEffect(() => {
    if (plan) {
      setPlanForm({
        plan_id: plan.plan_id,
        name: plan.name,
        description: plan.description || "",
        plan_type: plan.plan_type,
        scope_description: plan.scope_description,
        affected_processes: plan.affected_processes || [],
        affected_locations: plan.affected_locations || [],
        activation_criteria: plan.activation_criteria || [],
        response_phases: plan.response_phases || [],
        procedures: plan.procedures || [],
        roles_responsibilities: plan.roles_responsibilities || [],
        communication_tree: plan.communication_tree || [],
        contact_list: plan.contact_list || [],
        resources_required: plan.resources_required || [],
        activation_checklist: plan.activation_checklist || [],
        recovery_checklist: plan.recovery_checklist || [],
        version: plan.version,
        effective_date: plan.effective_date,
        review_date: plan.review_date,
      });
    }
  }, [plan]);

  // Mutations
  const savePlanMutation = useMutation({
    mutationFn: (data: typeof planForm) =>
      isNewPlan
        ? bcmAPI.createPlan(token!, data)
        : bcmAPI.updatePlan(token!, planId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
      if (isNewPlan && data?.id) {
        router.push(`/bcm/plans/${data.id}`);
      }
    },
  });

  const approvePlanMutation = useMutation({
    mutationFn: () => bcmAPI.approvePlan(token!, planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm", "plan", planId] });
      setIsApproveDialogOpen(false);
    },
  });

  const exportPdfMutation = useMutation({
    mutationFn: () => bcmAPI.exportPlanPdf(token!, planId),
    onSuccess: (data) => {
      // Handle PDF download
      const blob = new Blob([data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${plan?.plan_id || "plan"}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
  });

  // Helper functions for managing arrays
  const addArrayItem = <T,>(field: keyof typeof planForm, item: T) => {
    setPlanForm({
      ...planForm,
      [field]: [...(planForm[field] as T[]), item],
    });
  };

  const removeArrayItem = (field: keyof typeof planForm, index: number) => {
    setPlanForm({
      ...planForm,
      [field]: (planForm[field] as unknown[]).filter((_, i) => i !== index),
    });
  };

  const updateArrayItem = <T,>(field: keyof typeof planForm, index: number, item: T) => {
    const arr = [...(planForm[field] as T[])];
    arr[index] = item;
    setPlanForm({ ...planForm, [field]: arr });
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      draft: { variant: "secondary", label: "Draft" },
      review: { variant: "outline", label: "Under Review" },
      approved: { variant: "default", label: "Approved" },
      active: { variant: "default", label: "Active" },
      archived: { variant: "secondary", label: "Archived" },
    };
    const statusConfig = config[status] || { variant: "secondary", label: status };
    return <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>;
  };

  if (planLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading plan...</div>
      </div>
    );
  }

  if (!isNewPlan && !plan) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Plan not found</p>
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
        title={isNewPlan ? "Create Emergency Plan" : planForm.name}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/bcm")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            {!isNewPlan && plan?.status !== "approved" && (
              <Button variant="outline" onClick={() => setIsApproveDialogOpen(true)}>
                <Check className="h-4 w-4 mr-2" />
                Approve
              </Button>
            )}
            {!isNewPlan && (
              <Button
                variant="outline"
                onClick={() => exportPdfMutation.mutate()}
                disabled={exportPdfMutation.isPending}
              >
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
            )}
            <Button
              onClick={() => savePlanMutation.mutate(planForm)}
              disabled={savePlanMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {savePlanMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        {!isNewPlan && plan && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm font-mono text-muted-foreground">{plan.plan_id}</span>
            {getStatusBadge(plan.status)}
            <Badge variant="outline">v{plan.version}</Badge>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="flex-wrap">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="phases">Phases</TabsTrigger>
            <TabsTrigger value="procedures">Procedures</TabsTrigger>
            <TabsTrigger value="roles">Roles</TabsTrigger>
            <TabsTrigger value="contacts">Contacts</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
            <TabsTrigger value="checklists">Checklists</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Plan Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Plan ID</Label>
                      <Input
                        value={planForm.plan_id}
                        onChange={(e) => setPlanForm({ ...planForm, plan_id: e.target.value })}
                        placeholder="e.g., PLAN-001"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Plan Type</Label>
                      <Select
                        value={planForm.plan_type}
                        onValueChange={(value) => setPlanForm({ ...planForm, plan_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(PLAN_TYPE_LABELS).map(([value, label]) => (
                            <SelectItem key={value} value={value}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Plan Name</Label>
                    <Input
                      value={planForm.name}
                      onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                      placeholder="Enter plan name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={planForm.description}
                      onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                      placeholder="Brief description of the plan"
                      rows={3}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Version</Label>
                      <Input
                        value={planForm.version}
                        onChange={(e) => setPlanForm({ ...planForm, version: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Effective Date</Label>
                      <Input
                        type="date"
                        value={planForm.effective_date}
                        onChange={(e) =>
                          setPlanForm({ ...planForm, effective_date: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Review Date</Label>
                    <Input
                      type="date"
                      value={planForm.review_date}
                      onChange={(e) => setPlanForm({ ...planForm, review_date: e.target.value })}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Scope</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Scope Description</Label>
                    <Textarea
                      value={planForm.scope_description}
                      onChange={(e) =>
                        setPlanForm({ ...planForm, scope_description: e.target.value })
                      }
                      placeholder="Describe the scope of this plan"
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Affected Processes</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add process..."
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && e.currentTarget.value) {
                            setPlanForm({
                              ...planForm,
                              affected_processes: [
                                ...planForm.affected_processes,
                                e.currentTarget.value,
                              ],
                            });
                            e.currentTarget.value = "";
                          }
                        }}
                      />
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {planForm.affected_processes.map((proc, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="cursor-pointer"
                          onClick={() =>
                            setPlanForm({
                              ...planForm,
                              affected_processes: planForm.affected_processes.filter(
                                (_, i) => i !== idx
                              ),
                            })
                          }
                        >
                          {proc} &times;
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Affected Locations</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add location..."
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && e.currentTarget.value) {
                            setPlanForm({
                              ...planForm,
                              affected_locations: [
                                ...planForm.affected_locations,
                                e.currentTarget.value,
                              ],
                            });
                            e.currentTarget.value = "";
                          }
                        }}
                      />
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {planForm.affected_locations.map((loc, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="cursor-pointer"
                          onClick={() =>
                            setPlanForm({
                              ...planForm,
                              affected_locations: planForm.affected_locations.filter(
                                (_, i) => i !== idx
                              ),
                            })
                          }
                        >
                          {loc} &times;
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Activation Criteria */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Activation Criteria</CardTitle>
                  <CardDescription>When should this plan be activated?</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("activation_criteria", { condition: "", threshold: "" })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Criterion
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.activation_criteria.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No activation criteria defined</p>
                ) : (
                  <div className="space-y-4">
                    {planForm.activation_criteria.map((criterion, idx) => (
                      <div key={idx} className="flex gap-4 items-start">
                        <div className="flex-1 space-y-2">
                          <Label>Condition</Label>
                          <Input
                            value={criterion.condition}
                            onChange={(e) =>
                              updateArrayItem("activation_criteria", idx, {
                                ...criterion,
                                condition: e.target.value,
                              })
                            }
                            placeholder="e.g., Primary data center unavailable"
                          />
                        </div>
                        <div className="flex-1 space-y-2">
                          <Label>Threshold</Label>
                          <Input
                            value={criterion.threshold}
                            onChange={(e) =>
                              updateArrayItem("activation_criteria", idx, {
                                ...criterion,
                                threshold: e.target.value,
                              })
                            }
                            placeholder="e.g., > 4 hours"
                          />
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="mt-8"
                          onClick={() => removeArrayItem("activation_criteria", idx)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Phases Tab */}
          <TabsContent value="phases" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Response Phases</CardTitle>
                  <CardDescription>Define the phases of the response</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("response_phases", {
                      phase: "",
                      duration: "",
                      activities: [],
                      responsible: "",
                    })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Phase
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.response_phases.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No phases defined</p>
                ) : (
                  <Accordion type="single" collapsible className="space-y-2">
                    {planForm.response_phases.map((phase, idx) => (
                      <AccordionItem key={idx} value={`phase-${idx}`} className="border rounded-lg">
                        <AccordionTrigger className="px-4 hover:no-underline">
                          <div className="flex items-center gap-4">
                            <Badge variant="outline">Phase {idx + 1}</Badge>
                            <span>{phase.phase || "Unnamed Phase"}</span>
                            <span className="text-muted-foreground text-sm">
                              {phase.duration}
                            </span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="px-4 pb-4">
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Phase Name</Label>
                                <Input
                                  value={phase.phase}
                                  onChange={(e) =>
                                    updateArrayItem("response_phases", idx, {
                                      ...phase,
                                      phase: e.target.value,
                                    })
                                  }
                                  placeholder="e.g., Initial Response"
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Duration</Label>
                                <Input
                                  value={phase.duration}
                                  onChange={(e) =>
                                    updateArrayItem("response_phases", idx, {
                                      ...phase,
                                      duration: e.target.value,
                                    })
                                  }
                                  placeholder="e.g., 0-4 hours"
                                />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <Label>Responsible</Label>
                              <Input
                                value={phase.responsible}
                                onChange={(e) =>
                                  updateArrayItem("response_phases", idx, {
                                    ...phase,
                                    responsible: e.target.value,
                                  })
                                }
                                placeholder="e.g., Crisis Manager"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Activities</Label>
                              <Textarea
                                value={phase.activities.join("\n")}
                                onChange={(e) =>
                                  updateArrayItem("response_phases", idx, {
                                    ...phase,
                                    activities: e.target.value.split("\n").filter((a) => a.trim()),
                                  })
                                }
                                placeholder="Enter activities, one per line"
                                rows={4}
                              />
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive"
                              onClick={() => removeArrayItem("response_phases", idx)}
                            >
                              <Trash2 className="h-4 w-4 mr-1" />
                              Remove Phase
                            </Button>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Procedures Tab */}
          <TabsContent value="procedures" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Response Procedures</CardTitle>
                  <CardDescription>Step-by-step procedures to follow</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("procedures", {
                      step: planForm.procedures.length + 1,
                      action: "",
                      responsible: "",
                      notes: "",
                    })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Step
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.procedures.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No procedures defined</p>
                ) : (
                  <div className="space-y-4">
                    {planForm.procedures.map((proc, idx) => (
                      <Card key={idx}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-4">
                            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                              {idx + 1}
                            </div>
                            <div className="flex-1 space-y-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                  <Label>Action</Label>
                                  <Input
                                    value={proc.action}
                                    onChange={(e) =>
                                      updateArrayItem("procedures", idx, {
                                        ...proc,
                                        action: e.target.value,
                                      })
                                    }
                                    placeholder="What needs to be done"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label>Responsible</Label>
                                  <Input
                                    value={proc.responsible}
                                    onChange={(e) =>
                                      updateArrayItem("procedures", idx, {
                                        ...proc,
                                        responsible: e.target.value,
                                      })
                                    }
                                    placeholder="Who does it"
                                  />
                                </div>
                              </div>
                              <div className="space-y-2">
                                <Label>Notes</Label>
                                <Textarea
                                  value={proc.notes}
                                  onChange={(e) =>
                                    updateArrayItem("procedures", idx, {
                                      ...proc,
                                      notes: e.target.value,
                                    })
                                  }
                                  placeholder="Additional notes or details"
                                  rows={2}
                                />
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeArrayItem("procedures", idx)}
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

          {/* Roles Tab */}
          <TabsContent value="roles" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Roles & Responsibilities</CardTitle>
                  <CardDescription>Define team roles and their responsibilities</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("roles_responsibilities", {
                      role: "",
                      responsibilities: [],
                      contact: "",
                    })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Role
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.roles_responsibilities.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No roles defined</p>
                ) : (
                  <div className="space-y-4">
                    {planForm.roles_responsibilities.map((role, idx) => (
                      <Card key={idx}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-4">
                            <Users className="h-5 w-5 text-muted-foreground mt-2" />
                            <div className="flex-1 space-y-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                  <Label>Role</Label>
                                  <Input
                                    value={role.role}
                                    onChange={(e) =>
                                      updateArrayItem("roles_responsibilities", idx, {
                                        ...role,
                                        role: e.target.value,
                                      })
                                    }
                                    placeholder="e.g., Crisis Manager"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label>Contact</Label>
                                  <Input
                                    value={role.contact}
                                    onChange={(e) =>
                                      updateArrayItem("roles_responsibilities", idx, {
                                        ...role,
                                        contact: e.target.value,
                                      })
                                    }
                                    placeholder="e.g., John Smith"
                                  />
                                </div>
                              </div>
                              <div className="space-y-2">
                                <Label>Responsibilities</Label>
                                <Textarea
                                  value={role.responsibilities.join("\n")}
                                  onChange={(e) =>
                                    updateArrayItem("roles_responsibilities", idx, {
                                      ...role,
                                      responsibilities: e.target.value
                                        .split("\n")
                                        .filter((r) => r.trim()),
                                    })
                                  }
                                  placeholder="Enter responsibilities, one per line"
                                  rows={3}
                                />
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeArrayItem("roles_responsibilities", idx)}
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

          {/* Contacts Tab */}
          <TabsContent value="contacts" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Emergency Contacts</CardTitle>
                  <CardDescription>Key contacts for this plan</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("contact_list", { name: "", role: "", phone: "", email: "" })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Contact
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.contact_list.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No contacts added</p>
                ) : (
                  <div className="space-y-4">
                    {planForm.contact_list.map((contact, idx) => (
                      <Card key={idx}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-4">
                            <Phone className="h-5 w-5 text-muted-foreground mt-2" />
                            <div className="flex-1 grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Name</Label>
                                <Input
                                  value={contact.name}
                                  onChange={(e) =>
                                    updateArrayItem("contact_list", idx, {
                                      ...contact,
                                      name: e.target.value,
                                    })
                                  }
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Role</Label>
                                <Input
                                  value={contact.role}
                                  onChange={(e) =>
                                    updateArrayItem("contact_list", idx, {
                                      ...contact,
                                      role: e.target.value,
                                    })
                                  }
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Phone</Label>
                                <Input
                                  value={contact.phone}
                                  onChange={(e) =>
                                    updateArrayItem("contact_list", idx, {
                                      ...contact,
                                      phone: e.target.value,
                                    })
                                  }
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Email</Label>
                                <Input
                                  value={contact.email}
                                  onChange={(e) =>
                                    updateArrayItem("contact_list", idx, {
                                      ...contact,
                                      email: e.target.value,
                                    })
                                  }
                                />
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeArrayItem("contact_list", idx)}
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

          {/* Resources Tab */}
          <TabsContent value="resources" className="space-y-6 mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Required Resources</CardTitle>
                  <CardDescription>Resources needed to execute this plan</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    addArrayItem("resources_required", { resource: "", quantity: "", source: "" })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Resource
                </Button>
              </CardHeader>
              <CardContent>
                {planForm.resources_required.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No resources defined</p>
                ) : (
                  <div className="space-y-4">
                    {planForm.resources_required.map((resource, idx) => (
                      <div key={idx} className="flex gap-4 items-start">
                        <div className="flex-1 space-y-2">
                          <Label>Resource</Label>
                          <Input
                            value={resource.resource}
                            onChange={(e) =>
                              updateArrayItem("resources_required", idx, {
                                ...resource,
                                resource: e.target.value,
                              })
                            }
                            placeholder="e.g., Laptops"
                          />
                        </div>
                        <div className="w-32 space-y-2">
                          <Label>Quantity</Label>
                          <Input
                            value={resource.quantity}
                            onChange={(e) =>
                              updateArrayItem("resources_required", idx, {
                                ...resource,
                                quantity: e.target.value,
                              })
                            }
                            placeholder="e.g., 10"
                          />
                        </div>
                        <div className="flex-1 space-y-2">
                          <Label>Source</Label>
                          <Input
                            value={resource.source}
                            onChange={(e) =>
                              updateArrayItem("resources_required", idx, {
                                ...resource,
                                source: e.target.value,
                              })
                            }
                            placeholder="e.g., IT Storage"
                          />
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="mt-8"
                          onClick={() => removeArrayItem("resources_required", idx)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Checklists Tab */}
          <TabsContent value="checklists" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Activation Checklist */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Activation Checklist</CardTitle>
                    <CardDescription>Steps to activate the plan</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      addArrayItem("activation_checklist", { item: "", completed: false })
                    }
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </CardHeader>
                <CardContent>
                  {planForm.activation_checklist.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No items</p>
                  ) : (
                    <div className="space-y-2">
                      {planForm.activation_checklist.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <CheckSquare className="h-4 w-4 text-muted-foreground" />
                          <Input
                            value={item.item}
                            onChange={(e) =>
                              updateArrayItem("activation_checklist", idx, {
                                ...item,
                                item: e.target.value,
                              })
                            }
                            placeholder="Checklist item"
                            className="flex-1"
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeArrayItem("activation_checklist", idx)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recovery Checklist */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Recovery Checklist</CardTitle>
                    <CardDescription>Steps to recover operations</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      addArrayItem("recovery_checklist", { item: "", completed: false })
                    }
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </CardHeader>
                <CardContent>
                  {planForm.recovery_checklist.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No items</p>
                  ) : (
                    <div className="space-y-2">
                      {planForm.recovery_checklist.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <CheckSquare className="h-4 w-4 text-muted-foreground" />
                          <Input
                            value={item.item}
                            onChange={(e) =>
                              updateArrayItem("recovery_checklist", idx, {
                                ...item,
                                item: e.target.value,
                              })
                            }
                            placeholder="Checklist item"
                            className="flex-1"
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeArrayItem("recovery_checklist", idx)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Approve Dialog */}
      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Emergency Plan</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve this plan? Once approved, it will become the active
              version.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => approvePlanMutation.mutate()}
              disabled={approvePlanMutation.isPending}
            >
              {approvePlanMutation.isPending ? "Approving..." : "Approve Plan"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

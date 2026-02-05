"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  RefreshCw,
  Plus,
  Search,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  TrendingUp,
  Building2,
  Users,
  MoreHorizontal,
  Trash2,
  Eye,
  BarChart3,
  AlertTriangle,
  Calendar,
  Phone,
  Target,
  ClipboardList,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { bcmAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";

// Types
interface DashboardStats {
  total_processes: number;
  critical_processes: number;
  processes_by_criticality: Record<string, number>;
  bia_completion_percentage: number;
  processes_with_bia: number;
  average_rto_hours: number | null;
  total_scenarios: number;
  scenarios_by_category: Record<string, number>;
  high_risk_scenarios: number;
  total_plans: number;
  active_plans: number;
  plans_by_type: Record<string, number>;
  exercises_this_year: number;
  completed_exercises: number;
  upcoming_exercises: Array<{
    id: string;
    name: string;
    planned_date: string;
    exercise_type: string;
  }>;
  total_assessments: number;
  latest_assessment_score: number | null;
  recent_activity: Array<{
    type: string;
    action: string;
    name: string;
    date: string;
  }>;
}

interface Process {
  id: string;
  process_id: string;
  name: string;
  description: string | null;
  owner: string;
  department: string | null;
  criticality: string;
  status: string;
  has_bia: boolean;
  bia_status: string | null;
  created_at: string;
}

interface ProcessListResponse {
  processes: Process[];
  total: number;
}

interface Plan {
  id: string;
  plan_id: string;
  name: string;
  description: string | null;
  plan_type: string;
  status: string;
  version: string;
  effective_date: string;
  review_date: string;
}

interface PlanListResponse {
  plans: Plan[];
  total: number;
}

interface Exercise {
  id: string;
  exercise_id: string;
  name: string;
  description: string;
  exercise_type: string;
  status: string;
  planned_date: string;
  actual_date: string | null;
}

interface ExerciseListResponse {
  exercises: Exercise[];
  total: number;
}

const CRITICALITY_COLORS: Record<string, string> = {
  critical: "text-red-500",
  high: "text-orange-500",
  medium: "text-yellow-500",
  low: "text-green-500",
};

const PLAN_TYPE_LABELS: Record<string, string> = {
  crisis_management: "Crisis Management",
  emergency_response: "Emergency Response",
  business_recovery: "Business Recovery",
  it_disaster_recovery: "IT Disaster Recovery",
  communication: "Communication",
  evacuation: "Evacuation",
};

const EXERCISE_TYPE_LABELS: Record<string, string> = {
  tabletop: "Tabletop",
  walkthrough: "Walkthrough",
  simulation: "Simulation",
  parallel_test: "Parallel Test",
  full_interruption: "Full Interruption",
};

export default function BCMPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("dashboard");
  const [isCreateProcessOpen, setIsCreateProcessOpen] = useState(false);
  const [newProcess, setNewProcess] = useState({
    process_id: "",
    name: "",
    description: "",
    owner: "",
    department: "",
    criticality: "medium",
  });

  // Queries
  const { data: dashboard, isLoading: dashboardLoading } = useQuery<DashboardStats>({
    queryKey: ["bcm", "dashboard"],
    queryFn: () => bcmAPI.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
  });

  const { data: processesData, isLoading: processesLoading } = useQuery<ProcessListResponse>({
    queryKey: ["bcm", "processes"],
    queryFn: () => bcmAPI.listProcesses(token!) as Promise<ProcessListResponse>,
    enabled: !!token,
  });

  const { data: plansData, isLoading: plansLoading } = useQuery<PlanListResponse>({
    queryKey: ["bcm", "plans"],
    queryFn: () => bcmAPI.listPlans(token!) as Promise<PlanListResponse>,
    enabled: !!token,
  });

  const { data: exercisesData, isLoading: exercisesLoading } = useQuery<ExerciseListResponse>({
    queryKey: ["bcm", "exercises"],
    queryFn: () => bcmAPI.listExercises(token!) as Promise<ExerciseListResponse>,
    enabled: !!token,
  });

  // Mutations
  const createProcessMutation = useMutation({
    mutationFn: (data: typeof newProcess) => bcmAPI.createProcess(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
      setIsCreateProcessOpen(false);
      setNewProcess({
        process_id: "",
        name: "",
        description: "",
        owner: "",
        department: "",
        criticality: "medium",
      });
    },
  });

  const deleteProcessMutation = useMutation({
    mutationFn: (id: string) => bcmAPI.deleteProcess(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
    },
  });

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-muted-foreground";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getCriticalityBadge = (criticality: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "default",
      medium: "secondary",
      low: "outline",
    };
    return (
      <Badge variant={variants[criticality] || "secondary"}>
        {criticality.charAt(0).toUpperCase() + criticality.slice(1)}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      active: { variant: "default", label: "Active" },
      inactive: { variant: "secondary", label: "Inactive" },
      under_review: { variant: "outline", label: "Under Review" },
      draft: { variant: "secondary", label: "Draft" },
      review: { variant: "outline", label: "Review" },
      approved: { variant: "default", label: "Approved" },
      archived: { variant: "secondary", label: "Archived" },
      planned: { variant: "outline", label: "Planned" },
      in_progress: { variant: "default", label: "In Progress" },
      completed: { variant: "default", label: "Completed" },
      cancelled: { variant: "secondary", label: "Cancelled" },
    };
    const statusConfig = config[status] || { variant: "secondary", label: status };
    return <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>;
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Business Continuity Management"
        actions={
          <Dialog open={isCreateProcessOpen} onOpenChange={setIsCreateProcessOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Process
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Business Process</DialogTitle>
                <DialogDescription>
                  Document a new business process for continuity planning.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="process_id">Process ID</Label>
                    <Input
                      id="process_id"
                      value={newProcess.process_id}
                      onChange={(e) => setNewProcess({ ...newProcess, process_id: e.target.value })}
                      placeholder="e.g., PROC-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="criticality">Criticality</Label>
                    <Select
                      value={newProcess.criticality}
                      onValueChange={(value) => setNewProcess({ ...newProcess, criticality: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Process Name</Label>
                  <Input
                    id="name"
                    value={newProcess.name}
                    onChange={(e) => setNewProcess({ ...newProcess, name: e.target.value })}
                    placeholder="e.g., Payment Processing"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="owner">Process Owner</Label>
                  <Input
                    id="owner"
                    value={newProcess.owner}
                    onChange={(e) => setNewProcess({ ...newProcess, owner: e.target.value })}
                    placeholder="e.g., Finance Director"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Input
                    id="department"
                    value={newProcess.department}
                    onChange={(e) => setNewProcess({ ...newProcess, department: e.target.value })}
                    placeholder="e.g., Finance"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newProcess.description}
                    onChange={(e) => setNewProcess({ ...newProcess, description: e.target.value })}
                    placeholder="Brief description of the process"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateProcessOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createProcessMutation.mutate(newProcess)}
                  disabled={!newProcess.process_id || !newProcess.name || !newProcess.owner || createProcessMutation.isPending}
                >
                  {createProcessMutation.isPending ? "Creating..." : "Create Process"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex-1 p-4 md:p-6 space-y-4 md:space-y-6 overflow-y-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="processes" className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Processes
            </TabsTrigger>
            <TabsTrigger value="plans" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Plans
            </TabsTrigger>
            <TabsTrigger value="exercises" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Exercises
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Business Processes</CardTitle>
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.total_processes || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboard?.critical_processes || 0} critical
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">BIA Completion</CardTitle>
                  <ClipboardList className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getScoreColor(dashboard?.bia_completion_percentage ?? null)}`}>
                    {dashboard?.bia_completion_percentage?.toFixed(0) || 0}%
                  </div>
                  <Progress value={dashboard?.bia_completion_percentage || 0} className="h-2 mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Active Plans</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.active_plans || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboard?.total_plans || 0} total plans
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">BCM Maturity</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getScoreColor(dashboard?.latest_assessment_score ?? null)}`}>
                    {dashboard?.latest_assessment_score !== null && dashboard?.latest_assessment_score !== undefined
                      ? `${dashboard.latest_assessment_score.toFixed(0)}%`
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Latest assessment
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Risk and Exercise Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Risk Scenarios</CardTitle>
                  <CardDescription>Documented business continuity risks</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-3xl font-bold">{dashboard?.total_scenarios || 0}</div>
                      <p className="text-sm text-muted-foreground">Total scenarios</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-red-500">
                        {dashboard?.high_risk_scenarios || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">High risk</p>
                    </div>
                  </div>
                  {dashboard?.scenarios_by_category && Object.keys(dashboard.scenarios_by_category).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(dashboard.scenarios_by_category).map(([category, count]) => (
                        <div key={category} className="flex justify-between text-sm">
                          <span className="capitalize">{category.replace(/_/g, " ")}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No scenarios documented yet</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">BC Exercises</CardTitle>
                  <CardDescription>Tests and exercises this year</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-3xl font-bold">{dashboard?.exercises_this_year || 0}</div>
                      <p className="text-sm text-muted-foreground">This year</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-500">
                        {dashboard?.completed_exercises || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Completed</p>
                    </div>
                  </div>
                  {dashboard?.upcoming_exercises && dashboard.upcoming_exercises.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Upcoming:</p>
                      {dashboard.upcoming_exercises.slice(0, 3).map((ex) => (
                        <div key={ex.id} className="flex justify-between text-sm">
                          <span>{ex.name}</span>
                          <span className="text-muted-foreground">{ex.planned_date}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No upcoming exercises</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            {dashboard?.recent_activity && dashboard.recent_activity.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {dashboard.recent_activity.slice(0, 5).map((activity, idx) => (
                      <div key={idx} className="flex items-center gap-4">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                        <div className="flex-1">
                          <p className="text-sm">
                            <span className="capitalize">{activity.type}</span>
                            {" "}
                            <span className="text-muted-foreground">{activity.action}</span>
                            {": "}
                            <span className="font-medium">{activity.name}</span>
                          </p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(activity.date).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Processes Tab */}
          <TabsContent value="processes" className="space-y-4">
            <div className="space-y-4">
              {processesLoading ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Loading processes...
                  </CardContent>
                </Card>
              ) : processesData?.processes?.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">No processes documented</p>
                    <Button onClick={() => setIsCreateProcessOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add First Process
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                processesData?.processes?.map((process) => (
                  <Card key={process.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-muted-foreground">
                              {process.process_id}
                            </span>
                            <h3 className="font-semibold">{process.name}</h3>
                            {getCriticalityBadge(process.criticality)}
                            {getStatusBadge(process.status)}
                          </div>
                          {process.description && (
                            <p className="text-sm text-muted-foreground">{process.description}</p>
                          )}
                          <div className="flex flex-wrap gap-4 text-sm">
                            <div className="flex items-center gap-1">
                              <Users className="h-4 w-4 text-muted-foreground" />
                              <span>{process.owner}</span>
                            </div>
                            {process.department && (
                              <div className="flex items-center gap-1">
                                <Building2 className="h-4 w-4 text-muted-foreground" />
                                <span>{process.department}</span>
                              </div>
                            )}
                            <div className="flex items-center gap-1">
                              {process.has_bia ? (
                                <>
                                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                                  <span>BIA: {process.bia_status}</span>
                                </>
                              ) : (
                                <>
                                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                                  <span>No BIA</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => router.push(`/bcm/processes/${process.id}`)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => router.push(`/bcm/bia/${process.id}`)}>
                              <ClipboardList className="h-4 w-4 mr-2" />
                              {process.has_bia ? "Edit BIA" : "Create BIA"}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => deleteProcessMutation.mutate(process.id)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Plans Tab */}
          <TabsContent value="plans" className="space-y-4">
            <div className="space-y-4">
              {plansLoading ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Loading plans...
                  </CardContent>
                </Card>
              ) : plansData?.plans?.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">No emergency plans documented</p>
                    <Button onClick={() => router.push("/bcm/plans/new")}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create First Plan
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                plansData?.plans?.map((plan) => (
                  <Card key={plan.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-muted-foreground">
                              {plan.plan_id}
                            </span>
                            <h3 className="font-semibold">{plan.name}</h3>
                            {getStatusBadge(plan.status)}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {PLAN_TYPE_LABELS[plan.plan_type] || plan.plan_type}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              Version {plan.version}
                            </span>
                          </div>
                          {plan.description && (
                            <p className="text-sm text-muted-foreground">{plan.description}</p>
                          )}
                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              <span>Effective: {plan.effective_date}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              <span>Review: {plan.review_date}</span>
                            </div>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => router.push(`/bcm/plans/${plan.id}`)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View/Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => bcmAPI.deletePlan(token!, plan.id).then(() => queryClient.invalidateQueries({ queryKey: ["bcm"] }))}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Exercises Tab */}
          <TabsContent value="exercises" className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => router.push("/bcm/exercises/new")}>
                <Plus className="h-4 w-4 mr-2" />
                Schedule Exercise
              </Button>
            </div>
            <div className="space-y-4">
              {exercisesLoading ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Loading exercises...
                  </CardContent>
                </Card>
              ) : exercisesData?.exercises?.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Target className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">No exercises scheduled</p>
                    <Button onClick={() => router.push("/bcm/exercises/new")}>
                      <Plus className="h-4 w-4 mr-2" />
                      Schedule First Exercise
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                exercisesData?.exercises?.map((exercise) => (
                  <Card key={exercise.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-muted-foreground">
                              {exercise.exercise_id}
                            </span>
                            <h3 className="font-semibold">{exercise.name}</h3>
                            {getStatusBadge(exercise.status)}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {EXERCISE_TYPE_LABELS[exercise.exercise_type] || exercise.exercise_type}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{exercise.description}</p>
                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              <span>
                                {exercise.actual_date
                                  ? `Conducted: ${exercise.actual_date}`
                                  : `Planned: ${exercise.planned_date}`}
                              </span>
                            </div>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => router.push(`/bcm/exercises/${exercise.id}`)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => bcmAPI.deleteExercise(token!, exercise.id).then(() => queryClient.invalidateQueries({ queryKey: ["bcm"] }))}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

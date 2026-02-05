"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Shield,
  Plus,
  Search,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  TrendingUp,
  Building2,
  Users,
  Server,
  Laptop,
  MoreHorizontal,
  Trash2,
  Eye,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { iso27001API } from "@/lib/api-client";
import { Header } from "@/components/shared/header";

// Types
interface ThemeInfo {
  theme_id: string;
  name: string;
  control_count: number;
  description?: string;
}

interface ThemeListResponse {
  themes: ThemeInfo[];
  total_controls: number;
}

interface DashboardStats {
  total_assessments: number;
  active_assessments: number;
  completed_assessments: number;
  total_controls: number;
  average_compliance_score: number | null;
  theme_scores: Record<string, number | null>;
  recent_assessments: Assessment[];
}

interface Assessment {
  id: string;
  name: string;
  description: string | null;
  status: string;
  scope_description: string | null;
  overall_score: number | null;
  organizational_score: number | null;
  people_score: number | null;
  physical_score: number | null;
  technological_score: number | null;
  applicable_controls: number;
  compliant_controls: number;
  partial_controls: number;
  gap_controls: number;
  created_by: string | null;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
}

interface AssessmentListResponse {
  assessments: Assessment[];
  total: number;
  page: number;
  page_size: number;
}

const THEME_ICONS: Record<string, typeof Building2> = {
  "A.5": Building2,
  "A.6": Users,
  "A.7": Server,
  "A.8": Laptop,
};

const THEME_COLORS: Record<string, string> = {
  "A.5": "text-blue-500",
  "A.6": "text-green-500",
  "A.7": "text-orange-500",
  "A.8": "text-purple-500",
};

export default function ISO27001Page() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newAssessment, setNewAssessment] = useState({
    name: "",
    description: "",
  });

  // Queries
  const { data: themes } = useQuery<ThemeListResponse>({
    queryKey: ["iso27001", "themes"],
    queryFn: () => iso27001API.getThemes(token!) as Promise<ThemeListResponse>,
    enabled: !!token,
  });

  const { data: dashboard, isLoading: dashboardLoading } = useQuery<DashboardStats>({
    queryKey: ["iso27001", "dashboard"],
    queryFn: () => iso27001API.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
  });

  const { data: assessmentsData, isLoading: assessmentsLoading } = useQuery<AssessmentListResponse>({
    queryKey: ["iso27001", "assessments", searchQuery],
    queryFn: () => iso27001API.listAssessments(token!) as Promise<AssessmentListResponse>,
    enabled: !!token,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      iso27001API.createAssessment(token!, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["iso27001"] });
      setIsCreateOpen(false);
      setNewAssessment({ name: "", description: "" });
      // Navigate to the new assessment wizard
      if (data && typeof data === 'object' && 'id' in data) {
        router.push(`/compliance/iso27001/${data.id}`);
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => iso27001API.deleteAssessment(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iso27001"] });
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      draft: { variant: "secondary", label: "Draft" },
      scoping: { variant: "outline", label: "Scoping" },
      soa: { variant: "outline", label: "SoA" },
      assessment: { variant: "default", label: "Assessment" },
      gap_analysis: { variant: "default", label: "Gap Analysis" },
      completed: { variant: "default", label: "Completed" },
      archived: { variant: "secondary", label: "Archived" },
    };
    const config = variants[status] || { variant: "secondary", label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-muted-foreground";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getProgressColor = (score: number | null) => {
    if (score === null) return "bg-gray-300";
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="ISO 27001:2022 Compliance"
        actions={
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Assessment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create ISO 27001 Assessment</DialogTitle>
                <DialogDescription>
                  Start a new ISO 27001:2022 compliance assessment. You will be guided through scope definition, Statement of Applicability, and control assessment.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Assessment Name</Label>
                  <Input
                    id="name"
                    value={newAssessment.name}
                    onChange={(e) => setNewAssessment({ ...newAssessment, name: e.target.value })}
                    placeholder="e.g., Q1 2024 ISMS Assessment"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    value={newAssessment.description}
                    onChange={(e) => setNewAssessment({ ...newAssessment, description: e.target.value })}
                    placeholder="Brief description of the assessment scope and objectives"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate({
                    name: newAssessment.name,
                    description: newAssessment.description || undefined,
                  })}
                  disabled={!newAssessment.name || createMutation.isPending}
                >
                  {createMutation.isPending ? "Creating..." : "Create Assessment"}
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
            <TabsTrigger value="assessments" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Assessments
            </TabsTrigger>
            <TabsTrigger value="controls" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Control Catalog
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total Controls</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{themes?.total_controls || 93}</div>
                  <p className="text-xs text-muted-foreground">
                    Annex A controls in 4 themes
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Active Assessments</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.active_assessments || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {dashboard?.completed_assessments || 0} completed
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Average Score</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getScoreColor(dashboard?.average_compliance_score ?? null)}`}>
                    {dashboard?.average_compliance_score !== null && dashboard?.average_compliance_score !== undefined
                      ? `${dashboard.average_compliance_score.toFixed(1)}%`
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Across all assessments
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Compliance Status</CardTitle>
                  <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboard?.average_compliance_score !== null && dashboard?.average_compliance_score !== undefined
                      ? dashboard.average_compliance_score >= 80
                        ? "Good"
                        : dashboard.average_compliance_score >= 60
                        ? "Fair"
                        : "Needs Work"
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Overall ISMS health
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Theme Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">ISO 27001:2022 Themes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {themes?.themes.map((theme) => {
                    const Icon = THEME_ICONS[theme.theme_id] || Shield;
                    const colorClass = THEME_COLORS[theme.theme_id] || "text-gray-500";
                    const score = dashboard?.theme_scores?.[theme.theme_id];
                    return (
                      <Card key={theme.theme_id} className="border-l-4" style={{ borderLeftColor: colorClass.replace("text-", "var(--") + ")" }}>
                        <CardContent className="pt-4">
                          <div className="flex items-center gap-3 mb-3">
                            <Icon className={`h-5 w-5 ${colorClass}`} />
                            <div>
                              <p className="font-medium">{theme.name}</p>
                              <p className="text-xs text-muted-foreground">{theme.theme_id}</p>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>{theme.control_count} controls</span>
                              <span className={getScoreColor(score ?? null)}>
                                {score !== null && score !== undefined ? `${score.toFixed(0)}%` : "N/A"}
                              </span>
                            </div>
                            <Progress
                              value={score ?? 0}
                              className="h-2"
                            />
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Recent Assessments */}
            {dashboard?.recent_assessments && dashboard.recent_assessments.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recent Assessments</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {dashboard.recent_assessments.map((assessment) => (
                      <div
                        key={assessment.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                        onClick={() => router.push(`/compliance/iso27001/${assessment.id}`)}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{assessment.name}</p>
                            {getStatusBadge(assessment.status)}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {assessment.applicable_controls} applicable controls
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`text-xl font-bold ${getScoreColor(assessment.overall_score)}`}>
                            {assessment.overall_score !== null ? `${assessment.overall_score.toFixed(0)}%` : "N/A"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(assessment.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Assessments Tab */}
          <TabsContent value="assessments" className="space-y-4">
            {/* Search */}
            <div className="flex gap-4">
              <div className="flex-1 max-w-md">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search assessments..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            {/* Assessments List */}
            <div className="space-y-4">
              {assessmentsLoading ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Loading assessments...
                  </CardContent>
                </Card>
              ) : assessmentsData?.assessments?.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">No assessments found</p>
                    <Button onClick={() => setIsCreateOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create First Assessment
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                assessmentsData?.assessments?.map((assessment) => (
                  <Card key={assessment.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{assessment.name}</h3>
                            {getStatusBadge(assessment.status)}
                          </div>
                          {assessment.description && (
                            <p className="text-sm text-muted-foreground">{assessment.description}</p>
                          )}
                          <div className="flex flex-wrap gap-4 text-sm">
                            <div className="flex items-center gap-1">
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                              <span>{assessment.compliant_controls} compliant</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4 text-yellow-500" />
                              <span>{assessment.partial_controls} partial</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <AlertCircle className="h-4 w-4 text-red-500" />
                              <span>{assessment.gap_controls} gaps</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className={`text-2xl font-bold ${getScoreColor(assessment.overall_score)}`}>
                              {assessment.overall_score !== null ? `${assessment.overall_score.toFixed(0)}%` : "N/A"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {assessment.applicable_controls} controls
                            </p>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => router.push(`/compliance/iso27001/${assessment.id}`)}>
                                <Eye className="h-4 w-4 mr-2" />
                                Open Assessment
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => deleteMutation.mutate(assessment.id)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                      {/* Progress Bar */}
                      <div className="mt-4">
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                          <span>Completion</span>
                          <span>
                            {assessment.applicable_controls > 0
                              ? Math.round(
                                  ((assessment.compliant_controls + assessment.partial_controls + assessment.gap_controls) /
                                    assessment.applicable_controls) *
                                    100
                                )
                              : 0}
                            %
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getProgressColor(assessment.overall_score)}`}
                            style={{
                              width: `${
                                assessment.applicable_controls > 0
                                  ? ((assessment.compliant_controls + assessment.partial_controls + assessment.gap_controls) /
                                      assessment.applicable_controls) *
                                    100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Control Catalog Tab */}
          <TabsContent value="controls" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>ISO 27001:2022 Annex A Control Catalog</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {themes?.themes.map((theme) => {
                    const Icon = THEME_ICONS[theme.theme_id] || Shield;
                    const colorClass = THEME_COLORS[theme.theme_id] || "text-gray-500";
                    return (
                      <div key={theme.theme_id} className="border rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                          <Icon className={`h-6 w-6 ${colorClass}`} />
                          <div>
                            <h3 className="font-semibold">{theme.theme_id} - {theme.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {theme.control_count} controls
                            </p>
                          </div>
                        </div>
                        {theme.description && (
                          <p className="text-sm text-muted-foreground mt-2">{theme.description}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    The ISO 27001:2022 standard contains 93 controls organized into 4 themes.
                    To assess controls, create a new assessment and use the wizard to define scope,
                    Statement of Applicability (SoA), and evaluate each control.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

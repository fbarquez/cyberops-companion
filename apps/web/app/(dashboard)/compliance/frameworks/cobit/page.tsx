"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  BarChart3,
  Plus,
  Trash2,
  ChevronRight,
  FileCheck,
  AlertTriangle,
  TrendingUp,
  Target,
  Loader2,
  Settings,
  Cpu,
  Wrench,
  Headphones,
  ClipboardCheck,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const cobitAPI = {
  getDashboard: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard");
    return res.json();
  },
  listAssessments: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessments");
    return res.json();
  },
  createAssessment: async (token: string, data: { name: string; description?: string }) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create assessment");
    return res.json();
  },
  deleteAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete assessment");
  },
};

// Types
interface Assessment {
  id: string;
  name: string;
  description: string | null;
  status: string;
  organization_type: string | null;
  organization_size: string | null;
  employee_count: number | null;
  industry_sector: string | null;
  current_capability_level: string | null;
  target_capability_level: string | null;
  focus_areas: string[];
  overall_score: number;
  domain_scores: Record<string, number>;
  gaps_count: number;
  critical_gaps_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

interface DashboardStats {
  total_assessments: number;
  completed_assessments: number;
  in_progress_assessments: number;
  average_score: number;
  total_gaps: number;
  critical_gaps: number;
  assessments_by_level: Record<string, number>;
  average_domain_scores: Record<string, number>;
  achievement_distribution: {
    not_evaluated: number;
    not_achieved: number;
    partially_achieved: number;
    largely_achieved: number;
    fully_achieved: number;
    not_applicable: number;
  };
  recent_assessments: Assessment[];
}

// Capability level labels
const capabilityLabels: Record<string, { label: string; description: string }> = {
  level_0: { label: "Level 0 - Incomplete", description: "Nicht implementiert" },
  level_1: { label: "Level 1 - Performed", description: "Ausgeführt, ad-hoc" },
  level_2: { label: "Level 2 - Managed", description: "Geplant und überwacht" },
  level_3: { label: "Level 3 - Established", description: "Standardisiert, dokumentiert" },
  level_4: { label: "Level 4 - Predictable", description: "Quantitativ gesteuert" },
  level_5: { label: "Level 5 - Optimizing", description: "Kontinuierlich optimiert" },
};

// Organization type labels
const organizationTypeLabels: Record<string, string> = {
  enterprise: "Enterprise",
  sme: "KMU",
  public_sector: "Öffentlicher Sektor",
  nonprofit: "Non-Profit",
  financial_services: "Finanzdienstleistungen",
  healthcare: "Gesundheitswesen",
  manufacturing: "Fertigung",
  technology: "Technologie",
  retail: "Handel",
  education: "Bildung",
};

// Status labels
const statusLabels: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  draft: { label: "Entwurf", variant: "secondary" },
  in_progress: { label: "In Bearbeitung", variant: "default" },
  completed: { label: "Abgeschlossen", variant: "default" },
  archived: { label: "Archiviert", variant: "secondary" },
};

// Domain metadata
const domainMeta: Record<string, { name: string; code: string; color: string; icon: any }> = {
  edm: { name: "Evaluate, Direct, Monitor", code: "EDM", color: "bg-purple-500", icon: Settings },
  apo: { name: "Align, Plan, Organize", code: "APO", color: "bg-blue-500", icon: Target },
  bai: { name: "Build, Acquire, Implement", code: "BAI", color: "bg-green-500", icon: Wrench },
  dss: { name: "Deliver, Service, Support", code: "DSS", color: "bg-orange-500", icon: Headphones },
  mea: { name: "Monitor, Evaluate, Assess", code: "MEA", color: "bg-cyan-500", icon: ClipboardCheck },
};

export default function COBITPage() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [assessmentToDelete, setAssessmentToDelete] = useState<Assessment | null>(null);
  const [newAssessment, setNewAssessment] = useState({ name: "", description: "" });

  // Fetch dashboard stats
  const { data: dashboardStats, isLoading: dashboardLoading } = useQuery<DashboardStats>({
    queryKey: ["cobit", "dashboard"],
    queryFn: () => cobitAPI.getDashboard(token!),
    enabled: !!token,
  });

  // Fetch assessments
  const { data: assessmentsData, isLoading: assessmentsLoading } = useQuery({
    queryKey: ["cobit", "assessments"],
    queryFn: () => cobitAPI.listAssessments(token!),
    enabled: !!token,
  });

  // Create assessment mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      cobitAPI.createAssessment(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cobit"] });
      setCreateDialogOpen(false);
      setNewAssessment({ name: "", description: "" });
      toast.success("Assessment erstellt");
    },
    onError: () => {
      toast.error("Fehler beim Erstellen des Assessments");
    },
  });

  // Delete assessment mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => cobitAPI.deleteAssessment(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cobit"] });
      setDeleteDialogOpen(false);
      setAssessmentToDelete(null);
      toast.success("Assessment gelöscht");
    },
    onError: () => {
      toast.error("Fehler beim Löschen des Assessments");
    },
  });

  const handleCreateAssessment = () => {
    if (!newAssessment.name.trim()) {
      toast.error("Name ist erforderlich");
      return;
    }
    createMutation.mutate(newAssessment);
  };

  const handleDeleteAssessment = (assessment: Assessment) => {
    setAssessmentToDelete(assessment);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (assessmentToDelete) {
      deleteMutation.mutate(assessmentToDelete.id);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="COBIT 2019">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <BarChart3 className="h-3 w-3" />
            IT Governance
          </Badge>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Neues Assessment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Neues COBIT Assessment</DialogTitle>
                <DialogDescription>
                  Starten Sie ein neues COBIT 2019 IT Governance Assessment.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    placeholder="z.B. COBIT Assessment 2026"
                    value={newAssessment.name}
                    onChange={(e) => setNewAssessment({ ...newAssessment, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Beschreibung</Label>
                  <Textarea
                    id="description"
                    placeholder="Optionale Beschreibung..."
                    value={newAssessment.description}
                    onChange={(e) => setNewAssessment({ ...newAssessment, description: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Abbrechen
                </Button>
                <Button onClick={handleCreateAssessment} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Erstellen
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="dashboard" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="assessments" className="gap-2">
              <FileCheck className="h-4 w-4" />
              Assessments
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard">
            {dashboardLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : dashboardStats ? (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium">Gesamt Assessments</CardTitle>
                      <FileCheck className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{dashboardStats.total_assessments}</div>
                      <p className="text-xs text-muted-foreground">
                        {dashboardStats.completed_assessments} abgeschlossen
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium">Durchschn. Erfüllung</CardTitle>
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className={`text-2xl font-bold ${getScoreColor(dashboardStats.average_score)}`}>
                        {dashboardStats.average_score.toFixed(1)}%
                      </div>
                      <p className="text-xs text-muted-foreground">
                        COBIT Maturity Score
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium">Offene Gaps</CardTitle>
                      <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{dashboardStats.total_gaps}</div>
                      <p className="text-xs text-muted-foreground">
                        {dashboardStats.critical_gaps} kritisch
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium">40 Prozesse</CardTitle>
                      <Cpu className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">5</div>
                      <p className="text-xs text-muted-foreground">
                        Domains (EDM, APO, BAI, DSS, MEA)
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Domain Scores */}
                <Card>
                  <CardHeader>
                    <CardTitle>Domain Scores</CardTitle>
                    <CardDescription>COBIT 2019 Governance & Management Objectives</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(domainMeta).map(([key, domain]) => {
                        const score = dashboardStats.average_domain_scores?.[key] || 0;
                        const DomainIcon = domain.icon;
                        return (
                          <div key={key} className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <div className="flex items-center gap-2">
                                <div className={`p-1.5 rounded ${domain.color}`}>
                                  <DomainIcon className="h-3 w-3 text-white" />
                                </div>
                                <span className="font-medium">{domain.code}</span>
                                <span className="text-muted-foreground text-xs hidden sm:inline">
                                  {domain.name}
                                </span>
                              </div>
                              <span className={getScoreColor(score)}>{score.toFixed(1)}%</span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full ${domain.color} transition-all`}
                                style={{ width: `${score}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Achievement Distribution */}
                <Card>
                  <CardHeader>
                    <CardTitle>Prozess-Erreichungsgrad</CardTitle>
                    <CardDescription>Verteilung der 40 COBIT Prozesse</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { label: "Vollständig erreicht", count: dashboardStats.achievement_distribution.fully_achieved, color: "bg-green-500" },
                        { label: "Größtenteils erreicht", count: dashboardStats.achievement_distribution.largely_achieved, color: "bg-lime-500" },
                        { label: "Teilweise erreicht", count: dashboardStats.achievement_distribution.partially_achieved, color: "bg-yellow-500" },
                        { label: "Nicht erreicht", count: dashboardStats.achievement_distribution.not_achieved, color: "bg-red-500" },
                        { label: "Nicht bewertet", count: dashboardStats.achievement_distribution.not_evaluated, color: "bg-gray-400" },
                        { label: "Nicht anwendbar", count: dashboardStats.achievement_distribution.not_applicable, color: "bg-blue-400" },
                      ].map((item) => {
                        const total = Object.values(dashboardStats.achievement_distribution).reduce((a, b) => a + b, 0);
                        const percentage = total > 0 ? (item.count / total) * 100 : 0;
                        return (
                          <div key={item.label} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>{item.label}</span>
                              <span className="text-muted-foreground">{item.count} Prozesse</span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full ${item.color} transition-all`}
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Recent Assessments */}
                {dashboardStats.recent_assessments.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Letzte Assessments</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {dashboardStats.recent_assessments.map((assessment) => (
                          <Link
                            key={assessment.id}
                            href={`/compliance/frameworks/cobit/${assessment.id}`}
                            className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                                <BarChart3 className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                              </div>
                              <div>
                                <p className="font-medium">{assessment.name}</p>
                                <p className="text-sm text-muted-foreground">
                                  {assessment.target_capability_level
                                    ? capabilityLabels[assessment.target_capability_level]?.label || assessment.target_capability_level
                                    : "Nicht konfiguriert"}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <p className={`font-medium ${getScoreColor(assessment.overall_score)}`}>
                                  {assessment.overall_score.toFixed(1)}%
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {assessment.gaps_count} Gaps
                                </p>
                              </div>
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            </div>
                          </Link>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card className="text-center py-12">
                <CardContent>
                  <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Keine Daten verfügbar</h3>
                  <p className="text-muted-foreground mb-4">
                    Erstellen Sie Ihr erstes COBIT Assessment, um zu beginnen.
                  </p>
                  <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Assessment erstellen
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Assessments Tab */}
          <TabsContent value="assessments">
            {assessmentsLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : assessmentsData?.items?.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {assessmentsData.items.map((assessment: Assessment) => (
                  <Card key={assessment.id} className="group relative">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                            <BarChart3 className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                          </div>
                          <div>
                            <CardTitle className="text-base">{assessment.name}</CardTitle>
                            <CardDescription>
                              {assessment.organization_type
                                ? organizationTypeLabels[assessment.organization_type]
                                : "Nicht konfiguriert"}
                            </CardDescription>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.preventDefault();
                            handleDeleteAssessment(assessment);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {/* Score */}
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Erfüllungsgrad</span>
                            <span className={getScoreColor(assessment.overall_score)}>
                              {assessment.overall_score.toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                assessment.overall_score >= 80
                                  ? "bg-green-500"
                                  : assessment.overall_score >= 60
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }`}
                              style={{ width: `${assessment.overall_score}%` }}
                            />
                          </div>
                        </div>

                        {/* Gaps */}
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Gaps</span>
                          <span>
                            {assessment.gaps_count} ({assessment.critical_gaps_count} kritisch)
                          </span>
                        </div>

                        {/* Target Level */}
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Target Level</span>
                          <span>
                            {assessment.target_capability_level
                              ? capabilityLabels[assessment.target_capability_level]?.label.split(" - ")[0] || assessment.target_capability_level
                              : "-"}
                          </span>
                        </div>

                        {/* Domain Mini Bars */}
                        <div className="flex gap-1">
                          {Object.entries(domainMeta).map(([key, domain]) => {
                            const score = assessment.domain_scores?.[key] || 0;
                            return (
                              <div
                                key={key}
                                className="flex-1 h-2 bg-muted rounded-full overflow-hidden"
                                title={`${domain.code}: ${score.toFixed(0)}%`}
                              >
                                <div
                                  className={`h-full ${domain.color}`}
                                  style={{ width: `${score}%` }}
                                />
                              </div>
                            );
                          })}
                        </div>

                        {/* Status & Action */}
                        <div className="flex items-center justify-between pt-2">
                          <Badge variant={statusLabels[assessment.status]?.variant || "secondary"}>
                            {statusLabels[assessment.status]?.label || assessment.status}
                          </Badge>
                          <Link href={`/compliance/frameworks/cobit/${assessment.id}`}>
                            <Button variant="ghost" size="sm">
                              Öffnen
                              <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="text-center py-12">
                <CardContent>
                  <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Keine Assessments</h3>
                  <p className="text-muted-foreground mb-4">
                    Erstellen Sie Ihr erstes COBIT 2019 Assessment.
                  </p>
                  <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Assessment erstellen
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Assessment löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Sind Sie sicher, dass Sie das Assessment &quot;{assessmentToDelete?.name}&quot; löschen möchten?
              Diese Aktion kann nicht rückgängig gemacht werden.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Löschen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

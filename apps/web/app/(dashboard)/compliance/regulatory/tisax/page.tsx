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
  Car,
  Plus,
  Trash2,
  ChevronRight,
  BarChart3,
  FileCheck,
  AlertTriangle,
  TrendingUp,
  Shield,
  Factory,
  Truck,
  Settings,
  FileText,
  Building2,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const tisaxAPI = {
  getDashboard: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard");
    return res.json();
  },
  listAssessments: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessments");
    return res.json();
  },
  createAssessment: async (token: string, data: { name: string; description?: string }) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments`, {
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
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}`, {
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
  company_type: string | null;
  company_size: string | null;
  assessment_level: string | null;
  objectives: string[];
  oem_requirements: string[];
  overall_score: number;
  maturity_level: number;
  chapter_scores: Record<string, number>;
  gaps_count: number;
  critical_gaps_count: number;
  target_date: string | null;
  audit_date: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

interface DashboardStats {
  total_assessments: number;
  completed_assessments: number;
  in_progress_assessments: number;
  average_score: number;
  average_maturity: number;
  total_gaps: number;
  critical_gaps: number;
  assessments_by_level: Record<string, number>;
  assessments_by_objective: Record<string, number>;
  maturity_distribution: {
    level_0: number;
    level_1: number;
    level_2: number;
    level_3: number;
    level_4: number;
    level_5: number;
  };
  recent_assessments: Assessment[];
  upcoming_audits: Assessment[];
}

// Company type icons
const companyTypeIcons: Record<string, any> = {
  oem: Car,
  tier1: Factory,
  tier2: Factory,
  tier3: Factory,
  service_provider: Settings,
  logistics: Truck,
  development: FileText,
};

// Assessment level labels
const assessmentLevelLabels: Record<string, { label: string; color: string }> = {
  al1: { label: "AL1 - Normal", color: "bg-green-500" },
  al2: { label: "AL2 - Hoch", color: "bg-yellow-500" },
  al3: { label: "AL3 - Sehr hoch", color: "bg-red-500" },
};

// Status labels
const statusLabels: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  draft: { label: "Entwurf", variant: "secondary" },
  in_progress: { label: "In Bearbeitung", variant: "default" },
  under_review: { label: "In Prüfung", variant: "outline" },
  completed: { label: "Abgeschlossen", variant: "default" },
  archived: { label: "Archiviert", variant: "secondary" },
};

// Objective labels
const objectiveLabels: Record<string, string> = {
  info_high: "Info (Hoch)",
  info_very_high: "Info (Sehr hoch)",
  prototype: "Prototyp",
  prototype_vehicle: "Testfahrzeug",
  data_protection: "Datenschutz",
};

export default function TISAXPage() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [assessmentToDelete, setAssessmentToDelete] = useState<Assessment | null>(null);
  const [newAssessment, setNewAssessment] = useState({ name: "", description: "" });

  // Fetch dashboard stats
  const { data: dashboardStats, isLoading: dashboardLoading } = useQuery<DashboardStats>({
    queryKey: ["tisax", "dashboard"],
    queryFn: () => tisaxAPI.getDashboard(token!),
    enabled: !!token,
  });

  // Fetch assessments
  const { data: assessmentsData, isLoading: assessmentsLoading } = useQuery({
    queryKey: ["tisax", "assessments"],
    queryFn: () => tisaxAPI.listAssessments(token!),
    enabled: !!token,
  });

  // Create assessment mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      tisaxAPI.createAssessment(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tisax"] });
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
    mutationFn: (id: string) => tisaxAPI.deleteAssessment(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tisax"] });
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

  const getMaturityColor = (level: number) => {
    if (level >= 3) return "text-green-600";
    if (level >= 2) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="TISAX Compliance">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Car className="h-3 w-3" />
            VDA ISA
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
                <DialogTitle>Neues TISAX Assessment</DialogTitle>
                <DialogDescription>
                  Starten Sie ein neues TISAX Assessment nach VDA ISA.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    placeholder="z.B. TISAX Assessment 2026"
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
                      <CardTitle className="text-sm font-medium">Durchschn. Score</CardTitle>
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className={`text-2xl font-bold ${getScoreColor(dashboardStats.average_score)}`}>
                        {dashboardStats.average_score.toFixed(1)}%
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Reifegrad: {dashboardStats.average_maturity.toFixed(1)}/5.0
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
                      <CardTitle className="text-sm font-medium">In Bearbeitung</CardTitle>
                      <Shield className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{dashboardStats.in_progress_assessments}</div>
                      <p className="text-xs text-muted-foreground">
                        Aktive Assessments
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Maturity Distribution */}
                <Card>
                  <CardHeader>
                    <CardTitle>Reifegradverteilung</CardTitle>
                    <CardDescription>VDA ISA Maturity Level (0-5)</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { level: 0, label: "0 - Unvollständig", count: dashboardStats.maturity_distribution.level_0, color: "bg-red-500" },
                        { level: 1, label: "1 - Durchgeführt", count: dashboardStats.maturity_distribution.level_1, color: "bg-orange-500" },
                        { level: 2, label: "2 - Gesteuert", count: dashboardStats.maturity_distribution.level_2, color: "bg-yellow-500" },
                        { level: 3, label: "3 - Etabliert", count: dashboardStats.maturity_distribution.level_3, color: "bg-green-500" },
                        { level: 4, label: "4 - Vorhersagbar", count: dashboardStats.maturity_distribution.level_4, color: "bg-blue-500" },
                        { level: 5, label: "5 - Optimierend", count: dashboardStats.maturity_distribution.level_5, color: "bg-purple-500" },
                      ].map((item) => {
                        const total = Object.values(dashboardStats.maturity_distribution).reduce((a, b) => a + b, 0);
                        const percentage = total > 0 ? (item.count / total) * 100 : 0;
                        return (
                          <div key={item.level} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>{item.label}</span>
                              <span className="text-muted-foreground">{item.count} Kontrollen</span>
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

                {/* Assessment Levels Distribution */}
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Nach Assessment Level</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(assessmentLevelLabels).map(([key, { label, color }]) => (
                          <div key={key} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${color}`} />
                              <span className="text-sm">{label}</span>
                            </div>
                            <Badge variant="outline">
                              {dashboardStats.assessments_by_level[key] || 0}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Nach Schutzziel</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(objectiveLabels).map(([key, label]) => (
                          <div key={key} className="flex items-center justify-between">
                            <span className="text-sm">{label}</span>
                            <Badge variant="outline">
                              {dashboardStats.assessments_by_objective[key] || 0}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

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
                            href={`/compliance/regulatory/tisax/${assessment.id}`}
                            className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                                <Car className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                              </div>
                              <div>
                                <p className="font-medium">{assessment.name}</p>
                                <p className="text-sm text-muted-foreground">
                                  {assessment.assessment_level
                                    ? assessmentLevelLabels[assessment.assessment_level]?.label
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
                                  Reifegrad {assessment.maturity_level.toFixed(1)}
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
                  <Car className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Keine Daten verfügbar</h3>
                  <p className="text-muted-foreground mb-4">
                    Erstellen Sie Ihr erstes TISAX Assessment, um zu beginnen.
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
                {assessmentsData.items.map((assessment: Assessment) => {
                  const CompanyIcon = assessment.company_type
                    ? companyTypeIcons[assessment.company_type] || Building2
                    : Building2;
                  const levelInfo = assessment.assessment_level
                    ? assessmentLevelLabels[assessment.assessment_level]
                    : null;

                  return (
                    <Card key={assessment.id} className="group relative">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${
                              levelInfo?.color
                                ? levelInfo.color.replace("bg-", "bg-").replace("500", "100") +
                                  " dark:" + levelInfo.color.replace("500", "900")
                                : "bg-muted"
                            }`}>
                              <CompanyIcon className={`h-5 w-5 ${
                                levelInfo?.color
                                  ? levelInfo.color.replace("bg-", "text-").replace("500", "600")
                                  : "text-muted-foreground"
                              }`} />
                            </div>
                            <div>
                              <CardTitle className="text-base">{assessment.name}</CardTitle>
                              <CardDescription>
                                {levelInfo?.label || "Nicht konfiguriert"}
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
                              <span>Gesamtscore</span>
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

                          {/* Maturity */}
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Reifegrad</span>
                            <span className={getMaturityColor(assessment.maturity_level)}>
                              {assessment.maturity_level.toFixed(1)} / 5.0
                            </span>
                          </div>

                          {/* Gaps */}
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Gaps</span>
                            <span>
                              {assessment.gaps_count} ({assessment.critical_gaps_count} kritisch)
                            </span>
                          </div>

                          {/* Objectives */}
                          {assessment.objectives.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {assessment.objectives.slice(0, 3).map((obj) => (
                                <Badge key={obj} variant="secondary" className="text-xs">
                                  {objectiveLabels[obj] || obj}
                                </Badge>
                              ))}
                              {assessment.objectives.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{assessment.objectives.length - 3}
                                </Badge>
                              )}
                            </div>
                          )}

                          {/* Status & Action */}
                          <div className="flex items-center justify-between pt-2">
                            <Badge variant={statusLabels[assessment.status]?.variant || "secondary"}>
                              {statusLabels[assessment.status]?.label || assessment.status}
                            </Badge>
                            <Link href={`/compliance/regulatory/tisax/${assessment.id}`}>
                              <Button variant="ghost" size="sm">
                                Öffnen
                                <ChevronRight className="h-4 w-4 ml-1" />
                              </Button>
                            </Link>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <Card className="text-center py-12">
                <CardContent>
                  <Car className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Keine Assessments</h3>
                  <p className="text-muted-foreground mb-4">
                    Erstellen Sie Ihr erstes TISAX Assessment nach VDA ISA.
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

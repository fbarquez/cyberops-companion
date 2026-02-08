"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Factory,
  Plus,
  Trash2,
  ArrowRight,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Droplets,
  Utensils,
  Server,
  Heart,
  Landmark,
  Truck,
  Trash,
  BarChart3,
  Shield,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const kritisAPI = {
  getDashboard: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard");
    return res.json();
  },
  listAssessments: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessments");
    return res.json();
  },
  createAssessment: async (token: string, data: { name: string; description?: string }) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments`, {
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
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete assessment");
  },
};

const SECTOR_ICONS: Record<string, any> = {
  energy: Zap,
  water: Droplets,
  food: Utensils,
  it_telecom: Server,
  health: Heart,
  finance: Landmark,
  transport: Truck,
  waste: Trash,
};

const SECTOR_NAMES: Record<string, string> = {
  energy: "Energie",
  water: "Wasser",
  food: "Ernährung",
  it_telecom: "IT & Telekommunikation",
  health: "Gesundheit",
  finance: "Finanz- & Versicherungswesen",
  transport: "Transport & Verkehr",
  waste: "Siedlungsabfallentsorgung",
};

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  draft: { label: "Entwurf", color: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200", icon: FileText },
  in_progress: { label: "In Bearbeitung", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200", icon: Clock },
  completed: { label: "Abgeschlossen", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200", icon: CheckCircle },
  archived: { label: "Archiviert", color: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400", icon: FileText },
};

export default function KRITISPage() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAssessmentName, setNewAssessmentName] = useState("");
  const [newAssessmentDescription, setNewAssessmentDescription] = useState("");

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ["kritis-dashboard"],
    queryFn: () => kritisAPI.getDashboard(token!),
    enabled: !!token,
  });

  const { data: assessmentsData, isLoading: assessmentsLoading } = useQuery({
    queryKey: ["kritis-assessments"],
    queryFn: () => kritisAPI.listAssessments(token!),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      kritisAPI.createAssessment(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kritis-assessments"] });
      queryClient.invalidateQueries({ queryKey: ["kritis-dashboard"] });
      setCreateDialogOpen(false);
      setNewAssessmentName("");
      setNewAssessmentDescription("");
      toast.success("Assessment erstellt");
    },
    onError: () => toast.error("Fehler beim Erstellen"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => kritisAPI.deleteAssessment(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kritis-assessments"] });
      queryClient.invalidateQueries({ queryKey: ["kritis-dashboard"] });
      toast.success("Assessment gelöscht");
    },
    onError: () => toast.error("Fehler beim Löschen"),
  });

  const handleCreate = () => {
    if (!newAssessmentName.trim()) {
      toast.error("Bitte geben Sie einen Namen ein");
      return;
    }
    createMutation.mutate({
      name: newAssessmentName.trim(),
      description: newAssessmentDescription.trim() || undefined,
    });
  };

  const assessments = assessmentsData?.items || [];

  return (
    <div className="flex flex-col h-full">
      <Header title="KRITIS Compliance">
        <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
          BSI-Gesetz
        </Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {/* Info Banner */}
        <Card className="mb-6 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 border-red-200 dark:border-red-800">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <Factory className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  Kritische Infrastrukturen (KRITIS)
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  Bewerten Sie Ihre Compliance mit den Anforderungen des BSI-Gesetzes §8a.
                  KRITIS-Betreiber müssen angemessene technische und organisatorische Maßnahmen
                  nachweisen und alle 2 Jahre einen Nachweis beim BSI erbringen.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList>
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="assessments">Assessments</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Gesamt
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.total_assessments || 0}</div>
                  <p className="text-xs text-muted-foreground">Assessments</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Abgeschlossen
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {dashboard?.completed_assessments || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Ø Score: {dashboard?.average_score?.toFixed(0) || 0}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    In Bearbeitung
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">
                    {dashboard?.in_progress_assessments || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">Aktive Bewertungen</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Audits
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold">{dashboard?.upcoming_audits || 0}</span>
                    {(dashboard?.overdue_audits || 0) > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        {dashboard?.overdue_audits} überfällig
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">Anstehend</p>
                </CardContent>
              </Card>
            </div>

            {/* Sectors Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Assessments nach Sektor</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-4">
                  {Object.entries(SECTOR_NAMES).map(([key, name]) => {
                    const Icon = SECTOR_ICONS[key] || Factory;
                    const count = dashboard?.assessments_by_sector?.[key] || 0;
                    return (
                      <div
                        key={key}
                        className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                      >
                        <div className="p-2 bg-muted rounded-lg">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{name}</p>
                          <p className="text-xs text-muted-foreground">{count} Assessments</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Recent Assessments */}
            {dashboard?.recent_assessments?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Letzte Assessments</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {dashboard.recent_assessments.slice(0, 5).map((assessment: any) => {
                      const statusConfig = STATUS_CONFIG[assessment.status] || STATUS_CONFIG.draft;
                      const SectorIcon = SECTOR_ICONS[assessment.sector] || Factory;
                      return (
                        <Link
                          key={assessment.id}
                          href={`/compliance/regulatory/kritis/${assessment.id}`}
                          className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <SectorIcon className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{assessment.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {assessment.sector ? SECTOR_NAMES[assessment.sector] : "Kein Sektor"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                            <div className="text-right">
                              <p className="text-sm font-medium">{assessment.overall_score}%</p>
                              <Progress value={assessment.overall_score} className="w-20 h-1.5" />
                            </div>
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Assessments Tab */}
          <TabsContent value="assessments" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold">KRITIS Assessments</h2>
                <p className="text-sm text-muted-foreground">
                  Verwalten Sie Ihre KRITIS-Compliance-Bewertungen
                </p>
              </div>
              <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Neues Assessment
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Neues KRITIS Assessment</DialogTitle>
                    <DialogDescription>
                      Erstellen Sie ein neues Assessment zur Bewertung Ihrer KRITIS-Compliance.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Name *</Label>
                      <Input
                        id="name"
                        value={newAssessmentName}
                        onChange={(e) => setNewAssessmentName(e.target.value)}
                        placeholder="z.B. KRITIS Assessment 2026"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Beschreibung</Label>
                      <Textarea
                        id="description"
                        value={newAssessmentDescription}
                        onChange={(e) => setNewAssessmentDescription(e.target.value)}
                        placeholder="Optionale Beschreibung..."
                        rows={3}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                      Abbrechen
                    </Button>
                    <Button onClick={handleCreate} disabled={createMutation.isPending}>
                      {createMutation.isPending ? "Erstellen..." : "Erstellen"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {assessmentsLoading ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">Laden...</p>
              </div>
            ) : assessments.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Factory className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">Keine Assessments vorhanden</h3>
                  <p className="text-muted-foreground mb-4">
                    Erstellen Sie Ihr erstes KRITIS-Assessment, um Ihre Compliance zu bewerten.
                  </p>
                  <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Erstes Assessment erstellen
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {assessments.map((assessment: any) => {
                  const statusConfig = STATUS_CONFIG[assessment.status] || STATUS_CONFIG.draft;
                  const StatusIcon = statusConfig.icon;
                  const SectorIcon = SECTOR_ICONS[assessment.sector] || Factory;

                  return (
                    <Card key={assessment.id} className="hover:shadow-md transition-shadow">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                              <SectorIcon className="h-4 w-4 text-red-600 dark:text-red-400" />
                            </div>
                            <div>
                              <CardTitle className="text-base">{assessment.name}</CardTitle>
                              <p className="text-xs text-muted-foreground">
                                {assessment.sector ? SECTOR_NAMES[assessment.sector] : "Sektor nicht gewählt"}
                              </p>
                            </div>
                          </div>
                          <Badge className={statusConfig.color}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {statusConfig.label}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {assessment.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {assessment.description}
                          </p>
                        )}

                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Compliance Score</span>
                            <span className="font-medium">{assessment.overall_score}%</span>
                          </div>
                          <Progress value={assessment.overall_score} className="h-2" />
                        </div>

                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          {assessment.gaps_count > 0 && (
                            <span className="flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3 text-yellow-500" />
                              {assessment.gaps_count} Lücken
                            </span>
                          )}
                          {assessment.critical_gaps_count > 0 && (
                            <span className="flex items-center gap-1 text-red-500">
                              <AlertTriangle className="h-3 w-3" />
                              {assessment.critical_gaps_count} kritisch
                            </span>
                          )}
                          {assessment.bsi_registered && (
                            <span className="flex items-center gap-1 text-green-600">
                              <Shield className="h-3 w-3" />
                              BSI registriert
                            </span>
                          )}
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-destructive">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Assessment löschen?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Diese Aktion kann nicht rückgängig gemacht werden. Das Assessment
                                  und alle zugehörigen Daten werden dauerhaft gelöscht.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => deleteMutation.mutate(assessment.id)}
                                  className="bg-destructive text-destructive-foreground"
                                >
                                  Löschen
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>

                          <Link href={`/compliance/regulatory/kritis/${assessment.id}`}>
                            <Button size="sm">
                              Öffnen
                              <ArrowRight className="h-4 w-4 ml-2" />
                            </Button>
                          </Link>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

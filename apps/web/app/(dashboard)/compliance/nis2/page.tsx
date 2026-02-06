"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  ArrowRight,
  Building2,
  BarChart3,
  List,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { NIS2Dashboard } from "@/components/compliance";

// API functions
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nis2API = {
  listAssessments: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/nis2/assessments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessments");
    return res.json();
  },
  createAssessment: async (token: string, data: { name: string; description?: string }) => {
    const res = await fetch(`${API_URL}/api/v1/nis2/assessments`, {
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
    const res = await fetch(`${API_URL}/api/v1/nis2/assessments/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete assessment");
    return true;
  },
};

const STATUS_CONFIG = {
  draft: { label: "Draft", color: "bg-gray-100 text-gray-800", icon: FileText },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-800", icon: Clock },
  completed: { label: "Completed", color: "bg-green-100 text-green-800", icon: CheckCircle },
  archived: { label: "Archived", color: "bg-gray-100 text-gray-600", icon: FileText },
};

const ENTITY_TYPE_CONFIG = {
  essential: { label: "Essential Entity", color: "bg-red-100 text-red-800" },
  important: { label: "Important Entity", color: "bg-yellow-100 text-yellow-800" },
  out_of_scope: { label: "Out of Scope", color: "bg-gray-100 text-gray-600" },
};

export default function NIS2AssessmentsPage() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAssessment, setNewAssessment] = useState({ name: "", description: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["nis2-assessments"],
    queryFn: () => nis2API.listAssessments(token!),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      nis2API.createAssessment(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nis2-assessments"] });
      queryClient.invalidateQueries({ queryKey: ["nis2-dashboard"] });
      setCreateDialogOpen(false);
      setNewAssessment({ name: "", description: "" });
      toast.success("Assessment created");
      setActiveTab("assessments");
    },
    onError: () => {
      toast.error("Failed to create assessment");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => nis2API.deleteAssessment(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nis2-assessments"] });
      queryClient.invalidateQueries({ queryKey: ["nis2-dashboard"] });
      toast.success("Assessment deleted");
    },
    onError: () => {
      toast.error("Failed to delete assessment");
    },
  });

  const assessments = data?.assessments || [];

  return (
    <div className="flex flex-col h-full">
      <Header title="NIS2 Compliance Assessment">
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Assessment
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create NIS2 Assessment</DialogTitle>
              <DialogDescription>
                Start a new NIS2 compliance assessment for your organization.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Assessment Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Q1 2024 NIS2 Assessment"
                  value={newAssessment.name}
                  onChange={(e) => setNewAssessment({ ...newAssessment, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of this assessment..."
                  value={newAssessment.description}
                  onChange={(e) => setNewAssessment({ ...newAssessment, description: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => createMutation.mutate(newAssessment)}
                disabled={!newAssessment.name || createMutation.isPending}
              >
                {createMutation.isPending ? "Creating..." : "Create Assessment"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Header>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <div className="border-b px-4 md:px-6 pt-4">
          <TabsList>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="assessments" className="flex items-center gap-2">
              <List className="h-4 w-4" />
              Assessments
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="dashboard" className="flex-1 overflow-y-auto p-4 md:p-6 m-0">
          <NIS2Dashboard />
        </TabsContent>

        <TabsContent value="assessments" className="flex-1 overflow-y-auto p-4 md:p-6 m-0">
          {/* Info Banner */}
          <Card className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200">
            <CardContent className="py-4">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                    EU NIS2 Directive Compliance
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                    The NIS2 Directive requires essential and important entities to implement
                    cybersecurity risk-management measures. Use this wizard to assess your
                    organization&apos;s compliance status.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {isLoading ? (
            <PageLoading />
          ) : assessments.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Assessments Yet</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first NIS2 compliance assessment to get started.
                </p>
                <Button onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Assessment
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {assessments.map((assessment: any) => (
                <AssessmentCard
                  key={assessment.id}
                  assessment={assessment}
                  onDelete={() => deleteMutation.mutate(assessment.id)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AssessmentCard({
  assessment,
  onDelete,
}: {
  assessment: any;
  onDelete: () => void;
}) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const statusConfig = STATUS_CONFIG[assessment.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.draft;
  const entityConfig = assessment.entity_type
    ? ENTITY_TYPE_CONFIG[assessment.entity_type as keyof typeof ENTITY_TYPE_CONFIG]
    : null;
  const StatusIcon = statusConfig.icon;

  const handleDelete = () => {
    onDelete();
    setDeleteDialogOpen(false);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base">{assessment.name}</CardTitle>
            {assessment.description && (
              <CardDescription className="line-clamp-2">
                {assessment.description}
              </CardDescription>
            )}
          </div>
          <Badge className={statusConfig.color}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusConfig.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {entityConfig && (
          <Badge variant="outline" className={entityConfig.color}>
            {entityConfig.label}
          </Badge>
        )}

        {assessment.entity_type && assessment.entity_type !== "out_of_scope" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Compliance Score</span>
              <span className="font-medium">{assessment.overall_score.toFixed(0)}%</span>
            </div>
            <Progress value={assessment.overall_score} className="h-2" />
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              {assessment.gaps_count > 0 && (
                <span className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-yellow-500" />
                  {assessment.gaps_count} gaps
                </span>
              )}
              {assessment.critical_gaps_count > 0 && (
                <span className="flex items-center gap-1 text-red-500">
                  {assessment.critical_gaps_count} critical
                </span>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t">
          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600">
                <Trash2 className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete Assessment?</DialogTitle>
                <DialogDescription>
                  This will permanently delete the assessment and all its data.
                  This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Link href={`/compliance/nis2/${assessment.id}`}>
            <Button size="sm">
              {assessment.status === "draft" ? "Start Wizard" : "Continue"}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Shield,
  ArrowLeft,
  ArrowRight,
  Check,
  Building2,
  Users,
  Server,
  Laptop,
  FileText,
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  Save,
  ChevronRight,
  X,
  Link2,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import { iso27001API } from "@/lib/api-client";
import { Header } from "@/components/shared/header";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

// Types
interface Assessment {
  id: string;
  name: string;
  description: string | null;
  status: string;
  scope_description: string | null;
  scope_systems: string[];
  scope_locations: string[];
  scope_processes: string[];
  risk_appetite: string | null;
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

interface SoAEntry {
  id: string;
  assessment_id: string;
  control_id: string;
  control_code: string | null;
  control_title: string | null;
  control_theme: string | null;
  applicability: "applicable" | "not_applicable" | "excluded";
  justification: string | null;
  status: "not_evaluated" | "compliant" | "partial" | "gap" | "not_applicable";
  implementation_level: number;
  evidence: string | null;
  implementation_notes: string | null;
  gap_description: string | null;
  remediation_plan: string | null;
  remediation_owner: string | null;
  remediation_due_date: string | null;
  priority: number;
  assessed_by: string | null;
  assessed_at: string | null;
}

interface SoAListResponse {
  entries: SoAEntry[];
  total: number;
  by_theme: Record<string, number>;
  by_status: Record<string, number>;
}

// Update type for SoA entry (matches API client)
interface SoAEntryUpdate {
  applicability?: string;
  justification?: string;
  status?: string;
  implementation_level?: number;
  evidence?: string;
  implementation_notes?: string;
  gap_description?: string;
  remediation_plan?: string;
  remediation_owner?: string;
  remediation_due_date?: string;
  priority?: number;
}

interface GapItem {
  control_id: string;
  control_code: string;
  control_title: string;
  theme: string;
  status: string;
  implementation_level: number;
  gap_description: string | null;
  remediation_plan: string | null;
  remediation_owner: string | null;
  remediation_due_date: string | null;
  priority: number;
  cross_references: Record<string, string[]>;
}

interface GapAnalysisResponse {
  assessment_id: string;
  assessment_name: string;
  total_gaps: number;
  gaps_by_priority: Record<number, number>;
  gaps_by_theme: Record<string, number>;
  gaps: GapItem[];
}

interface ControlMapping {
  control_id: string;
  control_code: string;
  control_title: string;
  theme: string;
  status: string | null;
  related_controls: Array<{
    framework: string;
    control_id: string;
    control_name: string | null;
  }>;
}

interface CrossFrameworkMappingResponse {
  assessment_id: string;
  mappings: ControlMapping[];
  frameworks_referenced: string[];
  total_bsi_references: number;
  total_nis2_references: number;
  total_nist_references: number;
}

interface AssessmentOverview {
  assessment: Assessment;
  themes: Array<{
    theme_id: string;
    theme_name: string;
    total_controls: number;
    applicable_controls: number;
    compliant_controls: number;
    partial_controls: number;
    gap_controls: number;
    not_evaluated: number;
    score: number | null;
  }>;
  total_applicable: number;
  total_compliant: number;
  total_partial: number;
  total_gap: number;
  overall_score: number | null;
  completion_percentage: number;
}

const STEPS = [
  { id: 1, name: "Scope", description: "Define certification scope" },
  { id: 2, name: "SoA", description: "Statement of Applicability" },
  { id: 3, name: "Assessment", description: "Evaluate controls" },
  { id: 4, name: "Gap Analysis", description: "Review gaps" },
  { id: 5, name: "Cross-Framework", description: "Related controls" },
  { id: 6, name: "Report", description: "Summary & export" },
];

const THEME_ICONS: Record<string, typeof Building2> = {
  "A.5": Building2,
  "A.6": Users,
  "A.7": Server,
  "A.8": Laptop,
};

const THEME_NAMES: Record<string, string> = {
  "A.5": "Organizational",
  "A.6": "People",
  "A.7": "Physical",
  "A.8": "Technological",
};

export default function ISO27001AssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const assessmentId = params.id as string;
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedTheme, setSelectedTheme] = useState<string>("all");
  const [editingEntry, setEditingEntry] = useState<SoAEntry | null>(null);
  const [isCompleteDialogOpen, setIsCompleteDialogOpen] = useState(false);
  const [isExportingPDF, setIsExportingPDF] = useState(false);
  const [isExportingJSON, setIsExportingJSON] = useState(false);

  // Scope form state
  const [scopeForm, setScopeForm] = useState({
    scope_description: "",
    scope_systems: [] as string[],
    scope_locations: [] as string[],
    scope_processes: [] as string[],
    risk_appetite: "",
  });

  // Queries
  const { data: assessment, isLoading: assessmentLoading } = useQuery<Assessment>({
    queryKey: ["iso27001", "assessment", assessmentId],
    queryFn: () => iso27001API.getAssessment(token!, assessmentId) as Promise<Assessment>,
    enabled: !!token && !!assessmentId,
  });

  const { data: soaData, isLoading: soaLoading } = useQuery<SoAListResponse>({
    queryKey: ["iso27001", "soa", assessmentId, selectedTheme],
    queryFn: () => iso27001API.getSoAEntries(token!, assessmentId,
      selectedTheme !== "all" ? selectedTheme : undefined
    ) as Promise<SoAListResponse>,
    enabled: !!token && !!assessmentId && (currentStep === 2 || currentStep === 3),
  });

  const { data: overview } = useQuery<AssessmentOverview>({
    queryKey: ["iso27001", "overview", assessmentId],
    queryFn: () => iso27001API.getOverview(token!, assessmentId) as Promise<AssessmentOverview>,
    enabled: !!token && !!assessmentId && currentStep === 6,
  });

  const { data: gapAnalysis } = useQuery<GapAnalysisResponse>({
    queryKey: ["iso27001", "gaps", assessmentId],
    queryFn: () => iso27001API.getGapAnalysis(token!, assessmentId) as Promise<GapAnalysisResponse>,
    enabled: !!token && !!assessmentId && currentStep === 4,
  });

  const { data: crossFramework } = useQuery<CrossFrameworkMappingResponse>({
    queryKey: ["iso27001", "mapping", assessmentId],
    queryFn: () => iso27001API.getCrossFrameworkMapping(token!, assessmentId) as Promise<CrossFrameworkMappingResponse>,
    enabled: !!token && !!assessmentId && currentStep === 5,
  });

  // Initialize scope form from assessment
  useEffect(() => {
    if (assessment) {
      setScopeForm({
        scope_description: assessment.scope_description || "",
        scope_systems: assessment.scope_systems || [],
        scope_locations: assessment.scope_locations || [],
        scope_processes: assessment.scope_processes || [],
        risk_appetite: assessment.risk_appetite || "",
      });
    }
  }, [assessment]);

  // Mutations
  const updateScopeMutation = useMutation({
    mutationFn: (data: typeof scopeForm) =>
      iso27001API.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iso27001", "assessment", assessmentId] });
    },
  });

  const updateSoAMutation = useMutation({
    mutationFn: ({ controlId, data }: { controlId: string; data: SoAEntryUpdate }) =>
      iso27001API.updateSoAEntry(token!, assessmentId, controlId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iso27001", "soa", assessmentId] });
      queryClient.invalidateQueries({ queryKey: ["iso27001", "assessment", assessmentId] });
      setEditingEntry(null);
    },
  });

  const completeMutation = useMutation({
    mutationFn: () => iso27001API.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iso27001"] });
      setIsCompleteDialogOpen(false);
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "compliant":
        return "bg-green-500 text-white";
      case "partial":
        return "bg-yellow-500 text-white";
      case "gap":
        return "bg-red-500 text-white";
      case "not_applicable":
        return "bg-gray-400 text-white";
      default:
        return "bg-gray-200 text-gray-700";
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-muted-foreground";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getPriorityBadge = (priority: number) => {
    const configs: Record<number, { label: string; variant: "destructive" | "default" | "secondary" | "outline" }> = {
      1: { label: "Critical", variant: "destructive" },
      2: { label: "High", variant: "default" },
      3: { label: "Medium", variant: "secondary" },
      4: { label: "Low", variant: "outline" },
    };
    const config = configs[priority] || configs[3];
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handleSaveScope = () => {
    updateScopeMutation.mutate(scopeForm);
  };

  const handleAddListItem = (field: "scope_systems" | "scope_locations" | "scope_processes", value: string) => {
    if (value.trim()) {
      setScopeForm({
        ...scopeForm,
        [field]: [...scopeForm[field], value.trim()],
      });
    }
  };

  const handleRemoveListItem = (field: "scope_systems" | "scope_locations" | "scope_processes", index: number) => {
    setScopeForm({
      ...scopeForm,
      [field]: scopeForm[field].filter((_, i) => i !== index),
    });
  };

  const handleExportPDF = async () => {
    if (!token) {
      toast.error("Authentication required");
      return;
    }

    setIsExportingPDF(true);
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${API_BASE_URL}/api/v1/iso27001/assessments/${assessmentId}/report?format=pdf&include_gaps=true`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Export failed" }));
        throw new Error(error.detail || "Failed to export PDF");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `iso27001-assessment-${assessmentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("PDF report exported successfully");
    } catch (error) {
      console.error("PDF export error:", error);
      toast.error(error instanceof Error ? error.message : "Failed to export PDF report");
    } finally {
      setIsExportingPDF(false);
    }
  };

  const handleExportJSON = async () => {
    if (!token) {
      toast.error("Authentication required");
      return;
    }

    setIsExportingJSON(true);
    try {
      const report = await iso27001API.getReport(token, assessmentId, {
        format: "json",
        include_gaps: true,
        include_evidence: true,
      });

      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `iso27001-assessment-${assessmentId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("JSON report exported successfully");
    } catch (error) {
      console.error("JSON export error:", error);
      toast.error(error instanceof Error ? error.message : "Failed to export JSON report");
    } finally {
      setIsExportingJSON(false);
    }
  };

  if (assessmentLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading assessment...</div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Assessment not found</p>
        <Button onClick={() => router.push("/compliance/frameworks/iso27001")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Assessments
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header
        title={assessment.name}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/compliance/frameworks/iso27001")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            {assessment.status !== "completed" && (
              <Button onClick={() => setIsCompleteDialogOpen(true)}>
                <Check className="h-4 w-4 mr-2" />
                Complete Assessment
              </Button>
            )}
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        {/* Step Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => setCurrentStep(step.id)}
                  className={cn(
                    "flex flex-col items-center gap-1 transition-colors",
                    currentStep === step.id
                      ? "text-primary"
                      : currentStep > step.id
                      ? "text-green-600"
                      : "text-muted-foreground"
                  )}
                >
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
                      currentStep === step.id
                        ? "border-primary bg-primary text-primary-foreground"
                        : currentStep > step.id
                        ? "border-green-600 bg-green-600 text-white"
                        : "border-muted-foreground"
                    )}
                  >
                    {currentStep > step.id ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      step.id
                    )}
                  </div>
                  <span className="text-xs font-medium hidden md:block">{step.name}</span>
                </button>
                {index < STEPS.length - 1 && (
                  <ChevronRight className="h-5 w-5 mx-2 text-muted-foreground" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-6">
          {/* Step 1: Scope */}
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Define Certification Scope</CardTitle>
                <CardDescription>
                  Define the scope of your ISO 27001 certification, including systems, locations, and processes covered by the ISMS.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Scope Description</Label>
                  <Textarea
                    value={scopeForm.scope_description}
                    onChange={(e) => setScopeForm({ ...scopeForm, scope_description: e.target.value })}
                    placeholder="Describe the scope of your ISMS certification..."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Systems in Scope</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a system..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddListItem("scope_systems", e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <Button
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleAddListItem("scope_systems", input.value);
                        input.value = "";
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {scopeForm.scope_systems.map((item, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {item}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => handleRemoveListItem("scope_systems", index)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Locations</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a location..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddListItem("scope_locations", e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <Button
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleAddListItem("scope_locations", input.value);
                        input.value = "";
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {scopeForm.scope_locations.map((item, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {item}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => handleRemoveListItem("scope_locations", index)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Processes</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a process..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddListItem("scope_processes", e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <Button
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleAddListItem("scope_processes", input.value);
                        input.value = "";
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {scopeForm.scope_processes.map((item, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {item}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => handleRemoveListItem("scope_processes", index)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Risk Appetite</Label>
                  <Select
                    value={scopeForm.risk_appetite}
                    onValueChange={(value) => setScopeForm({ ...scopeForm, risk_appetite: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select risk appetite" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low - Conservative approach</SelectItem>
                      <SelectItem value="medium">Medium - Balanced approach</SelectItem>
                      <SelectItem value="high">High - Aggressive approach</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    onClick={handleSaveScope}
                    disabled={updateScopeMutation.isPending}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {updateScopeMutation.isPending ? "Saving..." : "Save Scope"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Statement of Applicability */}
          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle>Statement of Applicability (SoA)</CardTitle>
                <CardDescription>
                  Define which controls are applicable to your organization and provide justification for exclusions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <Select value={selectedTheme} onValueChange={setSelectedTheme}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Filter by theme" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Themes</SelectItem>
                      <SelectItem value="A.5">A.5 - Organizational</SelectItem>
                      <SelectItem value="A.6">A.6 - People</SelectItem>
                      <SelectItem value="A.7">A.7 - Physical</SelectItem>
                      <SelectItem value="A.8">A.8 - Technological</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {soaLoading ? (
                  <div className="py-8 text-center text-muted-foreground">Loading controls...</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[100px]">Control</TableHead>
                        <TableHead>Title</TableHead>
                        <TableHead className="w-[150px]">Applicability</TableHead>
                        <TableHead className="w-[100px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {soaData?.entries.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell className="font-mono text-sm">
                            {entry.control_code}
                          </TableCell>
                          <TableCell>{entry.control_title}</TableCell>
                          <TableCell>
                            <Select
                              value={entry.applicability}
                              onValueChange={(value) =>
                                updateSoAMutation.mutate({
                                  controlId: entry.control_id,
                                  data: { applicability: value as SoAEntry["applicability"] },
                                })
                              }
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="applicable">Applicable</SelectItem>
                                <SelectItem value="not_applicable">Not Applicable</SelectItem>
                                <SelectItem value="excluded">Excluded</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingEntry(entry)}
                            >
                              Edit
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          )}

          {/* Step 3: Assessment */}
          {currentStep === 3 && (
            <Card>
              <CardHeader>
                <CardTitle>Control Assessment</CardTitle>
                <CardDescription>
                  Evaluate the implementation status of each applicable control.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={selectedTheme} onValueChange={setSelectedTheme}>
                  <TabsList>
                    <TabsTrigger value="all">All</TabsTrigger>
                    <TabsTrigger value="A.5">Organizational</TabsTrigger>
                    <TabsTrigger value="A.6">People</TabsTrigger>
                    <TabsTrigger value="A.7">Physical</TabsTrigger>
                    <TabsTrigger value="A.8">Technological</TabsTrigger>
                  </TabsList>

                  <TabsContent value={selectedTheme} className="mt-4">
                    {soaLoading ? (
                      <div className="py-8 text-center text-muted-foreground">Loading controls...</div>
                    ) : (
                      <div className="space-y-4">
                        {soaData?.entries
                          .filter((e) => e.applicability === "applicable")
                          .map((entry) => (
                            <Card key={entry.id} className="border-l-4" style={{
                              borderLeftColor: entry.status === "compliant" ? "rgb(34, 197, 94)" :
                                entry.status === "partial" ? "rgb(234, 179, 8)" :
                                entry.status === "gap" ? "rgb(239, 68, 68)" : "rgb(156, 163, 175)"
                            }}>
                              <CardContent className="pt-4">
                                <div className="flex items-start justify-between">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono text-sm">{entry.control_code}</span>
                                      <Badge className={getStatusColor(entry.status)}>
                                        {entry.status.replace("_", " ")}
                                      </Badge>
                                    </div>
                                    <p className="font-medium">{entry.control_title}</p>
                                  </div>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setEditingEntry(entry)}
                                  >
                                    Assess
                                  </Button>
                                </div>
                                <div className="mt-3">
                                  <div className="flex justify-between text-sm mb-1">
                                    <span className="text-muted-foreground">Implementation Level</span>
                                    <span>{entry.implementation_level}%</span>
                                  </div>
                                  <Progress value={entry.implementation_level} className="h-2" />
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}

          {/* Step 4: Gap Analysis */}
          {currentStep === 4 && (
            <Card>
              <CardHeader>
                <CardTitle>Gap Analysis</CardTitle>
                <CardDescription>
                  Review identified gaps and plan remediation actions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-2xl font-bold text-red-600">
                        {gapAnalysis?.total_gaps || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Total Gaps</p>
                    </CardContent>
                  </Card>
                  {[1, 2, 3, 4].map((priority) => (
                    <Card key={priority}>
                      <CardContent className="pt-4">
                        <div className="text-2xl font-bold">
                          {gapAnalysis?.gaps_by_priority[priority] || 0}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {priority === 1 ? "Critical" : priority === 2 ? "High" : priority === 3 ? "Medium" : "Low"}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Gap List */}
                <Accordion type="single" collapsible className="space-y-2">
                  {gapAnalysis?.gaps.map((gap) => (
                    <AccordionItem key={gap.control_id} value={gap.control_id} className="border rounded-lg">
                      <AccordionTrigger className="px-4 hover:no-underline">
                        <div className="flex items-center gap-4 text-left">
                          <span className="font-mono text-sm">{gap.control_code}</span>
                          {getPriorityBadge(gap.priority)}
                          <span className="flex-1">{gap.control_title}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-4 pb-4">
                        <div className="space-y-4">
                          {gap.gap_description && (
                            <div>
                              <Label className="text-muted-foreground">Gap Description</Label>
                              <p className="mt-1">{gap.gap_description}</p>
                            </div>
                          )}
                          {gap.remediation_plan && (
                            <div>
                              <Label className="text-muted-foreground">Remediation Plan</Label>
                              <p className="mt-1">{gap.remediation_plan}</p>
                            </div>
                          )}
                          <div className="flex gap-4">
                            {gap.remediation_owner && (
                              <div>
                                <Label className="text-muted-foreground">Owner</Label>
                                <p className="mt-1">{gap.remediation_owner}</p>
                              </div>
                            )}
                            {gap.remediation_due_date && (
                              <div>
                                <Label className="text-muted-foreground">Due Date</Label>
                                <p className="mt-1">{new Date(gap.remediation_due_date).toLocaleDateString()}</p>
                              </div>
                            )}
                          </div>
                          {Object.keys(gap.cross_references).length > 0 && (
                            <div>
                              <Label className="text-muted-foreground">Cross-References</Label>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {Object.entries(gap.cross_references).map(([framework, refs]) =>
                                  refs.map((ref) => (
                                    <Badge key={`${framework}-${ref}`} variant="outline">
                                      {framework}: {ref}
                                    </Badge>
                                  ))
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          )}

          {/* Step 5: Cross-Framework Mapping */}
          {currentStep === 5 && (
            <Card>
              <CardHeader>
                <CardTitle>Cross-Framework Mapping</CardTitle>
                <CardDescription>
                  View how ISO 27001 controls relate to other frameworks (BSI IT-Grundschutz, NIS2, NIST CSF).
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Link2 className="h-5 w-5 text-blue-500" />
                        <div>
                          <div className="text-xl font-bold">{crossFramework?.total_bsi_references || 0}</div>
                          <p className="text-sm text-muted-foreground">BSI IT-Grundschutz</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Link2 className="h-5 w-5 text-green-500" />
                        <div>
                          <div className="text-xl font-bold">{crossFramework?.total_nis2_references || 0}</div>
                          <p className="text-sm text-muted-foreground">NIS2</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Link2 className="h-5 w-5 text-purple-500" />
                        <div>
                          <div className="text-xl font-bold">{crossFramework?.total_nist_references || 0}</div>
                          <p className="text-sm text-muted-foreground">NIST CSF</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Mapping Table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[100px]">Control</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Related Controls</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {crossFramework?.mappings.map((mapping) => (
                      <TableRow key={mapping.control_id}>
                        <TableCell className="font-mono text-sm">{mapping.control_code}</TableCell>
                        <TableCell>{mapping.control_title}</TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(mapping.status || "not_evaluated")}>
                            {(mapping.status || "not_evaluated").replace("_", " ")}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {mapping.related_controls.map((rel, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {rel.framework}: {rel.control_id}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Step 6: Report */}
          {currentStep === 6 && (
            <div className="space-y-6">
              {/* Executive Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Executive Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="pt-4">
                        <div className={`text-3xl font-bold ${getScoreColor(overview?.overall_score ?? null)}`}>
                          {overview?.overall_score !== null && overview?.overall_score !== undefined
                            ? `${overview.overall_score.toFixed(0)}%`
                            : "N/A"}
                        </div>
                        <p className="text-sm text-muted-foreground">Overall Compliance</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <div className="text-2xl font-bold">{overview?.total_compliant || 0}</div>
                        </div>
                        <p className="text-sm text-muted-foreground">Compliant Controls</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2">
                          <Clock className="h-5 w-5 text-yellow-500" />
                          <div className="text-2xl font-bold">{overview?.total_partial || 0}</div>
                        </div>
                        <p className="text-sm text-muted-foreground">Partial Implementation</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="h-5 w-5 text-red-500" />
                          <div className="text-2xl font-bold">{overview?.total_gap || 0}</div>
                        </div>
                        <p className="text-sm text-muted-foreground">Gaps Identified</p>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>

              {/* Theme Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Compliance by Theme</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {overview?.themes.map((theme) => {
                      const Icon = THEME_ICONS[theme.theme_id] || Shield;
                      return (
                        <div key={theme.theme_id} className="flex items-center gap-4">
                          <Icon className="h-5 w-5 text-muted-foreground" />
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="font-medium">{theme.theme_name}</span>
                              <span className={getScoreColor(theme.score)}>
                                {theme.score !== null ? `${theme.score.toFixed(0)}%` : "N/A"}
                              </span>
                            </div>
                            <Progress value={theme.score ?? 0} className="h-2" />
                            <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                              <span>{theme.compliant_controls} compliant</span>
                              <span>{theme.partial_controls} partial</span>
                              <span>{theme.gap_controls} gaps</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Export Options */}
              <Card>
                <CardHeader>
                  <CardTitle>Export Report</CardTitle>
                  <CardDescription>
                    Generate and download the compliance report in various formats.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <Button
                      variant="outline"
                      onClick={handleExportPDF}
                      disabled={isExportingPDF}
                    >
                      {isExportingPDF ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      {isExportingPDF ? "Exporting..." : "Export PDF"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleExportJSON}
                      disabled={isExportingJSON}
                    >
                      {isExportingJSON ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <FileText className="h-4 w-4 mr-2" />
                      )}
                      {isExportingJSON ? "Exporting..." : "Export JSON"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>
          <Button
            onClick={() => setCurrentStep(Math.min(6, currentStep + 1))}
            disabled={currentStep === 6}
          >
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* Edit Entry Dialog */}
      {editingEntry && (
        <Dialog open={!!editingEntry} onOpenChange={() => setEditingEntry(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingEntry.control_code} - {editingEntry.control_title}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Applicability</Label>
                  <Select
                    value={editingEntry.applicability}
                    onValueChange={(value) =>
                      setEditingEntry({ ...editingEntry, applicability: value as SoAEntry["applicability"] })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="applicable">Applicable</SelectItem>
                      <SelectItem value="not_applicable">Not Applicable</SelectItem>
                      <SelectItem value="excluded">Excluded</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={editingEntry.status}
                    onValueChange={(value) =>
                      setEditingEntry({ ...editingEntry, status: value as SoAEntry["status"] })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="not_evaluated">Not Evaluated</SelectItem>
                      <SelectItem value="compliant">Compliant</SelectItem>
                      <SelectItem value="partial">Partial</SelectItem>
                      <SelectItem value="gap">Gap</SelectItem>
                      <SelectItem value="not_applicable">Not Applicable</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Implementation Level ({editingEntry.implementation_level}%)</Label>
                <Input
                  type="range"
                  min="0"
                  max="100"
                  value={editingEntry.implementation_level}
                  onChange={(e) =>
                    setEditingEntry({ ...editingEntry, implementation_level: parseInt(e.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Justification</Label>
                <Textarea
                  value={editingEntry.justification || ""}
                  onChange={(e) => setEditingEntry({ ...editingEntry, justification: e.target.value })}
                  placeholder="Justify why this control is applicable/not applicable..."
                />
              </div>

              <div className="space-y-2">
                <Label>Evidence</Label>
                <Textarea
                  value={editingEntry.evidence || ""}
                  onChange={(e) => setEditingEntry({ ...editingEntry, evidence: e.target.value })}
                  placeholder="Document evidence of implementation..."
                />
              </div>

              <div className="space-y-2">
                <Label>Implementation Notes</Label>
                <Textarea
                  value={editingEntry.implementation_notes || ""}
                  onChange={(e) => setEditingEntry({ ...editingEntry, implementation_notes: e.target.value })}
                  placeholder="Additional notes about implementation..."
                />
              </div>

              {(editingEntry.status === "gap" || editingEntry.status === "partial") && (
                <>
                  <div className="space-y-2">
                    <Label>Gap Description</Label>
                    <Textarea
                      value={editingEntry.gap_description || ""}
                      onChange={(e) => setEditingEntry({ ...editingEntry, gap_description: e.target.value })}
                      placeholder="Describe the gap..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Remediation Plan</Label>
                    <Textarea
                      value={editingEntry.remediation_plan || ""}
                      onChange={(e) => setEditingEntry({ ...editingEntry, remediation_plan: e.target.value })}
                      placeholder="Plan to address the gap..."
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Remediation Owner</Label>
                      <Input
                        value={editingEntry.remediation_owner || ""}
                        onChange={(e) => setEditingEntry({ ...editingEntry, remediation_owner: e.target.value })}
                        placeholder="Responsible person..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <Select
                        value={editingEntry.priority.toString()}
                        onValueChange={(value) =>
                          setEditingEntry({ ...editingEntry, priority: parseInt(value) })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">1 - Critical</SelectItem>
                          <SelectItem value="2">2 - High</SelectItem>
                          <SelectItem value="3">3 - Medium</SelectItem>
                          <SelectItem value="4">4 - Low</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingEntry(null)}>
                Cancel
              </Button>
              <Button
                onClick={() => {
                  updateSoAMutation.mutate({
                    controlId: editingEntry.control_id,
                    data: {
                      applicability: editingEntry.applicability,
                      status: editingEntry.status,
                      implementation_level: editingEntry.implementation_level,
                      justification: editingEntry.justification ?? undefined,
                      evidence: editingEntry.evidence ?? undefined,
                      implementation_notes: editingEntry.implementation_notes ?? undefined,
                      gap_description: editingEntry.gap_description ?? undefined,
                      remediation_plan: editingEntry.remediation_plan ?? undefined,
                      remediation_owner: editingEntry.remediation_owner ?? undefined,
                      priority: editingEntry.priority,
                    },
                  });
                }}
                disabled={updateSoAMutation.isPending}
              >
                {updateSoAMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Complete Assessment Dialog */}
      <Dialog open={isCompleteDialogOpen} onOpenChange={setIsCompleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Assessment</DialogTitle>
            <DialogDescription>
              Are you sure you want to mark this assessment as complete? This will finalize the scores and generate the final report.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCompleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => completeMutation.mutate()}
              disabled={completeMutation.isPending}
            >
              {completeMutation.isPending ? "Completing..." : "Complete Assessment"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

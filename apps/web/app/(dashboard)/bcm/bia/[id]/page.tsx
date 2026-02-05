"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Building2,
  Users,
  Clock,
  Save,
  ChevronRight,
  AlertCircle,
  DollarSign,
  Scale,
  Shield,
  Heart,
  Server,
  HardDrive,
  Target,
  Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
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
import { useAuthStore } from "@/stores/auth-store";
import { bcmAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";
import { cn } from "@/lib/utils";

// Types
interface Process {
  id: string;
  process_id: string;
  name: string;
  description: string | null;
  owner: string;
  department: string | null;
  criticality: string;
  status: string;
  internal_dependencies: string[];
  external_dependencies: string[];
  it_systems: string[];
  key_personnel: string[];
}

interface BIA {
  id: string;
  process_id: string;
  rto_hours: number;
  rpo_hours: number;
  mtpd_hours: number;
  impact_1h: string;
  impact_4h: string;
  impact_8h: string;
  impact_24h: string;
  impact_72h: string;
  impact_1w: string;
  financial_impact: number;
  operational_impact: number;
  reputational_impact: number;
  legal_impact: number;
  safety_impact: number;
  financial_justification: string | null;
  operational_justification: string | null;
  minimum_staff: number;
  minimum_workspace: string | null;
  critical_equipment: string[];
  critical_data: string[];
  analysis_date: string;
  analyst: string;
  next_review_date: string | null;
  status: string;
}

const STEPS = [
  { id: 1, name: "Process", description: "Review process details" },
  { id: 2, name: "Impact Timeline", description: "Impact over time" },
  { id: 3, name: "Impact Categories", description: "Category assessment" },
  { id: 4, name: "Recovery Objectives", description: "RTO, RPO, MTPD" },
  { id: 5, name: "Resources", description: "Resource requirements" },
  { id: 6, name: "Review", description: "Complete BIA" },
];

const IMPACT_LEVELS = [
  { value: "none", label: "None", color: "bg-gray-200" },
  { value: "low", label: "Low", color: "bg-green-500" },
  { value: "medium", label: "Medium", color: "bg-yellow-500" },
  { value: "high", label: "High", color: "bg-orange-500" },
  { value: "critical", label: "Critical", color: "bg-red-500" },
];

const TIME_PERIODS = [
  { key: "impact_1h", label: "1 Hour" },
  { key: "impact_4h", label: "4 Hours" },
  { key: "impact_8h", label: "8 Hours" },
  { key: "impact_24h", label: "24 Hours" },
  { key: "impact_72h", label: "72 Hours" },
  { key: "impact_1w", label: "1 Week" },
];

export default function BIAWizardPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const processId = params.id as string;
  const [currentStep, setCurrentStep] = useState(1);
  const [isCompleteDialogOpen, setIsCompleteDialogOpen] = useState(false);

  // BIA form state
  const [biaForm, setBiaForm] = useState({
    rto_hours: 24,
    rpo_hours: 4,
    mtpd_hours: 72,
    impact_1h: "low",
    impact_4h: "medium",
    impact_8h: "medium",
    impact_24h: "high",
    impact_72h: "critical",
    impact_1w: "critical",
    financial_impact: 3,
    operational_impact: 3,
    reputational_impact: 2,
    legal_impact: 2,
    safety_impact: 1,
    financial_justification: "",
    operational_justification: "",
    minimum_staff: 1,
    minimum_workspace: "",
    critical_equipment: [] as string[],
    critical_data: [] as string[],
    analyst: "",
    next_review_date: "",
  });

  // Queries
  const { data: process, isLoading: processLoading } = useQuery<Process>({
    queryKey: ["bcm", "process", processId],
    queryFn: () => bcmAPI.getProcess(token!, processId) as Promise<Process>,
    enabled: !!token && !!processId,
  });

  const { data: existingBia, isLoading: biaLoading } = useQuery<BIA>({
    queryKey: ["bcm", "bia", processId],
    queryFn: () => bcmAPI.getBIA(token!, processId) as Promise<BIA>,
    enabled: !!token && !!processId,
  });

  // Initialize form from existing BIA
  useEffect(() => {
    if (existingBia) {
      setBiaForm({
        rto_hours: existingBia.rto_hours,
        rpo_hours: existingBia.rpo_hours,
        mtpd_hours: existingBia.mtpd_hours,
        impact_1h: existingBia.impact_1h,
        impact_4h: existingBia.impact_4h,
        impact_8h: existingBia.impact_8h,
        impact_24h: existingBia.impact_24h,
        impact_72h: existingBia.impact_72h,
        impact_1w: existingBia.impact_1w,
        financial_impact: existingBia.financial_impact,
        operational_impact: existingBia.operational_impact,
        reputational_impact: existingBia.reputational_impact,
        legal_impact: existingBia.legal_impact,
        safety_impact: existingBia.safety_impact,
        financial_justification: existingBia.financial_justification || "",
        operational_justification: existingBia.operational_justification || "",
        minimum_staff: existingBia.minimum_staff,
        minimum_workspace: existingBia.minimum_workspace || "",
        critical_equipment: existingBia.critical_equipment || [],
        critical_data: existingBia.critical_data || [],
        analyst: existingBia.analyst,
        next_review_date: existingBia.next_review_date || "",
      });
    }
  }, [existingBia]);

  // Mutations
  const saveBiaMutation = useMutation({
    mutationFn: (data: typeof biaForm) => bcmAPI.createOrUpdateBIA(token!, processId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
    },
  });

  const getImpactColor = (level: string) => {
    const impact = IMPACT_LEVELS.find((i) => i.value === level);
    return impact?.color || "bg-gray-200";
  };

  const getImpactLabel = (level: string) => {
    const impact = IMPACT_LEVELS.find((i) => i.value === level);
    return impact?.label || level;
  };

  const handleSave = () => {
    saveBiaMutation.mutate(biaForm);
  };

  const handleComplete = () => {
    saveBiaMutation.mutate({ ...biaForm, status: "completed" } as typeof biaForm);
    setIsCompleteDialogOpen(false);
    router.push("/bcm");
  };

  const handleAddListItem = (field: "critical_equipment" | "critical_data", value: string) => {
    if (value.trim()) {
      setBiaForm({
        ...biaForm,
        [field]: [...biaForm[field], value.trim()],
      });
    }
  };

  const handleRemoveListItem = (field: "critical_equipment" | "critical_data", index: number) => {
    setBiaForm({
      ...biaForm,
      [field]: biaForm[field].filter((_, i) => i !== index),
    });
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

  if (processLoading || biaLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!process) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Process not found</p>
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
        title={`Business Impact Analysis: ${process.name}`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/bcm")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Button onClick={handleSave} disabled={saveBiaMutation.isPending}>
              <Save className="h-4 w-4 mr-2" />
              {saveBiaMutation.isPending ? "Saving..." : "Save"}
            </Button>
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
          {/* Step 1: Process Details */}
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Process Details</CardTitle>
                <CardDescription>
                  Review the business process information before conducting the Business Impact Analysis.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-muted-foreground">Process ID</Label>
                      <p className="font-mono">{process.process_id}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Process Name</Label>
                      <p className="font-semibold">{process.name}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Description</Label>
                      <p>{process.description || "No description provided"}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Criticality</Label>
                      <div className="mt-1">{getCriticalityBadge(process.criticality)}</div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <Label className="text-muted-foreground">Process Owner</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{process.owner}</span>
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Department</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span>{process.department || "Not specified"}</span>
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Internal Dependencies</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {process.internal_dependencies?.length > 0 ? (
                          process.internal_dependencies.map((dep, idx) => (
                            <Badge key={idx} variant="outline">{dep}</Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">External Dependencies</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {process.external_dependencies?.length > 0 ? (
                          process.external_dependencies.map((dep, idx) => (
                            <Badge key={idx} variant="outline">{dep}</Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label className="text-muted-foreground">IT Systems</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {process.it_systems?.length > 0 ? (
                          process.it_systems.map((sys, idx) => (
                            <Badge key={idx} variant="secondary">
                              <Server className="h-3 w-3 mr-1" />
                              {sys}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None specified</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Key Personnel</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {process.key_personnel?.length > 0 ? (
                          process.key_personnel.map((person, idx) => (
                            <Badge key={idx} variant="secondary">
                              <Users className="h-3 w-3 mr-1" />
                              {person}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None specified</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Impact Timeline */}
          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle>Impact Timeline</CardTitle>
                <CardDescription>
                  Assess how the impact of process unavailability changes over time.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  {TIME_PERIODS.map((period) => (
                    <div key={period.key} className="flex items-center gap-4">
                      <div className="w-24 text-sm font-medium">{period.label}</div>
                      <div className="flex-1">
                        <Select
                          value={biaForm[period.key as keyof typeof biaForm] as string}
                          onValueChange={(value) =>
                            setBiaForm({ ...biaForm, [period.key]: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {IMPACT_LEVELS.map((level) => (
                              <SelectItem key={level.value} value={level.value}>
                                {level.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div
                        className={cn(
                          "w-6 h-6 rounded-full",
                          getImpactColor(biaForm[period.key as keyof typeof biaForm] as string)
                        )}
                      />
                    </div>
                  ))}
                </div>

                {/* Visual Timeline */}
                <div className="mt-8 p-4 bg-muted rounded-lg">
                  <Label className="text-sm font-medium mb-4 block">Impact Progression</Label>
                  <div className="flex items-end gap-2 h-32">
                    {TIME_PERIODS.map((period) => {
                      const level = biaForm[period.key as keyof typeof biaForm] as string;
                      const heights: Record<string, string> = {
                        none: "h-4",
                        low: "h-8",
                        medium: "h-16",
                        high: "h-24",
                        critical: "h-32",
                      };
                      return (
                        <div key={period.key} className="flex-1 flex flex-col items-center">
                          <div
                            className={cn(
                              "w-full rounded-t transition-all",
                              heights[level],
                              getImpactColor(level)
                            )}
                          />
                          <span className="text-xs text-muted-foreground mt-1">{period.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 3: Impact Categories */}
          {currentStep === 3 && (
            <Card>
              <CardHeader>
                <CardTitle>Impact Categories</CardTitle>
                <CardDescription>
                  Assess the impact severity for each category (1 = Minimal, 5 = Severe).
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Financial Impact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-green-600" />
                    <Label>Financial Impact</Label>
                    <Badge variant="outline">{biaForm.financial_impact}/5</Badge>
                  </div>
                  <Input
                    type="range"
                    min="1"
                    max="5"
                    value={biaForm.financial_impact}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, financial_impact: parseInt(e.target.value) })
                    }
                    className="w-full"
                  />
                  <Textarea
                    value={biaForm.financial_justification}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, financial_justification: e.target.value })
                    }
                    placeholder="Justify the financial impact rating..."
                    rows={2}
                  />
                </div>

                {/* Operational Impact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-blue-600" />
                    <Label>Operational Impact</Label>
                    <Badge variant="outline">{biaForm.operational_impact}/5</Badge>
                  </div>
                  <Input
                    type="range"
                    min="1"
                    max="5"
                    value={biaForm.operational_impact}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, operational_impact: parseInt(e.target.value) })
                    }
                    className="w-full"
                  />
                  <Textarea
                    value={biaForm.operational_justification}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, operational_justification: e.target.value })
                    }
                    placeholder="Justify the operational impact rating..."
                    rows={2}
                  />
                </div>

                {/* Reputational Impact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-600" />
                    <Label>Reputational Impact</Label>
                    <Badge variant="outline">{biaForm.reputational_impact}/5</Badge>
                  </div>
                  <Input
                    type="range"
                    min="1"
                    max="5"
                    value={biaForm.reputational_impact}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, reputational_impact: parseInt(e.target.value) })
                    }
                    className="w-full"
                  />
                </div>

                {/* Legal Impact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Scale className="h-5 w-5 text-orange-600" />
                    <Label>Legal/Compliance Impact</Label>
                    <Badge variant="outline">{biaForm.legal_impact}/5</Badge>
                  </div>
                  <Input
                    type="range"
                    min="1"
                    max="5"
                    value={biaForm.legal_impact}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, legal_impact: parseInt(e.target.value) })
                    }
                    className="w-full"
                  />
                </div>

                {/* Safety Impact */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Heart className="h-5 w-5 text-red-600" />
                    <Label>Health & Safety Impact</Label>
                    <Badge variant="outline">{biaForm.safety_impact}/5</Badge>
                  </div>
                  <Input
                    type="range"
                    min="1"
                    max="5"
                    value={biaForm.safety_impact}
                    onChange={(e) =>
                      setBiaForm({ ...biaForm, safety_impact: parseInt(e.target.value) })
                    }
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 4: Recovery Objectives */}
          {currentStep === 4 && (
            <Card>
              <CardHeader>
                <CardTitle>Recovery Objectives</CardTitle>
                <CardDescription>
                  Define the recovery time and point objectives based on impact analysis.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* RTO */}
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-5 w-5 text-blue-600" />
                        <Label className="font-semibold">RTO (Recovery Time Objective)</Label>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        Maximum acceptable time to restore the process after a disruption.
                      </p>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min="0"
                          value={biaForm.rto_hours}
                          onChange={(e) =>
                            setBiaForm({ ...biaForm, rto_hours: parseInt(e.target.value) || 0 })
                          }
                          className="w-24"
                        />
                        <span className="text-sm">hours</span>
                      </div>
                      <div className="mt-2 text-sm text-muted-foreground">
                        = {Math.floor(biaForm.rto_hours / 24)} days {biaForm.rto_hours % 24} hours
                      </div>
                    </CardContent>
                  </Card>

                  {/* RPO */}
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-4">
                        <HardDrive className="h-5 w-5 text-green-600" />
                        <Label className="font-semibold">RPO (Recovery Point Objective)</Label>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        Maximum acceptable data loss measured in time (backup frequency).
                      </p>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min="0"
                          value={biaForm.rpo_hours}
                          onChange={(e) =>
                            setBiaForm({ ...biaForm, rpo_hours: parseInt(e.target.value) || 0 })
                          }
                          className="w-24"
                        />
                        <span className="text-sm">hours</span>
                      </div>
                      <div className="mt-2 text-sm text-muted-foreground">
                        = {Math.floor(biaForm.rpo_hours / 24)} days {biaForm.rpo_hours % 24} hours
                      </div>
                    </CardContent>
                  </Card>

                  {/* MTPD */}
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-4">
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <Label className="font-semibold">MTPD (Maximum Tolerable Period)</Label>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        Maximum time before the organization suffers unacceptable consequences.
                      </p>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min="0"
                          value={biaForm.mtpd_hours}
                          onChange={(e) =>
                            setBiaForm({ ...biaForm, mtpd_hours: parseInt(e.target.value) || 0 })
                          }
                          className="w-24"
                        />
                        <span className="text-sm">hours</span>
                      </div>
                      <div className="mt-2 text-sm text-muted-foreground">
                        = {Math.floor(biaForm.mtpd_hours / 24)} days {biaForm.mtpd_hours % 24} hours
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Visual Comparison */}
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <Label className="text-sm font-medium mb-4 block">Recovery Timeline</Label>
                  <div className="relative h-12 bg-background rounded">
                    {/* RPO Marker */}
                    <div
                      className="absolute top-0 h-full border-l-2 border-green-600"
                      style={{
                        left: `${Math.min((biaForm.rpo_hours / biaForm.mtpd_hours) * 100, 100)}%`,
                      }}
                    >
                      <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs text-green-600 whitespace-nowrap">
                        RPO ({biaForm.rpo_hours}h)
                      </span>
                    </div>
                    {/* RTO Marker */}
                    <div
                      className="absolute top-0 h-full border-l-2 border-blue-600"
                      style={{
                        left: `${Math.min((biaForm.rto_hours / biaForm.mtpd_hours) * 100, 100)}%`,
                      }}
                    >
                      <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs text-blue-600 whitespace-nowrap">
                        RTO ({biaForm.rto_hours}h)
                      </span>
                    </div>
                    {/* MTPD Marker */}
                    <div className="absolute top-0 right-0 h-full border-l-2 border-red-600">
                      <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs text-red-600 whitespace-nowrap">
                        MTPD ({biaForm.mtpd_hours}h)
                      </span>
                    </div>
                    {/* Timeline bar */}
                    <div className="absolute top-1/2 left-0 right-0 h-1 bg-gray-300 -translate-y-1/2" />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-2">
                    <span>Disruption</span>
                    <span>Maximum Tolerable Period</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 5: Resource Requirements */}
          {currentStep === 5 && (
            <Card>
              <CardHeader>
                <CardTitle>Resource Requirements</CardTitle>
                <CardDescription>
                  Define the minimum resources needed to recover and operate the process.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Minimum Staff Required</Label>
                    <Input
                      type="number"
                      min="0"
                      value={biaForm.minimum_staff}
                      onChange={(e) =>
                        setBiaForm({ ...biaForm, minimum_staff: parseInt(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Minimum Workspace</Label>
                    <Input
                      value={biaForm.minimum_workspace}
                      onChange={(e) =>
                        setBiaForm({ ...biaForm, minimum_workspace: e.target.value })
                      }
                      placeholder="e.g., 10 workstations, backup office"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Critical Equipment</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add critical equipment..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddListItem("critical_equipment", e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <Button
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleAddListItem("critical_equipment", input.value);
                        input.value = "";
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {biaForm.critical_equipment.map((item, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => handleRemoveListItem("critical_equipment", index)}
                      >
                        {item} &times;
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Critical Data/Systems</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add critical data or system..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddListItem("critical_data", e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <Button
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleAddListItem("critical_data", input.value);
                        input.value = "";
                      }}
                    >
                      Add
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {biaForm.critical_data.map((item, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => handleRemoveListItem("critical_data", index)}
                      >
                        {item} &times;
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 6: Review & Complete */}
          {currentStep === 6 && (
            <div className="space-y-6">
              {/* Summary Card */}
              <Card>
                <CardHeader>
                  <CardTitle>BIA Summary</CardTitle>
                  <CardDescription>
                    Review the Business Impact Analysis before completing.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Recovery Objectives Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="pt-4 text-center">
                        <div className="text-3xl font-bold text-blue-600">{biaForm.rto_hours}h</div>
                        <p className="text-sm text-muted-foreground">RTO</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4 text-center">
                        <div className="text-3xl font-bold text-green-600">{biaForm.rpo_hours}h</div>
                        <p className="text-sm text-muted-foreground">RPO</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4 text-center">
                        <div className="text-3xl font-bold text-red-600">{biaForm.mtpd_hours}h</div>
                        <p className="text-sm text-muted-foreground">MTPD</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Impact Categories Summary */}
                  <div>
                    <Label className="text-sm font-medium mb-2 block">Impact Categories</Label>
                    <div className="grid grid-cols-5 gap-2">
                      {[
                        { label: "Financial", value: biaForm.financial_impact, icon: DollarSign },
                        { label: "Operational", value: biaForm.operational_impact, icon: Target },
                        { label: "Reputation", value: biaForm.reputational_impact, icon: Shield },
                        { label: "Legal", value: biaForm.legal_impact, icon: Scale },
                        { label: "Safety", value: biaForm.safety_impact, icon: Heart },
                      ].map((cat) => (
                        <div key={cat.label} className="text-center p-2 bg-muted rounded">
                          <cat.icon className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
                          <div className="text-lg font-bold">{cat.value}/5</div>
                          <p className="text-xs text-muted-foreground">{cat.label}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Resources Summary */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-muted-foreground">Minimum Staff</Label>
                      <p className="font-semibold">{biaForm.minimum_staff} personnel</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Workspace</Label>
                      <p className="font-semibold">{biaForm.minimum_workspace || "Not specified"}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Analyst & Review Date */}
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Metadata</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Analyst Name</Label>
                      <Input
                        value={biaForm.analyst}
                        onChange={(e) => setBiaForm({ ...biaForm, analyst: e.target.value })}
                        placeholder="Name of person conducting BIA"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Next Review Date</Label>
                      <Input
                        type="date"
                        value={biaForm.next_review_date}
                        onChange={(e) =>
                          setBiaForm({ ...biaForm, next_review_date: e.target.value })
                        }
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Complete Button */}
              <div className="flex justify-end">
                <Button onClick={() => setIsCompleteDialogOpen(true)}>
                  <Check className="h-4 w-4 mr-2" />
                  Complete BIA
                </Button>
              </div>
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

      {/* Complete BIA Dialog */}
      <Dialog open={isCompleteDialogOpen} onOpenChange={setIsCompleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Business Impact Analysis</DialogTitle>
            <DialogDescription>
              Are you sure you want to complete this BIA? The analysis will be marked as completed
              and can be used for continuity planning.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCompleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleComplete}>
              Complete BIA
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

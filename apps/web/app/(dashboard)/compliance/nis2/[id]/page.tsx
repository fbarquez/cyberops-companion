"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Building2,
  Shield,
  ClipboardList,
  AlertTriangle,
  FileText,
  Zap,
  Truck,
  Landmark,
  HeartPulse,
  Droplet,
  Server,
  Settings,
  Rocket,
  Mail,
  Trash2,
  FlaskConical,
  Utensils,
  Factory,
  Globe,
  Microscope,
  CheckCircle,
  XCircle,
  MinusCircle,
  HelpCircle,
  Download,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Checkbox } from "@/components/ui/checkbox";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

// Icon mapping for sectors
const SECTOR_ICONS: Record<string, any> = {
  energy: Zap,
  transport: Truck,
  banking: Landmark,
  financial_infrastructure: Landmark,
  health: HeartPulse,
  drinking_water: Droplet,
  waste_water: Droplet,
  digital_infrastructure: Server,
  ict_service_management: Settings,
  public_administration: Building2,
  space: Rocket,
  postal_courier: Mail,
  waste_management: Trash2,
  chemicals: FlaskConical,
  food: Utensils,
  manufacturing: Factory,
  digital_providers: Globe,
  research: Microscope,
};

// API functions
const nis2API = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`/api/v1/nis2/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getSectors: async (token: string) => {
    const res = await fetch("/api/v1/nis2/sectors", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch sectors");
    return res.json();
  },
  getMeasures: async (token: string) => {
    const res = await fetch("/api/v1/nis2/measures", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch measures");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`/api/v1/nis2/assessments/${id}/scope`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update scope");
    return res.json();
  },
  updateMeasure: async (token: string, assessmentId: string, measureId: string, data: any) => {
    const res = await fetch(`/api/v1/nis2/assessments/${assessmentId}/measures/${measureId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update measure");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`/api/v1/nis2/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  getReport: async (token: string, id: string) => {
    const res = await fetch(`/api/v1/nis2/assessments/${id}/report`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch report");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`/api/v1/nis2/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

const STEPS = [
  { id: 1, name: "Scope", icon: Building2, description: "Organization profile" },
  { id: 2, name: "Classification", icon: Shield, description: "Entity type" },
  { id: 3, name: "Measures", icon: ClipboardList, description: "Security assessment" },
  { id: 4, name: "Gaps", icon: AlertTriangle, description: "Gap analysis" },
  { id: 5, name: "Report", icon: FileText, description: "Final report" },
];

export default function NIS2WizardPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [currentStep, setCurrentStep] = useState(1);
  const [scopeData, setScopeData] = useState({
    sector: "",
    subsector: "",
    company_size: "",
    employee_count: 0,
    annual_turnover_eur: 0,
    operates_in_eu: true,
  });

  // Fetch assessment data
  const { data: assessmentData, isLoading: assessmentLoading, refetch: refetchAssessment } = useQuery({
    queryKey: ["nis2-assessment", assessmentId],
    queryFn: () => nis2API.getAssessment(token!, assessmentId),
    enabled: !!token && !!assessmentId,
  });

  // Fetch sectors
  const { data: sectorsData } = useQuery({
    queryKey: ["nis2-sectors"],
    queryFn: () => nis2API.getSectors(token!),
    enabled: !!token,
  });

  // Fetch measures
  const { data: measuresData } = useQuery({
    queryKey: ["nis2-measures"],
    queryFn: () => nis2API.getMeasures(token!),
    enabled: !!token,
  });

  // Fetch gap analysis
  const { data: gapsData, refetch: refetchGaps } = useQuery({
    queryKey: ["nis2-gaps", assessmentId],
    queryFn: () => nis2API.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessmentId && currentStep >= 4,
  });

  // Fetch report
  const { data: reportData, refetch: refetchReport } = useQuery({
    queryKey: ["nis2-report", assessmentId],
    queryFn: () => nis2API.getReport(token!, assessmentId),
    enabled: !!token && !!assessmentId && currentStep === 5,
  });

  // Update scope mutation
  const scopeMutation = useMutation({
    mutationFn: (data: any) => nis2API.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nis2-assessment", assessmentId] });
      refetchAssessment();
      setCurrentStep(2);
      toast.success("Scope updated");
    },
    onError: () => {
      toast.error("Failed to update scope");
    },
  });

  // Update measure mutation
  const measureMutation = useMutation({
    mutationFn: ({ measureId, data }: { measureId: string; data: any }) =>
      nis2API.updateMeasure(token!, assessmentId, measureId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nis2-assessment", assessmentId] });
      refetchAssessment();
    },
  });

  // Complete assessment mutation
  const completeMutation = useMutation({
    mutationFn: () => nis2API.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nis2-assessment", assessmentId] });
      toast.success("Assessment completed!");
    },
  });

  // Initialize scope data from assessment
  useEffect(() => {
    if (assessmentData?.assessment) {
      const a = assessmentData.assessment;
      setScopeData({
        sector: a.sector || "",
        subsector: a.subsector || "",
        company_size: a.company_size || "",
        employee_count: a.employee_count || 0,
        annual_turnover_eur: a.annual_turnover_eur || 0,
        operates_in_eu: a.operates_in_eu ?? true,
      });

      // Set current step based on assessment state
      if (a.entity_type && a.sector) {
        const evaluatedCount = assessmentData.measure_responses?.filter(
          (r: any) => r.status !== "not_evaluated"
        ).length || 0;

        if (a.status === "completed") {
          setCurrentStep(5);
        } else if (evaluatedCount === 10) {
          setCurrentStep(4);
        } else if (evaluatedCount > 0) {
          setCurrentStep(3);
        } else {
          setCurrentStep(2);
        }
      }
    }
  }, [assessmentData]);

  if (assessmentLoading) return <PageLoading />;

  const assessment = assessmentData?.assessment;
  const measureResponses = assessmentData?.measure_responses || [];
  const classification = assessmentData?.classification;
  const allSectors = [
    ...(sectorsData?.essential_sectors || []),
    ...(sectorsData?.important_sectors || []),
  ];
  const measures = measuresData?.measures || [];

  const handleScopeSubmit = () => {
    if (!scopeData.sector || !scopeData.company_size) {
      toast.error("Please select sector and company size");
      return;
    }
    scopeMutation.mutate(scopeData);
  };

  const handleMeasureUpdate = (measureId: string, status: string, implementationLevel: number) => {
    measureMutation.mutate({
      measureId,
      data: {
        measure_id: measureId,
        status,
        implementation_level: implementationLevel,
      },
    });
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return scopeData.sector && scopeData.company_size;
      case 2:
        return assessment?.entity_type;
      case 3:
        return measureResponses.some((r: any) => r.status !== "not_evaluated");
      case 4:
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={`${assessment?.name || "NIS2 Assessment"} - Step ${currentStep}/${STEPS.length}`}
        backHref="/compliance/nis2"
      />

      {/* Progress Steps */}
      <div className="border-b bg-muted/30 px-4 py-3">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          {STEPS.map((step, index) => {
            const StepIcon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;

            return (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => isCompleted && setCurrentStep(step.id)}
                  disabled={!isCompleted && !isActive}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg transition-colors",
                    isActive && "bg-primary text-primary-foreground",
                    isCompleted && "text-primary cursor-pointer hover:bg-primary/10",
                    !isActive && !isCompleted && "text-muted-foreground"
                  )}
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center",
                      isActive && "bg-primary-foreground/20",
                      isCompleted && "bg-primary/20"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <StepIcon className="h-4 w-4" />
                    )}
                  </div>
                  <div className="hidden md:block text-left">
                    <div className="text-sm font-medium">{step.name}</div>
                    <div className="text-xs opacity-70">{step.description}</div>
                  </div>
                </button>
                {index < STEPS.length - 1 && (
                  <div
                    className={cn(
                      "w-8 h-0.5 mx-2",
                      isCompleted ? "bg-primary" : "bg-muted"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          {currentStep === 1 && (
            <ScopeStep
              scopeData={scopeData}
              setScopeData={setScopeData}
              sectors={allSectors}
              onSubmit={handleScopeSubmit}
              isLoading={scopeMutation.isPending}
            />
          )}

          {currentStep === 2 && (
            <ClassificationStep
              assessment={assessment}
              classification={classification}
              onNext={() => setCurrentStep(3)}
              onBack={() => setCurrentStep(1)}
            />
          )}

          {currentStep === 3 && (
            <MeasuresStep
              measures={measures}
              responses={measureResponses}
              onUpdate={handleMeasureUpdate}
              onNext={() => {
                refetchGaps();
                setCurrentStep(4);
              }}
              onBack={() => setCurrentStep(2)}
              isUpdating={measureMutation.isPending}
            />
          )}

          {currentStep === 4 && (
            <GapsStep
              gapsData={gapsData}
              onNext={() => {
                refetchReport();
                setCurrentStep(5);
              }}
              onBack={() => setCurrentStep(3)}
            />
          )}

          {currentStep === 5 && (
            <ReportStep
              reportData={reportData}
              assessment={assessment}
              assessmentId={assessmentId}
              token={token}
              onComplete={() => completeMutation.mutate()}
              onBack={() => setCurrentStep(4)}
              isCompleting={completeMutation.isPending}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Step 1: Scope
function ScopeStep({
  scopeData,
  setScopeData,
  sectors,
  onSubmit,
  isLoading,
}: {
  scopeData: any;
  setScopeData: (data: any) => void;
  sectors: any[];
  onSubmit: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Organization Profile</h2>
        <p className="text-muted-foreground mt-1">
          Tell us about your organization to determine NIS2 applicability.
        </p>
      </div>

      {/* Sector Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. In which sector does your organization operate?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {sectors.map((sector: any) => {
              const Icon = SECTOR_ICONS[sector.sector] || Building2;
              const isSelected = scopeData.sector === sector.sector;

              return (
                <button
                  key={sector.sector}
                  onClick={() => setScopeData({ ...scopeData, sector: sector.sector })}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all",
                    isSelected
                      ? "border-primary bg-primary/5"
                      : "border-muted hover:border-primary/50"
                  )}
                >
                  <Icon className={cn("h-6 w-6", isSelected ? "text-primary" : "text-muted-foreground")} />
                  <span className="text-sm text-center font-medium">{sector.name_en}</span>
                  {sector.is_essential && (
                    <Badge variant="outline" className="text-xs">Essential</Badge>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Company Size */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. What is the size of your organization?</CardTitle>
          <CardDescription>
            Based on employee count and annual turnover (NIS2 thresholds)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={scopeData.company_size}
            onValueChange={(value) => setScopeData({ ...scopeData, company_size: value })}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {[
              { value: "micro", label: "Micro", desc: "<10 employees, <2M EUR" },
              { value: "small", label: "Small", desc: "<50 employees, <10M EUR" },
              { value: "medium", label: "Medium", desc: "50-249 employees, 10-50M EUR" },
              { value: "large", label: "Large", desc: "250+ employees, >50M EUR" },
            ].map((size) => (
              <div key={size.value} className="flex items-center space-x-3">
                <RadioGroupItem value={size.value} id={size.value} />
                <Label htmlFor={size.value} className="flex-1 cursor-pointer">
                  <span className="font-medium">{size.label}</span>
                  <span className="text-sm text-muted-foreground block">{size.desc}</span>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </CardContent>
      </Card>

      {/* EU Operations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">3. Does your organization operate in the EU?</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={scopeData.operates_in_eu ? "yes" : "no"}
            onValueChange={(value) => setScopeData({ ...scopeData, operates_in_eu: value === "yes" })}
            className="flex gap-6"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="yes" id="eu-yes" />
              <Label htmlFor="eu-yes">Yes</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="no" id="eu-no" />
              <Label htmlFor="eu-no">No</Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={onSubmit} disabled={isLoading || !scopeData.sector || !scopeData.company_size}>
          {isLoading ? "Saving..." : "Continue to Classification"}
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Step 2: Classification
function ClassificationStep({
  assessment,
  classification,
  onNext,
  onBack,
}: {
  assessment: any;
  classification: any;
  onNext: () => void;
  onBack: () => void;
}) {
  const isOutOfScope = assessment?.entity_type === "out_of_scope";
  const isEssential = assessment?.entity_type === "essential";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Classification Result</h2>
        <p className="text-muted-foreground mt-1">
          Based on your organization profile, here is your NIS2 classification.
        </p>
      </div>

      <Card className={cn(
        "border-2",
        isOutOfScope ? "border-gray-300" : isEssential ? "border-red-300 bg-red-50" : "border-yellow-300 bg-yellow-50"
      )}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className={cn(
              "p-3 rounded-full",
              isOutOfScope ? "bg-gray-200" : isEssential ? "bg-red-200" : "bg-yellow-200"
            )}>
              <Shield className={cn(
                "h-8 w-8",
                isOutOfScope ? "text-gray-600" : isEssential ? "text-red-600" : "text-yellow-600"
              )} />
            </div>
            <div>
              <h3 className="text-xl font-bold">
                {isOutOfScope ? "Out of Scope" : isEssential ? "Essential Entity" : "Important Entity"}
              </h3>
              <p className="text-muted-foreground mt-1">
                {assessment?.classification_reason}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {!isOutOfScope && classification && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Supervision Level</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{classification.supervision_level}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Incident Reporting Obligations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">Initial Notification</div>
                  <div className="font-semibold">{classification.reporting_obligations.initial_notification}</div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">Detailed Report</div>
                  <div className="font-semibold">{classification.reporting_obligations.incident_notification}</div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">Final Report</div>
                  <div className="font-semibold">{classification.reporting_obligations.final_report}</div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">Report To</div>
                  <div className="font-semibold text-sm">{classification.reporting_obligations.authority}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {!isOutOfScope && (
          <Button onClick={onNext}>
            Assess Security Measures
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}

// Step 3: Measures
function MeasuresStep({
  measures,
  responses,
  onUpdate,
  onNext,
  onBack,
  isUpdating,
}: {
  measures: any[];
  responses: any[];
  onUpdate: (measureId: string, status: string, level: number) => void;
  onNext: () => void;
  onBack: () => void;
  isUpdating: boolean;
}) {
  const responseMap = Object.fromEntries(responses.map((r: any) => [r.measure_id, r]));
  const evaluatedCount = responses.filter((r: any) => r.status !== "not_evaluated").length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Security Measures Assessment</h2>
        <p className="text-muted-foreground mt-1">
          Evaluate your organization against the 10 NIS2 security measures (Article 21).
        </p>
        <div className="mt-2">
          <Progress value={(evaluatedCount / 10) * 100} className="h-2" />
          <p className="text-sm text-muted-foreground mt-1">{evaluatedCount} of 10 measures evaluated</p>
        </div>
      </div>

      <Accordion type="single" collapsible className="space-y-3">
        {measures.map((measure: any) => {
          const response = responseMap[measure.id] || { status: "not_evaluated", implementation_level: 0 };

          return (
            <AccordionItem key={measure.id} value={measure.id} className="border rounded-lg px-4">
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-3 text-left">
                  <StatusIcon status={response.status} />
                  <div>
                    <div className="font-medium">{measure.id}</div>
                    <div className="text-sm text-muted-foreground">{measure.name_en}</div>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-4 space-y-4">
                <p className="text-sm text-muted-foreground">{measure.description_en}</p>

                <div>
                  <Label className="text-sm font-medium">Implementation Status</Label>
                  <RadioGroup
                    value={response.status}
                    onValueChange={(value) => onUpdate(measure.id, value, response.implementation_level)}
                    className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2"
                  >
                    {[
                      { value: "not_implemented", label: "Not Implemented" },
                      { value: "partially_implemented", label: "Partial" },
                      { value: "fully_implemented", label: "Fully Implemented" },
                      { value: "not_applicable", label: "N/A" },
                    ].map((opt) => (
                      <div key={opt.value} className="flex items-center space-x-2">
                        <RadioGroupItem value={opt.value} id={`${measure.id}-${opt.value}`} />
                        <Label htmlFor={`${measure.id}-${opt.value}`} className="text-sm cursor-pointer">
                          {opt.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {response.status === "partially_implemented" && (
                  <div>
                    <Label className="text-sm font-medium">
                      Implementation Level: {response.implementation_level}%
                    </Label>
                    <Slider
                      value={[response.implementation_level]}
                      onValueChange={([value]) => onUpdate(measure.id, response.status, value)}
                      max={100}
                      step={10}
                      className="mt-2"
                    />
                  </div>
                )}

                <div className="bg-muted p-3 rounded-lg">
                  <Label className="text-sm font-medium">Sub-requirements:</Label>
                  <ul className="mt-2 space-y-1">
                    {measure.sub_requirements.map((req: string, idx: number) => (
                      <li key={idx} className="text-sm text-muted-foreground flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext} disabled={evaluatedCount === 0}>
          View Gap Analysis
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Step 4: Gaps
function GapsStep({
  gapsData,
  onNext,
  onBack,
}: {
  gapsData: any;
  onNext: () => void;
  onBack: () => void;
}) {
  if (!gapsData) return <PageLoading />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Gap Analysis</h2>
        <p className="text-muted-foreground mt-1">
          Review identified gaps and recommendations for improvement.
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-3xl font-bold">{gapsData.total_gaps}</div>
            <div className="text-sm text-muted-foreground">Total Gaps</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-3xl font-bold text-red-500">{gapsData.critical_gaps}</div>
            <div className="text-sm text-muted-foreground">Critical</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-3xl font-bold text-yellow-500">{gapsData.high_priority_gaps}</div>
            <div className="text-sm text-muted-foreground">High Priority</div>
          </CardContent>
        </Card>
      </div>

      {/* Gaps List */}
      {gapsData.gaps.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Identified Gaps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {gapsData.gaps.map((gap: any, idx: number) => (
                <div key={idx} className="flex items-start gap-3 p-3 border rounded-lg">
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold",
                    gap.priority === 1 ? "bg-red-500" : gap.priority === 2 ? "bg-yellow-500" : "bg-blue-500"
                  )}>
                    {gap.priority}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{gap.measure_name}</div>
                    <div className="text-sm text-muted-foreground">
                      Status: {gap.status.replace("_", " ")} | Impact: {gap.impact_score}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
            <h3 className="text-lg font-semibold text-green-700">No Gaps Identified</h3>
            <p className="text-green-600">Your organization appears to be fully compliant!</p>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {gapsData.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {gapsData.recommendations.map((rec: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <ArrowRight className="h-4 w-4 mt-1 text-primary" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext}>
          View Report
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Step 5: Report
function ReportStep({
  reportData,
  assessment,
  assessmentId,
  token,
  onComplete,
  onBack,
  isCompleting,
}: {
  reportData: any;
  assessment: any;
  assessmentId: string;
  token: string | null;
  onComplete: () => void;
  onBack: () => void;
  isCompleting: boolean;
}) {
  const [isExportingPdf, setIsExportingPdf] = React.useState(false);
  const [isExportingJson, setIsExportingJson] = React.useState(false);

  const exportPdfReport = async () => {
    if (!token) {
      toast.error("Authentication required");
      return;
    }
    setIsExportingPdf(true);
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${API_BASE_URL}/api/v1/nis2/assessments/${assessmentId}/report?format=pdf`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Export failed" }));
        throw new Error(error.detail || "Failed to generate PDF");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `NIS2_Assessment_${assessment?.name?.replace(/\s+/g, "_") || assessmentId}_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("PDF report exported successfully");
    } catch (error) {
      console.error("PDF export failed:", error);
      toast.error(error instanceof Error ? error.message : "Failed to export PDF report");
    } finally {
      setIsExportingPdf(false);
    }
  };

  const exportJsonReport = async () => {
    if (!token) {
      toast.error("Authentication required");
      return;
    }
    setIsExportingJson(true);
    try {
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `NIS2_Assessment_${assessment?.name?.replace(/\s+/g, "_") || assessmentId}_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("JSON report exported successfully");
    } catch (error) {
      console.error("JSON export failed:", error);
      toast.error("Failed to export JSON report");
    } finally {
      setIsExportingJson(false);
    }
  };

  if (!reportData) return <PageLoading />;

  const complianceColor =
    reportData.compliance_level === "Compliant"
      ? "text-green-600"
      : reportData.compliance_level === "Partially Compliant"
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Assessment Report</h2>
        <p className="text-muted-foreground mt-1">
          Summary of your NIS2 compliance assessment.
        </p>
      </div>

      {/* Score Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Overall Compliance Score</h3>
              <div className={cn("text-4xl font-bold mt-2", complianceColor)}>
                {reportData.overall_score.toFixed(0)}%
              </div>
              <Badge className={cn("mt-2", complianceColor.replace("text-", "bg-").replace("600", "100"))}>
                {reportData.compliance_level}
              </Badge>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Entity Type</div>
              <div className="font-semibold">
                {reportData.entity_classification?.entity_type?.replace("_", " ").toUpperCase()}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground whitespace-pre-line">{reportData.executive_summary}</p>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Recommended Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2">
            {reportData.next_steps.map((step: string, idx: number) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </CardContent>
      </Card>

      {/* Export Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Export Report</CardTitle>
          <CardDescription>
            Download the compliance report in your preferred format.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={exportPdfReport}
              disabled={isExportingPdf}
              className="flex-1"
            >
              {isExportingPdf ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {isExportingPdf ? "Exporting..." : "Export PDF"}
            </Button>
            <Button
              variant="outline"
              onClick={exportJsonReport}
              disabled={isExportingJson}
              className="flex-1"
            >
              {isExportingJson ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileText className="h-4 w-4 mr-2" />
              )}
              {isExportingJson ? "Exporting..." : "Export JSON"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {assessment?.status !== "completed" && (
          <Button onClick={onComplete} disabled={isCompleting}>
            {isCompleting ? "Completing..." : "Complete Assessment"}
            <Check className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "fully_implemented":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "partially_implemented":
      return <MinusCircle className="h-5 w-5 text-yellow-500" />;
    case "not_implemented":
      return <XCircle className="h-5 w-5 text-red-500" />;
    case "not_applicable":
      return <HelpCircle className="h-5 w-5 text-gray-400" />;
    default:
      return <HelpCircle className="h-5 w-5 text-gray-400" />;
  }
}

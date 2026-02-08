"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Building2,
  Shield,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Landmark,
  TestTube,
  Users,
  Share2,
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
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
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
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// DORA API functions
const doraAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getEntityTypes: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/entity-types`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch entity types");
    return res.json();
  },
  getRequirements: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/requirements`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch requirements");
    return res.json();
  },
  getPillars: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/pillars`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch pillars");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${id}/scope`, {
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
  updateRequirement: async (token: string, assessmentId: string, reqId: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${assessmentId}/requirements/${reqId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update requirement");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  getReport: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${id}/report`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch report");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/dora/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

const PILLAR_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; stepNum: number }> = {
  ict_risk_management: { label: "ICT Risk Management", icon: ShieldCheck, color: "text-blue-600", stepNum: 2 },
  incident_reporting: { label: "Incident Reporting", icon: AlertTriangle, color: "text-orange-600", stepNum: 3 },
  resilience_testing: { label: "Resilience Testing", icon: TestTube, color: "text-purple-600", stepNum: 4 },
  third_party_risk: { label: "Third-Party Risk", icon: Users, color: "text-green-600", stepNum: 5 },
  information_sharing: { label: "Information Sharing", icon: Share2, color: "text-cyan-600", stepNum: 6 },
};

const STEPS = [
  { id: 1, name: "Scope", icon: Building2, description: "Entity scope", pillar: null },
  { id: 2, name: "Pillar 1", icon: ShieldCheck, description: "ICT Risk Management", pillar: "ict_risk_management" },
  { id: 3, name: "Pillar 2", icon: AlertTriangle, description: "Incident Reporting", pillar: "incident_reporting" },
  { id: 4, name: "Pillar 3", icon: TestTube, description: "Resilience Testing", pillar: "resilience_testing" },
  { id: 5, name: "Pillar 4", icon: Users, description: "Third-Party Risk", pillar: "third_party_risk" },
  { id: 6, name: "Pillar 5", icon: Share2, description: "Information Sharing", pillar: "information_sharing" },
  { id: 7, name: "Gaps", icon: AlertTriangle, description: "Gap analysis", pillar: null },
  { id: 8, name: "Report", icon: FileText, description: "Final report", pillar: null },
];

const ENTITY_TYPE_LABELS: Record<string, string> = {
  credit_institution: "Credit Institution",
  investment_firm: "Investment Firm",
  payment_institution: "Payment Institution",
  e_money_institution: "E-Money Institution",
  insurance_undertaking: "Insurance Undertaking",
  reinsurance_undertaking: "Reinsurance Undertaking",
  insurance_intermediary: "Insurance Intermediary",
  ucits_manager: "UCITS Manager",
  aifm: "AIFM",
  ccp: "Central Counterparty (CCP)",
  csd: "Central Securities Depository (CSD)",
  trading_venue: "Trading Venue",
  trade_repository: "Trade Repository",
  casp: "Crypto-Asset Service Provider",
  crowdfunding: "Crowdfunding Provider",
  cra: "Credit Rating Agency",
  pension_fund: "Pension Fund (IORP)",
  drsp: "Data Reporting Service Provider",
  securitisation_repository: "Securitisation Repository",
  ict_provider: "Critical ICT Third-Party Provider",
};

export default function DORAWizardPage() {
  const params = useParams();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [currentStep, setCurrentStep] = useState(1);
  const [scopeData, setScopeData] = useState({
    entity_type: "",
    company_size: "",
    employee_count: 0,
    annual_balance_eur: 0,
    is_ctpp: false,
    operates_in_eu: true,
    supervised_by: "",
    group_level_assessment: false,
  });

  // Fetch assessment data
  const { data: assessmentData, isLoading: assessmentLoading, refetch: refetchAssessment } = useQuery({
    queryKey: ["dora-assessment", assessmentId],
    queryFn: () => doraAPI.getAssessment(token!, assessmentId),
    enabled: !!token && !!assessmentId,
  });

  // Fetch entity types
  const { data: entityTypesData } = useQuery({
    queryKey: ["dora-entity-types"],
    queryFn: () => doraAPI.getEntityTypes(token!),
    enabled: !!token,
  });

  // Fetch requirements
  const { data: requirementsData } = useQuery({
    queryKey: ["dora-requirements"],
    queryFn: () => doraAPI.getRequirements(token!),
    enabled: !!token,
  });

  // Fetch pillars
  const { data: pillarsData } = useQuery({
    queryKey: ["dora-pillars"],
    queryFn: () => doraAPI.getPillars(token!),
    enabled: !!token,
  });

  // Fetch gap analysis
  const { data: gapsData, refetch: refetchGaps } = useQuery({
    queryKey: ["dora-gaps", assessmentId],
    queryFn: () => doraAPI.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessmentId && currentStep >= 7,
  });

  // Fetch report
  const { data: reportData, refetch: refetchReport } = useQuery({
    queryKey: ["dora-report", assessmentId],
    queryFn: () => doraAPI.getReport(token!, assessmentId),
    enabled: !!token && !!assessmentId && currentStep === 8,
  });

  // Update scope mutation
  const scopeMutation = useMutation({
    mutationFn: (data: any) => doraAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dora-assessment", assessmentId] });
      refetchAssessment();
      setCurrentStep(2);
      toast.success("Scope updated");
    },
    onError: () => {
      toast.error("Failed to update scope");
    },
  });

  // Update requirement mutation
  const reqMutation = useMutation({
    mutationFn: ({ reqId, data }: { reqId: string; data: any }) =>
      doraAPI.updateRequirement(token!, assessmentId, reqId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dora-assessment", assessmentId] });
      refetchAssessment();
    },
  });

  // Complete assessment mutation
  const completeMutation = useMutation({
    mutationFn: () => doraAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dora-assessment", assessmentId] });
      queryClient.invalidateQueries({ queryKey: ["dora-dashboard"] });
      toast.success("Assessment completed!");
    },
  });

  // Initialize scope data from assessment
  useEffect(() => {
    if (assessmentData?.assessment) {
      const a = assessmentData.assessment;
      setScopeData({
        entity_type: a.entity_type || "",
        company_size: a.company_size || "",
        employee_count: a.employee_count || 0,
        annual_balance_eur: a.annual_balance_eur || 0,
        is_ctpp: a.is_ctpp ?? false,
        operates_in_eu: a.operates_in_eu ?? true,
        supervised_by: a.supervised_by || "",
        group_level_assessment: a.group_level_assessment ?? false,
      });

      // Determine current step based on assessment state
      if (a.entity_type) {
        if (a.status === "completed") {
          setCurrentStep(8);
        } else {
          // Find the first pillar with unevaluated requirements
          const responses = assessmentData.requirement_responses || [];
          const responsesByPillar: Record<string, any[]> = {};
          responses.forEach((r: any) => {
            const pillar = r.pillar;
            if (!responsesByPillar[pillar]) responsesByPillar[pillar] = [];
            responsesByPillar[pillar].push(r);
          });

          let nextStep = 2;
          for (const [pillar, pillarConfig] of Object.entries(PILLAR_CONFIG)) {
            const pillarResponses = responsesByPillar[pillar] || [];
            const allEvaluated = pillarResponses.every((r: any) => r.status !== "not_evaluated");
            if (!allEvaluated) {
              nextStep = pillarConfig.stepNum;
              break;
            } else if (pillarConfig.stepNum >= nextStep) {
              nextStep = pillarConfig.stepNum + 1;
            }
          }
          setCurrentStep(Math.min(nextStep, 8));
        }
      }
    }
  }, [assessmentData]);

  if (assessmentLoading) return <PageLoading />;

  const assessment = assessmentData?.assessment;
  const requirementResponses = assessmentData?.requirement_responses || [];
  const responsesByPillar = assessmentData?.responses_by_pillar || {};
  const entityTypes = entityTypesData?.entity_types || [];
  const requirements = requirementsData?.requirements || [];
  const requirementsByPillar = requirementsData?.by_pillar || {};
  const pillars = pillarsData?.pillars || [];

  const handleScopeSubmit = () => {
    if (!scopeData.entity_type || !scopeData.company_size) {
      toast.error("Please select entity type and company size");
      return;
    }
    scopeMutation.mutate(scopeData);
  };

  const handleRequirementUpdate = (reqId: string, status: string, implementationLevel: number) => {
    reqMutation.mutate({
      reqId,
      data: {
        requirement_id: reqId,
        status,
        implementation_level: implementationLevel,
      },
    });
  };

  const getStepPillar = (stepId: number) => {
    const step = STEPS.find((s) => s.id === stepId);
    return step?.pillar || null;
  };

  const getPillarRequirements = (pillar: string) => {
    return requirementsByPillar[pillar] || [];
  };

  const getPillarResponses = (pillar: string) => {
    return responsesByPillar[pillar] || [];
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={`${assessment?.name || "DORA Assessment"} - Step ${currentStep}/${STEPS.length}`}
        backHref="/compliance/regulatory/dora"
      />

      {/* Progress Steps */}
      <div className="border-b bg-muted/30 px-4 py-3 overflow-x-auto">
        <div className="flex items-center gap-1 min-w-max">
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
                    "flex items-center gap-1 px-2 py-1.5 rounded-lg transition-colors",
                    isActive && "bg-primary text-primary-foreground",
                    isCompleted && "text-primary cursor-pointer hover:bg-primary/10",
                    !isActive && !isCompleted && "text-muted-foreground"
                  )}
                >
                  <div
                    className={cn(
                      "w-6 h-6 rounded-full flex items-center justify-center",
                      isActive && "bg-primary-foreground/20",
                      isCompleted && "bg-primary/20"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <StepIcon className="h-3 w-3" />
                    )}
                  </div>
                  <div className="hidden lg:block text-left">
                    <div className="text-xs font-medium">{step.name}</div>
                  </div>
                </button>
                {index < STEPS.length - 1 && (
                  <div className={cn("w-4 h-0.5", isCompleted ? "bg-primary" : "bg-muted")} />
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
              entityTypes={entityTypes}
              onSubmit={handleScopeSubmit}
              isLoading={scopeMutation.isPending}
            />
          )}

          {currentStep >= 2 && currentStep <= 6 && (
            <PillarStep
              pillar={getStepPillar(currentStep)!}
              pillarConfig={PILLAR_CONFIG[getStepPillar(currentStep)!]}
              requirements={getPillarRequirements(getStepPillar(currentStep)!)}
              responses={getPillarResponses(getStepPillar(currentStep)!)}
              assessment={assessment}
              onUpdate={handleRequirementUpdate}
              onNext={() => {
                if (currentStep === 6) {
                  refetchGaps();
                }
                setCurrentStep(currentStep + 1);
              }}
              onBack={() => setCurrentStep(currentStep - 1)}
              isUpdating={reqMutation.isPending}
            />
          )}

          {currentStep === 7 && (
            <GapsStep
              gapsData={gapsData}
              pillars={pillars}
              onNext={() => {
                refetchReport();
                setCurrentStep(8);
              }}
              onBack={() => setCurrentStep(6)}
            />
          )}

          {currentStep === 8 && (
            <ReportStep
              reportData={reportData}
              assessment={assessment}
              assessmentId={assessmentId}
              token={token}
              onComplete={() => completeMutation.mutate()}
              onBack={() => setCurrentStep(7)}
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
  entityTypes,
  onSubmit,
  isLoading,
}: {
  scopeData: any;
  setScopeData: (data: any) => void;
  entityTypes: any[];
  onSubmit: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Entity Scope</h2>
        <p className="text-muted-foreground mt-1">
          Define your organization&apos;s profile under DORA (EU 2022/2554).
        </p>
      </div>

      {/* Entity Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. What type of financial entity is your organization?</CardTitle>
          <CardDescription>Select the primary entity type under DORA scope</CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={scopeData.entity_type}
            onValueChange={(value) => setScopeData({ ...scopeData, entity_type: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select entity type..." />
            </SelectTrigger>
            <SelectContent>
              {entityTypes.map((et: any) => (
                <SelectItem key={et.entity_type} value={et.entity_type}>
                  <div className="flex items-center gap-2">
                    <Landmark className="h-4 w-4" />
                    <span>{et.name_en}</span>
                    {et.requires_tlpt && (
                      <Badge variant="outline" className="text-xs ml-2">TLPT Required</Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Company Size */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. What is the size of your organization?</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={scopeData.company_size}
            onValueChange={(value) => setScopeData({ ...scopeData, company_size: value })}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {[
              { value: "micro", label: "Micro", desc: "<10 employees, <€2M balance sheet" },
              { value: "small", label: "Small", desc: "<50 employees, <€10M balance sheet" },
              { value: "medium", label: "Medium", desc: "50-249 employees, €10-43M balance sheet" },
              { value: "large", label: "Large", desc: "250+ employees, >€43M balance sheet" },
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

      {/* CTPP Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">3. Is your organization a Critical Third-Party Provider (CTPP)?</CardTitle>
          <CardDescription>
            CTPPs are subject to the EU oversight framework under DORA
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <Switch
              id="is-ctpp"
              checked={scopeData.is_ctpp}
              onCheckedChange={(checked) => setScopeData({ ...scopeData, is_ctpp: checked })}
            />
            <Label htmlFor="is-ctpp">
              Yes, designated as a Critical Third-Party Provider
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* EU Operations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">4. Does your organization operate in the EU?</CardTitle>
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
        <Button onClick={onSubmit} disabled={isLoading || !scopeData.entity_type || !scopeData.company_size}>
          {isLoading ? "Saving..." : "Continue to Pillar 1"}
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Steps 2-6: Pillar Assessment
function PillarStep({
  pillar,
  pillarConfig,
  requirements,
  responses,
  assessment,
  onUpdate,
  onNext,
  onBack,
  isUpdating,
}: {
  pillar: string;
  pillarConfig: { label: string; icon: React.ElementType; color: string };
  requirements: any[];
  responses: any[];
  assessment: any;
  onUpdate: (reqId: string, status: string, level: number) => void;
  onNext: () => void;
  onBack: () => void;
  isUpdating: boolean;
}) {
  const PillarIcon = pillarConfig.icon;
  const responseMap = Object.fromEntries(responses.map((r: any) => [r.requirement_id, r]));
  const evaluatedCount = responses.filter((r: any) => r.status !== "not_evaluated").length;
  const totalCount = requirements.length;

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4">
        <div className={cn("p-3 rounded-lg bg-muted", pillarConfig.color)}>
          <PillarIcon className="h-8 w-8" />
        </div>
        <div>
          <h2 className="text-2xl font-bold">{pillarConfig.label}</h2>
          <p className="text-muted-foreground mt-1">
            Evaluate requirements for this DORA pillar.
          </p>
          <div className="mt-2">
            <Progress value={totalCount > 0 ? (evaluatedCount / totalCount) * 100 : 0} className="h-2" />
            <p className="text-sm text-muted-foreground mt-1">
              {evaluatedCount} of {totalCount} requirements evaluated
            </p>
          </div>
        </div>
      </div>

      <Accordion type="single" collapsible className="space-y-3">
        {requirements.map((req: any) => {
          const response = responseMap[req.id] || { status: "not_evaluated", implementation_level: 0 };

          return (
            <AccordionItem key={req.id} value={req.id} className="border rounded-lg px-4">
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-3 text-left">
                  <StatusIcon status={response.status} />
                  <div>
                    <div className="font-medium">{req.id}</div>
                    <div className="text-sm text-muted-foreground">{req.name_en}</div>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-4 space-y-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="outline">Article {req.article}</Badge>
                  <Badge variant="outline">Weight: {req.weight}</Badge>
                </div>
                <p className="text-sm text-muted-foreground">{req.description_en}</p>

                <div>
                  <Label className="text-sm font-medium">Implementation Status</Label>
                  <RadioGroup
                    value={response.status}
                    onValueChange={(value) => onUpdate(req.id, value, response.implementation_level)}
                    className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2"
                  >
                    {[
                      { value: "not_implemented", label: "Not Implemented" },
                      { value: "partially_implemented", label: "Partial" },
                      { value: "fully_implemented", label: "Fully Implemented" },
                      { value: "not_applicable", label: "N/A" },
                    ].map((opt) => (
                      <div key={opt.value} className="flex items-center space-x-2">
                        <RadioGroupItem value={opt.value} id={`${req.id}-${opt.value}`} />
                        <Label htmlFor={`${req.id}-${opt.value}`} className="text-sm cursor-pointer">
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
                      onValueChange={([value]) => onUpdate(req.id, response.status, value)}
                      max={100}
                      step={10}
                      className="mt-2"
                    />
                  </div>
                )}

                <div className="bg-muted p-3 rounded-lg">
                  <Label className="text-sm font-medium">Sub-requirements:</Label>
                  <ul className="mt-2 space-y-1">
                    {req.sub_requirements.map((sub: string, idx: number) => (
                      <li key={idx} className="text-sm text-muted-foreground flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                        {sub}
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
        <Button onClick={onNext}>
          {pillar === "information_sharing" ? "View Gap Analysis" : "Continue to Next Pillar"}
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Step 7: Gaps
function GapsStep({
  gapsData,
  pillars,
  onNext,
  onBack,
}: {
  gapsData: any;
  pillars: any[];
  onNext: () => void;
  onBack: () => void;
}) {
  if (!gapsData) return <PageLoading />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Gap Analysis</h2>
        <p className="text-muted-foreground mt-1">
          Review identified gaps across all DORA pillars.
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

      {/* Gaps by Pillar */}
      {gapsData.pillar_summaries?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Gaps by Pillar</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {gapsData.pillar_summaries.map((ps: any) => {
                const config = PILLAR_CONFIG[ps.pillar] || { label: ps.pillar_name, color: "text-gray-600" };
                return (
                  <div key={ps.pillar} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={cn("font-medium", config.color)}>{ps.pillar_name}</span>
                        <Badge variant="outline">{ps.gaps_count} gaps</Badge>
                      </div>
                      <span className={cn("font-bold", getScoreColor(ps.score))}>
                        {ps.score.toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={ps.score} className="h-2" />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Gaps */}
      {gapsData.all_gaps?.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>All Identified Gaps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {gapsData.all_gaps.map((gap: any, idx: number) => {
                const pillarConfig = PILLAR_CONFIG[gap.pillar] || { label: gap.pillar, color: "text-gray-600" };
                return (
                  <div key={idx} className="flex items-start gap-3 p-3 border rounded-lg">
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold",
                      gap.priority === 1 ? "bg-red-500" : gap.priority === 2 ? "bg-yellow-500" : "bg-blue-500"
                    )}>
                      {gap.priority}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{gap.requirement_name}</span>
                        <Badge variant="outline" className={pillarConfig.color}>
                          {pillarConfig.label}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Article {gap.article} | Status: {gap.status.replace(/_/g, " ")} | Impact: {gap.impact_score}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
            <h3 className="text-lg font-semibold text-green-700">No Gaps Identified</h3>
            <p className="text-green-600">Your organization demonstrates strong DORA compliance!</p>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {gapsData.recommendations?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {gapsData.recommendations.map((rec: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <ArrowRight className="h-4 w-4 mt-1 text-primary flex-shrink-0" />
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

// Step 8: Report
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
    if (!token) return;
    setIsExportingPdf(true);
    try {
      const response = await fetch(
        `${API_URL}/api/v1/dora/assessments/${assessmentId}/report?format=pdf`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) throw new Error("Failed to generate PDF");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DORA_Assessment_${assessment?.name?.replace(/\s+/g, "_") || assessmentId}_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("PDF exported successfully");
    } catch (error) {
      toast.error("Failed to export PDF");
    } finally {
      setIsExportingPdf(false);
    }
  };

  const exportJsonReport = () => {
    if (!reportData) return;
    setIsExportingJson(true);
    try {
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DORA_Assessment_${assessment?.name?.replace(/\s+/g, "_") || assessmentId}_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("JSON exported successfully");
    } catch (error) {
      toast.error("Failed to export JSON");
    } finally {
      setIsExportingJson(false);
    }
  };

  if (!reportData) return <PageLoading />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">DORA Assessment Report</h2>
        <p className="text-muted-foreground mt-1">
          Summary of your Digital Operational Resilience assessment.
        </p>
      </div>

      {/* Score Card */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Overall Compliance Score</h3>
              <div className={cn("text-4xl font-bold mt-2", getScoreColor(reportData.overall_score))}>
                {reportData.overall_score.toFixed(0)}%
              </div>
              <Badge className={cn("mt-2", getScoreBadgeColor(reportData.compliance_level))}>
                {reportData.compliance_level}
              </Badge>
            </div>
            <div className="text-right space-y-2">
              <div>
                <div className="text-sm text-muted-foreground">Entity Type</div>
                <div className="font-semibold">
                  {ENTITY_TYPE_LABELS[reportData.entity_type] || reportData.entity_type_name}
                </div>
              </div>
              {reportData.is_ctpp && (
                <Badge className="bg-purple-100 text-purple-700">CTPP</Badge>
              )}
              {reportData.requires_tlpt && (
                <Badge variant="outline">TLPT Required</Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pillar Scores */}
      <Card>
        <CardHeader>
          <CardTitle>Scores by Pillar</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            {reportData.pillar_summaries?.map((ps: any) => {
              const config = PILLAR_CONFIG[ps.pillar];
              const Icon = config?.icon || Shield;
              return (
                <div key={ps.pillar} className="text-center p-4 rounded-lg border">
                  <Icon className={cn("h-6 w-6 mx-auto mb-2", config?.color || "text-gray-600")} />
                  <p className="text-xs font-medium mb-1 truncate">{ps.pillar_name}</p>
                  <p className={cn("text-xl font-bold", getScoreColor(ps.score))}>
                    {ps.score.toFixed(0)}%
                  </p>
                  <Badge className={cn("mt-1 text-xs", getScoreBadgeColor(ps.compliance_level))}>
                    {ps.compliance_level}
                  </Badge>
                </div>
              );
            })}
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

      {/* Regulatory Deadlines */}
      <Card>
        <CardHeader>
          <CardTitle>Key DORA Deadlines</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(reportData.regulatory_deadlines || {}).map(([key, value]) => (
              <div key={key} className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground capitalize">
                  {key.replace(/_/g, " ")}
                </div>
                <div className="font-semibold text-sm">{value as string}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Recommended Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2">
            {reportData.next_steps?.map((step: string, idx: number) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </CardContent>
      </Card>

      {/* Export Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Export Report</CardTitle>
          <CardDescription>Download the compliance report in your preferred format.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button variant="outline" onClick={exportPdfReport} disabled={isExportingPdf} className="flex-1">
              {isExportingPdf ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {isExportingPdf ? "Exporting..." : "Export PDF"}
            </Button>
            <Button variant="outline" onClick={exportJsonReport} disabled={isExportingJson} className="flex-1">
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

// Helper components
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

function getScoreColor(score: number): string {
  if (score >= 85) return "text-green-600";
  if (score >= 70) return "text-lime-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-600";
}

function getScoreBadgeColor(level: string): string {
  switch (level) {
    case "Fully Compliant":
      return "bg-green-100 text-green-800";
    case "Largely Compliant":
      return "bg-lime-100 text-lime-800";
    case "Partially Compliant":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-red-100 text-red-800";
  }
}

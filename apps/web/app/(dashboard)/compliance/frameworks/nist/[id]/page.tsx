"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
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
import {
  Server,
  ArrowLeft,
  ArrowRight,
  Save,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Shield,
  Eye,
  Target,
  RefreshCw,
  Layers,
  Loader2,
  FileCheck,
  Download,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const nistAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getFunctions: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/functions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch functions");
    return res.json();
  },
  getCategories: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/categories`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch categories");
    return res.json();
  },
  getSubcategories: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/subcategories`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch subcategories");
    return res.json();
  },
  getTiers: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/tiers`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch tiers");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/nist/assessments/${id}/scope`, {
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
  updateSubcategory: async (token: string, id: string, subId: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/nist/assessments/${id}/subcategories/${subId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update subcategory");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/nist/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

// Types
interface SubcategoryResponse {
  id: string;
  subcategory_id: string;
  function_id: string;
  category_id: string;
  status: string;
  implementation_level: number;
  current_state: string | null;
  target_state: string | null;
  evidence: string | null;
  notes: string | null;
  gap_description: string | null;
  remediation_plan: string | null;
  priority: number;
  due_date: string | null;
  responsible: string | null;
  assessed_at: string | null;
}

interface Assessment {
  id: string;
  name: string;
  description: string | null;
  status: string;
  organization_type: string | null;
  organization_size: string | null;
  employee_count: number | null;
  industry_sector: string | null;
  current_tier: string | null;
  target_tier: string | null;
  profile_type: string | null;
  overall_score: number;
  function_scores: Record<string, number>;
  gaps_count: number;
  critical_gaps_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  responses: SubcategoryResponse[];
}

interface NISTFunction {
  id: string;
  code: string;
  name_en: string;
  name_de: string;
  description_en: string;
  description_de: string;
  weight: number;
  category_count: number;
}

interface Category {
  id: string;
  function: string;
  code: string;
  name_en: string;
  name_de: string;
  subcategory_count: number;
}

interface Subcategory {
  id: string;
  category: string;
  function: string;
  name_en: string;
  name_de: string;
  description_en: string;
  weight: number;
  priority: number;
}

interface GapItem {
  subcategory_id: string;
  subcategory_name: string;
  function_id: string;
  function_name: string;
  category_id: string;
  category_name: string;
  status: string;
  implementation_level: number;
  current_state: string | null;
  target_state: string | null;
  priority: number;
  weight: number;
  impact_score: number;
  gap_description: string | null;
  remediation_plan: string | null;
  due_date: string | null;
}

interface GapAnalysis {
  assessment_id: string;
  total_gaps: number;
  critical_gaps: number;
  gaps_by_function: Record<string, number>;
  gaps_by_priority: Record<number, number>;
  overall_compliance: number;
  current_tier: string | null;
  target_tier: string | null;
  tier_gap: string | null;
  gaps: GapItem[];
  function_summaries: any[];
  recommendations: string[];
}

// Function metadata
const functionMeta: Record<string, { icon: any; color: string; colorBg: string }> = {
  govern: { icon: Building2, color: "text-purple-600", colorBg: "bg-purple-100 dark:bg-purple-900" },
  identify: { icon: Eye, color: "text-blue-600", colorBg: "bg-blue-100 dark:bg-blue-900" },
  protect: { icon: Shield, color: "text-green-600", colorBg: "bg-green-100 dark:bg-green-900" },
  detect: { icon: Target, color: "text-yellow-600", colorBg: "bg-yellow-100 dark:bg-yellow-900" },
  respond: { icon: RefreshCw, color: "text-orange-600", colorBg: "bg-orange-100 dark:bg-orange-900" },
  recover: { icon: Layers, color: "text-cyan-600", colorBg: "bg-cyan-100 dark:bg-cyan-900" },
};

// Organization types
const organizationTypes = [
  { value: "private_sector", label: "Privatwirtschaft" },
  { value: "public_sector", label: "Öffentlicher Sektor" },
  { value: "nonprofit", label: "Non-Profit" },
  { value: "critical_infrastructure", label: "Kritische Infrastruktur" },
  { value: "healthcare", label: "Gesundheitswesen" },
  { value: "financial_services", label: "Finanzdienstleistungen" },
  { value: "education", label: "Bildung" },
  { value: "government", label: "Behörde" },
];

// Organization sizes
const organizationSizes = [
  { value: "micro", label: "Mikro (<10 Mitarbeiter)" },
  { value: "small", label: "Klein (10-49 Mitarbeiter)" },
  { value: "medium", label: "Mittel (50-249 Mitarbeiter)" },
  { value: "large", label: "Groß (250+ Mitarbeiter)" },
];

// Implementation tiers
const implementationTiers = [
  { value: "tier_1", label: "Tier 1 - Partial", description: "Ad-hoc, reaktiv, begrenzte Risikowahrnehmung" },
  { value: "tier_2", label: "Tier 2 - Risk Informed", description: "Risikobewusst, genehmigt aber nicht organisationsweit" },
  { value: "tier_3", label: "Tier 3 - Repeatable", description: "Formelle Richtlinien, regelmäßige Aktualisierung" },
  { value: "tier_4", label: "Tier 4 - Adaptive", description: "Adaptive Reaktion, kontinuierliche Verbesserung" },
];

// Outcome status options
const outcomeStatuses = [
  { value: "not_evaluated", label: "Nicht bewertet", color: "bg-gray-400" },
  { value: "not_implemented", label: "Nicht implementiert", color: "bg-red-500" },
  { value: "partially_implemented", label: "Teilweise", color: "bg-yellow-500" },
  { value: "largely_implemented", label: "Größtenteils", color: "bg-lime-500" },
  { value: "fully_implemented", label: "Vollständig", color: "bg-green-500" },
  { value: "not_applicable", label: "N/A", color: "bg-blue-400" },
];

// Priority labels
const priorityLabels: Record<number, { label: string; color: string }> = {
  1: { label: "Kritisch", color: "text-red-600" },
  2: { label: "Hoch", color: "text-orange-600" },
  3: { label: "Mittel", color: "text-yellow-600" },
  4: { label: "Niedrig", color: "text-green-600" },
};

export default function NISTAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [activeStep, setActiveStep] = useState(0);
  const [activeCategory, setActiveCategory] = useState<string>("");
  const [scopeData, setScopeData] = useState({
    organization_type: "",
    organization_size: "",
    employee_count: "",
    industry_sector: "",
    current_tier: "",
    target_tier: "",
    profile_type: "organizational",
  });
  const [subcategoryResponses, setSubcategoryResponses] = useState<Record<string, any>>({});

  // Fetch assessment
  const { data: assessment, isLoading } = useQuery<Assessment>({
    queryKey: ["nist", "assessment", assessmentId],
    queryFn: () => nistAPI.getAssessment(token!, assessmentId),
    enabled: !!token,
  });

  // Fetch functions
  const { data: functionsData } = useQuery({
    queryKey: ["nist", "functions"],
    queryFn: () => nistAPI.getFunctions(token!),
    enabled: !!token,
  });

  // Fetch categories
  const { data: categoriesData } = useQuery({
    queryKey: ["nist", "categories"],
    queryFn: () => nistAPI.getCategories(token!),
    enabled: !!token,
  });

  // Fetch subcategories
  const { data: subcategoriesData } = useQuery({
    queryKey: ["nist", "subcategories"],
    queryFn: () => nistAPI.getSubcategories(token!),
    enabled: !!token,
  });

  // Fetch gap analysis
  const { data: gapAnalysis } = useQuery<GapAnalysis>({
    queryKey: ["nist", "gaps", assessmentId],
    queryFn: () => nistAPI.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessment && assessment.status !== "draft",
  });

  const functions: NISTFunction[] = functionsData?.functions || [];
  const categories: Category[] = categoriesData?.categories || [];
  const subcategories: Subcategory[] = subcategoriesData?.subcategories || [];

  // Initialize scope data from assessment
  useEffect(() => {
    if (assessment) {
      setScopeData({
        organization_type: assessment.organization_type || "",
        organization_size: assessment.organization_size || "",
        employee_count: assessment.employee_count?.toString() || "",
        industry_sector: assessment.industry_sector || "",
        current_tier: assessment.current_tier || "",
        target_tier: assessment.target_tier || "",
        profile_type: assessment.profile_type || "organizational",
      });

      // Initialize subcategory responses
      const responses: Record<string, any> = {};
      assessment.responses?.forEach((resp) => {
        responses[resp.subcategory_id] = {
          status: resp.status,
          implementation_level: resp.implementation_level,
          current_state: resp.current_state || "",
          target_state: resp.target_state || "",
          evidence: resp.evidence || "",
          notes: resp.notes || "",
          gap_description: resp.gap_description || "",
          remediation_plan: resp.remediation_plan || "",
          priority: resp.priority || 2,
        };
      });
      setSubcategoryResponses(responses);

      // Set active step based on assessment state
      if (!assessment.organization_type) {
        setActiveStep(0);
      } else {
        setActiveStep(1);
      }
    }
  }, [assessment]);

  // Set first category when functions data loads
  useEffect(() => {
    if (categories.length > 0 && !activeCategory) {
      const functionId = functions[activeStep - 1]?.id;
      if (functionId) {
        const firstCat = categories.find((c) => c.function === functionId);
        if (firstCat) setActiveCategory(firstCat.id);
      }
    }
  }, [categories, functions, activeStep, activeCategory]);

  // Update scope mutation
  const updateScopeMutation = useMutation({
    mutationFn: (data: any) => nistAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nist"] });
      toast.success("Profil gespeichert");
      setActiveStep(1);
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Update subcategory mutation
  const updateSubcategoryMutation = useMutation({
    mutationFn: ({ subId, data }: { subId: string; data: any }) =>
      nistAPI.updateSubcategory(token!, assessmentId, subId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nist"] });
      toast.success("Outcome gespeichert");
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Complete assessment mutation
  const completeMutation = useMutation({
    mutationFn: () => nistAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nist"] });
      toast.success("Assessment abgeschlossen");
    },
    onError: () => {
      toast.error("Fehler beim Abschließen");
    },
  });

  const handleSaveScope = () => {
    if (!scopeData.organization_type || !scopeData.organization_size) {
      toast.error("Bitte füllen Sie alle Pflichtfelder aus");
      return;
    }
    if (!scopeData.current_tier || !scopeData.target_tier) {
      toast.error("Bitte wählen Sie Current und Target Tier");
      return;
    }

    updateScopeMutation.mutate({
      organization_type: scopeData.organization_type,
      organization_size: scopeData.organization_size,
      employee_count: scopeData.employee_count ? parseInt(scopeData.employee_count) : null,
      industry_sector: scopeData.industry_sector || null,
      current_tier: scopeData.current_tier,
      target_tier: scopeData.target_tier,
      profile_type: scopeData.profile_type,
    });
  };

  const handleSaveSubcategory = (subcategoryId: string) => {
    const response = subcategoryResponses[subcategoryId];
    if (!response) return;

    updateSubcategoryMutation.mutate({
      subId: subcategoryId,
      data: {
        subcategory_id: subcategoryId,
        status: response.status,
        implementation_level: response.implementation_level,
        current_state: response.current_state || null,
        target_state: response.target_state || null,
        evidence: response.evidence || null,
        notes: response.notes || null,
        gap_description: response.gap_description || null,
        remediation_plan: response.remediation_plan || null,
        priority: response.priority || 2,
      },
    });
  };

  const updateSubcategoryResponse = (subcategoryId: string, field: string, value: any) => {
    setSubcategoryResponses((prev) => ({
      ...prev,
      [subcategoryId]: {
        ...prev[subcategoryId],
        [field]: value,
      },
    }));
  };

  const getCurrentFunction = () => {
    if (activeStep === 0 || activeStep > functions.length) return null;
    return functions[activeStep - 1];
  };

  const getFunctionCategories = (functionId: string) => {
    return categories.filter((c) => c.function === functionId);
  };

  const getCategorySubcategories = (categoryId: string) => {
    return subcategories.filter((s) => s.category === categoryId);
  };

  const getFunctionProgress = (functionId: string) => {
    const funcSubcats = subcategories.filter((s) => s.function === functionId);
    if (funcSubcats.length === 0) return 0;

    const assessed = funcSubcats.filter(
      (s) =>
        subcategoryResponses[s.id]?.status &&
        subcategoryResponses[s.id]?.status !== "not_evaluated"
    ).length;
    return (assessed / funcSubcats.length) * 100;
  };

  const getCategoryProgress = (categoryId: string) => {
    const catSubcats = getCategorySubcategories(categoryId);
    if (catSubcats.length === 0) return 0;

    const assessed = catSubcats.filter(
      (s) =>
        subcategoryResponses[s.id]?.status &&
        subcategoryResponses[s.id]?.status !== "not_evaluated"
    ).length;
    return (assessed / catSubcats.length) * 100;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getStatusColor = (status: string) => {
    return outcomeStatuses.find((s) => s.value === status)?.color || "bg-gray-400";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Server className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Assessment nicht gefunden</p>
        <Link href="/compliance/frameworks/nist">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück
          </Button>
        </Link>
      </div>
    );
  }

  // Build steps: Scope + 6 Functions + Gap Analysis
  const steps = [
    { id: 0, name: "Profil", icon: Target },
    ...functions.map((f, idx) => ({
      id: idx + 1,
      name: f.name_de || f.name_en,
      icon: functionMeta[f.id]?.icon || Shield,
      functionId: f.id,
    })),
    { id: functions.length + 1, name: "Gap-Analyse", icon: AlertTriangle },
  ];

  const currentFunction = getCurrentFunction();
  const isGapStep = activeStep === functions.length + 1;

  return (
    <div className="flex flex-col h-full">
      <Header title={assessment.name}>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Server className="h-3 w-3" />
            NIST CSF 2.0
          </Badge>
          {assessment.target_tier && (
            <Badge variant="secondary">
              Target: {implementationTiers.find((t) => t.value === assessment.target_tier)?.label.split(" - ")[0]}
            </Badge>
          )}
          <Link href="/compliance/frameworks/nist">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Zurück
            </Button>
          </Link>
        </div>
      </Header>

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Progress Steps - Horizontal scrollable */}
        <div className="border-b bg-muted/30 px-4 py-3 overflow-x-auto">
          <div className="flex items-center gap-2 min-w-max">
            {steps.map((step, idx) => {
              const StepIcon = step.icon;
              const isActive = activeStep === step.id;
              const isCompleted = activeStep > step.id;
              const progress = step.id > 0 && step.id <= functions.length
                ? getFunctionProgress(functions[step.id - 1]?.id)
                : 0;

              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => {
                      if (step.id === 0 || assessment.organization_type) {
                        setActiveStep(step.id);
                        if (step.id > 0 && step.id <= functions.length) {
                          const funcId = functions[step.id - 1]?.id;
                          const firstCat = categories.find((c) => c.function === funcId);
                          if (firstCat) setActiveCategory(firstCat.id);
                        }
                      }
                    }}
                    disabled={step.id > 0 && !assessment.organization_type}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors text-sm whitespace-nowrap",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : isCompleted
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : "bg-muted text-muted-foreground hover:bg-muted/80",
                      step.id > 0 && !assessment.organization_type && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <StepIcon className="h-4 w-4" />
                    )}
                    <span className="font-medium">{step.name}</span>
                    {step.id > 0 && step.id <= functions.length && (
                      <span className="text-xs opacity-70">
                        {Math.round(progress)}%
                      </span>
                    )}
                  </button>
                  {idx < steps.length - 1 && (
                    <ArrowRight className="h-4 w-4 mx-1 text-muted-foreground shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {/* Step 0: Scope/Profile */}
          {activeStep === 0 && (
            <div className="max-w-3xl mx-auto space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Organisational Profile</CardTitle>
                  <CardDescription>
                    Definieren Sie Ihr Organisationsprofil und Ziel-Tier nach NIST CSF 2.0
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Organization Type */}
                  <div className="space-y-2">
                    <Label>Organisationstyp *</Label>
                    <Select
                      value={scopeData.organization_type}
                      onValueChange={(v) => setScopeData({ ...scopeData, organization_type: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Typ auswählen" />
                      </SelectTrigger>
                      <SelectContent>
                        {organizationTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Organization Size */}
                  <div className="space-y-2">
                    <Label>Unternehmensgröße *</Label>
                    <Select
                      value={scopeData.organization_size}
                      onValueChange={(v) => setScopeData({ ...scopeData, organization_size: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Größe auswählen" />
                      </SelectTrigger>
                      <SelectContent>
                        {organizationSizes.map((size) => (
                          <SelectItem key={size.value} value={size.value}>
                            {size.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Industry Sector */}
                  <div className="space-y-2">
                    <Label>Branche</Label>
                    <Input
                      placeholder="z.B. Fertigung, IT-Dienstleistungen..."
                      value={scopeData.industry_sector}
                      onChange={(e) => setScopeData({ ...scopeData, industry_sector: e.target.value })}
                    />
                  </div>

                  {/* Current Tier */}
                  <div className="space-y-3">
                    <Label>Current Implementation Tier *</Label>
                    <p className="text-sm text-muted-foreground">
                      Ihr aktueller Reifegrad im Cybersecurity Risk Management
                    </p>
                    <div className="grid gap-2">
                      {implementationTiers.map((tier) => (
                        <button
                          key={tier.value}
                          onClick={() => setScopeData({ ...scopeData, current_tier: tier.value })}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-lg border transition-colors text-left",
                            scopeData.current_tier === tier.value
                              ? "border-primary bg-primary/5"
                              : "hover:bg-muted/50"
                          )}
                        >
                          <div>
                            <p className="font-medium">{tier.label}</p>
                            <p className="text-sm text-muted-foreground">{tier.description}</p>
                          </div>
                          {scopeData.current_tier === tier.value && (
                            <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Target Tier */}
                  <div className="space-y-3">
                    <Label>Target Implementation Tier *</Label>
                    <p className="text-sm text-muted-foreground">
                      Ihr angestrebter Ziel-Reifegrad
                    </p>
                    <div className="grid gap-2">
                      {implementationTiers.map((tier) => (
                        <button
                          key={tier.value}
                          onClick={() => setScopeData({ ...scopeData, target_tier: tier.value })}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-lg border transition-colors text-left",
                            scopeData.target_tier === tier.value
                              ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                              : "hover:bg-muted/50"
                          )}
                        >
                          <div>
                            <p className="font-medium">{tier.label}</p>
                            <p className="text-sm text-muted-foreground">{tier.description}</p>
                          </div>
                          {scopeData.target_tier === tier.value && (
                            <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-end">
                <Button onClick={handleSaveScope} disabled={updateScopeMutation.isPending}>
                  {updateScopeMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  Speichern & Weiter
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Function Assessment Steps */}
          {currentFunction && !isGapStep && (
            <div className="flex gap-6 h-full">
              {/* Category Navigation */}
              <Card className="w-72 shrink-0">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    {(() => {
                      const FuncIcon = functionMeta[currentFunction.id]?.icon || Shield;
                      return (
                        <div className={cn("p-2 rounded-lg", functionMeta[currentFunction.id]?.colorBg)}>
                          <FuncIcon className={cn("h-4 w-4", functionMeta[currentFunction.id]?.color)} />
                        </div>
                      );
                    })()}
                    <div>
                      <CardTitle className="text-base">{currentFunction.name_de || currentFunction.name_en}</CardTitle>
                      <p className="text-xs text-muted-foreground">{currentFunction.code}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[calc(100vh-22rem)]">
                    <div className="space-y-1 p-2">
                      {getFunctionCategories(currentFunction.id).map((category) => {
                        const progress = getCategoryProgress(category.id);

                        return (
                          <button
                            key={category.id}
                            onClick={() => setActiveCategory(category.id)}
                            className={cn(
                              "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors",
                              activeCategory === category.id
                                ? "bg-primary text-primary-foreground"
                                : "hover:bg-muted"
                            )}
                          >
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                {category.name_de || category.name_en}
                              </p>
                              <p className="text-xs opacity-70">{category.code}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Progress value={progress} className="h-1 flex-1" />
                                <span className="text-xs opacity-70">
                                  {Math.round(progress)}%
                                </span>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Subcategory Assessment */}
              <Card className="flex-1">
                <CardHeader>
                  <CardTitle>
                    {categories.find((c) => c.id === activeCategory)?.name_de ||
                      categories.find((c) => c.id === activeCategory)?.name_en}
                  </CardTitle>
                  <CardDescription>
                    Bewerten Sie den Implementierungsstatus jedes Outcomes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[calc(100vh-24rem)]">
                    <Accordion type="single" collapsible className="space-y-2">
                      {getCategorySubcategories(activeCategory).map((subcat) => {
                        const response = subcategoryResponses[subcat.id] || {};
                        const currentStatus = response.status || "not_evaluated";

                        return (
                          <AccordionItem
                            key={subcat.id}
                            value={subcat.id}
                            className="border rounded-lg px-4"
                          >
                            <AccordionTrigger className="hover:no-underline py-3">
                              <div className="flex items-center gap-3 flex-1 text-left">
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full shrink-0",
                                    getStatusColor(currentStatus)
                                  )}
                                />
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-sm">
                                    {subcat.name_de || subcat.name_en}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    Gewicht: {subcat.weight} | Priorität: {subcat.priority}
                                  </p>
                                </div>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="pt-2 pb-4">
                              <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                  {subcat.description_en}
                                </p>

                                {/* Status Selection */}
                                <div className="space-y-2">
                                  <Label>Implementierungsstatus</Label>
                                  <div className="grid grid-cols-3 gap-2">
                                    {outcomeStatuses.map((status) => (
                                      <button
                                        key={status.value}
                                        onClick={() =>
                                          updateSubcategoryResponse(
                                            subcat.id,
                                            "status",
                                            status.value
                                          )
                                        }
                                        className={cn(
                                          "p-2 rounded border text-center text-xs transition-colors",
                                          response.status === status.value
                                            ? `${status.color} text-white border-transparent`
                                            : "hover:bg-muted"
                                        )}
                                      >
                                        {status.label}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                {/* Implementation Level Slider */}
                                <div className="space-y-2">
                                  <div className="flex justify-between">
                                    <Label>Implementierungsgrad</Label>
                                    <span className="text-sm text-muted-foreground">
                                      {response.implementation_level || 0}%
                                    </span>
                                  </div>
                                  <Slider
                                    value={[response.implementation_level || 0]}
                                    max={100}
                                    step={5}
                                    onValueChange={([value]) =>
                                      updateSubcategoryResponse(subcat.id, "implementation_level", value)
                                    }
                                  />
                                </div>

                                {/* Evidence */}
                                <div className="space-y-2">
                                  <Label>Nachweise / Evidence</Label>
                                  <Textarea
                                    placeholder="Dokumentation, Prozesse, Policies..."
                                    value={response.evidence || ""}
                                    onChange={(e) =>
                                      updateSubcategoryResponse(subcat.id, "evidence", e.target.value)
                                    }
                                    rows={2}
                                  />
                                </div>

                                {/* Gap Description (if not fully implemented) */}
                                {currentStatus !== "fully_implemented" &&
                                  currentStatus !== "not_applicable" &&
                                  currentStatus !== "not_evaluated" && (
                                    <>
                                      <div className="space-y-2">
                                        <Label>Gap-Beschreibung</Label>
                                        <Textarea
                                          placeholder="Beschreiben Sie die identifizierte Lücke..."
                                          value={response.gap_description || ""}
                                          onChange={(e) =>
                                            updateSubcategoryResponse(
                                              subcat.id,
                                              "gap_description",
                                              e.target.value
                                            )
                                          }
                                          rows={2}
                                        />
                                      </div>
                                      <div className="space-y-2">
                                        <Label>Maßnahmenplan</Label>
                                        <Textarea
                                          placeholder="Geplante Maßnahmen zur Schließung der Lücke..."
                                          value={response.remediation_plan || ""}
                                          onChange={(e) =>
                                            updateSubcategoryResponse(
                                              subcat.id,
                                              "remediation_plan",
                                              e.target.value
                                            )
                                          }
                                          rows={2}
                                        />
                                      </div>
                                    </>
                                  )}

                                <div className="flex justify-end">
                                  <Button
                                    size="sm"
                                    onClick={() => handleSaveSubcategory(subcat.id)}
                                    disabled={updateSubcategoryMutation.isPending}
                                  >
                                    {updateSubcategoryMutation.isPending && (
                                      <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                                    )}
                                    <Save className="h-3 w-3 mr-2" />
                                    Speichern
                                  </Button>
                                </div>
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        );
                      })}
                    </Accordion>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Gap Analysis Step */}
          {isGapStep && (
            <div className="max-w-5xl mx-auto space-y-6">
              {/* Summary Cards */}
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Gesamtscore</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-2xl font-bold ${getScoreColor(assessment.overall_score)}`}>
                      {assessment.overall_score.toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Current Tier</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {assessment.current_tier?.replace("tier_", "Tier ") || "-"}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Target Tier</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      {assessment.target_tier?.replace("tier_", "Tier ") || "-"}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Kritische Gaps</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">
                      {gapAnalysis?.critical_gaps || 0}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Function Scores */}
              <Card>
                <CardHeader>
                  <CardTitle>Funktions-Scores</CardTitle>
                  <CardDescription>Reifegrad pro NIST CSF Core Function</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {functions.map((func) => {
                      const score = assessment.function_scores?.[func.id] || 0;
                      const FuncIcon = functionMeta[func.id]?.icon || Shield;
                      return (
                        <div key={func.id} className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <div className={cn("p-1.5 rounded", functionMeta[func.id]?.colorBg)}>
                                <FuncIcon className={cn("h-3 w-3", functionMeta[func.id]?.color)} />
                              </div>
                              <span className="font-medium">{func.name_de || func.name_en}</span>
                            </div>
                            <span className={getScoreColor(score)}>{score.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full transition-all",
                                score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500"
                              )}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              {gapAnalysis?.recommendations && gapAnalysis.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Empfehlungen</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {gapAnalysis.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                          <span className="text-sm">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Gap List */}
              {gapAnalysis?.gaps && gapAnalysis.gaps.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Identifizierte Gaps ({gapAnalysis.total_gaps})</CardTitle>
                    <CardDescription>
                      Outcomes mit Implementierungslücken
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {gapAnalysis.gaps.slice(0, 20).map((gap) => (
                        <div
                          key={gap.subcategory_id}
                          className="flex items-center justify-between p-3 rounded-lg border"
                        >
                          <div className="flex items-center gap-3">
                            <AlertTriangle
                              className={cn(
                                "h-4 w-4",
                                gap.priority === 1
                                  ? "text-red-500"
                                  : gap.priority === 2
                                  ? "text-orange-500"
                                  : "text-yellow-500"
                              )}
                            />
                            <div>
                              <p className="font-medium text-sm">{gap.subcategory_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {gap.function_name} &gt; {gap.category_name}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs",
                                  gap.status === "not_implemented"
                                    ? "border-red-500 text-red-600"
                                    : "border-yellow-500 text-yellow-600"
                                )}
                              >
                                {gap.implementation_level}%
                              </Badge>
                              <p
                                className={cn(
                                  "text-xs mt-1",
                                  priorityLabels[gap.priority]?.color
                                )}
                              >
                                {priorityLabels[gap.priority]?.label}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Actions */}
              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setActiveStep(functions.length)}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Zurück zu {functions[functions.length - 1]?.name_de || "Recover"}
                </Button>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      toast.info("Report-Export wird vorbereitet...");
                    }}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Report exportieren
                  </Button>
                  {assessment.status !== "completed" && (
                    <Button
                      onClick={() => completeMutation.mutate()}
                      disabled={completeMutation.isPending}
                    >
                      {completeMutation.isPending && (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      )}
                      <FileCheck className="h-4 w-4 mr-2" />
                      Assessment abschließen
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Shield,
  ArrowLeft,
  ArrowRight,
  Save,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Users,
  Lock,
  FileText,
  Globe,
  Scale,
  UserCheck,
  Loader2,
  FileCheck,
  Target,
  Download,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const gdprAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getChapters: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/chapters`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch chapters");
    return res.json();
  },
  getRequirements: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/requirements`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch requirements");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/assessments/${id}/scope`, {
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
  updateRequirement: async (token: string, id: string, reqId: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/assessments/${id}/requirements/${reqId}`, {
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
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/gdpr/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

// Types
interface RequirementResponse {
  id: string;
  requirement_id: string;
  chapter_id: string;
  compliance_level: string;
  evidence: string | null;
  notes: string | null;
  gap_description: string | null;
  remediation_plan: string | null;
  requirements_met: string[];
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
  processes_special_categories: boolean;
  processes_criminal_data: boolean;
  large_scale_processing: boolean;
  systematic_monitoring: boolean;
  cross_border_processing: boolean;
  requires_dpo: boolean;
  data_categories: string[];
  legal_bases: string[];
  eu_countries: string[];
  dpo_appointed: boolean;
  dpo_name: string | null;
  dpo_email: string | null;
  lead_authority: string | null;
  overall_score: number;
  chapter_scores: Record<string, number>;
  gaps_count: number;
  critical_gaps_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  responses: RequirementResponse[];
}

interface Chapter {
  id: string;
  number: string;
  name_en: string;
  name_de: string;
  articles: string;
  description_en: string;
  requirement_count: number;
}

interface Requirement {
  id: string;
  chapter: string;
  article: string;
  name_en: string;
  name_de: string;
  description_en: string;
  description_de: string;
  weight: number;
  priority: number;
  requirements: string[];
}

interface GapItem {
  requirement_id: string;
  requirement_name: string;
  chapter_id: string;
  chapter_name: string;
  article: string;
  compliance_level: string;
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
  gaps_by_chapter: Record<string, number>;
  gaps_by_priority: Record<number, number>;
  overall_compliance: number;
  gaps: GapItem[];
  chapter_summaries: any[];
  recommendations: string[];
}

// Icons for chapters
const chapterIcons: Record<string, any> = {
  chapter_1: FileText,
  chapter_2: Scale,
  chapter_3: Users,
  chapter_4: Building2,
  chapter_5: Globe,
};

// Organization types
const organizationTypes = [
  { value: "controller", label: "Verantwortlicher", description: "Bestimmt Zweck und Mittel der Verarbeitung" },
  { value: "processor", label: "Auftragsverarbeiter", description: "Verarbeitet im Auftrag des Verantwortlichen" },
  { value: "joint_controller", label: "Gemeinsam Verantwortliche", description: "Gemeinsame Zweck- und Mittelbestimmung" },
  { value: "controller_processor", label: "Verantwortlicher & Auftragsverarbeiter", description: "Beide Rollen" },
];

// Organization sizes
const organizationSizes = [
  { value: "micro", label: "Mikro (<10 Mitarbeiter)" },
  { value: "small", label: "Klein (10-49 Mitarbeiter)" },
  { value: "medium", label: "Mittel (50-249 Mitarbeiter)" },
  { value: "large", label: "Groß (250+ Mitarbeiter)" },
];

// Data categories
const dataCategories = [
  { value: "basic_identity", label: "Stammdaten (Name, Adresse, E-Mail)" },
  { value: "financial", label: "Finanzdaten (Bankdaten, Zahlungen)" },
  { value: "contact", label: "Kontaktdaten (Telefon, E-Mail, Adresse)" },
  { value: "behavioral", label: "Verhaltensdaten (Kaufhistorie, Browsing)" },
  { value: "technical", label: "Technische Daten (IP, Device-IDs, Cookies)" },
  { value: "location", label: "Standortdaten (GPS, Reisehistorie)" },
  { value: "special_category", label: "Besondere Kategorien (Art. 9)" },
  { value: "criminal", label: "Strafdaten (Art. 10)" },
];

// Legal bases
const legalBases = [
  { value: "consent", label: "Einwilligung (Art. 6(1)(a))" },
  { value: "contract", label: "Vertrag (Art. 6(1)(b))" },
  { value: "legal_obligation", label: "Rechtliche Verpflichtung (Art. 6(1)(c))" },
  { value: "vital_interests", label: "Lebenswichtige Interessen (Art. 6(1)(d))" },
  { value: "public_task", label: "Öffentliches Interesse (Art. 6(1)(e))" },
  { value: "legitimate_interests", label: "Berechtigte Interessen (Art. 6(1)(f))" },
];

// Compliance levels
const complianceLevels = [
  { value: "not_evaluated", label: "Nicht bewertet", color: "bg-gray-400" },
  { value: "non_compliant", label: "Nicht konform", color: "bg-red-500" },
  { value: "partially_compliant", label: "Teilweise konform", color: "bg-yellow-500" },
  { value: "fully_compliant", label: "Vollständig konform", color: "bg-green-500" },
  { value: "not_applicable", label: "Nicht anwendbar", color: "bg-blue-400" },
];

// Priority labels
const priorityLabels: Record<number, { label: string; color: string }> = {
  1: { label: "Kritisch", color: "text-red-600" },
  2: { label: "Hoch", color: "text-orange-600" },
  3: { label: "Mittel", color: "text-yellow-600" },
  4: { label: "Niedrig", color: "text-green-600" },
};

export default function GDPRAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [activeStep, setActiveStep] = useState(0);
  const [activeChapter, setActiveChapter] = useState("chapter_2");
  const [scopeData, setScopeData] = useState({
    organization_type: "",
    organization_size: "",
    employee_count: "",
    processes_special_categories: false,
    processes_criminal_data: false,
    large_scale_processing: false,
    systematic_monitoring: false,
    cross_border_processing: false,
    data_categories: [] as string[],
    legal_bases: [] as string[],
    eu_countries: [] as string[],
    dpo_appointed: false,
    dpo_name: "",
    dpo_email: "",
    lead_authority: "",
  });
  const [requirementResponses, setRequirementResponses] = useState<Record<string, any>>({});

  // Fetch assessment
  const { data: assessment, isLoading } = useQuery<Assessment>({
    queryKey: ["gdpr", "assessment", assessmentId],
    queryFn: () => gdprAPI.getAssessment(token!, assessmentId),
    enabled: !!token,
  });

  // Fetch chapters
  const { data: chaptersData } = useQuery({
    queryKey: ["gdpr", "chapters"],
    queryFn: () => gdprAPI.getChapters(token!),
    enabled: !!token,
  });

  // Fetch requirements
  const { data: requirementsData } = useQuery({
    queryKey: ["gdpr", "requirements"],
    queryFn: () => gdprAPI.getRequirements(token!),
    enabled: !!token,
  });

  // Fetch gap analysis
  const { data: gapAnalysis } = useQuery<GapAnalysis>({
    queryKey: ["gdpr", "gaps", assessmentId],
    queryFn: () => gdprAPI.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessment && assessment.status !== "draft",
  });

  // Initialize scope data from assessment
  useEffect(() => {
    if (assessment) {
      setScopeData({
        organization_type: assessment.organization_type || "",
        organization_size: assessment.organization_size || "",
        employee_count: assessment.employee_count?.toString() || "",
        processes_special_categories: assessment.processes_special_categories,
        processes_criminal_data: assessment.processes_criminal_data,
        large_scale_processing: assessment.large_scale_processing,
        systematic_monitoring: assessment.systematic_monitoring,
        cross_border_processing: assessment.cross_border_processing,
        data_categories: assessment.data_categories || [],
        legal_bases: assessment.legal_bases || [],
        eu_countries: assessment.eu_countries || [],
        dpo_appointed: assessment.dpo_appointed,
        dpo_name: assessment.dpo_name || "",
        dpo_email: assessment.dpo_email || "",
        lead_authority: assessment.lead_authority || "",
      });

      // Initialize requirement responses
      const responses: Record<string, any> = {};
      assessment.responses?.forEach((resp) => {
        responses[resp.requirement_id] = {
          compliance_level: resp.compliance_level,
          evidence: resp.evidence || "",
          notes: resp.notes || "",
          gap_description: resp.gap_description || "",
          remediation_plan: resp.remediation_plan || "",
          requirements_met: resp.requirements_met || [],
          priority: resp.priority || 2,
        };
      });
      setRequirementResponses(responses);

      // Set active step based on assessment state
      if (!assessment.organization_type) {
        setActiveStep(0);
      } else {
        setActiveStep(1);
      }
    }
  }, [assessment]);

  // Update scope mutation
  const updateScopeMutation = useMutation({
    mutationFn: (data: any) => gdprAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gdpr"] });
      toast.success("Geltungsbereich gespeichert");
      setActiveStep(1);
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Update requirement mutation
  const updateRequirementMutation = useMutation({
    mutationFn: ({ reqId, data }: { reqId: string; data: any }) =>
      gdprAPI.updateRequirement(token!, assessmentId, reqId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gdpr"] });
      toast.success("Anforderung gespeichert");
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Complete assessment mutation
  const completeMutation = useMutation({
    mutationFn: () => gdprAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gdpr"] });
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
    if (scopeData.data_categories.length === 0) {
      toast.error("Bitte wählen Sie mindestens eine Datenkategorie");
      return;
    }
    if (scopeData.legal_bases.length === 0) {
      toast.error("Bitte wählen Sie mindestens eine Rechtsgrundlage");
      return;
    }

    updateScopeMutation.mutate({
      organization_type: scopeData.organization_type,
      organization_size: scopeData.organization_size,
      employee_count: scopeData.employee_count ? parseInt(scopeData.employee_count) : null,
      processes_special_categories: scopeData.processes_special_categories,
      processes_criminal_data: scopeData.processes_criminal_data,
      large_scale_processing: scopeData.large_scale_processing,
      systematic_monitoring: scopeData.systematic_monitoring,
      cross_border_processing: scopeData.cross_border_processing,
      data_categories: scopeData.data_categories,
      legal_bases: scopeData.legal_bases,
      eu_countries: scopeData.eu_countries,
      dpo_appointed: scopeData.dpo_appointed,
      dpo_name: scopeData.dpo_name || null,
      dpo_email: scopeData.dpo_email || null,
      lead_authority: scopeData.lead_authority || null,
    });
  };

  const handleSaveRequirement = (requirementId: string) => {
    const response = requirementResponses[requirementId];
    if (!response) return;

    updateRequirementMutation.mutate({
      reqId: requirementId,
      data: {
        requirement_id: requirementId,
        compliance_level: response.compliance_level,
        evidence: response.evidence || null,
        notes: response.notes || null,
        gap_description: response.gap_description || null,
        remediation_plan: response.remediation_plan || null,
        requirements_met: response.requirements_met || [],
        priority: response.priority || 2,
      },
    });
  };

  const updateRequirementResponse = (requirementId: string, field: string, value: any) => {
    setRequirementResponses((prev) => ({
      ...prev,
      [requirementId]: {
        ...prev[requirementId],
        [field]: value,
      },
    }));
  };

  const toggleDataCategory = (value: string) => {
    setScopeData((prev) => ({
      ...prev,
      data_categories: prev.data_categories.includes(value)
        ? prev.data_categories.filter((c) => c !== value)
        : [...prev.data_categories, value],
    }));
  };

  const toggleLegalBasis = (value: string) => {
    setScopeData((prev) => ({
      ...prev,
      legal_bases: prev.legal_bases.includes(value)
        ? prev.legal_bases.filter((b) => b !== value)
        : [...prev.legal_bases, value],
    }));
  };

  const chapters = chaptersData?.chapters || [];
  const requirements = requirementsData?.requirements || [];

  const getChapterRequirements = (chapterId: string) => {
    return requirements.filter((r: Requirement) => r.chapter === chapterId);
  };

  const getChapterProgress = (chapterId: string) => {
    const chapterReqs = getChapterRequirements(chapterId);
    if (chapterReqs.length === 0) return 0;

    const assessed = chapterReqs.filter(
      (r: Requirement) =>
        requirementResponses[r.id]?.compliance_level &&
        requirementResponses[r.id]?.compliance_level !== "not_evaluated"
    ).length;
    return (assessed / chapterReqs.length) * 100;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getComplianceColor = (level: string) => {
    return complianceLevels.find((l) => l.value === level)?.color || "bg-gray-400";
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
        <Shield className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Assessment nicht gefunden</p>
        <Link href="/compliance/regulatory/gdpr">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück
          </Button>
        </Link>
      </div>
    );
  }

  const steps = [
    { id: 0, name: "Geltungsbereich", icon: Target },
    { id: 1, name: "Anforderungen", icon: Shield },
    { id: 2, name: "Gap-Analyse", icon: AlertTriangle },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header title={assessment.name}>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Shield className="h-3 w-3" />
            DSGVO
          </Badge>
          {assessment.organization_type && (
            <Badge variant="secondary">
              {organizationTypes.find((t) => t.value === assessment.organization_type)?.label}
            </Badge>
          )}
          <Link href="/compliance/regulatory/gdpr">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Zurück
            </Button>
          </Link>
        </div>
      </Header>

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Progress Steps */}
        <div className="border-b bg-muted/30 px-6 py-4">
          <div className="flex items-center justify-between max-w-3xl mx-auto">
            {steps.map((step, idx) => {
              const StepIcon = step.icon;
              const isActive = activeStep === step.id;
              const isCompleted = activeStep > step.id;

              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => setActiveStep(step.id)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : isCompleted
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <StepIcon className="h-4 w-4" />
                    )}
                    <span className="font-medium">{step.name}</span>
                  </button>
                  {idx < steps.length - 1 && (
                    <ArrowRight className="h-4 w-4 mx-4 text-muted-foreground" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {/* Step 0: Scope */}
          {activeStep === 0 && (
            <div className="max-w-3xl mx-auto space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Organisationsinformationen</CardTitle>
                  <CardDescription>
                    Definieren Sie den Geltungsbereich des DSGVO Assessments
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Organization Type */}
                  <div className="space-y-3">
                    <Label>Rolle nach DSGVO *</Label>
                    <div className="grid gap-3">
                      {organizationTypes.map((type) => (
                        <button
                          key={type.value}
                          onClick={() =>
                            setScopeData({ ...scopeData, organization_type: type.value })
                          }
                          className={cn(
                            "flex items-center justify-between p-4 rounded-lg border transition-colors text-left",
                            scopeData.organization_type === type.value
                              ? "border-primary bg-primary/5"
                              : "hover:bg-muted/50"
                          )}
                        >
                          <div>
                            <p className="font-medium">{type.label}</p>
                            <p className="text-sm text-muted-foreground">{type.description}</p>
                          </div>
                          {scopeData.organization_type === type.value && (
                            <CheckCircle2 className="h-5 w-5 text-primary" />
                          )}
                        </button>
                      ))}
                    </div>
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

                  {/* Data Categories */}
                  <div className="space-y-3">
                    <Label>Verarbeitete Datenkategorien *</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {dataCategories.map((cat) => (
                        <div
                          key={cat.value}
                          className="flex items-center space-x-3 p-3 rounded-lg border"
                        >
                          <Checkbox
                            id={cat.value}
                            checked={scopeData.data_categories.includes(cat.value)}
                            onCheckedChange={() => toggleDataCategory(cat.value)}
                          />
                          <label
                            htmlFor={cat.value}
                            className="text-sm font-medium cursor-pointer flex-1"
                          >
                            {cat.label}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Legal Bases */}
                  <div className="space-y-3">
                    <Label>Rechtsgrundlagen *</Label>
                    <div className="grid gap-2">
                      {legalBases.map((basis) => (
                        <div
                          key={basis.value}
                          className="flex items-center space-x-3 p-3 rounded-lg border"
                        >
                          <Checkbox
                            id={basis.value}
                            checked={scopeData.legal_bases.includes(basis.value)}
                            onCheckedChange={() => toggleLegalBasis(basis.value)}
                          />
                          <label
                            htmlFor={basis.value}
                            className="text-sm font-medium cursor-pointer flex-1"
                          >
                            {basis.label}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Processing Flags */}
                  <div className="space-y-4">
                    <Label>Verarbeitungsmerkmale</Label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg border">
                        <div>
                          <p className="font-medium">Besondere Datenkategorien (Art. 9)</p>
                          <p className="text-sm text-muted-foreground">
                            Gesundheit, Religion, politische Meinung, etc.
                          </p>
                        </div>
                        <Switch
                          checked={scopeData.processes_special_categories}
                          onCheckedChange={(v) =>
                            setScopeData({ ...scopeData, processes_special_categories: v })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg border">
                        <div>
                          <p className="font-medium">Umfangreiche Verarbeitung</p>
                          <p className="text-sm text-muted-foreground">
                            Große Datenmenge oder viele betroffene Personen
                          </p>
                        </div>
                        <Switch
                          checked={scopeData.large_scale_processing}
                          onCheckedChange={(v) =>
                            setScopeData({ ...scopeData, large_scale_processing: v })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg border">
                        <div>
                          <p className="font-medium">Systematische Überwachung</p>
                          <p className="text-sm text-muted-foreground">
                            Regelmäßiges Tracking oder Profiling
                          </p>
                        </div>
                        <Switch
                          checked={scopeData.systematic_monitoring}
                          onCheckedChange={(v) =>
                            setScopeData({ ...scopeData, systematic_monitoring: v })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg border">
                        <div>
                          <p className="font-medium">Grenzüberschreitende Verarbeitung</p>
                          <p className="text-sm text-muted-foreground">
                            Verarbeitung in mehreren EU-Mitgliedstaaten
                          </p>
                        </div>
                        <Switch
                          checked={scopeData.cross_border_processing}
                          onCheckedChange={(v) =>
                            setScopeData({ ...scopeData, cross_border_processing: v })
                          }
                        />
                      </div>
                    </div>
                  </div>

                  {/* DPO */}
                  <div className="space-y-4">
                    <Label>Datenschutzbeauftragter (DSB)</Label>
                    <div className="flex items-center justify-between p-3 rounded-lg border">
                      <div>
                        <p className="font-medium">DSB ernannt</p>
                        <p className="text-sm text-muted-foreground">
                          Datenschutzbeauftragter ist benannt
                        </p>
                      </div>
                      <Switch
                        checked={scopeData.dpo_appointed}
                        onCheckedChange={(v) => setScopeData({ ...scopeData, dpo_appointed: v })}
                      />
                    </div>
                    {scopeData.dpo_appointed && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Name des DSB</Label>
                          <Input
                            value={scopeData.dpo_name}
                            onChange={(e) =>
                              setScopeData({ ...scopeData, dpo_name: e.target.value })
                            }
                            placeholder="Max Mustermann"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>E-Mail des DSB</Label>
                          <Input
                            type="email"
                            value={scopeData.dpo_email}
                            onChange={(e) =>
                              setScopeData({ ...scopeData, dpo_email: e.target.value })
                            }
                            placeholder="dsb@unternehmen.de"
                          />
                        </div>
                      </div>
                    )}
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

          {/* Step 1: Requirements */}
          {activeStep === 1 && (
            <div className="flex gap-6 h-full">
              {/* Chapter Navigation */}
              <Card className="w-72 shrink-0">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">DSGVO Kapitel</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[calc(100vh-20rem)]">
                    <div className="space-y-1 p-2">
                      {chapters.map((chapter: Chapter) => {
                        const ChapterIcon = chapterIcons[chapter.id] || FileText;
                        const progress = getChapterProgress(chapter.id);

                        return (
                          <button
                            key={chapter.id}
                            onClick={() => setActiveChapter(chapter.id)}
                            className={cn(
                              "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors",
                              activeChapter === chapter.id
                                ? "bg-primary text-primary-foreground"
                                : "hover:bg-muted"
                            )}
                          >
                            <ChapterIcon className="h-4 w-4 shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                Kap. {chapter.number}: {chapter.name_de}
                              </p>
                              <p className="text-xs opacity-70">Art. {chapter.articles}</p>
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

              {/* Requirements Assessment */}
              <Card className="flex-1">
                <CardHeader>
                  <CardTitle>
                    {chapters.find((c: Chapter) => c.id === activeChapter)?.name_de}
                  </CardTitle>
                  <CardDescription>
                    Bewerten Sie den Erfüllungsgrad jeder Anforderung
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[calc(100vh-22rem)]">
                    <Accordion type="single" collapsible className="space-y-2">
                      {getChapterRequirements(activeChapter).map((req: Requirement) => {
                        const response = requirementResponses[req.id] || {};
                        const currentLevel = response.compliance_level || "not_evaluated";

                        return (
                          <AccordionItem
                            key={req.id}
                            value={req.id}
                            className="border rounded-lg px-4"
                          >
                            <AccordionTrigger className="hover:no-underline py-3">
                              <div className="flex items-center gap-3 flex-1 text-left">
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full shrink-0",
                                    getComplianceColor(currentLevel)
                                  )}
                                />
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-sm">
                                    {req.name_de}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    Art. {req.article} | Gewicht: {req.weight}
                                  </p>
                                </div>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="pt-2 pb-4">
                              <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                  {req.description_de}
                                </p>

                                {/* Compliance Level Selection */}
                                <div className="space-y-2">
                                  <Label>Erfüllungsgrad</Label>
                                  <div className="grid grid-cols-5 gap-2">
                                    {complianceLevels.map((level) => (
                                      <button
                                        key={level.value}
                                        onClick={() =>
                                          updateRequirementResponse(
                                            req.id,
                                            "compliance_level",
                                            level.value
                                          )
                                        }
                                        className={cn(
                                          "p-2 rounded border text-center text-xs transition-colors",
                                          response.compliance_level === level.value
                                            ? `${level.color} text-white border-transparent`
                                            : "hover:bg-muted"
                                        )}
                                      >
                                        {level.label}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                {/* Sub-requirements */}
                                {req.requirements.length > 0 && (
                                  <div className="space-y-2">
                                    <Label className="text-sm">Teilanforderungen</Label>
                                    <div className="space-y-1">
                                      {req.requirements.map((subReq, idx) => (
                                        <div
                                          key={idx}
                                          className="flex items-center gap-2 text-sm"
                                        >
                                          <Checkbox
                                            checked={response.requirements_met?.includes(subReq)}
                                            onCheckedChange={(checked) => {
                                              const met = response.requirements_met || [];
                                              updateRequirementResponse(
                                                req.id,
                                                "requirements_met",
                                                checked
                                                  ? [...met, subReq]
                                                  : met.filter((r: string) => r !== subReq)
                                              );
                                            }}
                                          />
                                          <span>{subReq}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Evidence */}
                                <div className="space-y-2">
                                  <Label>Nachweise</Label>
                                  <Textarea
                                    placeholder="Vorhandene Dokumentation, Prozesse, Maßnahmen..."
                                    value={response.evidence || ""}
                                    onChange={(e) =>
                                      updateRequirementResponse(req.id, "evidence", e.target.value)
                                    }
                                    rows={2}
                                  />
                                </div>

                                {/* Gap Description (if not fully compliant) */}
                                {currentLevel !== "fully_compliant" &&
                                  currentLevel !== "not_applicable" &&
                                  currentLevel !== "not_evaluated" && (
                                    <div className="space-y-2">
                                      <Label>Gap-Beschreibung</Label>
                                      <Textarea
                                        placeholder="Beschreiben Sie die identifizierte Lücke..."
                                        value={response.gap_description || ""}
                                        onChange={(e) =>
                                          updateRequirementResponse(
                                            req.id,
                                            "gap_description",
                                            e.target.value
                                          )
                                        }
                                        rows={2}
                                      />
                                    </div>
                                  )}

                                <div className="flex justify-end">
                                  <Button
                                    size="sm"
                                    onClick={() => handleSaveRequirement(req.id)}
                                    disabled={updateRequirementMutation.isPending}
                                  >
                                    {updateRequirementMutation.isPending && (
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

          {/* Step 2: Gap Analysis */}
          {activeStep === 2 && (
            <div className="max-w-5xl mx-auto space-y-6">
              {/* Summary Cards */}
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Erfüllungsgrad</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-2xl font-bold ${getScoreColor(assessment.overall_score)}`}>
                      {assessment.overall_score.toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">DSB Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {assessment.dpo_appointed ? (
                        <span className="text-green-600">Ernannt</span>
                      ) : assessment.requires_dpo ? (
                        <span className="text-red-600">Fehlt</span>
                      ) : (
                        <span className="text-muted-foreground">N/A</span>
                      )}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Gaps gesamt</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{gapAnalysis?.total_gaps || 0}</div>
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
                    <CardTitle>Identifizierte Gaps</CardTitle>
                    <CardDescription>
                      Anforderungen mit nicht vollständiger Erfüllung
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {gapAnalysis.gaps.slice(0, 20).map((gap) => (
                        <div
                          key={gap.requirement_id}
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
                              <p className="font-medium text-sm">{gap.requirement_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {gap.chapter_name} | Art. {gap.article}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs",
                                  gap.compliance_level === "non_compliant"
                                    ? "border-red-500 text-red-600"
                                    : "border-yellow-500 text-yellow-600"
                                )}
                              >
                                {gap.compliance_level === "non_compliant"
                                  ? "Nicht konform"
                                  : "Teilweise"}
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
                <Button variant="outline" onClick={() => setActiveStep(1)}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Zurück zu Anforderungen
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

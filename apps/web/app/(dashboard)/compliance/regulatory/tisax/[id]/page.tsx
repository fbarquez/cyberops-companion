"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Car,
  ArrowLeft,
  ArrowRight,
  Save,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Factory,
  Truck,
  Settings,
  FileText,
  Shield,
  Lock,
  Users,
  Database,
  Key,
  Monitor,
  Network,
  Code,
  Link2,
  Bell,
  RefreshCw,
  Scale,
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
const tisaxAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getChapters: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/chapters`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch chapters");
    return res.json();
  },
  getControls: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/controls`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch controls");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}/scope`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update scope");
    return res.json();
  },
  updateControl: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}/controls`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update control");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/tisax/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

// Types
interface ControlResponse {
  id: string;
  control_id: string;
  chapter_id: string;
  maturity_level: string;
  target_maturity: string;
  evidence: string | null;
  notes: string | null;
  gap_description: string | null;
  remediation_plan: string | null;
  must_fulfilled: string[];
  should_fulfilled: string[];
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
  company_type: string | null;
  company_size: string | null;
  employee_count: number | null;
  location_count: number;
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
  auditor_name: string | null;
  audit_provider: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  responses: ControlResponse[];
}

interface Chapter {
  id: string;
  number: string;
  name_en: string;
  name_de: string;
  description_en: string;
  control_count: number;
}

interface Control {
  id: string;
  chapter: string;
  number: string;
  name_en: string;
  name_de: string;
  description_en: string;
  description_de: string;
  objective: string;
  weight: number;
  must_requirements: string[];
  should_requirements: string[];
}

interface GapItem {
  control_id: string;
  control_name: string;
  chapter_id: string;
  chapter_name: string;
  current_maturity: number;
  target_maturity: number;
  maturity_gap: number;
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
  average_maturity: number;
  target_maturity: number;
  gaps: GapItem[];
  chapter_summaries: any[];
  recommendations: string[];
}

// Icons for chapters
const chapterIcons: Record<string, any> = {
  chapter_1: FileText,
  chapter_2: Building2,
  chapter_3: Users,
  chapter_4: Database,
  chapter_5: Key,
  chapter_6: Lock,
  chapter_7: Shield,
  chapter_8: Monitor,
  chapter_9: Network,
  chapter_10: Code,
  chapter_11: Link2,
  chapter_12: Bell,
  chapter_13: RefreshCw,
  chapter_14: Scale,
};

// Company types
const companyTypes = [
  { value: "oem", label: "OEM (Hersteller)", icon: Car },
  { value: "tier1", label: "Tier 1 Zulieferer", icon: Factory },
  { value: "tier2", label: "Tier 2 Zulieferer", icon: Factory },
  { value: "tier3", label: "Tier 3 Zulieferer", icon: Factory },
  { value: "service_provider", label: "Dienstleister", icon: Settings },
  { value: "logistics", label: "Logistik", icon: Truck },
  { value: "development", label: "Entwicklungspartner", icon: FileText },
];

// Company sizes
const companySizes = [
  { value: "micro", label: "Mikro (<10 Mitarbeiter)" },
  { value: "small", label: "Klein (10-49 Mitarbeiter)" },
  { value: "medium", label: "Mittel (50-249 Mitarbeiter)" },
  { value: "large", label: "Groß (250+ Mitarbeiter)" },
];

// Assessment levels
const assessmentLevels = [
  { value: "al1", label: "AL1 - Normal", description: "Selbstbewertung" },
  { value: "al2", label: "AL2 - Hoch", description: "Remote-Audit durch Prüfer" },
  { value: "al3", label: "AL3 - Sehr hoch", description: "Vor-Ort-Audit durch Prüfer" },
];

// Objectives
const objectives = [
  { value: "info_high", label: "Informationen mit hohem Schutzbedarf" },
  { value: "info_very_high", label: "Informationen mit sehr hohem Schutzbedarf" },
  { value: "prototype", label: "Prototypenschutz" },
  { value: "prototype_vehicle", label: "Testfahrzeugschutz" },
  { value: "data_protection", label: "Datenschutz (DSGVO)" },
];

// Maturity levels
const maturityLevels = [
  { value: "0", label: "0 - Unvollständig", color: "bg-red-500" },
  { value: "1", label: "1 - Durchgeführt", color: "bg-orange-500" },
  { value: "2", label: "2 - Gesteuert", color: "bg-yellow-500" },
  { value: "3", label: "3 - Etabliert", color: "bg-green-500" },
  { value: "4", label: "4 - Vorhersagbar", color: "bg-blue-500" },
  { value: "5", label: "5 - Optimierend", color: "bg-purple-500" },
];

// Priority labels
const priorityLabels: Record<number, { label: string; color: string }> = {
  1: { label: "Kritisch", color: "text-red-600" },
  2: { label: "Hoch", color: "text-orange-600" },
  3: { label: "Mittel", color: "text-yellow-600" },
  4: { label: "Niedrig", color: "text-green-600" },
};

export default function TISAXAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [activeStep, setActiveStep] = useState(0);
  const [activeChapter, setActiveChapter] = useState("chapter_1");
  const [scopeData, setScopeData] = useState({
    company_type: "",
    company_size: "",
    employee_count: "",
    location_count: "1",
    assessment_level: "",
    objectives: [] as string[],
    oem_requirements: [] as string[],
  });
  const [controlResponses, setControlResponses] = useState<Record<string, any>>({});

  // Fetch assessment
  const { data: assessment, isLoading } = useQuery<Assessment>({
    queryKey: ["tisax", "assessment", assessmentId],
    queryFn: () => tisaxAPI.getAssessment(token!, assessmentId),
    enabled: !!token,
  });

  // Fetch chapters
  const { data: chaptersData } = useQuery({
    queryKey: ["tisax", "chapters"],
    queryFn: () => tisaxAPI.getChapters(token!),
    enabled: !!token,
  });

  // Fetch controls
  const { data: controlsData } = useQuery({
    queryKey: ["tisax", "controls"],
    queryFn: () => tisaxAPI.getControls(token!),
    enabled: !!token,
  });

  // Fetch gap analysis
  const { data: gapAnalysis } = useQuery<GapAnalysis>({
    queryKey: ["tisax", "gaps", assessmentId],
    queryFn: () => tisaxAPI.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessment && assessment.status !== "draft",
  });

  // Initialize scope data from assessment
  useEffect(() => {
    if (assessment) {
      setScopeData({
        company_type: assessment.company_type || "",
        company_size: assessment.company_size || "",
        employee_count: assessment.employee_count?.toString() || "",
        location_count: assessment.location_count?.toString() || "1",
        assessment_level: assessment.assessment_level || "",
        objectives: assessment.objectives || [],
        oem_requirements: assessment.oem_requirements || [],
      });

      // Initialize control responses
      const responses: Record<string, any> = {};
      assessment.responses?.forEach((resp) => {
        responses[resp.control_id] = {
          maturity_level: resp.maturity_level,
          target_maturity: resp.target_maturity,
          evidence: resp.evidence || "",
          notes: resp.notes || "",
          gap_description: resp.gap_description || "",
          remediation_plan: resp.remediation_plan || "",
          must_fulfilled: resp.must_fulfilled || [],
          should_fulfilled: resp.should_fulfilled || [],
          priority: resp.priority || 2,
        };
      });
      setControlResponses(responses);

      // Set active step based on assessment state
      if (!assessment.assessment_level) {
        setActiveStep(0);
      } else {
        setActiveStep(1);
      }
    }
  }, [assessment]);

  // Update scope mutation
  const updateScopeMutation = useMutation({
    mutationFn: (data: any) => tisaxAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tisax"] });
      toast.success("Geltungsbereich gespeichert");
      setActiveStep(1);
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Update control mutation
  const updateControlMutation = useMutation({
    mutationFn: (data: any) => tisaxAPI.updateControl(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tisax"] });
      toast.success("Kontrolle gespeichert");
    },
    onError: () => {
      toast.error("Fehler beim Speichern");
    },
  });

  // Complete assessment mutation
  const completeMutation = useMutation({
    mutationFn: () => tisaxAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tisax"] });
      toast.success("Assessment abgeschlossen");
    },
    onError: () => {
      toast.error("Fehler beim Abschließen");
    },
  });

  const handleSaveScope = () => {
    if (!scopeData.company_type || !scopeData.company_size || !scopeData.assessment_level) {
      toast.error("Bitte füllen Sie alle Pflichtfelder aus");
      return;
    }
    if (scopeData.objectives.length === 0) {
      toast.error("Bitte wählen Sie mindestens ein Schutzziel");
      return;
    }

    updateScopeMutation.mutate({
      company_type: scopeData.company_type,
      company_size: scopeData.company_size,
      employee_count: scopeData.employee_count ? parseInt(scopeData.employee_count) : null,
      location_count: parseInt(scopeData.location_count) || 1,
      assessment_level: scopeData.assessment_level,
      objectives: scopeData.objectives,
      oem_requirements: scopeData.oem_requirements,
    });
  };

  const handleSaveControl = (controlId: string) => {
    const response = controlResponses[controlId];
    if (!response) return;

    updateControlMutation.mutate({
      control_id: controlId,
      maturity_level: response.maturity_level,
      target_maturity: response.target_maturity || "3",
      evidence: response.evidence || null,
      notes: response.notes || null,
      gap_description: response.gap_description || null,
      remediation_plan: response.remediation_plan || null,
      must_fulfilled: response.must_fulfilled || [],
      should_fulfilled: response.should_fulfilled || [],
      priority: response.priority || 2,
    });
  };

  const updateControlResponse = (controlId: string, field: string, value: any) => {
    setControlResponses((prev) => ({
      ...prev,
      [controlId]: {
        ...prev[controlId],
        [field]: value,
      },
    }));
  };

  const toggleObjective = (value: string) => {
    setScopeData((prev) => ({
      ...prev,
      objectives: prev.objectives.includes(value)
        ? prev.objectives.filter((o) => o !== value)
        : [...prev.objectives, value],
    }));
  };

  const chapters = chaptersData?.chapters || [];
  const controls = controlsData?.controls || [];

  const getChapterControls = (chapterId: string) => {
    return controls.filter((c: Control) => c.chapter === chapterId);
  };

  const getChapterProgress = (chapterId: string) => {
    const chapterControls = getChapterControls(chapterId);
    if (chapterControls.length === 0) return 0;

    const assessed = chapterControls.filter(
      (c: Control) => controlResponses[c.id]?.maturity_level
    ).length;
    return (assessed / chapterControls.length) * 100;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getMaturityColor = (level: string) => {
    return maturityLevels.find((m) => m.value === level)?.color || "bg-gray-500";
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
        <Car className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Assessment nicht gefunden</p>
        <Link href="/compliance/regulatory/tisax">
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
    { id: 1, name: "Kontrollen", icon: Shield },
    { id: 2, name: "Gap-Analyse", icon: AlertTriangle },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header title={assessment.name}>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Car className="h-3 w-3" />
            TISAX
          </Badge>
          {assessment.assessment_level && (
            <Badge variant="secondary">
              {assessmentLevels.find((l) => l.value === assessment.assessment_level)?.label}
            </Badge>
          )}
          <Link href="/compliance/regulatory/tisax">
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
                  <CardTitle>Unternehmensinformationen</CardTitle>
                  <CardDescription>
                    Definieren Sie den Geltungsbereich des TISAX Assessments
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Company Type */}
                  <div className="space-y-3">
                    <Label>Unternehmenstyp *</Label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {companyTypes.map((type) => {
                        const TypeIcon = type.icon;
                        return (
                          <button
                            key={type.value}
                            onClick={() =>
                              setScopeData({ ...scopeData, company_type: type.value })
                            }
                            className={cn(
                              "flex items-center gap-3 p-4 rounded-lg border transition-colors",
                              scopeData.company_type === type.value
                                ? "border-primary bg-primary/5"
                                : "hover:bg-muted/50"
                            )}
                          >
                            <TypeIcon className="h-5 w-5" />
                            <span className="text-sm font-medium">{type.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Company Size */}
                  <div className="space-y-2">
                    <Label>Unternehmensgröße *</Label>
                    <Select
                      value={scopeData.company_size}
                      onValueChange={(v) => setScopeData({ ...scopeData, company_size: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Größe auswählen" />
                      </SelectTrigger>
                      <SelectContent>
                        {companySizes.map((size) => (
                          <SelectItem key={size.value} value={size.value}>
                            {size.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Assessment Level */}
                  <div className="space-y-3">
                    <Label>Assessment Level *</Label>
                    <div className="grid gap-3">
                      {assessmentLevels.map((level) => (
                        <button
                          key={level.value}
                          onClick={() =>
                            setScopeData({ ...scopeData, assessment_level: level.value })
                          }
                          className={cn(
                            "flex items-center justify-between p-4 rounded-lg border transition-colors text-left",
                            scopeData.assessment_level === level.value
                              ? "border-primary bg-primary/5"
                              : "hover:bg-muted/50"
                          )}
                        >
                          <div>
                            <p className="font-medium">{level.label}</p>
                            <p className="text-sm text-muted-foreground">{level.description}</p>
                          </div>
                          {scopeData.assessment_level === level.value && (
                            <CheckCircle2 className="h-5 w-5 text-primary" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Objectives */}
                  <div className="space-y-3">
                    <Label>Schutzziele *</Label>
                    <div className="grid gap-2">
                      {objectives.map((obj) => (
                        <div
                          key={obj.value}
                          className="flex items-center space-x-3 p-3 rounded-lg border"
                        >
                          <Checkbox
                            id={obj.value}
                            checked={scopeData.objectives.includes(obj.value)}
                            onCheckedChange={() => toggleObjective(obj.value)}
                          />
                          <label
                            htmlFor={obj.value}
                            className="text-sm font-medium cursor-pointer flex-1"
                          >
                            {obj.label}
                          </label>
                        </div>
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

          {/* Step 1: Controls */}
          {activeStep === 1 && (
            <div className="flex gap-6 h-full">
              {/* Chapter Navigation */}
              <Card className="w-72 shrink-0">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">VDA ISA Kapitel</CardTitle>
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
                                {chapter.number}. {chapter.name_de}
                              </p>
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

              {/* Controls Assessment */}
              <Card className="flex-1">
                <CardHeader>
                  <CardTitle>
                    {chapters.find((c: Chapter) => c.id === activeChapter)?.name_de}
                  </CardTitle>
                  <CardDescription>
                    Bewerten Sie den Reifegrad jeder Kontrolle (0-5)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[calc(100vh-22rem)]">
                    <Accordion type="single" collapsible className="space-y-2">
                      {getChapterControls(activeChapter).map((control: Control) => {
                        const response = controlResponses[control.id] || {};
                        const currentMaturity = response.maturity_level || "0";

                        return (
                          <AccordionItem
                            key={control.id}
                            value={control.id}
                            className="border rounded-lg px-4"
                          >
                            <AccordionTrigger className="hover:no-underline py-3">
                              <div className="flex items-center gap-3 flex-1 text-left">
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full shrink-0",
                                    getMaturityColor(currentMaturity)
                                  )}
                                />
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-sm">
                                    {control.number} - {control.name_de}
                                  </p>
                                  <p className="text-xs text-muted-foreground truncate">
                                    Reifegrad: {currentMaturity}/5
                                  </p>
                                </div>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="pt-2 pb-4">
                              <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                  {control.description_de}
                                </p>

                                {/* Maturity Selection */}
                                <div className="space-y-2">
                                  <Label>Reifegrad</Label>
                                  <div className="grid grid-cols-6 gap-2">
                                    {maturityLevels.map((level) => (
                                      <button
                                        key={level.value}
                                        onClick={() =>
                                          updateControlResponse(
                                            control.id,
                                            "maturity_level",
                                            level.value
                                          )
                                        }
                                        className={cn(
                                          "p-2 rounded border text-center text-sm transition-colors",
                                          response.maturity_level === level.value
                                            ? `${level.color} text-white border-transparent`
                                            : "hover:bg-muted"
                                        )}
                                      >
                                        {level.value}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                {/* Must Requirements */}
                                {control.must_requirements.length > 0 && (
                                  <div className="space-y-2">
                                    <Label className="text-sm">MUSS-Anforderungen</Label>
                                    <div className="space-y-1">
                                      {control.must_requirements.map((req, idx) => (
                                        <div
                                          key={idx}
                                          className="flex items-center gap-2 text-sm"
                                        >
                                          <Checkbox
                                            checked={response.must_fulfilled?.includes(req)}
                                            onCheckedChange={(checked) => {
                                              const fulfilled = response.must_fulfilled || [];
                                              updateControlResponse(
                                                control.id,
                                                "must_fulfilled",
                                                checked
                                                  ? [...fulfilled, req]
                                                  : fulfilled.filter((r: string) => r !== req)
                                              );
                                            }}
                                          />
                                          <span>{req}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Notes */}
                                <div className="space-y-2">
                                  <Label>Notizen</Label>
                                  <Textarea
                                    placeholder="Ergänzende Informationen..."
                                    value={response.notes || ""}
                                    onChange={(e) =>
                                      updateControlResponse(control.id, "notes", e.target.value)
                                    }
                                    rows={2}
                                  />
                                </div>

                                {/* Gap Description (if maturity < 3) */}
                                {parseInt(currentMaturity) < 3 && (
                                  <div className="space-y-2">
                                    <Label>Gap-Beschreibung</Label>
                                    <Textarea
                                      placeholder="Beschreiben Sie die Lücke..."
                                      value={response.gap_description || ""}
                                      onChange={(e) =>
                                        updateControlResponse(
                                          control.id,
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
                                    onClick={() => handleSaveControl(control.id)}
                                    disabled={updateControlMutation.isPending}
                                  >
                                    {updateControlMutation.isPending && (
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
                    <CardTitle className="text-sm font-medium">Reifegrad</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {assessment.maturity_level.toFixed(1)} / 5.0
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
                      Kontrollen mit Reifegrad unter Zielwert
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {gapAnalysis.gaps.slice(0, 20).map((gap) => (
                        <div
                          key={gap.control_id}
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
                              <p className="font-medium text-sm">{gap.control_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {gap.chapter_name}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-sm font-medium">
                                Reifegrad {gap.current_maturity} → {gap.target_maturity}
                              </p>
                              <p
                                className={cn(
                                  "text-xs",
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
                  Zurück zu Kontrollen
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

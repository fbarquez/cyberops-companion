"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Factory,
  ArrowLeft,
  ArrowRight,
  Check,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Download,
  Zap,
  Droplets,
  Utensils,
  Server,
  Heart,
  Landmark,
  Truck,
  Trash,
  Shield,
  Building2,
  Calendar,
  Users,
  Target,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const kritisAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}/scope`, {
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
  submitResponse: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}/responses`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to submit response");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}/gaps`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch gaps");
    return res.json();
  },
  getReport: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}/report`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch report");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/assessments/${id}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
  getRequirements: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/kritis/requirements`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch requirements");
    return res.json();
  },
};

const SECTOR_OPTIONS = [
  { value: "energy", label: "Energie", icon: Zap },
  { value: "water", label: "Wasser", icon: Droplets },
  { value: "food", label: "Ernährung", icon: Utensils },
  { value: "it_telecom", label: "IT & Telekommunikation", icon: Server },
  { value: "health", label: "Gesundheit", icon: Heart },
  { value: "finance", label: "Finanz- & Versicherungswesen", icon: Landmark },
  { value: "transport", label: "Transport & Verkehr", icon: Truck },
  { value: "waste", label: "Siedlungsabfallentsorgung", icon: Trash },
];

const SIZE_OPTIONS = [
  { value: "small", label: "Klein (<50 Mitarbeiter)" },
  { value: "medium", label: "Mittel (50-250 Mitarbeiter)" },
  { value: "large", label: "Groß (250-1000 Mitarbeiter)" },
  { value: "enterprise", label: "Enterprise (>1000 Mitarbeiter)" },
];

const STATUS_OPTIONS = [
  { value: "not_evaluated", label: "Nicht bewertet", color: "bg-gray-100 text-gray-800" },
  { value: "not_implemented", label: "Nicht umgesetzt", color: "bg-red-100 text-red-800" },
  { value: "partially_implemented", label: "Teilweise umgesetzt", color: "bg-yellow-100 text-yellow-800" },
  { value: "fully_implemented", label: "Vollständig umgesetzt", color: "bg-green-100 text-green-800" },
  { value: "not_applicable", label: "Nicht anwendbar", color: "bg-gray-100 text-gray-600" },
];

const CATEGORY_NAMES: Record<string, string> = {
  governance: "Governance & Organisation",
  risk_management: "Risikomanagement",
  technical: "Technische Maßnahmen",
  incident_management: "Vorfallsmanagement",
  business_continuity: "Business Continuity",
  supply_chain: "Lieferkettensicherheit",
  personnel: "Personalsicherheit",
  physical: "Physische Sicherheit",
  compliance: "Compliance & Audit",
};

export default function KRITISAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [currentStep, setCurrentStep] = useState(0);
  const [activeCategory, setActiveCategory] = useState("governance");

  // Scope form state
  const [scopeForm, setScopeForm] = useState({
    sector: "",
    subsector: "",
    company_size: "",
    employee_count: "",
    bsi_registered: false,
    bsi_contact_established: false,
  });

  // Queries
  const { data: assessment, isLoading, refetch } = useQuery({
    queryKey: ["kritis-assessment", assessmentId],
    queryFn: () => kritisAPI.getAssessment(token!, assessmentId),
    enabled: !!token && !!assessmentId,
  });

  const { data: requirementsData } = useQuery({
    queryKey: ["kritis-requirements"],
    queryFn: () => kritisAPI.getRequirements(token!),
    enabled: !!token,
  });

  const { data: gapAnalysis } = useQuery({
    queryKey: ["kritis-gaps", assessmentId],
    queryFn: () => kritisAPI.getGapAnalysis(token!, assessmentId),
    enabled: !!token && !!assessmentId && currentStep >= 2,
  });

  // Initialize scope form when assessment loads
  useEffect(() => {
    if (assessment) {
      setScopeForm({
        sector: assessment.sector || "",
        subsector: assessment.subsector || "",
        company_size: assessment.company_size || "",
        employee_count: assessment.employee_count?.toString() || "",
        bsi_registered: assessment.bsi_registered || false,
        bsi_contact_established: assessment.bsi_contact_established || false,
      });
      // Set initial step based on assessment state
      if (assessment.sector) {
        setCurrentStep(1);
      }
    }
  }, [assessment]);

  // Mutations
  const scopeMutation = useMutation({
    mutationFn: (data: any) => kritisAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kritis-assessment", assessmentId] });
      toast.success("Scope aktualisiert");
      setCurrentStep(1);
    },
    onError: () => toast.error("Fehler beim Speichern"),
  });

  const responseMutation = useMutation({
    mutationFn: (data: any) => kritisAPI.submitResponse(token!, assessmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kritis-assessment", assessmentId] });
      queryClient.invalidateQueries({ queryKey: ["kritis-gaps", assessmentId] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: () => kritisAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kritis-assessment", assessmentId] });
      toast.success("Assessment abgeschlossen");
    },
    onError: () => toast.error("Fehler beim Abschließen"),
  });

  const handleSaveScope = () => {
    if (!scopeForm.sector || !scopeForm.company_size) {
      toast.error("Bitte wählen Sie Sektor und Unternehmensgröße");
      return;
    }
    scopeMutation.mutate({
      sector: scopeForm.sector,
      subsector: scopeForm.subsector || null,
      company_size: scopeForm.company_size,
      employee_count: scopeForm.employee_count ? parseInt(scopeForm.employee_count) : null,
      bsi_registered: scopeForm.bsi_registered,
      bsi_contact_established: scopeForm.bsi_contact_established,
      operates_in_germany: true,
    });
  };

  const handleResponseChange = (requirementId: string, field: string, value: any) => {
    const existingResponse = assessment?.requirement_responses?.find(
      (r: any) => r.requirement_id === requirementId
    );

    const data = {
      requirement_id: requirementId,
      status: existingResponse?.status || "not_evaluated",
      implementation_level: existingResponse?.implementation_level || 0,
      ...{ [field]: value },
    };

    responseMutation.mutate(data);
  };

  const requirements = requirementsData?.requirements || [];
  const categories = requirementsData?.categories || [];

  const getCategoryRequirements = (categoryId: string) => {
    return requirements.filter((r: any) => r.category === categoryId);
  };

  const getResponseForRequirement = (requirementId: string) => {
    return assessment?.requirement_responses?.find(
      (r: any) => r.requirement_id === requirementId
    );
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
        <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Assessment nicht gefunden</p>
        <Link href="/compliance/regulatory/kritis">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück zur Übersicht
          </Button>
        </Link>
      </div>
    );
  }

  const steps = [
    { id: 0, name: "Scope", icon: Building2 },
    { id: 1, name: "Anforderungen", icon: Target },
    { id: 2, name: "Gap-Analyse", icon: AlertTriangle },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header title={assessment.name}>
        <Link href="/compliance/regulatory/kritis">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück
          </Button>
        </Link>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between max-w-2xl mx-auto">
            {steps.map((step, index) => {
              const StepIcon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className={`flex flex-col items-center ${
                      isActive || isCompleted ? "cursor-pointer" : "cursor-default"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : isCompleted
                          ? "bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {isCompleted ? <Check className="h-5 w-5" /> : <StepIcon className="h-5 w-5" />}
                    </div>
                    <span className="text-xs mt-1 font-medium">{step.name}</span>
                  </button>
                  {index < steps.length - 1 && (
                    <div
                      className={`w-24 h-0.5 mx-2 ${
                        currentStep > step.id ? "bg-green-500" : "bg-muted"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Score Overview */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold">{assessment.overall_score}%</p>
                  <p className="text-xs text-muted-foreground">Compliance Score</p>
                </div>
                <Progress value={assessment.overall_score} className="w-32 h-2" />
              </div>
              <div className="flex items-center gap-4 text-sm">
                {assessment.gaps_count > 0 && (
                  <Badge variant="outline" className="gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    {assessment.gaps_count} Lücken
                  </Badge>
                )}
                {assessment.bsi_registered && (
                  <Badge className="bg-green-100 text-green-800 gap-1">
                    <Shield className="h-3 w-3" />
                    BSI registriert
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Step Content */}
        {currentStep === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Scope & Organisation</CardTitle>
              <CardDescription>
                Definieren Sie den Geltungsbereich Ihrer KRITIS-Bewertung
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Sector Selection */}
              <div className="space-y-3">
                <Label>KRITIS-Sektor *</Label>
                <div className="grid gap-3 md:grid-cols-4">
                  {SECTOR_OPTIONS.map((sector) => {
                    const Icon = sector.icon;
                    const isSelected = scopeForm.sector === sector.value;
                    return (
                      <button
                        key={sector.value}
                        onClick={() => setScopeForm({ ...scopeForm, sector: sector.value })}
                        className={`p-4 rounded-lg border text-left transition-all ${
                          isSelected
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        <Icon className={`h-6 w-6 mb-2 ${isSelected ? "text-primary" : ""}`} />
                        <p className="font-medium text-sm">{sector.label}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Company Size */}
              <div className="space-y-2">
                <Label>Unternehmensgröße *</Label>
                <Select
                  value={scopeForm.company_size}
                  onValueChange={(v) => setScopeForm({ ...scopeForm, company_size: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Wählen Sie die Größe..." />
                  </SelectTrigger>
                  <SelectContent>
                    {SIZE_OPTIONS.map((size) => (
                      <SelectItem key={size.value} value={size.value}>
                        {size.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Employee Count */}
              <div className="space-y-2">
                <Label>Anzahl Mitarbeiter (optional)</Label>
                <Input
                  type="number"
                  value={scopeForm.employee_count}
                  onChange={(e) => setScopeForm({ ...scopeForm, employee_count: e.target.value })}
                  placeholder="z.B. 500"
                />
              </div>

              {/* BSI Registration */}
              <div className="space-y-4 pt-4 border-t">
                <h4 className="font-medium">BSI-Registrierung</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="bsi_registered"
                      checked={scopeForm.bsi_registered}
                      onCheckedChange={(checked) =>
                        setScopeForm({ ...scopeForm, bsi_registered: !!checked })
                      }
                    />
                    <Label htmlFor="bsi_registered" className="font-normal">
                      Wir sind beim BSI als KRITIS-Betreiber registriert
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="bsi_contact"
                      checked={scopeForm.bsi_contact_established}
                      onCheckedChange={(checked) =>
                        setScopeForm({ ...scopeForm, bsi_contact_established: !!checked })
                      }
                    />
                    <Label htmlFor="bsi_contact" className="font-normal">
                      Kontakt zum BSI für Vorfallsmeldungen ist etabliert
                    </Label>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSaveScope} disabled={scopeMutation.isPending}>
                  {scopeMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Speichern...
                    </>
                  ) : (
                    <>
                      Weiter
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {currentStep === 1 && (
          <div className="space-y-6">
            <Tabs value={activeCategory} onValueChange={setActiveCategory}>
              <TabsList className="flex-wrap h-auto gap-1">
                {categories.map((cat: any) => (
                  <TabsTrigger key={cat.id} value={cat.id} className="text-xs">
                    {cat.name_de}
                  </TabsTrigger>
                ))}
              </TabsList>

              {categories.map((cat: any) => (
                <TabsContent key={cat.id} value={cat.id} className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>{cat.name_de}</CardTitle>
                      <CardDescription>
                        {cat.requirements_count} Anforderungen in dieser Kategorie
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {getCategoryRequirements(cat.id).map((req: any) => {
                        const response = getResponseForRequirement(req.id);
                        return (
                          <div key={req.id} className="p-4 border rounded-lg space-y-4">
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className="text-xs">
                                    {req.id}
                                  </Badge>
                                  <Badge variant="secondary" className="text-xs">
                                    {req.article}
                                  </Badge>
                                </div>
                                <h4 className="font-medium mt-2">{req.name_de}</h4>
                                <p className="text-sm text-muted-foreground mt-1">
                                  {req.description_de}
                                </p>
                              </div>
                            </div>

                            {/* Sub-requirements */}
                            {req.sub_requirements?.length > 0 && (
                              <div className="space-y-2 pl-4 border-l-2">
                                <p className="text-xs font-medium text-muted-foreground">
                                  Teilanforderungen:
                                </p>
                                {req.sub_requirements.map((sub: string, idx: number) => (
                                  <div key={idx} className="flex items-center gap-2">
                                    <Checkbox
                                      checked={response?.sub_requirements_status?.[idx] || false}
                                      onCheckedChange={(checked) => {
                                        const newStatus = [
                                          ...(response?.sub_requirements_status ||
                                            new Array(req.sub_requirements.length).fill(false)),
                                        ];
                                        newStatus[idx] = !!checked;
                                        handleResponseChange(
                                          req.id,
                                          "sub_requirements_status",
                                          newStatus
                                        );
                                      }}
                                    />
                                    <span className="text-sm">{sub}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Status Selection */}
                            <div className="grid gap-4 md:grid-cols-2">
                              <div className="space-y-2">
                                <Label>Status</Label>
                                <Select
                                  value={response?.status || "not_evaluated"}
                                  onValueChange={(v) => handleResponseChange(req.id, "status", v)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {STATUS_OPTIONS.map((status) => (
                                      <SelectItem key={status.value} value={status.value}>
                                        {status.label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>

                              <div className="space-y-2">
                                <Label>Umsetzungsgrad (%)</Label>
                                <Input
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={response?.implementation_level || 0}
                                  onChange={(e) =>
                                    handleResponseChange(
                                      req.id,
                                      "implementation_level",
                                      parseInt(e.target.value) || 0
                                    )
                                  }
                                />
                              </div>
                            </div>

                            {/* Evidence & Notes */}
                            <div className="space-y-2">
                              <Label>Nachweise / Kommentare</Label>
                              <Textarea
                                value={response?.evidence || ""}
                                onChange={(e) =>
                                  handleResponseChange(req.id, "evidence", e.target.value)
                                }
                                placeholder="Dokumentieren Sie Ihre Nachweise..."
                                rows={2}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </CardContent>
                  </Card>
                </TabsContent>
              ))}
            </Tabs>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setCurrentStep(0)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Zurück
              </Button>
              <Button onClick={() => setCurrentStep(2)}>
                Gap-Analyse
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-6">
            {/* Gap Summary */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-3xl font-bold">{gapAnalysis?.overall_score || 0}%</p>
                  <p className="text-sm text-muted-foreground">Gesamtscore</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-3xl font-bold text-yellow-600">{gapAnalysis?.total_gaps || 0}</p>
                  <p className="text-sm text-muted-foreground">Offene Lücken</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-3xl font-bold text-red-600">{gapAnalysis?.critical_gaps || 0}</p>
                  <p className="text-sm text-muted-foreground">Kritische Lücken</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {requirements.length - (gapAnalysis?.total_gaps || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground">Erfüllt</p>
                </CardContent>
              </Card>
            </div>

            {/* Category Scores */}
            <Card>
              <CardHeader>
                <CardTitle>Score nach Kategorie</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {gapAnalysis?.gaps_by_category?.map((cat: any) => (
                    <div key={cat.category} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{cat.name_de}</span>
                        <span className="font-medium">{cat.score}%</span>
                      </div>
                      <Progress value={cat.score} className="h-2" />
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span className="text-green-600">{cat.fully_implemented} vollständig</span>
                        <span className="text-yellow-600">{cat.partially_implemented} teilweise</span>
                        <span className="text-red-600">{cat.not_implemented} nicht umgesetzt</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            {gapAnalysis?.recommendations?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Empfehlungen</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {gapAnalysis.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Critical Gaps */}
            {gapAnalysis?.gaps?.filter((g: any) => g.priority === 1).length > 0 && (
              <Card className="border-red-200">
                <CardHeader>
                  <CardTitle className="text-red-600 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Kritische Lücken
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {gapAnalysis.gaps
                      .filter((g: any) => g.priority === 1)
                      .map((gap: any) => (
                        <div
                          key={gap.requirement_id}
                          className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-950 rounded-lg"
                        >
                          <div>
                            <p className="font-medium">{gap.requirement_name}</p>
                            <p className="text-sm text-muted-foreground">
                              {gap.article} • Umsetzung: {gap.implementation_level}%
                            </p>
                          </div>
                          <Badge variant="destructive">Kritisch</Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setCurrentStep(1)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Anforderungen bearbeiten
              </Button>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => completeMutation.mutate()}
                  disabled={completeMutation.isPending}
                >
                  {completeMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle className="h-4 w-4 mr-2" />
                  )}
                  Assessment abschließen
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import {
  BarChart3, ArrowLeft, ArrowRight, Save, CheckCircle2, AlertTriangle,
  Settings, Target, Wrench, Headphones, ClipboardCheck, Loader2, FileCheck, Download,
} from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const cobitAPI = {
  getAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error("Failed to fetch assessment");
    return res.json();
  },
  getDomains: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/domains`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error("Failed to fetch domains");
    return res.json();
  },
  getProcesses: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/processes`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error("Failed to fetch processes");
    return res.json();
  },
  getGapAnalysis: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}/gaps`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error("Failed to fetch gap analysis");
    return res.json();
  },
  updateScope: async (token: string, id: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}/scope`, {
      method: "PUT", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update scope");
    return res.json();
  },
  updateProcess: async (token: string, id: string, processId: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}/processes/${processId}`, {
      method: "PUT", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update process");
    return res.json();
  },
  completeAssessment: async (token: string, id: string) => {
    const res = await fetch(`${API_URL}/api/v1/cobit/assessments/${id}/complete`, {
      method: "POST", headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to complete assessment");
    return res.json();
  },
};

interface ProcessResponse { id: string; process_id: string; domain_id: string; status: string; capability_level: string | null; achievement_percentage: number; evidence: string | null; gap_description: string | null; remediation_plan: string | null; priority: number; }
interface Assessment { id: string; name: string; status: string; organization_type: string | null; organization_size: string | null; current_capability_level: string | null; target_capability_level: string | null; overall_score: number; domain_scores: Record<string, number>; gaps_count: number; critical_gaps_count: number; responses: ProcessResponse[]; }
interface Domain { id: string; code: string; name_en: string; name_de: string; process_count: number; }
interface Process { id: string; domain: string; name_en: string; name_de: string; description_en: string; weight: number; priority: number; }

const domainMeta: Record<string, { icon: any; color: string; colorBg: string }> = {
  edm: { icon: Settings, color: "text-purple-600", colorBg: "bg-purple-100 dark:bg-purple-900" },
  apo: { icon: Target, color: "text-blue-600", colorBg: "bg-blue-100 dark:bg-blue-900" },
  bai: { icon: Wrench, color: "text-green-600", colorBg: "bg-green-100 dark:bg-green-900" },
  dss: { icon: Headphones, color: "text-orange-600", colorBg: "bg-orange-100 dark:bg-orange-900" },
  mea: { icon: ClipboardCheck, color: "text-cyan-600", colorBg: "bg-cyan-100 dark:bg-cyan-900" },
};

const organizationTypes = [
  { value: "enterprise", label: "Enterprise" }, { value: "sme", label: "KMU" },
  { value: "public_sector", label: "Öffentlicher Sektor" }, { value: "financial_services", label: "Finanzdienstleistungen" },
  { value: "healthcare", label: "Gesundheitswesen" }, { value: "technology", label: "Technologie" },
];
const organizationSizes = [
  { value: "micro", label: "Mikro (<10)" }, { value: "small", label: "Klein (10-49)" },
  { value: "medium", label: "Mittel (50-249)" }, { value: "large", label: "Groß (250+)" },
];
const capabilityLevels = [
  { value: "level_0", label: "Level 0 - Incomplete", description: "Nicht implementiert" },
  { value: "level_1", label: "Level 1 - Performed", description: "Ausgeführt, ad-hoc" },
  { value: "level_2", label: "Level 2 - Managed", description: "Geplant und überwacht" },
  { value: "level_3", label: "Level 3 - Established", description: "Standardisiert" },
  { value: "level_4", label: "Level 4 - Predictable", description: "Quantitativ gesteuert" },
  { value: "level_5", label: "Level 5 - Optimizing", description: "Kontinuierlich optimiert" },
];
const processStatuses = [
  { value: "not_evaluated", label: "Nicht bewertet", color: "bg-gray-400" },
  { value: "not_achieved", label: "Nicht erreicht", color: "bg-red-500" },
  { value: "partially_achieved", label: "Teilweise", color: "bg-yellow-500" },
  { value: "largely_achieved", label: "Größtenteils", color: "bg-lime-500" },
  { value: "fully_achieved", label: "Vollständig", color: "bg-green-500" },
  { value: "not_applicable", label: "N/A", color: "bg-blue-400" },
];
const priorityLabels: Record<number, { label: string; color: string }> = {
  1: { label: "Kritisch", color: "text-red-600" }, 2: { label: "Hoch", color: "text-orange-600" },
  3: { label: "Mittel", color: "text-yellow-600" }, 4: { label: "Niedrig", color: "text-green-600" },
};

export default function COBITAssessmentPage() {
  const params = useParams();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const assessmentId = params.id as string;

  const [activeStep, setActiveStep] = useState(0);
  const [activeDomain, setActiveDomain] = useState("edm");
  const [scopeData, setScopeData] = useState({ organization_type: "", organization_size: "", current_capability_level: "", target_capability_level: "" });
  const [processResponses, setProcessResponses] = useState<Record<string, any>>({});

  const { data: assessment, isLoading } = useQuery<Assessment>({ queryKey: ["cobit", "assessment", assessmentId], queryFn: () => cobitAPI.getAssessment(token!, assessmentId), enabled: !!token });
  const { data: domainsData } = useQuery({ queryKey: ["cobit", "domains"], queryFn: () => cobitAPI.getDomains(token!), enabled: !!token });
  const { data: processesData } = useQuery({ queryKey: ["cobit", "processes"], queryFn: () => cobitAPI.getProcesses(token!), enabled: !!token });
  const { data: gapAnalysis } = useQuery({ queryKey: ["cobit", "gaps", assessmentId], queryFn: () => cobitAPI.getGapAnalysis(token!, assessmentId), enabled: !!token && !!assessment && assessment.status !== "draft" });

  const domains: Domain[] = domainsData?.domains || [];
  const processes: Process[] = processesData?.processes || [];

  useEffect(() => {
    if (assessment) {
      setScopeData({
        organization_type: assessment.organization_type || "",
        organization_size: assessment.organization_size || "",
        current_capability_level: assessment.current_capability_level || "",
        target_capability_level: assessment.target_capability_level || "",
      });
      const responses: Record<string, any> = {};
      assessment.responses?.forEach((resp) => {
        responses[resp.process_id] = { status: resp.status, capability_level: resp.capability_level, achievement_percentage: resp.achievement_percentage, evidence: resp.evidence || "", gap_description: resp.gap_description || "", remediation_plan: resp.remediation_plan || "", priority: resp.priority || 2 };
      });
      setProcessResponses(responses);
      setActiveStep(assessment.organization_type ? 1 : 0);
    }
  }, [assessment]);

  const updateScopeMutation = useMutation({
    mutationFn: (data: any) => cobitAPI.updateScope(token!, assessmentId, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["cobit"] }); toast.success("Profil gespeichert"); setActiveStep(1); },
    onError: () => { toast.error("Fehler beim Speichern"); },
  });

  const updateProcessMutation = useMutation({
    mutationFn: ({ processId, data }: { processId: string; data: any }) => cobitAPI.updateProcess(token!, assessmentId, processId, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["cobit"] }); toast.success("Prozess gespeichert"); },
    onError: () => { toast.error("Fehler beim Speichern"); },
  });

  const completeMutation = useMutation({
    mutationFn: () => cobitAPI.completeAssessment(token!, assessmentId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["cobit"] }); toast.success("Assessment abgeschlossen"); },
    onError: () => { toast.error("Fehler beim Abschließen"); },
  });

  const handleSaveScope = () => {
    if (!scopeData.organization_type || !scopeData.organization_size || !scopeData.current_capability_level || !scopeData.target_capability_level) {
      toast.error("Bitte füllen Sie alle Pflichtfelder aus"); return;
    }
    updateScopeMutation.mutate(scopeData);
  };

  const handleSaveProcess = (processId: string) => {
    const response = processResponses[processId];
    if (!response) return;
    updateProcessMutation.mutate({ processId, data: { process_id: processId, status: response.status, capability_level: response.capability_level, achievement_percentage: response.achievement_percentage, evidence: response.evidence || null, gap_description: response.gap_description || null, remediation_plan: response.remediation_plan || null, priority: response.priority || 2 } });
  };

  const updateProcessResponse = (processId: string, field: string, value: any) => {
    setProcessResponses((prev) => ({ ...prev, [processId]: { ...prev[processId], [field]: value } }));
  };

  const getDomainProcesses = (domainId: string) => processes.filter((p) => p.domain === domainId);
  const getDomainProgress = (domainId: string) => {
    const domainProcs = getDomainProcesses(domainId);
    if (domainProcs.length === 0) return 0;
    const assessed = domainProcs.filter((p) => processResponses[p.id]?.status && processResponses[p.id]?.status !== "not_evaluated").length;
    return (assessed / domainProcs.length) * 100;
  };
  const getScoreColor = (score: number) => score >= 80 ? "text-green-600" : score >= 60 ? "text-yellow-600" : "text-red-600";
  const getStatusColor = (status: string) => processStatuses.find((s) => s.value === status)?.color || "bg-gray-400";

  if (isLoading) return <div className="flex items-center justify-center h-full"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!assessment) return <div className="flex flex-col items-center justify-center h-full"><BarChart3 className="h-12 w-12 text-muted-foreground mb-4" /><p className="text-muted-foreground">Assessment nicht gefunden</p><Link href="/compliance/frameworks/cobit"><Button variant="outline" className="mt-4"><ArrowLeft className="h-4 w-4 mr-2" />Zurück</Button></Link></div>;

  const steps = [{ id: 0, name: "Profil", icon: Target }, ...domains.map((d, idx) => ({ id: idx + 1, name: d.code, icon: domainMeta[d.id]?.icon || Settings, domainId: d.id })), { id: domains.length + 1, name: "Gap-Analyse", icon: AlertTriangle }];
  const currentDomain = domains.find((d) => d.id === activeDomain);
  const isGapStep = activeStep === domains.length + 1;

  return (
    <div className="flex flex-col h-full">
      <Header title={assessment.name}>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1"><BarChart3 className="h-3 w-3" />COBIT 2019</Badge>
          {assessment.target_capability_level && <Badge variant="secondary">Target: {capabilityLevels.find((l) => l.value === assessment.target_capability_level)?.label.split(" - ")[0]}</Badge>}
          <Link href="/compliance/frameworks/cobit"><Button variant="outline" size="sm"><ArrowLeft className="h-4 w-4 mr-2" />Zurück</Button></Link>
        </div>
      </Header>

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="border-b bg-muted/30 px-4 py-3 overflow-x-auto">
          <div className="flex items-center gap-2 min-w-max">
            {steps.map((step, idx) => {
              const StepIcon = step.icon;
              const isActive = activeStep === step.id;
              const isCompleted = activeStep > step.id;
              const progress = step.id > 0 && step.id <= domains.length ? getDomainProgress(domains[step.id - 1]?.id) : 0;
              return (
                <div key={step.id} className="flex items-center">
                  <button onClick={() => { if (step.id === 0 || assessment.organization_type) { setActiveStep(step.id); if (step.id > 0 && step.id <= domains.length) setActiveDomain(domains[step.id - 1]?.id); } }} disabled={step.id > 0 && !assessment.organization_type}
                    className={cn("flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors text-sm whitespace-nowrap", isActive ? "bg-primary text-primary-foreground" : isCompleted ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" : "bg-muted text-muted-foreground hover:bg-muted/80", step.id > 0 && !assessment.organization_type && "opacity-50 cursor-not-allowed")}>
                    {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <StepIcon className="h-4 w-4" />}
                    <span className="font-medium">{step.name}</span>
                    {step.id > 0 && step.id <= domains.length && <span className="text-xs opacity-70">{Math.round(progress)}%</span>}
                  </button>
                  {idx < steps.length - 1 && <ArrowRight className="h-4 w-4 mx-1 text-muted-foreground shrink-0" />}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {activeStep === 0 && (
            <div className="max-w-3xl mx-auto space-y-6">
              <Card>
                <CardHeader><CardTitle>Organisationsprofil</CardTitle><CardDescription>Definieren Sie Ihr Organisationsprofil und Ziel-Capability Level</CardDescription></CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2"><Label>Organisationstyp *</Label><Select value={scopeData.organization_type} onValueChange={(v) => setScopeData({ ...scopeData, organization_type: v })}><SelectTrigger><SelectValue placeholder="Typ auswählen" /></SelectTrigger><SelectContent>{organizationTypes.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></div>
                    <div className="space-y-2"><Label>Größe *</Label><Select value={scopeData.organization_size} onValueChange={(v) => setScopeData({ ...scopeData, organization_size: v })}><SelectTrigger><SelectValue placeholder="Größe auswählen" /></SelectTrigger><SelectContent>{organizationSizes.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent></Select></div>
                  </div>
                  <div className="space-y-3"><Label>Current Capability Level *</Label><div className="grid gap-2">{capabilityLevels.map((level) => (<button key={level.value} onClick={() => setScopeData({ ...scopeData, current_capability_level: level.value })} className={cn("flex items-center justify-between p-3 rounded-lg border text-left", scopeData.current_capability_level === level.value ? "border-primary bg-primary/5" : "hover:bg-muted/50")}><div><p className="font-medium text-sm">{level.label}</p><p className="text-xs text-muted-foreground">{level.description}</p></div>{scopeData.current_capability_level === level.value && <CheckCircle2 className="h-4 w-4 text-primary" />}</button>))}</div></div>
                  <div className="space-y-3"><Label>Target Capability Level *</Label><div className="grid gap-2">{capabilityLevels.map((level) => (<button key={level.value} onClick={() => setScopeData({ ...scopeData, target_capability_level: level.value })} className={cn("flex items-center justify-between p-3 rounded-lg border text-left", scopeData.target_capability_level === level.value ? "border-green-500 bg-green-50 dark:bg-green-900/20" : "hover:bg-muted/50")}><div><p className="font-medium text-sm">{level.label}</p><p className="text-xs text-muted-foreground">{level.description}</p></div>{scopeData.target_capability_level === level.value && <CheckCircle2 className="h-4 w-4 text-green-600" />}</button>))}</div></div>
                </CardContent>
              </Card>
              <div className="flex justify-end"><Button onClick={handleSaveScope} disabled={updateScopeMutation.isPending}>{updateScopeMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}Speichern & Weiter<ArrowRight className="h-4 w-4 ml-2" /></Button></div>
            </div>
          )}

          {currentDomain && !isGapStep && activeStep > 0 && activeStep <= domains.length && (
            <div className="flex gap-6 h-full">
              <Card className="w-64 shrink-0">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">{(() => { const Icon = domainMeta[currentDomain.id]?.icon || Settings; return <div className={cn("p-2 rounded-lg", domainMeta[currentDomain.id]?.colorBg)}><Icon className={cn("h-4 w-4", domainMeta[currentDomain.id]?.color)} /></div>; })()}<div><CardTitle className="text-base">{currentDomain.code}</CardTitle><p className="text-xs text-muted-foreground">{currentDomain.process_count} Prozesse</p></div></div>
                </CardHeader>
                <CardContent><p className="text-sm text-muted-foreground">{currentDomain.name_de || currentDomain.name_en}</p><div className="mt-4"><div className="flex justify-between text-xs mb-1"><span>Fortschritt</span><span>{Math.round(getDomainProgress(currentDomain.id))}%</span></div><Progress value={getDomainProgress(currentDomain.id)} className="h-2" /></div></CardContent>
              </Card>
              <Card className="flex-1">
                <CardHeader><CardTitle>Prozesse bewerten</CardTitle><CardDescription>Bewerten Sie den Erreichungsgrad jedes Prozesses</CardDescription></CardHeader>
                <CardContent>
                  <ScrollArea className="h-[calc(100vh-24rem)]">
                    <Accordion type="single" collapsible className="space-y-2">
                      {getDomainProcesses(currentDomain.id).map((proc) => {
                        const response = processResponses[proc.id] || {};
                        const currentStatus = response.status || "not_evaluated";
                        return (
                          <AccordionItem key={proc.id} value={proc.id} className="border rounded-lg px-4">
                            <AccordionTrigger className="hover:no-underline py-3">
                              <div className="flex items-center gap-3 flex-1 text-left"><div className={cn("w-2 h-2 rounded-full shrink-0", getStatusColor(currentStatus))} /><div className="flex-1 min-w-0"><p className="font-medium text-sm">{proc.id}: {proc.name_de || proc.name_en}</p><p className="text-xs text-muted-foreground">Gewicht: {proc.weight}</p></div></div>
                            </AccordionTrigger>
                            <AccordionContent className="pt-2 pb-4">
                              <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">{proc.description_en}</p>
                                <div className="space-y-2"><Label>Erreichungsgrad</Label><div className="grid grid-cols-3 gap-2">{processStatuses.map((status) => (<button key={status.value} onClick={() => updateProcessResponse(proc.id, "status", status.value)} className={cn("p-2 rounded border text-center text-xs", response.status === status.value ? `${status.color} text-white border-transparent` : "hover:bg-muted")}>{status.label}</button>))}</div></div>
                                <div className="space-y-2"><div className="flex justify-between"><Label>Achievement %</Label><span className="text-sm text-muted-foreground">{response.achievement_percentage || 0}%</span></div><Slider value={[response.achievement_percentage || 0]} max={100} step={5} onValueChange={([v]) => updateProcessResponse(proc.id, "achievement_percentage", v)} /></div>
                                <div className="space-y-2"><Label>Nachweise</Label><Textarea placeholder="Dokumentation, Prozesse..." value={response.evidence || ""} onChange={(e) => updateProcessResponse(proc.id, "evidence", e.target.value)} rows={2} /></div>
                                {currentStatus !== "fully_achieved" && currentStatus !== "not_applicable" && currentStatus !== "not_evaluated" && (<div className="space-y-2"><Label>Gap-Beschreibung</Label><Textarea placeholder="Identifizierte Lücke..." value={response.gap_description || ""} onChange={(e) => updateProcessResponse(proc.id, "gap_description", e.target.value)} rows={2} /></div>)}
                                <div className="flex justify-end"><Button size="sm" onClick={() => handleSaveProcess(proc.id)} disabled={updateProcessMutation.isPending}>{updateProcessMutation.isPending && <Loader2 className="h-3 w-3 mr-2 animate-spin" />}<Save className="h-3 w-3 mr-2" />Speichern</Button></div>
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

          {isGapStep && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="grid gap-4 md:grid-cols-4">
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Gesamtscore</CardTitle></CardHeader><CardContent><div className={`text-2xl font-bold ${getScoreColor(assessment.overall_score)}`}>{assessment.overall_score.toFixed(1)}%</div></CardContent></Card>
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Current Level</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{assessment.current_capability_level?.replace("level_", "L") || "-"}</div></CardContent></Card>
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Target Level</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{assessment.target_capability_level?.replace("level_", "L") || "-"}</div></CardContent></Card>
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Kritische Gaps</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{gapAnalysis?.critical_gaps || 0}</div></CardContent></Card>
              </div>
              <Card><CardHeader><CardTitle>Domain Scores</CardTitle></CardHeader><CardContent><div className="space-y-4">{domains.map((domain) => { const score = assessment.domain_scores?.[domain.id] || 0; const Icon = domainMeta[domain.id]?.icon || Settings; return (<div key={domain.id} className="space-y-2"><div className="flex justify-between text-sm"><div className="flex items-center gap-2"><div className={cn("p-1.5 rounded", domainMeta[domain.id]?.colorBg)}><Icon className={cn("h-3 w-3", domainMeta[domain.id]?.color)} /></div><span className="font-medium">{domain.code}</span></div><span className={getScoreColor(score)}>{score.toFixed(1)}%</span></div><div className="h-2 bg-muted rounded-full overflow-hidden"><div className={cn("h-full", score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500")} style={{ width: `${score}%` }} /></div></div>); })}</div></CardContent></Card>
              {gapAnalysis?.recommendations?.length > 0 && (<Card><CardHeader><CardTitle>Empfehlungen</CardTitle></CardHeader><CardContent><ul className="space-y-2">{gapAnalysis.recommendations.map((rec: string, idx: number) => (<li key={idx} className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 text-primary mt-0.5 shrink-0" /><span className="text-sm">{rec}</span></li>))}</ul></CardContent></Card>)}
              {gapAnalysis?.gaps?.length > 0 && (<Card><CardHeader><CardTitle>Identifizierte Gaps ({gapAnalysis.total_gaps})</CardTitle></CardHeader><CardContent><div className="space-y-3">{gapAnalysis.gaps.slice(0, 15).map((gap: any) => (<div key={gap.process_id} className="flex items-center justify-between p-3 rounded-lg border"><div className="flex items-center gap-3"><AlertTriangle className={cn("h-4 w-4", gap.priority === 1 ? "text-red-500" : gap.priority === 2 ? "text-orange-500" : "text-yellow-500")} /><div><p className="font-medium text-sm">{gap.process_id}: {gap.process_name}</p><p className="text-xs text-muted-foreground">{gap.domain_name}</p></div></div><div className="text-right"><Badge variant="outline" className="text-xs">{gap.achievement_percentage}%</Badge><p className={cn("text-xs mt-1", priorityLabels[gap.priority]?.color)}>{priorityLabels[gap.priority]?.label}</p></div></div>))}</div></CardContent></Card>)}
              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setActiveStep(domains.length)}><ArrowLeft className="h-4 w-4 mr-2" />Zurück zu {domains[domains.length - 1]?.code}</Button>
                <div className="flex gap-2"><Button variant="outline" onClick={() => toast.info("Report-Export wird vorbereitet...")}><Download className="h-4 w-4 mr-2" />Report</Button>{assessment.status !== "completed" && <Button onClick={() => completeMutation.mutate()} disabled={completeMutation.isPending}>{completeMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}<FileCheck className="h-4 w-4 mr-2" />Abschließen</Button>}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

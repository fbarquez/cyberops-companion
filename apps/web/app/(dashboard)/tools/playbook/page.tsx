"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { BookOpen, Wand2, Download, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
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
import { useTranslations } from "@/hooks/use-translations";
import { toolsAPI } from "@/lib/api-client";
import { toast } from "sonner";

interface PlaybookPhase {
  id?: string;
  phase: string;
  name: string;
  short_name?: string;
  description: string;
  objective: string;
  key_questions: string[];
  critical_reminders: string[];
  common_mistakes: string[];
  forensic_considerations: string[];
  severity_considerations?: string[];
  icon?: string;
  order: number;
}

interface GeneratedPlaybook {
  incident_type: string;
  severity: string;
  generated_at: string;
  phases: PlaybookPhase[];
  compliance_mappings: string[];
  affected_systems: string[];
  metadata: {
    base_playbook: string | null;
    version: string;
  };
}

export default function PlaybookPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [incidentType, setIncidentType] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [affectedSystems, setAffectedSystems] = useState("");
  const [generatedPlaybook, setGeneratedPlaybook] = useState<GeneratedPlaybook | null>(null);

  const { data: types, isLoading } = useQuery({
    queryKey: ["playbook-types"],
    queryFn: () => toolsAPI.getPlaybookTypes(token!),
    enabled: !!token,
  });

  const generateMutation = useMutation<GeneratedPlaybook, Error, void>({
    mutationFn: async () => {
      const result = await toolsAPI.generatePlaybook(token!, {
        incident_type: incidentType,
        severity,
        affected_systems: affectedSystems.split(",").map((s) => s.trim()).filter(Boolean),
        compliance_frameworks: ["bsi", "nist", "iso27001"],
      });
      return result as GeneratedPlaybook;
    },
    onSuccess: (data) => {
      setGeneratedPlaybook(data);
      toast.success(t("playbook.toastGenerated"));
    },
    onError: () => {
      toast.error(t("playbook.toastGenerateFailed"));
    },
  });

  const exportMutation = useMutation({
    mutationFn: (playbookId: string) => toolsAPI.exportPlaybook(token!, playbookId, "markdown"),
    onSuccess: (data: any) => {
      const blob = new Blob([data.content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `playbook-${data.playbook_id}.md`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(t("playbook.toastExported"));
    },
    onError: () => {
      toast.error(t("playbook.toastExportFailed"));
    },
  });

  if (isLoading) return <PageLoading />;

  const typeList = (types as any[]) || [];

  const downloadGeneratedPlaybook = () => {
    if (!generatedPlaybook) return;

    const content = generateMarkdown(generatedPlaybook);
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `playbook-${generatedPlaybook.incident_type}-${severity}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(t("playbook.toastDownloaded"));
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={t("nav.playbook")} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Generator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" />
              {t("playbook.title")}
            </CardTitle>
            <CardDescription>
              {t("playbook.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>{t("playbook.incidentType")}</Label>
                <Select value={incidentType} onValueChange={setIncidentType}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("playbook.selectIncidentType")} />
                  </SelectTrigger>
                  <SelectContent>
                    {typeList.map((type: any) => (
                      <SelectItem key={type.id} value={type.id}>
                        {type.name}
                        {type.available && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {t("playbook.template")}
                          </Badge>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t("playbook.severity")}</Label>
                <Select value={severity} onValueChange={setSeverity}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="critical">{t("playbook.severityCritical")}</SelectItem>
                    <SelectItem value="high">{t("playbook.severityHigh")}</SelectItem>
                    <SelectItem value="medium">{t("playbook.severityMedium")}</SelectItem>
                    <SelectItem value="low">{t("playbook.severityLow")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t("playbook.affectedSystems")}</Label>
                <Input
                  placeholder={t("playbook.affectedSystemsPlaceholder")}
                  value={affectedSystems}
                  onChange={(e) => setAffectedSystems(e.target.value)}
                />
              </div>
            </div>

            <Button
              onClick={() => generateMutation.mutate()}
              disabled={!incidentType || generateMutation.isPending}
            >
              <Wand2 className="h-4 w-4 mr-2" />
              {generateMutation.isPending ? t("playbook.generating") : t("playbook.generatePlaybook")}
            </Button>
          </CardContent>
        </Card>

        {/* Generated Playbook */}
        {generatedPlaybook && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {t("playbook.generatedPlaybookTitle").replace("{type}", generatedPlaybook.incident_type)}
                </CardTitle>
                <CardDescription>
                  {t("playbook.severityLabel")} {generatedPlaybook.severity} | {t("playbook.generatedLabel")}{" "}
                  {new Date(generatedPlaybook.generated_at).toLocaleString()}
                </CardDescription>
              </div>
              <Button variant="outline" onClick={downloadGeneratedPlaybook}>
                <Download className="h-4 w-4 mr-2" />
                {t("playbook.download")}
              </Button>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {generatedPlaybook.phases.map((phase, index) => (
                  <AccordionItem key={phase.phase} value={phase.phase}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">{index + 1}</Badge>
                        <span className="text-lg">{phase.icon}</span>
                        <span className="font-semibold">{phase.name}</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4 pt-4">
                      <div>
                        <p className="text-muted-foreground">{phase.description}</p>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">{t("playbook.objective")}</h4>
                        <p className="text-sm text-muted-foreground">{phase.objective}</p>
                      </div>

                      {phase.key_questions && phase.key_questions.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">{t("playbook.keyQuestions")}</h4>
                          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                            {phase.key_questions.map((q, i) => (
                              <li key={i}>{q}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {phase.critical_reminders && phase.critical_reminders.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2 text-destructive">{t("playbook.criticalReminders")}</h4>
                          <ul className="list-disc list-inside text-sm space-y-1">
                            {phase.critical_reminders.map((r, i) => (
                              <li key={i} className="text-destructive">
                                {r}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {phase.severity_considerations && phase.severity_considerations.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">
                            {t("playbook.severityConsiderations").replace("{severity}", generatedPlaybook.severity)}
                          </h4>
                          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                            {phase.severity_considerations.map((c, i) => (
                              <li key={i}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {phase.forensic_considerations && phase.forensic_considerations.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">{t("playbook.forensicConsiderations")}</h4>
                          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                            {phase.forensic_considerations.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {phase.common_mistakes && phase.common_mistakes.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2 text-yellow-600">{t("playbook.commonMistakes")}</h4>
                          <ul className="list-disc list-inside text-sm text-yellow-600 space-y-1">
                            {phase.common_mistakes.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        )}

        {/* Available Playbooks */}
        <div>
          <h2 className="text-lg font-semibold mb-4">{t("playbook.availableTemplates")}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {typeList.map((type: any) => (
              <Card key={type.id} className={type.available ? "" : "opacity-60"}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-primary" />
                    {type.name}
                  </CardTitle>
                  <CardDescription>{type.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    {type.available ? (
                      <>
                        <Button
                          variant="outline"
                          className="flex-1"
                          onClick={() => exportMutation.mutate(type.id)}
                          disabled={exportMutation.isPending}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          {t("playbook.export")}
                        </Button>
                        <Button
                          className="flex-1"
                          onClick={() => {
                            setIncidentType(type.id);
                            generateMutation.mutate();
                          }}
                          disabled={generateMutation.isPending}
                        >
                          <Wand2 className="h-4 w-4 mr-2" />
                          {t("playbook.use")}
                        </Button>
                      </>
                    ) : (
                      <Badge variant="secondary" className="w-full justify-center py-2">
                        {t("playbook.comingSoon")}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function generateMarkdown(playbook: GeneratedPlaybook): string {
  const lines: string[] = [
    `# Incident Response Playbook: ${playbook.incident_type}`,
    "",
    `**Severity:** ${playbook.severity}`,
    `**Generated:** ${new Date(playbook.generated_at).toLocaleString()}`,
    "",
  ];

  if (playbook.affected_systems.length > 0) {
    lines.push(`**Affected Systems:** ${playbook.affected_systems.join(", ")}`);
    lines.push("");
  }

  lines.push("---", "");

  for (const phase of playbook.phases) {
    lines.push(`## ${phase.icon || ""} ${phase.name}`, "");
    lines.push(`**Objective:** ${phase.objective}`, "");
    lines.push(phase.description, "");

    if (phase.key_questions && phase.key_questions.length > 0) {
      lines.push("### Key Questions", "");
      for (const q of phase.key_questions) {
        lines.push(`- ${q}`);
      }
      lines.push("");
    }

    if (phase.critical_reminders && phase.critical_reminders.length > 0) {
      lines.push("### Critical Reminders", "");
      for (const r of phase.critical_reminders) {
        lines.push(`- **${r}**`);
      }
      lines.push("");
    }

    if (phase.severity_considerations && phase.severity_considerations.length > 0) {
      lines.push(`### Severity Considerations (${playbook.severity})`, "");
      for (const c of phase.severity_considerations) {
        lines.push(`- ${c}`);
      }
      lines.push("");
    }

    if (phase.forensic_considerations && phase.forensic_considerations.length > 0) {
      lines.push("### Forensic Considerations", "");
      for (const f of phase.forensic_considerations) {
        lines.push(`- ${f}`);
      }
      lines.push("");
    }

    if (phase.common_mistakes && phase.common_mistakes.length > 0) {
      lines.push("### Common Mistakes to Avoid", "");
      for (const m of phase.common_mistakes) {
        lines.push(`- ${m}`);
      }
      lines.push("");
    }

    lines.push("---", "");
  }

  return lines.join("\n");
}

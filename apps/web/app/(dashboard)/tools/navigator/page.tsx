"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Map, Search, ExternalLink, CheckSquare, Download, Filter } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { toolsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface Technique {
  technique_id: string;
  name: string;
  description: string;
  tactics: string[];
  is_subtechnique: boolean;
  parent_technique: string | null;
  platforms: string[];
  url: string;
  mitigations: Array<{ id: string; name: string; description?: string }>;
}

interface Tactic {
  id: string;
  name: string;
  short_name: string;
}

const tacticColors: Record<string, string> = {
  "reconnaissance": "bg-slate-500",
  "resource-development": "bg-gray-500",
  "initial-access": "bg-red-500",
  "execution": "bg-orange-500",
  "persistence": "bg-yellow-500",
  "privilege-escalation": "bg-lime-500",
  "defense-evasion": "bg-green-500",
  "credential-access": "bg-teal-500",
  "discovery": "bg-cyan-500",
  "lateral-movement": "bg-blue-500",
  "collection": "bg-indigo-500",
  "command-and-control": "bg-violet-500",
  "exfiltration": "bg-purple-500",
  "impact": "bg-pink-500",
};

export default function NavigatorPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTechniques, setSelectedTechniques] = useState<string[]>([]);
  const [selectedTactic, setSelectedTactic] = useState<string>("all");
  const [expandedTechnique, setExpandedTechnique] = useState<string | null>(null);

  // Fetch tactics
  const { data: tacticsData } = useQuery({
    queryKey: ["mitre-tactics"],
    queryFn: () => toolsAPI.getMITRETactics(token!),
    enabled: !!token,
  });

  // Fetch techniques
  const { data: techniquesData, isLoading } = useQuery({
    queryKey: ["mitre-techniques", selectedTactic],
    queryFn: () => toolsAPI.getMITRETechniques(token!, selectedTactic !== "all" ? selectedTactic : undefined),
    enabled: !!token,
  });

  // Map to MITRE mutation
  const mapMutation = useMutation({
    mutationFn: (incidentId: string) =>
      toolsAPI.mapToMITRE(token!, incidentId, selectedTechniques),
    onSuccess: (data: any) => {
      toast.success(t("navigator.toastMappedSuccess"));
      // Download the layer file
      const blob = new Blob([JSON.stringify(data.navigator_layer, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mitre-layer-${data.incident_id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    },
    onError: () => {
      toast.error(t("navigator.toastMappedError"));
    },
  });

  const tactics: Tactic[] = (tacticsData as any)?.tactics || [];
  const techniques: Technique[] = (techniquesData as any)?.techniques || [];

  // Filter techniques by search query
  const filteredTechniques = useMemo(() => {
    if (!searchQuery) return techniques;
    const query = searchQuery.toLowerCase();
    return techniques.filter(
      (t) =>
        t.technique_id.toLowerCase().includes(query) ||
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query)
    );
  }, [techniques, searchQuery]);

  // Group techniques by tactic
  const techniquesByTactic = useMemo(() => {
    const grouped: Record<string, Technique[]> = {};
    for (const technique of filteredTechniques) {
      for (const tactic of technique.tactics) {
        if (!grouped[tactic]) {
          grouped[tactic] = [];
        }
        grouped[tactic].push(technique);
      }
    }
    return grouped;
  }, [filteredTechniques]);

  const toggleTechnique = (techniqueId: string) => {
    setSelectedTechniques((prev) =>
      prev.includes(techniqueId)
        ? prev.filter((t) => t !== techniqueId)
        : [...prev, techniqueId]
    );
  };

  if (isLoading) return <PageLoading />;

  return (
    <div className="flex flex-col h-full">
      <Header
        title={t("nav.navigator")}
        actions={
          <Button variant="outline" asChild>
            <a
              href="https://attack.mitre.org/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              {t("navigator.openAttack")}
            </a>
          </Button>
        }
      />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Search and Filter */}
        <div className="flex gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t("navigator.searchPlaceholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={selectedTactic} onValueChange={setSelectedTactic}>
            <SelectTrigger className="w-[200px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder={t("navigator.filterByTactic")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("navigator.allTactics")}</SelectItem>
              {tactics.map((tactic) => (
                <SelectItem key={tactic.short_name} value={tactic.short_name}>
                  {tactic.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Badge variant="secondary" className="h-10 px-4 flex items-center">
            {selectedTechniques.length} {t("navigator.selected")}
          </Badge>
        </div>

        {/* Navigator Matrix */}
        <Card>
          <CardHeader>
            <CardTitle>{t("navigator.matrixTitle")}</CardTitle>
            <CardDescription>
              {t("navigator.matrixDescription")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
              {Object.entries(techniquesByTactic).map(([tactic, tacticTechniques]) => (
                <div key={tactic} className="space-y-2">
                  <div
                    className={cn(
                      "p-2 rounded text-white text-xs font-medium text-center",
                      tacticColors[tactic] || "bg-gray-500"
                    )}
                  >
                    {tactic.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </div>
                  <div className="space-y-1 max-h-[300px] overflow-y-auto">
                    {tacticTechniques.slice(0, 10).map((technique) => (
                      <div
                        key={`${tactic}-${technique.technique_id}`}
                        className={cn(
                          "p-2 rounded border text-xs cursor-pointer transition-colors",
                          selectedTechniques.includes(technique.technique_id)
                            ? "bg-primary text-primary-foreground border-primary"
                            : "hover:bg-muted hover:border-primary"
                        )}
                        onClick={() => toggleTechnique(technique.technique_id)}
                        title={technique.description}
                      >
                        <div className="font-mono text-[10px] opacity-70">
                          {technique.technique_id}
                        </div>
                        <div className="truncate">{technique.name}</div>
                      </div>
                    ))}
                    {tacticTechniques.length > 10 && (
                      <div className="text-xs text-muted-foreground text-center py-1">
                        +{tacticTechniques.length - 10} {t("navigator.more")}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Selected Techniques */}
        {selectedTechniques.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckSquare className="h-5 w-5" />
                {t("navigator.selectedTechniques")} ({selectedTechniques.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {selectedTechniques.map((techId) => {
                  const technique = techniques.find((t) => t.technique_id === techId);
                  return (
                    <Badge
                      key={techId}
                      variant="secondary"
                      className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => toggleTechnique(techId)}
                    >
                      {techId}: {technique?.name || techId}
                      <span className="ml-2">×</span>
                    </Badge>
                  );
                })}
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    const incidentId = prompt(t("navigator.promptIncidentId"));
                    if (incidentId) {
                      mapMutation.mutate(incidentId);
                    }
                  }}
                  disabled={mapMutation.isPending}
                >
                  <Map className="h-4 w-4 mr-2" />
                  {t("navigator.mapToIncident")}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    // Download as Navigator layer JSON
                    const layer = {
                      name: "Selected Techniques",
                      versions: { attack: "14", navigator: "4.9.1", layer: "4.5" },
                      domain: "enterprise-attack",
                      techniques: selectedTechniques.map((t) => ({
                        techniqueID: t,
                        score: 1,
                        color: "#ff6666",
                      })),
                    };
                    const blob = new Blob([JSON.stringify(layer, null, 2)], {
                      type: "application/json",
                    });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "mitre-navigator-layer.json";
                    a.click();
                    URL.revokeObjectURL(url);
                    toast.success(t("navigator.toastLayerDownloaded"));
                  }}
                >
                  <Download className="h-4 w-4 mr-2" />
                  {t("navigator.exportLayer")}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedTechniques([])}
                >
                  {t("navigator.clearAll")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Technique Details */}
        {expandedTechnique && (
          <TechniqueDetails
            technique={techniques.find((t) => t.technique_id === expandedTechnique)}
            onClose={() => setExpandedTechnique(null)}
          />
        )}

        {/* Info */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <Map className="h-10 w-10 text-primary flex-shrink-0" />
              <div>
                <h3 className="font-semibold">{t("navigator.aboutTitle")}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {t("navigator.aboutDescription")}
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  {t("navigator.version")} {(techniquesData as any)?.version || "v14"} |{" "}
                  {t("navigator.techniquesLoaded")} {techniques.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TechniqueDetails({
  technique,
  onClose,
}: {
  technique?: Technique;
  onClose: () => void;
}) {
  const { t } = useTranslations();
  if (!technique) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>
            {technique.technique_id}: {technique.name}
          </CardTitle>
          <CardDescription>
            {t("navigator.tactics")} {technique.tactics.join(", ")}
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ×
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-medium mb-1">{t("navigator.description")}</h4>
          <p className="text-sm text-muted-foreground">{technique.description}</p>
        </div>
        {technique.platforms.length > 0 && (
          <div>
            <h4 className="font-medium mb-1">{t("navigator.platforms")}</h4>
            <div className="flex flex-wrap gap-1">
              {technique.platforms.map((p) => (
                <Badge key={p} variant="outline">
                  {p}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {technique.mitigations.length > 0 && (
          <div>
            <h4 className="font-medium mb-1">{t("navigator.mitigations")}</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              {technique.mitigations.map((m) => (
                <li key={m.id}>
                  <strong>{m.id}:</strong> {m.name}
                </li>
              ))}
            </ul>
          </div>
        )}
        <Button variant="outline" asChild>
          <a href={technique.url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="h-4 w-4 mr-2" />
            {t("navigator.viewOnAttack")}
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}

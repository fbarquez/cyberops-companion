"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Filter,
  Shield,
  ShieldCheck,
  Users,
  ClipboardList,
  Cog,
  AlertTriangle,
  LayoutGrid,
  Server,
  Network,
  Building,
  Factory,
  ChevronRight,
  BarChart3,
  List,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";
import { BSIDashboard } from "@/components/compliance";

interface BSIKategorie {
  kategorie: string;
  name_de: string;
  name_en: string;
  baustein_count: number;
}

interface BSIBaustein {
  id: string;
  baustein_id: string;
  kategorie: string;
  titel: string;
  title_en?: string;
  beschreibung?: string;
  version?: string;
  ir_phases?: string[];
  anforderungen_count?: number;
}

const KATEGORIE_ICONS: Record<string, React.ReactNode> = {
  ISMS: <ShieldCheck className="h-5 w-5" />,
  ORP: <Users className="h-5 w-5" />,
  CON: <ClipboardList className="h-5 w-5" />,
  OPS: <Cog className="h-5 w-5" />,
  DER: <AlertTriangle className="h-5 w-5" />,
  APP: <LayoutGrid className="h-5 w-5" />,
  SYS: <Server className="h-5 w-5" />,
  NET: <Network className="h-5 w-5" />,
  INF: <Building className="h-5 w-5" />,
  IND: <Factory className="h-5 w-5" />,
};

export default function BSIGrundschutzPage() {
  const { token } = useAuthStore();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedKategorie, setSelectedKategorie] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [schutzbedarf, setSchutzbedarf] = useState<string>("standard");

  // Fetch categories
  const { data: kategorienData, isLoading: kategorienLoading } = useQuery({
    queryKey: ["bsi-kategorien"],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/bsi/grundschutz/kategorien`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.json();
    },
    enabled: !!token,
  });

  // Fetch Bausteine
  const { data: bausteineData, isLoading: bausteineLoading } = useQuery({
    queryKey: ["bsi-bausteine", selectedKategorie, searchQuery],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const params = new URLSearchParams();
      if (selectedKategorie !== "all") params.append("kategorie", selectedKategorie);
      if (searchQuery) params.append("search", searchQuery);
      params.append("size", "200");

      const response = await fetch(`${apiUrl}/api/v1/bsi/grundschutz/bausteine?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.json();
    },
    enabled: !!token,
  });

  // Fetch compliance overview
  const { data: overviewData } = useQuery({
    queryKey: ["bsi-compliance-overview", schutzbedarf],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/v1/bsi/grundschutz/compliance/overview?schutzbedarf=${schutzbedarf}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.json();
    },
    enabled: !!token,
  });

  const kategorien = kategorienData?.kategorien || [];
  const bausteine = bausteineData?.bausteine || [];

  const filteredBausteine = bausteine.filter((b: BSIBaustein) =>
    b.titel.toLowerCase().includes(searchQuery.toLowerCase()) ||
    b.baustein_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isLoading = kategorienLoading || bausteineLoading;

  return (
    <div className="flex flex-col h-full">
      <Header title="BSI IT-Grundschutz 2023">
        <Select value={schutzbedarf} onValueChange={setSchutzbedarf}>
          <SelectTrigger className="w-40">
            <Shield className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="basis">Basis</SelectItem>
            <SelectItem value="standard">Standard</SelectItem>
            <SelectItem value="hoch">Hoch</SelectItem>
          </SelectContent>
        </Select>
      </Header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Categories */}
        <aside className="w-64 border-r bg-muted/30 overflow-y-auto hidden md:block">
          <div className="p-4">
            <h3 className="font-semibold mb-3 text-sm uppercase text-muted-foreground">
              Kategorien
            </h3>
            <nav className="space-y-1">
              <button
                onClick={() => {
                  setSelectedKategorie("all");
                  setActiveTab("catalogue");
                }}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors",
                  selectedKategorie === "all" && activeTab === "catalogue"
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                )}
              >
                <span className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Alle Bausteine
                </span>
                <Badge variant="secondary" className="ml-2">
                  {bausteine.length}
                </Badge>
              </button>

              {kategorien.map((kat: BSIKategorie) => (
                <button
                  key={kat.kategorie}
                  onClick={() => {
                    setSelectedKategorie(kat.kategorie);
                    setActiveTab("catalogue");
                  }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors",
                    selectedKategorie === kat.kategorie && activeTab === "catalogue"
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {KATEGORIE_ICONS[kat.kategorie] || <Shield className="h-4 w-4" />}
                    <span className="truncate">{kat.kategorie}</span>
                  </span>
                  <Badge variant="secondary" className="ml-2">
                    {kat.baustein_count}
                  </Badge>
                </button>
              ))}
            </nav>
          </div>

          {/* Compliance Summary */}
          {overviewData && (
            <div className="p-4 border-t">
              <h3 className="font-semibold mb-3 text-sm uppercase text-muted-foreground">
                Compliance Score
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">
                    {overviewData.overall_score_percent || 0}%
                  </span>
                  <Badge variant={overviewData.overall_score_percent >= 80 ? "default" : "destructive"}>
                    {schutzbedarf}
                  </Badge>
                </div>
                <Progress value={overviewData.overall_score_percent || 0} className="h-2" />
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <div>
                    <span className="text-green-600">{overviewData.compliant || 0}</span> Compliant
                  </div>
                  <div>
                    <span className="text-yellow-600">{overviewData.partial || 0}</span> Partial
                  </div>
                  <div>
                    <span className="text-red-600">{overviewData.gap || 0}</span> Gaps
                  </div>
                  <div>
                    <span className="text-gray-600">{overviewData.not_evaluated || 0}</span> Open
                  </div>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="border-b px-4 md:px-6 pt-4">
              <TabsList>
                <TabsTrigger value="dashboard" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Dashboard
                </TabsTrigger>
                <TabsTrigger value="catalogue" className="flex items-center gap-2">
                  <List className="h-4 w-4" />
                  Catalogue
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="dashboard" className="flex-1 overflow-y-auto p-4 md:p-6 m-0">
              <BSIDashboard schutzbedarf={schutzbedarf} />
            </TabsContent>

            <TabsContent value="catalogue" className="flex-1 overflow-y-auto p-4 md:p-6 m-0">
              {/* Search and Filters */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 mb-6">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Baustein suchen..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <div className="md:hidden">
                  <Select
                    value={selectedKategorie}
                    onValueChange={setSelectedKategorie}
                  >
                    <SelectTrigger className="w-full sm:w-40">
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue placeholder="Kategorie" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Alle</SelectItem>
                      {kategorien.map((kat: BSIKategorie) => (
                        <SelectItem key={kat.kategorie} value={kat.kategorie}>
                          {kat.kategorie} - {kat.name_de}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Bausteine Grid */}
              {isLoading ? (
                <PageLoading />
              ) : filteredBausteine.length === 0 ? (
                <div className="text-center text-muted-foreground p-8">
                  Keine Bausteine gefunden.
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {filteredBausteine.map((baustein: BSIBaustein) => (
                    <BausteinCard key={baustein.id} baustein={baustein} />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  );
}

function BausteinCard({ baustein }: { baustein: BSIBaustein }) {
  const { token } = useAuthStore();

  const { data: scoreData } = useQuery({
    queryKey: ["bsi-baustein-score", baustein.baustein_id],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/v1/bsi/grundschutz/compliance/score/${encodeURIComponent(baustein.baustein_id)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.json();
    },
    enabled: !!token,
    staleTime: 60000,
  });

  return (
    <Link href={`/compliance/frameworks/bsi/${encodeURIComponent(baustein.baustein_id)}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {KATEGORIE_ICONS[baustein.kategorie] || <Shield className="h-5 w-5" />}
              <Badge variant="outline">{baustein.baustein_id}</Badge>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </div>
          <CardTitle className="text-base mt-2 line-clamp-2">
            {baustein.titel}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {baustein.anforderungen_count !== undefined && (
              <div className="text-sm text-muted-foreground">
                {baustein.anforderungen_count} Anforderungen
              </div>
            )}

            {baustein.ir_phases && baustein.ir_phases.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {baustein.ir_phases.slice(0, 3).map((phase) => (
                  <Badge key={phase} variant="secondary" className="text-xs">
                    {phase}
                  </Badge>
                ))}
                {baustein.ir_phases.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{baustein.ir_phases.length - 3}
                  </Badge>
                )}
              </div>
            )}

            {scoreData && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Score</span>
                  <span className="font-medium">{scoreData.score_percent || 0}%</span>
                </div>
                <Progress value={scoreData.score_percent || 0} className="h-1.5" />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

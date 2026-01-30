"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Radar,
  Crosshair,
  Users,
  Target,
  AlertTriangle,
  Shield,
  Plus,
  Search,
  RefreshCw,
  ExternalLink,
  Trash2,
  MoreHorizontal,
  Upload,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { threatsAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface IOC {
  id: string;
  value: string;
  type: string;
  status: string;
  threat_level: string;
  risk_score: number;
  confidence: number;
  description?: string;
  tags: string[];
  categories: string[];
  source?: string;
  country?: string;
  mitre_techniques: string[];
  first_seen?: string;
  last_seen?: string;
  created_at: string;
}

interface ThreatStats {
  total_iocs: number;
  active_iocs: number;
  iocs_by_type: Record<string, number>;
  iocs_by_threat_level: Record<string, number>;
  total_actors: number;
  active_actors: number;
  total_campaigns: number;
  active_campaigns: number;
  recent_iocs: IOC[];
}

const threatLevelColors: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-blue-500",
  unknown: "bg-gray-500",
};

const threatLevelBadgeVariants: Record<string, "destructive" | "default" | "secondary" | "outline"> = {
  critical: "destructive",
  high: "destructive",
  medium: "default",
  low: "secondary",
  unknown: "outline",
};

const iocTypeIcons: Record<string, string> = {
  ip: "IP",
  domain: "DOM",
  url: "URL",
  md5: "MD5",
  sha1: "SHA1",
  sha256: "SHA256",
  email: "EMAIL",
  cve: "CVE",
};

export default function ThreatsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("overview");
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [threatLevelFilter, setThreatLevelFilter] = useState<string>("all");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showBulkDialog, setShowBulkDialog] = useState(false);
  const [showEnrichDialog, setShowEnrichDialog] = useState(false);
  const [newIOC, setNewIOC] = useState({ value: "", description: "", source: "" });
  const [bulkIOCs, setBulkIOCs] = useState("");
  const [enrichValue, setEnrichValue] = useState("");

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["threat-stats"],
    queryFn: () => threatsAPI.getStats(token!) as Promise<ThreatStats>,
    enabled: !!token,
  });

  // Fetch IOCs
  const { data: iocsData, isLoading: iocsLoading, refetch: refetchIOCs } = useQuery({
    queryKey: ["iocs", searchTerm, typeFilter, threatLevelFilter],
    queryFn: () =>
      threatsAPI.listIOCs(token!, {
        search: searchTerm || undefined,
        type: typeFilter !== "all" ? typeFilter : undefined,
        threat_level: threatLevelFilter !== "all" ? threatLevelFilter : undefined,
        page_size: 50,
      }) as Promise<{ iocs: IOC[]; total: number }>,
    enabled: !!token,
  });

  // Create IOC mutation
  const createMutation = useMutation({
    mutationFn: (data: { value: string; description?: string; source?: string }) =>
      threatsAPI.createIOC(token!, data),
    onSuccess: () => {
      toast.success("IOC created and enriched successfully");
      setShowAddDialog(false);
      setNewIOC({ value: "", description: "", source: "" });
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create IOC");
    },
  });

  // Bulk create mutation
  const bulkCreateMutation = useMutation({
    mutationFn: (values: string[]) =>
      threatsAPI.createIOCsBulk(token!, values.map((v) => ({ value: v.trim() }))),
    onSuccess: (data: any) => {
      toast.success(`Created ${data.length} IOCs`);
      setShowBulkDialog(false);
      setBulkIOCs("");
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create IOCs");
    },
  });

  // Enrich mutation
  const enrichMutation = useMutation({
    mutationFn: (value: string) => threatsAPI.enrichIOC(token!, { value, save: true }),
    onSuccess: (data: any) => {
      toast.success(`IOC enriched: ${data.threat_level} threat level`);
      setShowEnrichDialog(false);
      setEnrichValue("");
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to enrich IOC");
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => threatsAPI.deleteIOC(token!, id),
    onSuccess: () => {
      toast.success("IOC deleted");
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
    },
  });

  if (statsLoading) return <PageLoading />;

  const iocs = iocsData?.iocs || [];

  return (
    <div className="flex flex-col h-full">
      <Header title={t("threats.title")} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total IOCs</CardTitle>
              <Crosshair className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_iocs || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.active_iocs || 0} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Threat Actors</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_actors || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.active_actors || 0} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Campaigns</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_campaigns || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.active_campaigns || 0} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Critical IOCs</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">
                {stats?.iocs_by_threat_level?.critical || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.iocs_by_threat_level?.high || 0} high severity
              </p>
            </CardContent>
          </Card>
        </div>

        {/* IOCs by Type Chart */}
        {stats?.iocs_by_type && Object.keys(stats.iocs_by_type).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">IOCs by Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {Object.entries(stats.iocs_by_type).map(([type, count]) => (
                  <Badge key={type} variant="outline" className="text-sm">
                    {iocTypeIcons[type] || type.toUpperCase()}: {count}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="iocs">{t("threats.iocs")}</TabsTrigger>
              <TabsTrigger value="actors">{t("threats.actors")}</TabsTrigger>
              <TabsTrigger value="campaigns">{t("threats.campaigns")}</TabsTrigger>
            </TabsList>

            <div className="flex gap-2">
              <Dialog open={showEnrichDialog} onOpenChange={setShowEnrichDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Search className="h-4 w-4 mr-2" />
                    {t("threats.enrich")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Enrich IOC</DialogTitle>
                    <DialogDescription>
                      Enter an IOC value to enrich with threat intelligence
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>IOC Value</Label>
                      <Input
                        placeholder="e.g., 192.168.1.1, evil.com, hash..."
                        value={enrichValue}
                        onChange={(e) => setEnrichValue(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      onClick={() => enrichMutation.mutate(enrichValue)}
                      disabled={!enrichValue || enrichMutation.isPending}
                    >
                      {enrichMutation.isPending ? "Enriching..." : "Enrich & Save"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Upload className="h-4 w-4 mr-2" />
                    {t("threats.addBulk")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Bulk Import IOCs</DialogTitle>
                    <DialogDescription>
                      Enter one IOC per line. They will be auto-enriched.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <Textarea
                      placeholder="192.168.1.1&#10;evil-domain.com&#10;abc123hash..."
                      rows={10}
                      value={bulkIOCs}
                      onChange={(e) => setBulkIOCs(e.target.value)}
                    />
                  </div>
                  <DialogFooter>
                    <Button
                      onClick={() => {
                        const values = bulkIOCs.split("\n").filter((v) => v.trim());
                        if (values.length > 0) {
                          bulkCreateMutation.mutate(values);
                        }
                      }}
                      disabled={!bulkIOCs.trim() || bulkCreateMutation.isPending}
                    >
                      {bulkCreateMutation.isPending
                        ? "Importing..."
                        : `Import ${bulkIOCs.split("\n").filter((v) => v.trim()).length} IOCs`}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    {t("threats.addIOC")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add IOC</DialogTitle>
                    <DialogDescription>
                      Add a new indicator of compromise. It will be auto-enriched.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>IOC Value *</Label>
                      <Input
                        placeholder="IP, domain, hash, URL, email..."
                        value={newIOC.value}
                        onChange={(e) => setNewIOC({ ...newIOC, value: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Description</Label>
                      <Input
                        placeholder="Optional description"
                        value={newIOC.description}
                        onChange={(e) => setNewIOC({ ...newIOC, description: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Source</Label>
                      <Input
                        placeholder="Where did you find this IOC?"
                        value={newIOC.source}
                        onChange={(e) => setNewIOC({ ...newIOC, source: e.target.value })}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      onClick={() => createMutation.mutate(newIOC)}
                      disabled={!newIOC.value || createMutation.isPending}
                    >
                      {createMutation.isPending ? "Creating..." : "Create IOC"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent IOCs</CardTitle>
                <CardDescription>Latest indicators added to the system</CardDescription>
              </CardHeader>
              <CardContent>
                {stats?.recent_iocs && stats.recent_iocs.length > 0 ? (
                  <div className="space-y-3">
                    {stats.recent_iocs.map((ioc) => (
                      <IOCRow key={ioc.id} ioc={ioc} onDelete={deleteMutation.mutate} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    {t("threats.noIOCs")}
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* IOCs Tab */}
          <TabsContent value="iocs" className="mt-4 space-y-4">
            {/* Filters */}
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Search IOCs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="ip">IP Address</SelectItem>
                  <SelectItem value="domain">Domain</SelectItem>
                  <SelectItem value="url">URL</SelectItem>
                  <SelectItem value="sha256">SHA256</SelectItem>
                  <SelectItem value="md5">MD5</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                </SelectContent>
              </Select>
              <Select value={threatLevelFilter} onValueChange={setThreatLevelFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Threat Level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" onClick={() => refetchIOCs()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>

            {/* IOCs List */}
            <Card>
              <CardContent className="p-0">
                {iocsLoading ? (
                  <div className="p-8 text-center">Loading...</div>
                ) : iocs.length > 0 ? (
                  <div className="divide-y">
                    {iocs.map((ioc) => (
                      <IOCRow key={ioc.id} ioc={ioc} onDelete={deleteMutation.mutate} />
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    {t("threats.noIOCs")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Actors Tab */}
          <TabsContent value="actors" className="mt-4">
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>{t("threats.noActors")}</p>
                <Button className="mt-4" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Threat Actor
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Campaigns Tab */}
          <TabsContent value="campaigns" className="mt-4">
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>{t("threats.noCampaigns")}</p>
                <Button className="mt-4" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Campaign
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function IOCRow({ ioc, onDelete }: { ioc: IOC; onDelete: (id: string) => void }) {
  return (
    <div className="flex items-center justify-between p-4 hover:bg-muted/50">
      <div className="flex items-center gap-4">
        <Badge variant="outline" className="font-mono text-xs">
          {iocTypeIcons[ioc.type] || ioc.type.toUpperCase()}
        </Badge>
        <div>
          <div className="font-mono text-sm truncate max-w-md">{ioc.value}</div>
          <div className="flex items-center gap-2 mt-1">
            {ioc.tags?.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {ioc.country && (
              <span className="text-xs text-muted-foreground">{ioc.country}</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <Badge variant={threatLevelBadgeVariants[ioc.threat_level] || "outline"}>
            {ioc.threat_level}
          </Badge>
          <div className="text-xs text-muted-foreground mt-1">
            Score: {ioc.risk_score.toFixed(0)} | Conf: {(ioc.confidence * 100).toFixed(0)}%
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <RefreshCw className="h-4 w-4 mr-2" />
              Re-enrich
            </DropdownMenuItem>
            <DropdownMenuItem>
              <ExternalLink className="h-4 w-4 mr-2" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => onDelete(ioc.id)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

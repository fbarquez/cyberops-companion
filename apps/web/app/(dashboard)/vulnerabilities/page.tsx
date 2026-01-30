"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bug,
  Server,
  Scan,
  AlertTriangle,
  Shield,
  Plus,
  Search,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Trash2,
  FileUp,
  Activity,
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
import { Progress } from "@/components/ui/progress";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { vulnerabilitiesAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface Vulnerability {
  id: string;
  title: string;
  description?: string;
  severity: string;
  status: string;
  cvss_score?: number;
  risk_score: number;
  vulnerability_type?: string;
  affected_component?: string;
  remediation_steps?: string;
  remediation_deadline?: string;
  first_detected?: string;
  tags: string[];
  affected_assets: Asset[];
  cves: CVE[];
  created_at: string;
}

interface Asset {
  id: string;
  name: string;
  asset_type: string;
  hostname?: string;
  ip_address?: string;
  criticality: string;
  environment?: string;
  operating_system?: string;
  is_active: boolean;
  vulnerability_count: number;
  created_at: string;
}

interface CVE {
  id: string;
  cve_id: string;
  description?: string;
  cvss_score?: number;
  severity?: string;
  is_kev: boolean;
}

interface VulnStats {
  total_vulnerabilities: number;
  open_vulnerabilities: number;
  in_progress_vulnerabilities: number;
  remediated_vulnerabilities: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  total_assets: number;
  assets_with_vulnerabilities: number;
  total_scans: number;
  scans_last_30_days: number;
  mean_time_to_remediate_days?: number;
  overdue_vulnerabilities: number;
  top_vulnerable_assets: Array<{
    id: string;
    name: string;
    criticality: string;
    vulnerability_count: number;
  }>;
  recent_vulnerabilities: Vulnerability[];
}

const severityColors: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-blue-500",
  info: "bg-gray-500",
};

const severityBadgeVariants: Record<string, "destructive" | "default" | "secondary" | "outline"> = {
  critical: "destructive",
  high: "destructive",
  medium: "default",
  low: "secondary",
  info: "outline",
};

const statusIcons: Record<string, React.ReactNode> = {
  open: <AlertTriangle className="h-4 w-4 text-red-500" />,
  in_progress: <Clock className="h-4 w-4 text-yellow-500" />,
  remediated: <CheckCircle className="h-4 w-4 text-green-500" />,
  accepted: <Shield className="h-4 w-4 text-blue-500" />,
  false_positive: <XCircle className="h-4 w-4 text-gray-500" />,
  mitigated: <Shield className="h-4 w-4 text-purple-500" />,
};

export default function VulnerabilitiesPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("overview");
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [showAddVulnDialog, setShowAddVulnDialog] = useState(false);
  const [showAddAssetDialog, setShowAddAssetDialog] = useState(false);
  const [newVuln, setNewVuln] = useState({
    title: "",
    description: "",
    severity: "medium",
    cvss_score: "",
    affected_component: "",
    remediation_steps: "",
  });
  const [newAsset, setNewAsset] = useState({
    name: "",
    asset_type: "server",
    hostname: "",
    ip_address: "",
    criticality: "medium",
    environment: "production",
  });

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["vuln-stats"],
    queryFn: () => vulnerabilitiesAPI.getStats(token!) as Promise<VulnStats>,
    enabled: !!token,
  });

  // Fetch vulnerabilities
  const { data: vulnsData, isLoading: vulnsLoading, refetch: refetchVulns } = useQuery({
    queryKey: ["vulnerabilities", searchTerm, severityFilter, statusFilter],
    queryFn: () =>
      vulnerabilitiesAPI.listVulnerabilities(token!, {
        search: searchTerm || undefined,
        severity: severityFilter !== "all" ? severityFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        page_size: 50,
      }) as Promise<{ vulnerabilities: Vulnerability[]; total: number }>,
    enabled: !!token,
  });

  // Fetch assets
  const { data: assetsData, isLoading: assetsLoading, refetch: refetchAssets } = useQuery({
    queryKey: ["assets"],
    queryFn: () =>
      vulnerabilitiesAPI.listAssets(token!, { page_size: 50 }) as Promise<{
        assets: Asset[];
        total: number;
      }>,
    enabled: !!token,
  });

  // Create vulnerability mutation
  const createVulnMutation = useMutation({
    mutationFn: (data: any) => vulnerabilitiesAPI.createVulnerability(token!, data),
    onSuccess: () => {
      toast.success("Vulnerability created successfully");
      setShowAddVulnDialog(false);
      setNewVuln({
        title: "",
        description: "",
        severity: "medium",
        cvss_score: "",
        affected_component: "",
        remediation_steps: "",
      });
      queryClient.invalidateQueries({ queryKey: ["vulnerabilities"] });
      queryClient.invalidateQueries({ queryKey: ["vuln-stats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create vulnerability");
    },
  });

  // Create asset mutation
  const createAssetMutation = useMutation({
    mutationFn: (data: any) => vulnerabilitiesAPI.createAsset(token!, data),
    onSuccess: () => {
      toast.success("Asset created successfully");
      setShowAddAssetDialog(false);
      setNewAsset({
        name: "",
        asset_type: "server",
        hostname: "",
        ip_address: "",
        criticality: "medium",
        environment: "production",
      });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["vuln-stats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create asset");
    },
  });

  // Delete vulnerability mutation
  const deleteVulnMutation = useMutation({
    mutationFn: (id: string) => vulnerabilitiesAPI.deleteVulnerability(token!, id),
    onSuccess: () => {
      toast.success("Vulnerability deleted");
      queryClient.invalidateQueries({ queryKey: ["vulnerabilities"] });
      queryClient.invalidateQueries({ queryKey: ["vuln-stats"] });
    },
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      vulnerabilitiesAPI.updateVulnerabilityStatus(token!, id, { status }),
    onSuccess: () => {
      toast.success("Status updated");
      queryClient.invalidateQueries({ queryKey: ["vulnerabilities"] });
      queryClient.invalidateQueries({ queryKey: ["vuln-stats"] });
    },
  });

  if (statsLoading) return <PageLoading />;

  const vulnerabilities = vulnsData?.vulnerabilities || [];
  const assets = assetsData?.assets || [];

  const openPercent = stats?.total_vulnerabilities
    ? Math.round((stats.open_vulnerabilities / stats.total_vulnerabilities) * 100)
    : 0;

  return (
    <div className="flex flex-col h-full">
      <Header title={t("vulnerabilities.title")} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("vulnerabilities.totalVulnerabilities")}</CardTitle>
              <Bug className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_vulnerabilities || 0}</div>
              <div className="flex items-center gap-2 mt-2">
                <Progress value={100 - openPercent} className="h-2" />
                <span className="text-xs text-muted-foreground">
                  {stats?.remediated_vulnerabilities || 0} {t("vulnerabilities.fixed")}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("vulnerabilities.openIssues")}</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">
                {stats?.open_vulnerabilities || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.in_progress_vulnerabilities || 0} {t("vulnerabilities.inProgressCount")}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("vulnerabilities.assetsAtRisk")}</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.assets_with_vulnerabilities || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {t("vulnerabilities.ofTotalAssets").replace("{count}", String(stats?.total_assets || 0))}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("vulnerabilities.mttr")}</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.mean_time_to_remediate_days
                  ? `${stats.mean_time_to_remediate_days}d`
                  : "N/A"}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.overdue_vulnerabilities || 0} {t("vulnerabilities.overdue")}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Severity Breakdown */}
        {stats?.by_severity && Object.keys(stats.by_severity).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">{t("vulnerabilities.bySeverity")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                {["critical", "high", "medium", "low", "info"].map((severity) => (
                  <div key={severity} className="flex items-center gap-2">
                    <div className={cn("w-3 h-3 rounded-full", severityColors[severity])} />
                    <span className="text-sm">{t(`vulnerabilities.${severity}`)}:</span>
                    <span className="font-bold">{stats.by_severity[severity] || 0}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="overview">{t("vulnerabilities.overview")}</TabsTrigger>
              <TabsTrigger value="vulnerabilities">{t("vulnerabilities.list")}</TabsTrigger>
              <TabsTrigger value="assets">{t("vulnerabilities.assets")}</TabsTrigger>
              <TabsTrigger value="scans">{t("vulnerabilities.scans")}</TabsTrigger>
            </TabsList>

            <div className="flex gap-2">
              <Dialog open={showAddAssetDialog} onOpenChange={setShowAddAssetDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Server className="h-4 w-4 mr-2" />
                    {t("vulnerabilities.addAsset")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("vulnerabilities.addAssetTitle")}</DialogTitle>
                    <DialogDescription>{t("vulnerabilities.addAssetDescription")}</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>{t("vulnerabilities.nameRequired")}</Label>
                      <Input
                        placeholder={t("vulnerabilities.assetNamePlaceholder")}
                        value={newAsset.name}
                        onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>{t("vulnerabilities.type")}</Label>
                        <Select
                          value={newAsset.asset_type}
                          onValueChange={(v) => setNewAsset({ ...newAsset, asset_type: v })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="server">{t("vulnerabilities.server")}</SelectItem>
                            <SelectItem value="workstation">{t("vulnerabilities.workstation")}</SelectItem>
                            <SelectItem value="network_device">{t("vulnerabilities.networkDevice")}</SelectItem>
                            <SelectItem value="database">{t("vulnerabilities.database")}</SelectItem>
                            <SelectItem value="web_application">{t("vulnerabilities.webApplication")}</SelectItem>
                            <SelectItem value="container">{t("vulnerabilities.container")}</SelectItem>
                            <SelectItem value="cloud_resource">{t("vulnerabilities.cloudResource")}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>{t("vulnerabilities.criticality")}</Label>
                        <Select
                          value={newAsset.criticality}
                          onValueChange={(v) => setNewAsset({ ...newAsset, criticality: v })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="critical">{t("vulnerabilities.critical")}</SelectItem>
                            <SelectItem value="high">{t("vulnerabilities.high")}</SelectItem>
                            <SelectItem value="medium">{t("vulnerabilities.medium")}</SelectItem>
                            <SelectItem value="low">{t("vulnerabilities.low")}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>{t("vulnerabilities.hostname")}</Label>
                        <Input
                          placeholder={t("vulnerabilities.hostnamePlaceholder")}
                          value={newAsset.hostname}
                          onChange={(e) => setNewAsset({ ...newAsset, hostname: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>{t("vulnerabilities.ipAddress")}</Label>
                        <Input
                          placeholder={t("vulnerabilities.ipAddressPlaceholder")}
                          value={newAsset.ip_address}
                          onChange={(e) => setNewAsset({ ...newAsset, ip_address: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label>{t("vulnerabilities.environment")}</Label>
                      <Select
                        value={newAsset.environment}
                        onValueChange={(v) => setNewAsset({ ...newAsset, environment: v })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="production">{t("vulnerabilities.production")}</SelectItem>
                          <SelectItem value="staging">{t("vulnerabilities.staging")}</SelectItem>
                          <SelectItem value="development">{t("vulnerabilities.development")}</SelectItem>
                          <SelectItem value="testing">{t("vulnerabilities.testing")}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      onClick={() => createAssetMutation.mutate(newAsset)}
                      disabled={!newAsset.name || createAssetMutation.isPending}
                    >
                      {createAssetMutation.isPending ? t("vulnerabilities.creating") : t("vulnerabilities.createAsset")}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={showAddVulnDialog} onOpenChange={setShowAddVulnDialog}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    {t("vulnerabilities.addVulnerability")}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>{t("vulnerabilities.addVulnerabilityTitle")}</DialogTitle>
                    <DialogDescription>{t("vulnerabilities.addVulnerabilityDescription")}</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>{t("vulnerabilities.titleRequired")}</Label>
                      <Input
                        placeholder={t("vulnerabilities.vulnTitlePlaceholder")}
                        value={newVuln.title}
                        onChange={(e) => setNewVuln({ ...newVuln, title: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>{t("vulnerabilities.description")}</Label>
                      <Textarea
                        placeholder={t("vulnerabilities.vulnDescriptionPlaceholder")}
                        value={newVuln.description}
                        onChange={(e) => setNewVuln({ ...newVuln, description: e.target.value })}
                        rows={3}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>{t("vulnerabilities.severity")}</Label>
                        <Select
                          value={newVuln.severity}
                          onValueChange={(v) => setNewVuln({ ...newVuln, severity: v })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="critical">{t("vulnerabilities.critical")}</SelectItem>
                            <SelectItem value="high">{t("vulnerabilities.high")}</SelectItem>
                            <SelectItem value="medium">{t("vulnerabilities.medium")}</SelectItem>
                            <SelectItem value="low">{t("vulnerabilities.low")}</SelectItem>
                            <SelectItem value="info">{t("vulnerabilities.info")}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>{t("vulnerabilities.cvssScore")}</Label>
                        <Input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          placeholder={t("vulnerabilities.cvssScorePlaceholder")}
                          value={newVuln.cvss_score}
                          onChange={(e) => setNewVuln({ ...newVuln, cvss_score: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label>{t("vulnerabilities.affectedComponent")}</Label>
                      <Input
                        placeholder={t("vulnerabilities.affectedComponentPlaceholder")}
                        value={newVuln.affected_component}
                        onChange={(e) =>
                          setNewVuln({ ...newVuln, affected_component: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label>{t("vulnerabilities.remediationSteps")}</Label>
                      <Textarea
                        placeholder={t("vulnerabilities.remediationStepsPlaceholder")}
                        value={newVuln.remediation_steps}
                        onChange={(e) =>
                          setNewVuln({ ...newVuln, remediation_steps: e.target.value })
                        }
                        rows={2}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      onClick={() =>
                        createVulnMutation.mutate({
                          ...newVuln,
                          cvss_score: newVuln.cvss_score ? parseFloat(newVuln.cvss_score) : undefined,
                        })
                      }
                      disabled={!newVuln.title || createVulnMutation.isPending}
                    >
                      {createVulnMutation.isPending ? t("vulnerabilities.creating") : t("vulnerabilities.createVulnerability")}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-4 space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Top Vulnerable Assets */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{t("vulnerabilities.topVulnerableAssets")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.top_vulnerable_assets && stats.top_vulnerable_assets.length > 0 ? (
                    <div className="space-y-3">
                      {stats.top_vulnerable_assets.map((asset) => (
                        <div
                          key={asset.id}
                          className="flex items-center justify-between p-2 rounded-md bg-muted/50"
                        >
                          <div className="flex items-center gap-2">
                            <Server className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">{asset.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {asset.criticality}
                            </Badge>
                          </div>
                          <Badge variant="destructive">{asset.vulnerability_count} {t("vulnerabilities.vulns")}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">{t("vulnerabilities.noVulnerableAssets")}</p>
                  )}
                </CardContent>
              </Card>

              {/* Recent Vulnerabilities */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{t("vulnerabilities.recentVulnerabilities")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.recent_vulnerabilities && stats.recent_vulnerabilities.length > 0 ? (
                    <div className="space-y-3">
                      {stats.recent_vulnerabilities.slice(0, 5).map((vuln) => (
                        <div
                          key={vuln.id}
                          className="flex items-center justify-between p-2 rounded-md bg-muted/50"
                        >
                          <div className="flex items-center gap-2">
                            {statusIcons[vuln.status]}
                            <span className="font-medium truncate max-w-xs">{vuln.title}</span>
                          </div>
                          <Badge variant={severityBadgeVariants[vuln.severity]}>
                            {t(`vulnerabilities.${vuln.severity}`)}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">
                      {t("vulnerabilities.noVulnerabilities")}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Vulnerabilities Tab */}
          <TabsContent value="vulnerabilities" className="mt-4 space-y-4">
            {/* Filters */}
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  placeholder={t("vulnerabilities.searchVulnerabilities")}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>
              <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder={t("vulnerabilities.severity")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("vulnerabilities.allSeverities")}</SelectItem>
                  <SelectItem value="critical">{t("vulnerabilities.critical")}</SelectItem>
                  <SelectItem value="high">{t("vulnerabilities.high")}</SelectItem>
                  <SelectItem value="medium">{t("vulnerabilities.medium")}</SelectItem>
                  <SelectItem value="low">{t("vulnerabilities.low")}</SelectItem>
                  <SelectItem value="info">{t("vulnerabilities.info")}</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder={t("vulnerabilities.status")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("vulnerabilities.allStatuses")}</SelectItem>
                  <SelectItem value="open">{t("vulnerabilities.open")}</SelectItem>
                  <SelectItem value="in_progress">{t("vulnerabilities.inProgress")}</SelectItem>
                  <SelectItem value="remediated">{t("vulnerabilities.remediated")}</SelectItem>
                  <SelectItem value="accepted">{t("vulnerabilities.accepted")}</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" onClick={() => refetchVulns()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>

            {/* Vulnerabilities List */}
            <Card>
              <CardContent className="p-0">
                {vulnsLoading ? (
                  <div className="p-8 text-center">{t("vulnerabilities.loading")}</div>
                ) : vulnerabilities.length > 0 ? (
                  <div className="divide-y">
                    {vulnerabilities.map((vuln) => (
                      <VulnerabilityRow
                        key={vuln.id}
                        vulnerability={vuln}
                        onDelete={() => deleteVulnMutation.mutate(vuln.id)}
                        onStatusChange={(status) =>
                          updateStatusMutation.mutate({ id: vuln.id, status })
                        }
                        t={t}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    {t("vulnerabilities.noVulnerabilities")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Assets Tab */}
          <TabsContent value="assets" className="mt-4">
            <Card>
              <CardContent className="p-0">
                {assetsLoading ? (
                  <div className="p-8 text-center">{t("vulnerabilities.loading")}</div>
                ) : assets.length > 0 ? (
                  <div className="divide-y">
                    {assets.map((asset) => (
                      <AssetRow key={asset.id} asset={asset} t={t} />
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    {t("vulnerabilities.noAssets")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scans Tab */}
          <TabsContent value="scans" className="mt-4">
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <Scan className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>{t("vulnerabilities.noScans")}</p>
                <Button className="mt-4" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  {t("vulnerabilities.newScan")}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function VulnerabilityRow({
  vulnerability,
  onDelete,
  onStatusChange,
  t,
}: {
  vulnerability: Vulnerability;
  onDelete: () => void;
  onStatusChange: (status: string) => void;
  t: (key: string) => string;
}) {
  return (
    <div className="flex items-center justify-between p-4 hover:bg-muted/50">
      <div className="flex items-center gap-4">
        {statusIcons[vulnerability.status]}
        <div>
          <div className="font-medium">{vulnerability.title}</div>
          <div className="flex items-center gap-2 mt-1">
            {vulnerability.affected_component && (
              <span className="text-xs text-muted-foreground">
                {vulnerability.affected_component}
              </span>
            )}
            {vulnerability.cves?.length > 0 && (
              <Badge variant="outline" className="text-xs">
                {vulnerability.cves[0].cve_id}
              </Badge>
            )}
            {vulnerability.affected_assets?.length > 0 && (
              <span className="text-xs text-muted-foreground">
                {vulnerability.affected_assets.length} {t("vulnerabilities.assetCount")}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <Badge variant={severityBadgeVariants[vulnerability.severity]}>
            {t(`vulnerabilities.${vulnerability.severity}`)}
          </Badge>
          {vulnerability.cvss_score && (
            <div className="text-xs text-muted-foreground mt-1">
              CVSS: {vulnerability.cvss_score.toFixed(1)}
            </div>
          )}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {vulnerability.status === "open" && (
              <DropdownMenuItem onClick={() => onStatusChange("in_progress")}>
                <Clock className="h-4 w-4 mr-2" />
                {t("vulnerabilities.markInProgress")}
              </DropdownMenuItem>
            )}
            {vulnerability.status !== "remediated" && (
              <DropdownMenuItem onClick={() => onStatusChange("remediated")}>
                <CheckCircle className="h-4 w-4 mr-2" />
                {t("vulnerabilities.markRemediated")}
              </DropdownMenuItem>
            )}
            {vulnerability.status !== "accepted" && (
              <DropdownMenuItem onClick={() => onStatusChange("accepted")}>
                <Shield className="h-4 w-4 mr-2" />
                {t("vulnerabilities.acceptRisk")}
              </DropdownMenuItem>
            )}
            <DropdownMenuItem className="text-destructive" onClick={onDelete}>
              <Trash2 className="h-4 w-4 mr-2" />
              {t("vulnerabilities.delete")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

function AssetRow({ asset, t }: { asset: Asset; t: (key: string) => string }) {
  return (
    <div className="flex items-center justify-between p-4 hover:bg-muted/50">
      <div className="flex items-center gap-4">
        <Server className="h-5 w-5 text-muted-foreground" />
        <div>
          <div className="font-medium">{asset.name}</div>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {asset.asset_type.replace("_", " ")}
            </Badge>
            {asset.ip_address && (
              <span className="text-xs text-muted-foreground font-mono">{asset.ip_address}</span>
            )}
            {asset.environment && (
              <span className="text-xs text-muted-foreground">{asset.environment}</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <Badge variant={asset.criticality === "critical" ? "destructive" : "secondary"}>
          {t(`vulnerabilities.${asset.criticality}`)}
        </Badge>
        {asset.vulnerability_count > 0 && (
          <Badge variant="outline">{asset.vulnerability_count} {t("vulnerabilities.vulns")}</Badge>
        )}
      </div>
    </div>
  );
}

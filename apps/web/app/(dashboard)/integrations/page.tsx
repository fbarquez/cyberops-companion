"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plug,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Play,
  Pause,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Webhook,
  ArrowDownToLine,
  ArrowUpFromLine,
  ArrowLeftRight,
  Zap,
  Shield,
  Database,
  Mail,
  Bug,
  Cloud,
  FileCode,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { integrationsAPI } from "@/lib/api-client";

interface DashboardStats {
  total_integrations: number;
  active_integrations: number;
  integrations_with_errors: number;
  integrations_by_category: Record<string, number>;
  integrations_by_status: Record<string, number>;
  total_syncs_today: number;
  successful_syncs_today: number;
  failed_syncs_today: number;
  records_synced_today: number;
  webhooks_received_today: number;
  webhooks_processed_today: number;
  webhooks_failed_today: number;
  awareness_metrics?: {
    total_users?: number;
    average_score?: number;
    phishing_click_rate?: number;
    training_completion_rate?: number;
  };
}

interface Integration {
  id: string;
  name: string;
  description?: string;
  integration_type: string;
  category: string;
  status: string;
  is_enabled: boolean;
  base_url?: string;
  config?: Record<string, any>;
  sync_direction: string;
  sync_frequency: string;
  last_sync_at?: string;
  next_sync_at?: string;
  webhook_url?: string;
  last_health_check?: string;
  health_status?: string;
  error_message?: string;
  consecutive_failures: number;
  created_at: string;
  updated_at: string;
}

interface IntegrationTemplate {
  id: string;
  integration_type: string;
  category: string;
  name: string;
  description?: string;
  vendor?: string;
  logo_url?: string;
  documentation_url?: string;
  supports_inbound: boolean;
  supports_outbound: boolean;
  supports_webhook: boolean;
  supported_entities?: string[];
  auth_methods?: string[];
  is_active: boolean;
}

interface SyncLog {
  id: string;
  integration_id: string;
  sync_type?: string;
  direction?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  status?: string;
  records_fetched: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  error_message?: string;
  triggered_by?: string;
}

interface IntegrationListResponse {
  items: Integration[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface SyncLogListResponse {
  items: SyncLog[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function IntegrationsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddIntegrationOpen, setIsAddIntegrationOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<IntegrationTemplate | null>(null);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [newIntegration, setNewIntegration] = useState({
    name: "",
    description: "",
    integration_type: "",
    category: "",
    base_url: "",
    api_key: "",
    sync_frequency: "hourly",
  });

  // Dashboard stats
  const { data: dashboardData } = useQuery({
    queryKey: ["integrations-dashboard"],
    queryFn: () => integrationsAPI.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
    refetchInterval: 30000,
  });

  // Templates
  const { data: templatesData } = useQuery({
    queryKey: ["integration-templates", categoryFilter],
    queryFn: () =>
      integrationsAPI.listTemplates(
        token!,
        categoryFilter !== "all" ? categoryFilter : undefined
      ) as Promise<IntegrationTemplate[]>,
    enabled: !!token && (activeTab === "templates" || activeTab === "dashboard"),
  });

  // Integrations list
  const { data: integrationsData, refetch: refetchIntegrations } = useQuery({
    queryKey: ["integrations", categoryFilter, statusFilter, searchQuery],
    queryFn: () =>
      integrationsAPI.listIntegrations(token!, {
        category: categoryFilter !== "all" ? categoryFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        search: searchQuery || undefined,
        size: 50,
      }) as Promise<IntegrationListResponse>,
    enabled: !!token && activeTab === "integrations",
  });

  // Sync logs (for selected integration)
  const { data: syncLogsData } = useQuery({
    queryKey: ["sync-logs", selectedIntegration?.id],
    queryFn: () =>
      integrationsAPI.getSyncLogs(token!, selectedIntegration!.id) as Promise<SyncLogListResponse>,
    enabled: !!token && !!selectedIntegration && activeTab === "logs",
  });

  // Seed templates mutation
  const seedTemplatesMutation = useMutation({
    mutationFn: () => integrationsAPI.seedTemplates(token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integration-templates"] });
    },
  });

  // Create integration mutation
  const createIntegrationMutation = useMutation({
    mutationFn: (data: any) => integrationsAPI.createIntegration(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      queryClient.invalidateQueries({ queryKey: ["integrations-dashboard"] });
      setIsAddIntegrationOpen(false);
      setSelectedTemplate(null);
      setNewIntegration({
        name: "",
        description: "",
        integration_type: "",
        category: "",
        base_url: "",
        api_key: "",
        sync_frequency: "hourly",
      });
    },
  });

  // Toggle integration mutation
  const toggleIntegrationMutation = useMutation({
    mutationFn: ({ id, enable }: { id: string; enable: boolean }) =>
      enable ? integrationsAPI.enableIntegration(token!, id) : integrationsAPI.disableIntegration(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      queryClient.invalidateQueries({ queryKey: ["integrations-dashboard"] });
    },
  });

  // Trigger sync mutation
  const triggerSyncMutation = useMutation({
    mutationFn: (id: string) => integrationsAPI.triggerSync(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      queryClient.invalidateQueries({ queryKey: ["sync-logs"] });
    },
  });

  const handleCreateIntegration = async () => {
    if (!newIntegration.name || !newIntegration.integration_type) return;

    createIntegrationMutation.mutate({
      ...newIntegration,
      category: selectedTemplate?.category || newIntegration.category,
    });
  };

  const handleSelectTemplate = (template: IntegrationTemplate) => {
    setSelectedTemplate(template);
    setNewIntegration({
      ...newIntegration,
      name: template.name,
      integration_type: template.integration_type,
      category: template.category,
    });
    setIsAddIntegrationOpen(true);
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, any> = {
      security_awareness: Shield,
      siem: Database,
      edr_xdr: Zap,
      ticketing: FileCode,
      email_security: Mail,
      vulnerability: Bug,
      threat_intel: AlertTriangle,
      cloud_security: Cloud,
      custom: Plug,
    };
    return icons[category] || Plug;
  };

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      active: "default",
      inactive: "secondary",
      error: "destructive",
      configuring: "outline",
      testing: "outline",
    };
    return variants[status] || "secondary";
  };

  const getSyncDirectionIcon = (direction: string) => {
    if (direction === "inbound") return ArrowDownToLine;
    if (direction === "outbound") return ArrowUpFromLine;
    return ArrowLeftRight;
  };

  const stats = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("integrations.title")}</h1>
          <p className="text-muted-foreground">
            {t("integrations.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => seedTemplatesMutation.mutate()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            {t("integrations.seedTemplates")}
          </Button>
          <Dialog open={isAddIntegrationOpen} onOpenChange={setIsAddIntegrationOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                {t("integrations.addIntegration")}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>
                  {selectedTemplate ? t("integrations.configureX").replace("{name}", selectedTemplate.name) : t("integrations.addIntegration")}
                </DialogTitle>
                <DialogDescription>
                  {selectedTemplate
                    ? selectedTemplate.description
                    : t("integrations.connectNewPlatform")}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">{t("integrations.integrationName")}</Label>
                  <Input
                    id="name"
                    value={newIntegration.name}
                    onChange={(e) =>
                      setNewIntegration({ ...newIntegration, name: e.target.value })
                    }
                    placeholder={t("integrations.namePlaceholder")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="base_url">{t("integrations.baseUrlEndpoint")}</Label>
                  <Input
                    id="base_url"
                    value={newIntegration.base_url}
                    onChange={(e) =>
                      setNewIntegration({ ...newIntegration, base_url: e.target.value })
                    }
                    placeholder={t("integrations.urlPlaceholder")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api_key">{t("integrations.apiKey")}</Label>
                  <Input
                    id="api_key"
                    type="password"
                    value={newIntegration.api_key}
                    onChange={(e) =>
                      setNewIntegration({ ...newIntegration, api_key: e.target.value })
                    }
                    placeholder={t("integrations.apiKeyPlaceholder")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sync_frequency">{t("integrations.syncFrequency")}</Label>
                  <Select
                    value={newIntegration.sync_frequency}
                    onValueChange={(v) =>
                      setNewIntegration({ ...newIntegration, sync_frequency: v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="realtime">{t("integrations.realtime")}</SelectItem>
                      <SelectItem value="hourly">{t("integrations.hourly")}</SelectItem>
                      <SelectItem value="daily">{t("integrations.daily")}</SelectItem>
                      <SelectItem value="weekly">{t("integrations.weekly")}</SelectItem>
                      <SelectItem value="manual">{t("integrations.manual")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">{t("integrations.description")}</Label>
                  <Textarea
                    id="description"
                    value={newIntegration.description}
                    onChange={(e) =>
                      setNewIntegration({ ...newIntegration, description: e.target.value })
                    }
                    placeholder={t("integrations.descriptionPlaceholder")}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddIntegrationOpen(false)}>
                  {t("integrations.cancel")}
                </Button>
                <Button
                  onClick={handleCreateIntegration}
                  disabled={!newIntegration.name || createIntegrationMutation.isPending}
                >
                  {createIntegrationMutation.isPending ? t("integrations.creating") : t("integrations.createIntegration")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            {t("integrations.dashboard")}
          </TabsTrigger>
          <TabsTrigger value="integrations" className="flex items-center gap-2">
            <Plug className="h-4 w-4" />
            {t("integrations.list")}
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <FileCode className="h-4 w-4" />
            {t("integrations.templates")}
          </TabsTrigger>
          <TabsTrigger value="logs" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            {t("integrations.syncLogs")}
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("integrations.totalIntegrations")}
                </CardTitle>
                <Plug className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_integrations || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.active_integrations || 0} {t("integrations.active")}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("integrations.withErrors")}
                </CardTitle>
                <XCircle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-destructive">
                  {stats?.integrations_with_errors || 0}
                </div>
                <p className="text-xs text-muted-foreground">{t("integrations.requireAttention")}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("integrations.syncsToday")}
                </CardTitle>
                <RefreshCw className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_syncs_today || 0}</div>
                <div className="flex gap-2 text-xs">
                  <span className="text-green-600">
                    {stats?.successful_syncs_today || 0} {t("integrations.success")}
                  </span>
                  <span className="text-destructive">
                    {stats?.failed_syncs_today || 0} {t("integrations.failed")}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("integrations.recordsSynced")}
                </CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(stats?.records_synced_today || 0).toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">{t("integrations.today")}</p>
              </CardContent>
            </Card>
          </div>

          {/* Webhook Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("integrations.webhooksToday")}
                </CardTitle>
                <Webhook className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.webhooks_received_today || 0}</div>
                <div className="flex gap-2 text-xs">
                  <span className="text-green-600">
                    {stats?.webhooks_processed_today || 0} {t("integrations.processed")}
                  </span>
                  <span className="text-destructive">
                    {stats?.webhooks_failed_today || 0} {t("integrations.failed")}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Security Awareness Metrics */}
            {stats?.awareness_metrics && (
              <>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">{t("integrations.awarenessScore")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {stats.awareness_metrics.average_score || 0}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {stats.awareness_metrics.total_users || 0} {t("integrations.usersTracked")}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">{t("integrations.phishingClickRate")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {stats.awareness_metrics.phishing_click_rate || 0}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {stats.awareness_metrics.training_completion_rate || 0}% {t("integrations.trainingComplete")}
                    </p>
                  </CardContent>
                </Card>
              </>
            )}
          </div>

          {/* Category Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">{t("integrations.integrationsByCategory")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {Object.entries(stats?.integrations_by_category || {}).map(([category, count]) => {
                  const Icon = getCategoryIcon(category);
                  return (
                    <div key={category} className="flex items-center gap-2 bg-muted px-3 py-2 rounded-md">
                      <Icon className="h-4 w-4" />
                      <span className="text-sm capitalize">{category.replace(/_/g, " ")}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Integrations Tab */}
        <TabsContent value="integrations" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t("integrations.searchIntegrations")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("integrations.allCategories")}</SelectItem>
                <SelectItem value="security_awareness">{t("integrations.securityAwareness")}</SelectItem>
                <SelectItem value="siem">{t("integrations.siem")}</SelectItem>
                <SelectItem value="edr_xdr">{t("integrations.edrXdr")}</SelectItem>
                <SelectItem value="ticketing">{t("integrations.ticketing")}</SelectItem>
                <SelectItem value="threat_intel">{t("integrations.threatIntel")}</SelectItem>
                <SelectItem value="vulnerability">{t("integrations.vulnerability")}</SelectItem>
                <SelectItem value="cloud_security">{t("integrations.cloudSecurity")}</SelectItem>
                <SelectItem value="custom">{t("integrations.custom")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("integrations.allStatus")}</SelectItem>
                <SelectItem value="active">{t("integrations.active")}</SelectItem>
                <SelectItem value="inactive">{t("integrations.inactive")}</SelectItem>
                <SelectItem value="error">{t("integrations.error")}</SelectItem>
                <SelectItem value="configuring">{t("integrations.configuring")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Integrations List */}
          <div className="grid gap-4">
            {integrationsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Plug className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("integrations.noIntegrations")}</p>
                  <Button variant="outline" className="mt-4" onClick={() => setActiveTab("templates")}>
                    {t("integrations.browseTemplates")}
                  </Button>
                </CardContent>
              </Card>
            )}
            {integrationsData?.items?.map((integration) => {
              const CategoryIcon = getCategoryIcon(integration.category);
              const DirectionIcon = getSyncDirectionIcon(integration.sync_direction);
              return (
                <Card key={integration.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="p-2 bg-muted rounded-lg">
                          <CategoryIcon className="h-6 w-6" />
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{integration.name}</h3>
                            <Badge variant={getStatusBadgeVariant(integration.status)}>
                              {integration.status}
                            </Badge>
                            {integration.is_enabled ? (
                              <Badge variant="default" className="bg-green-600">{t("integrations.enabled")}</Badge>
                            ) : (
                              <Badge variant="secondary">{t("integrations.disabled")}</Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {integration.description || integration.integration_type}
                          </p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            <Badge variant="outline" className="flex items-center gap-1">
                              <DirectionIcon className="h-3 w-3" />
                              {integration.sync_direction}
                            </Badge>
                            <Badge variant="outline">
                              <Clock className="h-3 w-3 mr-1" />
                              {integration.sync_frequency}
                            </Badge>
                            {integration.consecutive_failures > 0 && (
                              <Badge variant="destructive">
                                {integration.consecutive_failures} {t("integrations.failures")}
                              </Badge>
                            )}
                          </div>
                          {integration.error_message && (
                            <p className="text-xs text-destructive mt-2">
                              {integration.error_message}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => triggerSyncMutation.mutate(integration.id)}
                            disabled={!integration.is_enabled}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              toggleIntegrationMutation.mutate({
                                id: integration.id,
                                enable: !integration.is_enabled,
                              })
                            }
                          >
                            {integration.is_enabled ? (
                              <Pause className="h-4 w-4" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedIntegration(integration);
                              setActiveTab("logs");
                            }}
                          >
                            <Clock className="h-4 w-4" />
                          </Button>
                        </div>
                        {integration.last_sync_at && (
                          <p className="text-xs text-muted-foreground">
                            {t("integrations.lastSyncLabel")} {new Date(integration.last_sync_at).toLocaleString()}
                          </p>
                        )}
                        {integration.next_sync_at && (
                          <p className="text-xs text-muted-foreground">
                            {t("integrations.nextLabel")} {new Date(integration.next_sync_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          {/* Category Filter */}
          <div className="flex gap-4">
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[200px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("integrations.allCategories")}</SelectItem>
                <SelectItem value="security_awareness">{t("integrations.securityAwareness")}</SelectItem>
                <SelectItem value="siem">{t("integrations.siem")}</SelectItem>
                <SelectItem value="edr_xdr">{t("integrations.edrXdr")}</SelectItem>
                <SelectItem value="ticketing">{t("integrations.ticketing")}</SelectItem>
                <SelectItem value="threat_intel">{t("integrations.threatIntel")}</SelectItem>
                <SelectItem value="vulnerability">{t("integrations.vulnerability")}</SelectItem>
                <SelectItem value="cloud_security">{t("integrations.cloudSecurity")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Templates Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templatesData?.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FileCode className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("integrations.noTemplates")}</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => seedTemplatesMutation.mutate()}
                  >
                    {t("integrations.seedDefaultTemplates")}
                  </Button>
                </CardContent>
              </Card>
            )}
            {templatesData?.map((template) => {
              const CategoryIcon = getCategoryIcon(template.category);
              return (
                <Card key={template.id} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-muted rounded-lg">
                          <CategoryIcon className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base">{template.name}</CardTitle>
                          {template.vendor && (
                            <p className="text-xs text-muted-foreground">{template.vendor}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-3">
                      {template.description || t("integrations.noDescriptionAvailable")}
                    </p>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <Badge variant="secondary" className="capitalize">
                        {template.category.replace(/_/g, " ")}
                      </Badge>
                      {template.supports_inbound && (
                        <Badge variant="outline">
                          <ArrowDownToLine className="h-3 w-3 mr-1" />
                          {t("integrations.inbound")}
                        </Badge>
                      )}
                      {template.supports_outbound && (
                        <Badge variant="outline">
                          <ArrowUpFromLine className="h-3 w-3 mr-1" />
                          {t("integrations.outbound")}
                        </Badge>
                      )}
                      {template.supports_webhook && (
                        <Badge variant="outline">
                          <Webhook className="h-3 w-3 mr-1" />
                          {t("integrations.webhook")}
                        </Badge>
                      )}
                    </div>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => handleSelectTemplate(template)}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      {t("integrations.configure")}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Sync Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          {/* Integration Selector */}
          <div className="flex gap-4">
            <Select
              value={selectedIntegration?.id || ""}
              onValueChange={(id) => {
                const integration = integrationsData?.items?.find((i) => i.id === id);
                setSelectedIntegration(integration || null);
              }}
            >
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder={t("integrations.selectIntegration")} />
              </SelectTrigger>
              <SelectContent>
                {integrationsData?.items?.map((integration) => (
                  <SelectItem key={integration.id} value={integration.id}>
                    {integration.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Logs List */}
          <div className="space-y-3">
            {!selectedIntegration && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("integrations.selectIntegrationToViewLogs")}</p>
                </CardContent>
              </Card>
            )}
            {selectedIntegration && syncLogsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("integrations.noSyncLogs")}</p>
                </CardContent>
              </Card>
            )}
            {syncLogsData?.items?.map((log) => (
              <Card key={log.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {log.status === "success" ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : log.status === "failed" ? (
                        <XCircle className="h-5 w-5 text-destructive" />
                      ) : (
                        <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium capitalize">{log.sync_type || "sync"}</span>
                          <Badge variant={log.status === "success" ? "default" : "destructive"}>
                            {log.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {new Date(log.started_at).toLocaleString()}
                          {log.duration_seconds && ` (${log.duration_seconds}s)`}
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <p>
                        <span className="text-muted-foreground">{t("integrations.fetched")}</span> {log.records_fetched}
                      </p>
                      <p>
                        <span className="text-muted-foreground">{t("integrations.created")}</span> {log.records_created}
                        <span className="mx-1">|</span>
                        <span className="text-muted-foreground">{t("integrations.updated")}</span> {log.records_updated}
                      </p>
                      {log.records_failed > 0 && (
                        <p className="text-destructive">{t("integrations.failedLabel")} {log.records_failed}</p>
                      )}
                    </div>
                  </div>
                  {log.error_message && (
                    <p className="text-sm text-destructive mt-2 bg-destructive/10 p-2 rounded">
                      {log.error_message}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

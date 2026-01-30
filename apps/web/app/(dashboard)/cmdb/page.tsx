"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Server,
  Package,
  Key,
  GitBranch,
  History,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Box,
  Database,
  Cloud,
  Monitor,
  HardDrive,
  Cpu,
} from "lucide-react";
import { cmdbAPI, vulnerabilitiesAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

// Types
interface CMDBStats {
  total_cis: number;
  total_assets: number;
  total_software: number;
  total_licenses: number;
  total_relationships: number;
  expiring_licenses: number;
  warranty_expiring: number;
  cis_by_type: Record<string, number>;
  cis_by_status: Record<string, number>;
  assets_by_type: Record<string, number>;
}

interface ConfigurationItem {
  id: string;
  ci_id: string;
  name: string;
  ci_type: string;
  status: string;
  environment: string;
  department: string;
  business_service: string;
  owner: string;
  version: string;
  created_at: string;
  updated_at: string;
}

interface ConfigurationItemList {
  items: ConfigurationItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface SoftwareItem {
  id: string;
  name: string;
  vendor: string;
  category: string;
  latest_version: string;
  is_approved: boolean;
  is_prohibited: boolean;
  security_rating: number;
  installation_count?: number;
  end_of_life_date?: string;
  created_at: string;
}

interface SoftwareItemList {
  items: SoftwareItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const tabs = [
  { id: "dashboard", icon: Server, labelKey: "cmdb.dashboard" },
  { id: "config-items", icon: Box, labelKey: "cmdb.configItems" },
  { id: "software", icon: Package, labelKey: "cmdb.software" },
  { id: "licenses", icon: Key, labelKey: "cmdb.licenses" },
  { id: "changes", icon: History, labelKey: "cmdb.changes" },
];

const ciTypeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  application: Package,
  service: Server,
  database: Database,
  server: Cpu,
  network_device: GitBranch,
  storage: HardDrive,
  container: Box,
  virtual_machine: Monitor,
  cloud_service: Cloud,
  endpoint: Monitor,
};

export default function CMDBPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [search, setSearch] = useState("");
  const [ciTypeFilter, setCITypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [isAddCIOpen, setIsAddCIOpen] = useState(false);
  const [isAddSoftwareOpen, setIsAddSoftwareOpen] = useState(false);

  // Form states
  const [ciForm, setCIForm] = useState({
    name: "",
    ci_type: "",
    environment: "",
    description: "",
  });
  const [softwareForm, setSoftwareForm] = useState({
    name: "",
    vendor: "",
    category: "",
    latest_version: "",
  });

  const queryClient = useQueryClient();

  // Stats query
  const { data: stats } = useQuery<CMDBStats>({
    queryKey: ["cmdb-stats"],
    queryFn: () => cmdbAPI.getStats(token!) as Promise<CMDBStats>,
    enabled: !!token,
  });

  // Configuration Items query
  const { data: ciList, isLoading: ciLoading } = useQuery<ConfigurationItemList>({
    queryKey: ["cmdb-cis", search, ciTypeFilter, statusFilter],
    queryFn: () =>
      cmdbAPI.listCIs(token!, {
        search: search || undefined,
        ci_type: ciTypeFilter !== "all" ? ciTypeFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      }) as Promise<ConfigurationItemList>,
    enabled: !!token && activeTab === "config-items",
  });

  // Software query
  const { data: softwareList, isLoading: softwareLoading } = useQuery<SoftwareItemList>({
    queryKey: ["cmdb-software", search, categoryFilter],
    queryFn: () =>
      cmdbAPI.listSoftware(token!, {
        search: search || undefined,
        category: categoryFilter !== "all" ? categoryFilter : undefined,
      }) as Promise<SoftwareItemList>,
    enabled: !!token && activeTab === "software",
  });

  // Assets query for relationships
  const { data: assetList } = useQuery({
    queryKey: ["assets-list"],
    queryFn: () => vulnerabilitiesAPI.listAssets(token!, { page_size: 100 }),
    enabled: !!token,
  });

  // Create CI mutation
  const createCIMutation = useMutation({
    mutationFn: (data: typeof ciForm) => cmdbAPI.createCI(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cmdb-cis"] });
      queryClient.invalidateQueries({ queryKey: ["cmdb-stats"] });
      setIsAddCIOpen(false);
      setCIForm({ name: "", ci_type: "", environment: "", description: "" });
    },
  });

  // Create Software mutation
  const createSoftwareMutation = useMutation({
    mutationFn: (data: typeof softwareForm) => cmdbAPI.createSoftware(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cmdb-software"] });
      queryClient.invalidateQueries({ queryKey: ["cmdb-stats"] });
      setIsAddSoftwareOpen(false);
      setSoftwareForm({ name: "", vendor: "", category: "", latest_version: "" });
    },
  });

  const handleCreateCI = () => {
    if (!ciForm.name || !ciForm.ci_type) return;
    createCIMutation.mutate(ciForm);
  };

  const handleCreateSoftware = () => {
    if (!softwareForm.name || !softwareForm.vendor || !softwareForm.category) return;
    createSoftwareMutation.mutate(softwareForm);
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      production: "default",
      development: "secondary",
      testing: "outline",
      staging: "outline",
      planned: "secondary",
      maintenance: "destructive",
      retired: "destructive",
      decommissioned: "destructive",
    };
    return <Badge variant={variants[status] || "default"}>{status}</Badge>;
  };

  const getCITypeIcon = (type: string) => {
    const Icon = ciTypeIcons[type] || Box;
    return <Icon className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{t("cmdb.title")}</h1>
          <p className="text-muted-foreground">
            Manage configuration items, software, and asset relationships
          </p>
        </div>
        <div className="flex gap-2">
          {activeTab === "config-items" && (
            <Dialog open={isAddCIOpen} onOpenChange={setIsAddCIOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("cmdb.addCI")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>{t("cmdb.addCI")}</DialogTitle>
                  <DialogDescription>
                    Create a new configuration item in the CMDB
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="ci-name">Name</Label>
                    <Input
                      id="ci-name"
                      placeholder="Enter CI name"
                      value={ciForm.name}
                      onChange={(e) => setCIForm({ ...ciForm, name: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ci-type">Type</Label>
                    <Select
                      value={ciForm.ci_type}
                      onValueChange={(value) => setCIForm({ ...ciForm, ci_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="application">{t("cmdb.application")}</SelectItem>
                        <SelectItem value="service">{t("cmdb.service")}</SelectItem>
                        <SelectItem value="database">{t("cmdb.database")}</SelectItem>
                        <SelectItem value="server">{t("cmdb.server")}</SelectItem>
                        <SelectItem value="container">{t("cmdb.container")}</SelectItem>
                        <SelectItem value="virtual_machine">{t("cmdb.virtual_machine")}</SelectItem>
                        <SelectItem value="cloud_service">{t("cmdb.cloud_service")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ci-env">Environment</Label>
                    <Select
                      value={ciForm.environment}
                      onValueChange={(value) => setCIForm({ ...ciForm, environment: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select environment" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="development">{t("cmdb.development")}</SelectItem>
                        <SelectItem value="testing">{t("cmdb.testing")}</SelectItem>
                        <SelectItem value="staging">{t("cmdb.staging")}</SelectItem>
                        <SelectItem value="production">{t("cmdb.production")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ci-desc">Description</Label>
                    <Textarea
                      id="ci-desc"
                      placeholder="Enter description"
                      value={ciForm.description}
                      onChange={(e) => setCIForm({ ...ciForm, description: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddCIOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                  <Button
                    onClick={handleCreateCI}
                    disabled={createCIMutation.isPending || !ciForm.name || !ciForm.ci_type}
                  >
                    {createCIMutation.isPending ? t("common.saving") : t("common.save")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          {activeTab === "software" && (
            <Dialog open={isAddSoftwareOpen} onOpenChange={setIsAddSoftwareOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("cmdb.addSoftware")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>{t("cmdb.addSoftware")}</DialogTitle>
                  <DialogDescription>
                    Add a new software item to the catalog
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="sw-name">Name</Label>
                    <Input
                      id="sw-name"
                      placeholder="Enter software name"
                      value={softwareForm.name}
                      onChange={(e) => setSoftwareForm({ ...softwareForm, name: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="sw-vendor">Vendor</Label>
                    <Input
                      id="sw-vendor"
                      placeholder="Enter vendor"
                      value={softwareForm.vendor}
                      onChange={(e) => setSoftwareForm({ ...softwareForm, vendor: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="sw-category">Category</Label>
                    <Select
                      value={softwareForm.category}
                      onValueChange={(value) => setSoftwareForm({ ...softwareForm, category: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="os">{t("cmdb.os")}</SelectItem>
                        <SelectItem value="database">{t("cmdb.database")}</SelectItem>
                        <SelectItem value="security">{t("cmdb.securitySoftware")}</SelectItem>
                        <SelectItem value="productivity">{t("cmdb.productivity")}</SelectItem>
                        <SelectItem value="development">{t("cmdb.developmentSoftware")}</SelectItem>
                        <SelectItem value="monitoring">{t("cmdb.monitoring")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="sw-version">Latest Version</Label>
                    <Input
                      id="sw-version"
                      placeholder="e.g., 1.0.0"
                      value={softwareForm.latest_version}
                      onChange={(e) => setSoftwareForm({ ...softwareForm, latest_version: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddSoftwareOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                  <Button
                    onClick={handleCreateSoftware}
                    disabled={createSoftwareMutation.isPending || !softwareForm.name || !softwareForm.vendor || !softwareForm.category}
                  >
                    {createSoftwareMutation.isPending ? t("common.saving") : t("common.save")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-2">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "default" : "ghost"}
            onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-2"
          >
            <tab.icon className="h-4 w-4" />
            {t(tab.labelKey)}
          </Button>
        ))}
      </div>

      {/* Dashboard Tab */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("cmdb.totalCIs")}
                </CardTitle>
                <Box className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_cis || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.cis_by_status?.production || 0} in production
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("cmdb.softwareItems")}
                </CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_software || 0}</div>
                <p className="text-xs text-muted-foreground">
                  In software catalog
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("cmdb.activeRelationships")}
                </CardTitle>
                <GitBranch className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_relationships || 0}</div>
                <p className="text-xs text-muted-foreground">
                  Asset dependencies
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("cmdb.expiringLicenses")}
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-yellow-500">
                  {stats?.expiring_licenses || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Within 90 days
                </p>
              </CardContent>
            </Card>
          </div>

          {/* CIs by Type */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Configuration Items by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stats?.cis_by_type && Object.entries(stats.cis_by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getCITypeIcon(type)}
                        <span className="capitalize">{type.replace(/_/g, " ")}</span>
                      </div>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
                  {(!stats?.cis_by_type || Object.keys(stats.cis_by_type).length === 0) && (
                    <p className="text-muted-foreground text-sm">No configuration items yet</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Configuration Items by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stats?.cis_by_status && Object.entries(stats.cis_by_status).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <span className="capitalize">{status.replace(/_/g, " ")}</span>
                      {getStatusBadge(status)}
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                  {(!stats?.cis_by_status || Object.keys(stats.cis_by_status).length === 0) && (
                    <p className="text-muted-foreground text-sm">No configuration items yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Assets Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Assets by Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {stats?.assets_by_type && Object.entries(stats.assets_by_type).map(([type, count]) => (
                  <div key={type} className="text-center p-4 border rounded-lg">
                    {getCITypeIcon(type)}
                    <div className="text-2xl font-bold mt-2">{count}</div>
                    <div className="text-xs text-muted-foreground capitalize">
                      {type.replace(/_/g, " ")}
                    </div>
                  </div>
                ))}
                {(!stats?.assets_by_type || Object.keys(stats.assets_by_type).length === 0) && (
                  <p className="text-muted-foreground text-sm col-span-full">No assets yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Configuration Items Tab */}
      {activeTab === "config-items" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search configuration items..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={ciTypeFilter} onValueChange={setCITypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="application">{t("cmdb.application")}</SelectItem>
                <SelectItem value="service">{t("cmdb.service")}</SelectItem>
                <SelectItem value="database">{t("cmdb.database")}</SelectItem>
                <SelectItem value="server">{t("cmdb.server")}</SelectItem>
                <SelectItem value="container">{t("cmdb.container")}</SelectItem>
                <SelectItem value="virtual_machine">{t("cmdb.virtual_machine")}</SelectItem>
                <SelectItem value="cloud_service">{t("cmdb.cloud_service")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="production">{t("cmdb.production")}</SelectItem>
                <SelectItem value="development">{t("cmdb.development")}</SelectItem>
                <SelectItem value="testing">{t("cmdb.testing")}</SelectItem>
                <SelectItem value="staging">{t("cmdb.staging")}</SelectItem>
                <SelectItem value="maintenance">{t("cmdb.maintenance")}</SelectItem>
                <SelectItem value="retired">{t("cmdb.retired")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CI ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Environment</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ciLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      {t("common.loading")}
                    </TableCell>
                  </TableRow>
                ) : ciList?.items && ciList.items.length > 0 ? (
                  ciList.items.map((ci) => (
                    <TableRow key={ci.id}>
                      <TableCell className="font-mono text-sm">{ci.ci_id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getCITypeIcon(ci.ci_type)}
                          <span className="font-medium">{ci.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">
                        {ci.ci_type.replace(/_/g, " ")}
                      </TableCell>
                      <TableCell>{getStatusBadge(ci.status)}</TableCell>
                      <TableCell>{ci.environment || "-"}</TableCell>
                      <TableCell>{ci.owner || "-"}</TableCell>
                      <TableCell>{ci.version || "1.0"}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>{t("common.view")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("common.edit")}</DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">
                              {t("common.delete")}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {t("cmdb.noCIs")}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}

      {/* Software Tab */}
      {activeTab === "software" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search software..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="os">{t("cmdb.os")}</SelectItem>
                <SelectItem value="database">{t("cmdb.database")}</SelectItem>
                <SelectItem value="security">{t("cmdb.securitySoftware")}</SelectItem>
                <SelectItem value="productivity">{t("cmdb.productivity")}</SelectItem>
                <SelectItem value="development">{t("cmdb.developmentSoftware")}</SelectItem>
                <SelectItem value="monitoring">{t("cmdb.monitoring")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Latest Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Security Rating</TableHead>
                  <TableHead>Installations</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {softwareLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      {t("common.loading")}
                    </TableCell>
                  </TableRow>
                ) : softwareList?.items && softwareList.items.length > 0 ? (
                  softwareList.items.map((sw) => (
                    <TableRow key={sw.id}>
                      <TableCell className="font-medium">{sw.name}</TableCell>
                      <TableCell>{sw.vendor}</TableCell>
                      <TableCell className="capitalize">
                        {sw.category.replace(/_/g, " ")}
                      </TableCell>
                      <TableCell>{sw.latest_version || "-"}</TableCell>
                      <TableCell>
                        {sw.is_prohibited ? (
                          <Badge variant="destructive">
                            <XCircle className="h-3 w-3 mr-1" />
                            Prohibited
                          </Badge>
                        ) : sw.is_approved ? (
                          <Badge variant="default">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Approved
                          </Badge>
                        ) : (
                          <Badge variant="secondary">
                            <Clock className="h-3 w-3 mr-1" />
                            Pending
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {sw.security_rating ? (
                          <div className="flex items-center gap-1">
                            <span>{sw.security_rating}/10</span>
                          </div>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>{sw.installation_count || 0}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>{t("common.view")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("common.edit")}</DropdownMenuItem>
                            <DropdownMenuItem>Approve</DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">
                              Mark Prohibited
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {t("cmdb.noSoftware")}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}

      {/* Licenses Tab */}
      {activeTab === "licenses" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("cmdb.licenses")}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{t("cmdb.noLicenses")}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Changes Tab */}
      {activeTab === "changes" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("cmdb.changes")}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{t("cmdb.noChanges")}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

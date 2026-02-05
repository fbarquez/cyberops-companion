"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Route,
  Plus,
  Shield,
  AlertTriangle,
  Target,
  BarChart3,
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  RefreshCw,
  Network,
  Crown,
  MapPin,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { attackPathsAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

// Types
interface DashboardStats {
  total_graphs: number;
  total_paths: number;
  critical_paths: number;
  high_risk_paths: number;
  entry_points_count: number;
  crown_jewels_count: number;
  top_chokepoints: ChokepointInfo[];
  recent_simulations: unknown[];
  risk_distribution: Record<string, number>;
  paths_by_status: Record<string, number>;
}

interface ChokepointInfo {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  paths_affected: number;
  total_risk_mitigated: number;
  priority_score: number;
  vulnerabilities_count: number;
  recommendations: string[];
}

interface AttackGraph {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  scope_type: string;
  scope_filter: Record<string, unknown> | null;
  nodes: unknown[];
  edges: unknown[];
  total_nodes: number;
  total_edges: number;
  entry_points_count: number;
  crown_jewels_count: number;
  status: string;
  computed_at: string | null;
  created_at: string;
  updated_at: string | null;
}

interface AttackPath {
  id: string;
  graph_id: string;
  path_id: string;
  name: string;
  entry_point_name: string;
  target_name: string;
  target_criticality: string;
  hop_count: number;
  risk_score: number;
  exploitability_score: number;
  impact_score: number;
  exploitable_vulns: number;
  status: string;
  created_at: string;
}

interface CrownJewel {
  id: string;
  asset_id: string;
  asset_name: string | null;
  asset_type: string | null;
  jewel_type: string;
  business_impact: string;
  description: string;
  business_owner: string;
  is_active: boolean;
  created_at: string;
}

interface EntryPoint {
  id: string;
  asset_id: string;
  asset_name: string | null;
  asset_type: string | null;
  entry_type: string;
  exposure_level: string;
  authentication_required: boolean;
  mfa_enabled: boolean;
  description: string;
  known_vulnerabilities: number;
  is_active: boolean;
  created_at: string;
}

interface GraphListResponse {
  graphs: AttackGraph[];
  total: number;
  page: number;
  page_size: number;
}

interface ChokepointListResponse {
  chokepoints: ChokepointInfo[];
  total: number;
}

const SCOPE_TYPES = ["full", "zone", "custom"];
const JEWEL_TYPES = ["data", "system", "credential", "network", "identity"];
const BUSINESS_IMPACTS = ["critical", "high", "medium"];
const ENTRY_TYPES = ["internet_facing", "vpn_endpoint", "email_gateway", "remote_access", "partner_connection", "physical_access", "supply_chain"];
const EXPOSURE_LEVELS = ["public", "semi_public", "internal"];

export default function AttackPathsPage() {
  const router = useRouter();
  const { token } = useAuthStore();
  const { t } = useTranslations();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGraph, setSelectedGraph] = useState<AttackGraph | null>(null);
  const [isCreateGraphOpen, setIsCreateGraphOpen] = useState(false);
  const [isCreateJewelOpen, setIsCreateJewelOpen] = useState(false);
  const [isCreateEntryPointOpen, setIsCreateEntryPointOpen] = useState(false);

  // Form state for new graph
  const [newGraph, setNewGraph] = useState({
    name: "",
    description: "",
    scope_type: "full",
  });

  // Form state for new crown jewel
  const [newJewel, setNewJewel] = useState({
    asset_id: "",
    jewel_type: "system",
    business_impact: "high",
    description: "",
    business_owner: "",
  });

  // Form state for new entry point
  const [newEntryPoint, setNewEntryPoint] = useState({
    asset_id: "",
    entry_type: "internet_facing",
    exposure_level: "public",
    description: "",
    authentication_required: true,
    mfa_enabled: false,
  });

  // Queries
  const { data: dashboard, isLoading: dashboardLoading, refetch: refetchDashboard } = useQuery<DashboardStats>({
    queryKey: ["attack-paths", "dashboard"],
    queryFn: () => attackPathsAPI.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
  });

  const { data: chokepoints } = useQuery<ChokepointListResponse>({
    queryKey: ["attack-paths", "chokepoints"],
    queryFn: () => attackPathsAPI.getChokepoints(token!, 10) as Promise<ChokepointListResponse>,
    enabled: !!token && activeTab === "dashboard",
  });

  const { data: graphsData, isLoading: graphsLoading, refetch: refetchGraphs } = useQuery<GraphListResponse>({
    queryKey: ["attack-paths", "graphs"],
    queryFn: () => attackPathsAPI.listGraphs(token!) as Promise<GraphListResponse>,
    enabled: !!token,
  });

  const { data: crownJewelsData, isLoading: jewelsLoading } = useQuery<{ crown_jewels: CrownJewel[]; total: number }>({
    queryKey: ["attack-paths", "crown-jewels"],
    queryFn: () => attackPathsAPI.listCrownJewels(token!) as Promise<{ crown_jewels: CrownJewel[]; total: number }>,
    enabled: !!token && activeTab === "crown-jewels",
  });

  const { data: entryPointsData, isLoading: entryPointsLoading } = useQuery<{ entry_points: EntryPoint[]; total: number }>({
    queryKey: ["attack-paths", "entry-points"],
    queryFn: () => attackPathsAPI.listEntryPoints(token!) as Promise<{ entry_points: EntryPoint[]; total: number }>,
    enabled: !!token && activeTab === "entry-points",
  });

  // Mutations
  const createGraphMutation = useMutation({
    mutationFn: (data: typeof newGraph) => attackPathsAPI.createGraph(token!, {
      name: data.name,
      description: data.description || undefined,
      scope_type: data.scope_type,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths"] });
      setIsCreateGraphOpen(false);
      setNewGraph({ name: "", description: "", scope_type: "full" });
    },
  });

  const deleteGraphMutation = useMutation({
    mutationFn: (id: string) => attackPathsAPI.deleteGraph(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths"] });
    },
  });

  const refreshGraphMutation = useMutation({
    mutationFn: (id: string) => attackPathsAPI.refreshGraph(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths"] });
    },
  });

  const createJewelMutation = useMutation({
    mutationFn: (data: typeof newJewel) => attackPathsAPI.createCrownJewel(token!, {
      asset_id: data.asset_id,
      jewel_type: data.jewel_type,
      business_impact: data.business_impact,
      description: data.description,
      business_owner: data.business_owner,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "crown-jewels"] });
      setIsCreateJewelOpen(false);
      setNewJewel({ asset_id: "", jewel_type: "system", business_impact: "high", description: "", business_owner: "" });
    },
  });

  const deleteJewelMutation = useMutation({
    mutationFn: (id: string) => attackPathsAPI.deleteCrownJewel(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "crown-jewels"] });
    },
  });

  const createEntryPointMutation = useMutation({
    mutationFn: (data: typeof newEntryPoint) => attackPathsAPI.createEntryPoint(token!, {
      asset_id: data.asset_id,
      entry_type: data.entry_type,
      exposure_level: data.exposure_level,
      description: data.description,
      authentication_required: data.authentication_required,
      mfa_enabled: data.mfa_enabled,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "entry-points"] });
      setIsCreateEntryPointOpen(false);
      setNewEntryPoint({ asset_id: "", entry_type: "internet_facing", exposure_level: "public", description: "", authentication_required: true, mfa_enabled: false });
    },
  });

  const deleteEntryPointMutation = useMutation({
    mutationFn: (id: string) => attackPathsAPI.deleteEntryPoint(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "entry-points"] });
    },
  });

  const getRiskLevelColor = (score: number) => {
    if (score >= 8) return "bg-red-500 text-white";
    if (score >= 6) return "bg-orange-500 text-white";
    if (score >= 4) return "bg-yellow-500 text-black";
    return "bg-green-500 text-white";
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "ready": return "bg-green-100 text-green-800";
      case "computing": return "bg-blue-100 text-blue-800";
      case "stale": return "bg-yellow-100 text-yellow-800";
      case "error": return "bg-red-100 text-red-800";
      case "active": return "bg-blue-100 text-blue-800";
      case "mitigated": return "bg-green-100 text-green-800";
      case "accepted": return "bg-gray-100 text-gray-800";
      case "false_positive": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getBusinessImpactColor = (impact: string) => {
    switch (impact?.toLowerCase()) {
      case "critical": return "bg-red-500 text-white";
      case "high": return "bg-orange-500 text-white";
      case "medium": return "bg-yellow-500 text-black";
      default: return "bg-gray-500 text-white";
    }
  };

  const getExposureColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "public": return "bg-red-100 text-red-800";
      case "semi_public": return "bg-yellow-100 text-yellow-800";
      case "internal": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const formatLabel = (str: string) => {
    return str?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) || "-";
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Attack Path Analysis"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetchDashboard()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={isCreateGraphOpen} onOpenChange={setIsCreateGraphOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Graph
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Attack Graph</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label>Name</Label>
                    <Input
                      value={newGraph.name}
                      onChange={(e) => setNewGraph({ ...newGraph, name: e.target.value })}
                      placeholder="e.g., Production Environment Graph"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Description</Label>
                    <Textarea
                      value={newGraph.description}
                      onChange={(e) => setNewGraph({ ...newGraph, description: e.target.value })}
                      placeholder="Describe the scope and purpose of this graph"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Scope Type</Label>
                    <Select
                      value={newGraph.scope_type}
                      onValueChange={(value) => setNewGraph({ ...newGraph, scope_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SCOPE_TYPES.map((type) => (
                          <SelectItem key={type} value={type}>
                            {formatLabel(type)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={() => createGraphMutation.mutate(newGraph)}
                    disabled={!newGraph.name || createGraphMutation.isPending}
                  >
                    {createGraphMutation.isPending ? "Creating..." : "Create Graph"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 space-y-4 md:space-y-6 overflow-y-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="dashboard">
              <BarChart3 className="h-4 w-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="graphs">
              <Network className="h-4 w-4 mr-2" />
              Graphs
            </TabsTrigger>
            <TabsTrigger value="crown-jewels">
              <Crown className="h-4 w-4 mr-2" />
              Crown Jewels
            </TabsTrigger>
            <TabsTrigger value="entry-points">
              <MapPin className="h-4 w-4 mr-2" />
              Entry Points
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Attack Graphs</CardTitle>
                  <Network className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.total_graphs || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    Computed graphs
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Attack Paths</CardTitle>
                  <Route className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.total_paths || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    <span className="text-red-600 font-medium">{dashboard?.critical_paths || 0}</span> critical
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Crown Jewels</CardTitle>
                  <Crown className="h-4 w-4 text-yellow-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.crown_jewels_count || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    Critical assets
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Entry Points</CardTitle>
                  <MapPin className="h-4 w-4 text-red-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboard?.entry_points_count || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    Attack surfaces
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Risk Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Risk Distribution</CardTitle>
                  <CardDescription>Paths by risk level</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {["critical", "high", "medium", "low"].map((level) => {
                      const count = dashboard?.risk_distribution?.[level] || 0;
                      const total = dashboard?.total_paths || 1;
                      return (
                        <div key={level} className="flex items-center justify-between">
                          <Badge className={getRiskLevelColor(
                            level === "critical" ? 9 : level === "high" ? 7 : level === "medium" ? 5 : 2
                          )}>
                            {formatLabel(level)}
                          </Badge>
                          <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div
                                className={cn(
                                  "h-2 rounded-full",
                                  level === "critical" ? "bg-red-500" :
                                  level === "high" ? "bg-orange-500" :
                                  level === "medium" ? "bg-yellow-500" : "bg-green-500"
                                )}
                                style={{ width: `${(count / total) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium w-8 text-right">{count}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Paths by Status</CardTitle>
                  <CardDescription>Current remediation status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {["active", "mitigated", "accepted", "false_positive"].map((status) => {
                      const count = dashboard?.paths_by_status?.[status] || 0;
                      return (
                        <div key={status} className="flex items-center justify-between">
                          <Badge variant="outline" className={getStatusColor(status)}>
                            {formatLabel(status)}
                          </Badge>
                          <span className="text-sm font-medium">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Top Chokepoints */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  Top Chokepoints
                </CardTitle>
                <CardDescription>
                  Assets appearing in multiple attack paths - prioritize remediation here for maximum impact
                </CardDescription>
              </CardHeader>
              <CardContent>
                {chokepoints?.chokepoints && chokepoints.chokepoints.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Asset</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Paths Affected</TableHead>
                        <TableHead>Vulnerabilities</TableHead>
                        <TableHead>Priority Score</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {chokepoints.chokepoints.map((cp) => (
                        <TableRow key={cp.asset_id}>
                          <TableCell className="font-medium">{cp.asset_name}</TableCell>
                          <TableCell className="capitalize">{cp.asset_type}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{cp.paths_affected}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={cp.vulnerabilities_count > 0 ? "destructive" : "secondary"}>
                              {cp.vulnerabilities_count}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className={cn(
                                    "h-2 rounded-full",
                                    cp.priority_score >= 8 ? "bg-red-500" :
                                    cp.priority_score >= 5 ? "bg-orange-500" : "bg-yellow-500"
                                  )}
                                  style={{ width: `${(cp.priority_score / 10) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm">{cp.priority_score.toFixed(1)}</span>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No chokepoints identified yet. Create an attack graph to analyze chokepoints.
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Graphs Tab */}
          <TabsContent value="graphs" className="space-y-4">
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Scope</TableHead>
                      <TableHead>Nodes</TableHead>
                      <TableHead>Paths</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Computed</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {graphsLoading ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          Loading...
                        </TableCell>
                      </TableRow>
                    ) : graphsData?.graphs?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          No attack graphs found. Create one to start analyzing attack paths.
                        </TableCell>
                      </TableRow>
                    ) : (
                      graphsData?.graphs?.map((graph) => (
                        <TableRow key={graph.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{graph.name}</div>
                              {graph.description && (
                                <div className="text-sm text-muted-foreground truncate max-w-[250px]">
                                  {graph.description}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="capitalize">{graph.scope_type}</TableCell>
                          <TableCell>{graph.total_nodes}</TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {graph.entry_points_count} entry / {graph.crown_jewels_count} target
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={getStatusColor(graph.status)}>
                              {formatLabel(graph.status)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {graph.computed_at ? new Date(graph.computed_at).toLocaleDateString() : "-"}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => router.push(`/attack-paths/graphs/${graph.id}`)}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  View Paths
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => refreshGraphMutation.mutate(graph.id)}
                                  disabled={refreshGraphMutation.isPending}
                                >
                                  <RefreshCw className="h-4 w-4 mr-2" />
                                  Refresh Graph
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => deleteGraphMutation.mutate(graph.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Crown Jewels Tab */}
          <TabsContent value="crown-jewels" className="space-y-4">
            <div className="flex justify-end">
              <Dialog open={isCreateJewelOpen} onOpenChange={setIsCreateJewelOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Crown Jewel
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Designate Crown Jewel</DialogTitle>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label>Asset ID (from CMDB)</Label>
                      <Input
                        value={newJewel.asset_id}
                        onChange={(e) => setNewJewel({ ...newJewel, asset_id: e.target.value })}
                        placeholder="e.g., asset-uuid-here"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Type</Label>
                        <Select
                          value={newJewel.jewel_type}
                          onValueChange={(value) => setNewJewel({ ...newJewel, jewel_type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {JEWEL_TYPES.map((type) => (
                              <SelectItem key={type} value={type}>
                                {formatLabel(type)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid gap-2">
                        <Label>Business Impact</Label>
                        <Select
                          value={newJewel.business_impact}
                          onValueChange={(value) => setNewJewel({ ...newJewel, business_impact: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {BUSINESS_IMPACTS.map((impact) => (
                              <SelectItem key={impact} value={impact}>
                                {formatLabel(impact)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <Label>Business Owner</Label>
                      <Input
                        value={newJewel.business_owner}
                        onChange={(e) => setNewJewel({ ...newJewel, business_owner: e.target.value })}
                        placeholder="e.g., John Smith"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label>Description</Label>
                      <Textarea
                        value={newJewel.description}
                        onChange={(e) => setNewJewel({ ...newJewel, description: e.target.value })}
                        placeholder="Why is this a crown jewel? What data/services does it protect?"
                      />
                    </div>
                    <Button
                      onClick={() => createJewelMutation.mutate(newJewel)}
                      disabled={!newJewel.asset_id || !newJewel.description || !newJewel.business_owner || createJewelMutation.isPending}
                    >
                      {createJewelMutation.isPending ? "Creating..." : "Create Crown Jewel"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Business Impact</TableHead>
                      <TableHead>Owner</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jewelsLoading ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8">
                          Loading...
                        </TableCell>
                      </TableRow>
                    ) : crownJewelsData?.crown_jewels?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No crown jewels designated. Add critical assets that need protection.
                        </TableCell>
                      </TableRow>
                    ) : (
                      crownJewelsData?.crown_jewels?.map((jewel) => (
                        <TableRow key={jewel.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{jewel.asset_name || jewel.asset_id}</div>
                              <div className="text-sm text-muted-foreground truncate max-w-[250px]">
                                {jewel.description}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{formatLabel(jewel.jewel_type)}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={getBusinessImpactColor(jewel.business_impact)}>
                              {formatLabel(jewel.business_impact)}
                            </Badge>
                          </TableCell>
                          <TableCell>{jewel.business_owner}</TableCell>
                          <TableCell>
                            {jewel.is_active ? (
                              <Badge className="bg-green-100 text-green-800">Active</Badge>
                            ) : (
                              <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => deleteJewelMutation.mutate(jewel.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Entry Points Tab */}
          <TabsContent value="entry-points" className="space-y-4">
            <div className="flex justify-end">
              <Dialog open={isCreateEntryPointOpen} onOpenChange={setIsCreateEntryPointOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Entry Point
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Designate Entry Point</DialogTitle>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label>Asset ID (from CMDB)</Label>
                      <Input
                        value={newEntryPoint.asset_id}
                        onChange={(e) => setNewEntryPoint({ ...newEntryPoint, asset_id: e.target.value })}
                        placeholder="e.g., asset-uuid-here"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Entry Type</Label>
                        <Select
                          value={newEntryPoint.entry_type}
                          onValueChange={(value) => setNewEntryPoint({ ...newEntryPoint, entry_type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {ENTRY_TYPES.map((type) => (
                              <SelectItem key={type} value={type}>
                                {formatLabel(type)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid gap-2">
                        <Label>Exposure Level</Label>
                        <Select
                          value={newEntryPoint.exposure_level}
                          onValueChange={(value) => setNewEntryPoint({ ...newEntryPoint, exposure_level: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {EXPOSURE_LEVELS.map((level) => (
                              <SelectItem key={level} value={level}>
                                {formatLabel(level)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="auth_required"
                          checked={newEntryPoint.authentication_required}
                          onChange={(e) => setNewEntryPoint({ ...newEntryPoint, authentication_required: e.target.checked })}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="auth_required">Auth Required</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="mfa_enabled"
                          checked={newEntryPoint.mfa_enabled}
                          onChange={(e) => setNewEntryPoint({ ...newEntryPoint, mfa_enabled: e.target.checked })}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="mfa_enabled">MFA Enabled</Label>
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <Label>Description</Label>
                      <Textarea
                        value={newEntryPoint.description}
                        onChange={(e) => setNewEntryPoint({ ...newEntryPoint, description: e.target.value })}
                        placeholder="Describe this entry point and its exposure"
                      />
                    </div>
                    <Button
                      onClick={() => createEntryPointMutation.mutate(newEntryPoint)}
                      disabled={!newEntryPoint.asset_id || !newEntryPoint.description || createEntryPointMutation.isPending}
                    >
                      {createEntryPointMutation.isPending ? "Creating..." : "Create Entry Point"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Exposure</TableHead>
                      <TableHead>Auth</TableHead>
                      <TableHead>Vulnerabilities</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entryPointsLoading ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          Loading...
                        </TableCell>
                      </TableRow>
                    ) : entryPointsData?.entry_points?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          No entry points designated. Add assets that could be initial attack vectors.
                        </TableCell>
                      </TableRow>
                    ) : (
                      entryPointsData?.entry_points?.map((point) => (
                        <TableRow key={point.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{point.asset_name || point.asset_id}</div>
                              <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                                {point.description}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{formatLabel(point.entry_type)}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={getExposureColor(point.exposure_level)}>
                              {formatLabel(point.exposure_level)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {point.authentication_required ? (
                                <CheckCircle className="h-4 w-4 text-green-500" title="Auth Required" />
                              ) : (
                                <XCircle className="h-4 w-4 text-red-500" title="No Auth" />
                              )}
                              {point.mfa_enabled ? (
                                <Shield className="h-4 w-4 text-green-500" title="MFA Enabled" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-yellow-500" title="No MFA" />
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={point.known_vulnerabilities > 0 ? "destructive" : "secondary"}>
                              {point.known_vulnerabilities}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {point.is_active ? (
                              <Badge className="bg-green-100 text-green-800">Active</Badge>
                            ) : (
                              <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => deleteEntryPointMutation.mutate(point.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Graph Detail Dialog */}
      {selectedGraph && (
        <Dialog open={!!selectedGraph} onOpenChange={() => setSelectedGraph(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedGraph.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge className={getStatusColor(selectedGraph.status)}>
                  {formatLabel(selectedGraph.status)}
                </Badge>
                <Badge variant="outline" className="capitalize">
                  {selectedGraph.scope_type} scope
                </Badge>
              </div>

              {selectedGraph.description && (
                <div>
                  <Label className="text-muted-foreground">Description</Label>
                  <p className="mt-1">{selectedGraph.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <Label className="text-muted-foreground">Nodes</Label>
                  <p className="text-lg font-semibold">{selectedGraph.total_nodes}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Edges</Label>
                  <p className="text-lg font-semibold">{selectedGraph.total_edges}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Entry Points</Label>
                  <p className="text-lg font-semibold">{selectedGraph.entry_points_count}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Crown Jewels</Label>
                  <p className="text-lg font-semibold">{selectedGraph.crown_jewels_count}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Created</Label>
                  <p>{new Date(selectedGraph.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Last Computed</Label>
                  <p>{selectedGraph.computed_at ? new Date(selectedGraph.computed_at).toLocaleString() : "Never"}</p>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

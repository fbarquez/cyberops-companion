"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  RefreshCw,
  Network,
  Route,
  Crown,
  MapPin,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Filter,
  MoreHorizontal,
  Eye,
  Shield,
  Zap,
  Clock,
  Target,
  ChevronDown,
  ChevronUp,
  Plus,
  PlayCircle,
  TrendingDown,
  Trash2,
  FlaskConical,
  Download,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { attackPathsAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import { AttackPathVisualization, AttackPathList } from "@/components/dashboard/attack-path-viz";

// Types
interface AttackGraph {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  scope_type: string;
  scope_filter: Record<string, unknown> | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  entry_points_count: number;
  crown_jewels_count: number;
  status: string;
  error_message: string | null;
  computed_at: string | null;
  computation_duration_ms: number | null;
  last_cmdb_sync: string | null;
  last_vuln_sync: string | null;
  is_stale: boolean;
  created_at: string;
  updated_at: string | null;
}

interface GraphNode {
  id: string;
  name: string;
  type: string;
  criticality: string | null;
  zone: string | null;
  vulnerabilities: Array<{ cve_id: string; severity: string }>;
  is_entry_point: boolean;
  is_crown_jewel: boolean;
  risk_score: number;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  direction: string;
  protocol: string | null;
  requires_auth: boolean;
  traversal_difficulty: number;
}

interface AttackPath {
  id: string;
  tenant_id: string;
  graph_id: string;
  path_id: string;
  name: string;
  entry_point_id: string;
  entry_point_name: string;
  entry_point_type: string;
  target_id: string;
  target_name: string;
  target_type: string;
  target_criticality: string;
  path_nodes: string[];
  path_edges: Array<{ source: string; target: string; type: string }>;
  hop_count: number;
  risk_score: number;
  exploitability_score: number;
  impact_score: number;
  vulns_in_path: Array<{ cve_id: string; severity: string; node_id: string }> | null;
  exploitable_vulns: number;
  chokepoints: Array<{ node_id: string; paths_affected: number }> | null;
  alternative_paths: number;
  status: string;
  mitigated_at: string | null;
  mitigated_by: string | null;
  created_at: string;
  updated_at: string | null;
}

interface PathListResponse {
  paths: AttackPath[];
  total: number;
  page: number;
  page_size: number;
}

interface Simulation {
  id: string;
  tenant_id: string;
  graph_id: string;
  name: string;
  description: string | null;
  simulation_type: string;
  parameters: Record<string, unknown>;
  original_paths_count: number | null;
  resulting_paths_count: number | null;
  paths_eliminated: number | null;
  risk_reduction_percent: number | null;
  affected_paths: string[] | null;
  new_risk_scores: Record<string, number> | null;
  recommendation: string | null;
  status: string;
  computed_at: string | null;
  created_at: string;
  created_by: string | null;
}

interface SimulationListResponse {
  simulations: Simulation[];
  total: number;
  page: number;
  page_size: number;
}

const PATH_STATUSES = ["active", "mitigated", "accepted", "false_positive"];
const SIMULATION_TYPES = [
  { value: "patch_vulnerability", label: "Patch Vulnerability", description: "Simulate patching specific CVEs" },
  { value: "segment_network", label: "Segment Network", description: "Simulate isolating an asset" },
  { value: "add_control", label: "Add Control", description: "Simulate adding security controls (MFA, firewall, etc.)" },
  { value: "compromise_asset", label: "Compromise Asset", description: "Simulate what happens if an asset is compromised" },
];
const CONTROL_TYPES = ["mfa", "firewall", "edr", "dlp", "encryption"];

export default function GraphDetailPage() {
  const params = useParams();
  const router = useRouter();
  const graphId = params.graphId as string;
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("paths");
  const [minRiskScore, setMinRiskScore] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedPath, setSelectedPath] = useState<AttackPath | null>(null);
  const [isStatusDialogOpen, setIsStatusDialogOpen] = useState(false);
  const [statusUpdateData, setStatusUpdateData] = useState({ status: "", reason: "" });
  const [expandedPathId, setExpandedPathId] = useState<string | null>(null);

  // Simulation state
  const [isSimulationDialogOpen, setIsSimulationDialogOpen] = useState(false);
  const [newSimulation, setNewSimulation] = useState({
    name: "",
    description: "",
    simulation_type: "add_control",
    parameters: {} as Record<string, unknown>,
  });

  // Queries
  const { data: graph, isLoading: graphLoading, refetch: refetchGraph } = useQuery<AttackGraph>({
    queryKey: ["attack-paths", "graphs", graphId],
    queryFn: () => attackPathsAPI.getGraph(token!, graphId) as Promise<AttackGraph>,
    enabled: !!token && !!graphId,
  });

  const { data: pathsData, isLoading: pathsLoading, refetch: refetchPaths } = useQuery<PathListResponse>({
    queryKey: ["attack-paths", "graphs", graphId, "paths", minRiskScore, statusFilter],
    queryFn: () => attackPathsAPI.listPaths(token!, graphId, {
      min_risk_score: minRiskScore > 0 ? minRiskScore : undefined,
      status: statusFilter || undefined,
      page_size: 50,
    }) as Promise<PathListResponse>,
    enabled: !!token && !!graphId,
  });

  const { data: simulationsData, isLoading: simulationsLoading, refetch: refetchSimulations } = useQuery<SimulationListResponse>({
    queryKey: ["attack-paths", "simulations", graphId],
    queryFn: () => attackPathsAPI.listSimulations(token!, { graph_id: graphId }) as Promise<SimulationListResponse>,
    enabled: !!token && !!graphId && activeTab === "simulations",
  });

  // Mutations
  const refreshGraphMutation = useMutation({
    mutationFn: () => attackPathsAPI.refreshGraph(token!, graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "graphs", graphId] });
      refetchPaths();
    },
  });

  const updatePathStatusMutation = useMutation({
    mutationFn: ({ pathId, data }: { pathId: string; data: { status: string; reason?: string } }) =>
      attackPathsAPI.updatePathStatus(token!, pathId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "graphs", graphId, "paths"] });
      setIsStatusDialogOpen(false);
      setSelectedPath(null);
      setStatusUpdateData({ status: "", reason: "" });
    },
  });

  const createSimulationMutation = useMutation({
    mutationFn: (data: typeof newSimulation) =>
      attackPathsAPI.createSimulation(token!, {
        name: data.name,
        description: data.description || undefined,
        graph_id: graphId,
        simulation_type: data.simulation_type,
        parameters: data.parameters,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "simulations", graphId] });
      setIsSimulationDialogOpen(false);
      setNewSimulation({
        name: "",
        description: "",
        simulation_type: "add_control",
        parameters: {},
      });
    },
  });

  const deleteSimulationMutation = useMutation({
    mutationFn: (id: string) => attackPathsAPI.deleteSimulation(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attack-paths", "simulations", graphId] });
    },
  });

  const [isExporting, setIsExporting] = useState(false);

  const handleExportPDF = async () => {
    if (!token || !graphId) return;

    setIsExporting(true);
    try {
      const blob = await attackPathsAPI.exportGraphReport(token, graphId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `attack-path-report-${graph?.name?.replace(/\s+/g, "-").toLowerCase() || graphId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  // Helpers
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

  const getRiskColor = (score: number) => {
    if (score >= 8) return "text-red-600";
    if (score >= 6) return "text-orange-600";
    if (score >= 4) return "text-yellow-600";
    return "text-green-600";
  };

  const getRiskBgColor = (score: number) => {
    if (score >= 8) return "bg-red-500 text-white";
    if (score >= 6) return "bg-orange-500 text-white";
    if (score >= 4) return "bg-yellow-500 text-black";
    return "bg-green-500 text-white";
  };

  const getCriticalityColor = (criticality: string) => {
    switch (criticality?.toLowerCase()) {
      case "critical": return "bg-red-500 text-white";
      case "high": return "bg-orange-500 text-white";
      case "medium": return "bg-yellow-500 text-black";
      case "low": return "bg-green-500 text-white";
      default: return "bg-gray-500 text-white";
    }
  };

  const formatLabel = (str: string) => {
    return str?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) || "-";
  };

  const getNodeById = (nodeId: string) => {
    return graph?.nodes?.find(n => n.id === nodeId);
  };

  const handleStatusUpdate = (path: AttackPath) => {
    setSelectedPath(path);
    setStatusUpdateData({ status: path.status, reason: "" });
    setIsStatusDialogOpen(true);
  };

  if (graphLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading graph...</div>
      </div>
    );
  }

  if (!graph) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <div className="text-muted-foreground">Graph not found</div>
        <Button variant="outline" onClick={() => router.push("/attack-paths")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Attack Paths
        </Button>
      </div>
    );
  }

  // Calculate stats from paths
  const criticalPaths = pathsData?.paths?.filter(p => p.risk_score >= 8).length || 0;
  const highRiskPaths = pathsData?.paths?.filter(p => p.risk_score >= 6 && p.risk_score < 8).length || 0;
  const activePaths = pathsData?.paths?.filter(p => p.status === "active").length || 0;

  return (
    <div className="flex flex-col h-full">
      <Header
        title={graph.name}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => router.push("/attack-paths")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportPDF}
              disabled={isExporting}
            >
              <Download className={cn("h-4 w-4 mr-2", isExporting && "animate-pulse")} />
              {isExporting ? "Exporting..." : "Export PDF"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refreshGraphMutation.mutate()}
              disabled={refreshGraphMutation.isPending}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", refreshGraphMutation.isPending && "animate-spin")} />
              Refresh Graph
            </Button>
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 space-y-6 overflow-y-auto">
        {/* Graph Info Card */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className={getStatusColor(graph.status)}>
                    {formatLabel(graph.status)}
                  </Badge>
                  {graph.is_stale && (
                    <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                      <Clock className="h-3 w-3 mr-1" />
                      Stale
                    </Badge>
                  )}
                  <Badge variant="outline">{formatLabel(graph.scope_type)} scope</Badge>
                </div>
                {graph.description && (
                  <p className="text-sm text-muted-foreground max-w-xl">{graph.description}</p>
                )}
                {graph.error_message && (
                  <p className="text-sm text-red-500">{graph.error_message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{graph.total_nodes}</div>
                  <div className="text-xs text-muted-foreground">Nodes</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{graph.total_edges}</div>
                  <div className="text-xs text-muted-foreground">Edges</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{graph.entry_points_count}</div>
                  <div className="text-xs text-muted-foreground">Entry Points</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">{graph.crown_jewels_count}</div>
                  <div className="text-xs text-muted-foreground">Crown Jewels</div>
                </div>
              </div>
            </div>

            {graph.computed_at && (
              <div className="mt-4 pt-4 border-t text-xs text-muted-foreground flex gap-4">
                <span>Computed: {new Date(graph.computed_at).toLocaleString()}</span>
                {graph.computation_duration_ms && (
                  <span>Duration: {(graph.computation_duration_ms / 1000).toFixed(2)}s</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Path Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Paths</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{pathsData?.total || 0}</div>
              <p className="text-xs text-muted-foreground">{activePaths} active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-1">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                Critical Paths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{criticalPaths}</div>
              <p className="text-xs text-muted-foreground">Risk score &ge; 8</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-1">
                <Zap className="h-4 w-4 text-orange-500" />
                High Risk Paths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{highRiskPaths}</div>
              <p className="text-xs text-muted-foreground">Risk score 6-8</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-1">
                <Target className="h-4 w-4 text-blue-500" />
                Avg Hops
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {pathsData?.paths && pathsData.paths.length > 0
                  ? (pathsData.paths.reduce((sum, p) => sum + p.hop_count, 0) / pathsData.paths.length).toFixed(1)
                  : "-"}
              </div>
              <p className="text-xs text-muted-foreground">Steps to target</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="paths">
              <Route className="h-4 w-4 mr-2" />
              Attack Paths ({pathsData?.total || 0})
            </TabsTrigger>
            <TabsTrigger value="nodes">
              <Network className="h-4 w-4 mr-2" />
              Nodes ({graph.total_nodes})
            </TabsTrigger>
            <TabsTrigger value="simulations">
              <FlaskConical className="h-4 w-4 mr-2" />
              Simulations
            </TabsTrigger>
          </TabsList>

          {/* Paths Tab */}
          <TabsContent value="paths" className="space-y-4">
            {/* Filters */}
            <Card>
              <CardContent className="pt-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Label className="text-sm">Min Risk:</Label>
                    <div className="w-32">
                      <Slider
                        value={[minRiskScore]}
                        onValueChange={(v) => setMinRiskScore(v[0])}
                        max={10}
                        step={0.5}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{minRiskScore}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Label className="text-sm">Status:</Label>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="All statuses" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All statuses</SelectItem>
                        {PATH_STATUSES.map((status) => (
                          <SelectItem key={status} value={status}>
                            {formatLabel(status)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <Button variant="outline" size="sm" onClick={() => refetchPaths()}>
                    <Filter className="h-4 w-4 mr-2" />
                    Apply
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Paths List */}
            <Card>
              <CardContent className="p-0">
                {pathsLoading ? (
                  <div className="text-center py-8 text-muted-foreground">Loading paths...</div>
                ) : !pathsData?.paths || pathsData.paths.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No attack paths found matching the filters.
                  </div>
                ) : (
                  <div className="divide-y">
                    {pathsData.paths.map((path) => (
                      <div key={path.id} className="p-4">
                        {/* Path Header */}
                        <div
                          className="flex items-center justify-between cursor-pointer"
                          onClick={() => setExpandedPathId(expandedPathId === path.id ? null : path.id)}
                        >
                          <div className="flex items-center gap-4 flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <MapPin className="h-4 w-4 text-red-500 flex-shrink-0" />
                              <span className="text-sm font-medium truncate max-w-[150px]">
                                {path.entry_point_name}
                              </span>
                            </div>

                            <div className="hidden md:flex items-center text-muted-foreground">
                              <span className="text-xs">{path.hop_count} hops</span>
                              <span className="mx-2">→</span>
                            </div>

                            <div className="flex items-center gap-2">
                              <Crown className="h-4 w-4 text-yellow-500 flex-shrink-0" />
                              <span className="text-sm font-medium truncate max-w-[150px]">
                                {path.target_name}
                              </span>
                              <Badge className={getCriticalityColor(path.target_criticality)}>
                                {formatLabel(path.target_criticality)}
                              </Badge>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            {path.exploitable_vulns > 0 && (
                              <Badge variant="destructive" className="hidden md:flex">
                                {path.exploitable_vulns} vulns
                              </Badge>
                            )}
                            <Badge variant="outline" className={getStatusColor(path.status)}>
                              {formatLabel(path.status)}
                            </Badge>
                            <div className={cn("font-bold text-lg w-12 text-right", getRiskColor(path.risk_score))}>
                              {path.risk_score.toFixed(1)}
                            </div>
                            {expandedPathId === path.id ? (
                              <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {expandedPathId === path.id && (
                          <div className="mt-4 pt-4 border-t space-y-4">
                            {/* Path Visualization */}
                            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                              {path.path_nodes.map((nodeId, index) => {
                                const node = getNodeById(nodeId);
                                const isFirst = index === 0;
                                const isLast = index === path.path_nodes.length - 1;

                                return (
                                  <div key={nodeId} className="flex items-center">
                                    <div
                                      className={cn(
                                        "flex flex-col items-center p-2 rounded-lg border-2 min-w-[80px]",
                                        isFirst && "border-red-400 bg-red-50",
                                        isLast && "border-yellow-400 bg-yellow-50",
                                        !isFirst && !isLast && "border-gray-300 bg-gray-50"
                                      )}
                                    >
                                      <div className="flex items-center gap-1 mb-1">
                                        {isFirst && <MapPin className="h-4 w-4 text-red-500" />}
                                        {isLast && <Crown className="h-4 w-4 text-yellow-500" />}
                                        {!isFirst && !isLast && <Shield className="h-4 w-4 text-gray-500" />}
                                      </div>
                                      <span className="text-xs font-medium text-center truncate max-w-[70px]">
                                        {node?.name || nodeId}
                                      </span>
                                      <span className="text-[10px] text-muted-foreground capitalize">
                                        {node?.type || "unknown"}
                                      </span>
                                      {node?.vulnerabilities && node.vulnerabilities.length > 0 && (
                                        <Badge variant="destructive" className="mt-1 text-[10px] h-4">
                                          {node.vulnerabilities.length} CVE
                                        </Badge>
                                      )}
                                    </div>
                                    {index < path.path_nodes.length - 1 && (
                                      <span className="mx-1 text-gray-400">→</span>
                                    )}
                                  </div>
                                );
                              })}
                            </div>

                            {/* Path Scores */}
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Exploitability:</span>
                                <span className="ml-2 font-medium">{path.exploitability_score.toFixed(1)}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Impact:</span>
                                <span className="ml-2 font-medium">{path.impact_score.toFixed(1)}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Alternative paths:</span>
                                <span className="ml-2 font-medium">{path.alternative_paths}</span>
                              </div>
                            </div>

                            {/* Vulnerabilities in path */}
                            {path.vulns_in_path && path.vulns_in_path.length > 0 && (
                              <div>
                                <span className="text-sm text-muted-foreground">Vulnerabilities in path:</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {path.vulns_in_path.slice(0, 5).map((vuln, i) => (
                                    <Badge key={i} variant="outline" className="text-xs">
                                      {vuln.cve_id}
                                    </Badge>
                                  ))}
                                  {path.vulns_in_path.length > 5 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{path.vulns_in_path.length - 5} more
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Actions */}
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleStatusUpdate(path)}
                              >
                                Update Status
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Nodes Tab */}
          <TabsContent value="nodes" className="space-y-4">
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Zone</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Vulnerabilities</TableHead>
                      <TableHead>Risk Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {graph.nodes?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No nodes in this graph.
                        </TableCell>
                      </TableRow>
                    ) : (
                      graph.nodes?.map((node) => (
                        <TableRow key={node.id}>
                          <TableCell className="font-medium">{node.name}</TableCell>
                          <TableCell className="capitalize">{node.type}</TableCell>
                          <TableCell>{node.zone || "-"}</TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {node.is_entry_point && (
                                <Badge className="bg-red-100 text-red-800">
                                  <MapPin className="h-3 w-3 mr-1" />
                                  Entry
                                </Badge>
                              )}
                              {node.is_crown_jewel && (
                                <Badge className="bg-yellow-100 text-yellow-800">
                                  <Crown className="h-3 w-3 mr-1" />
                                  Jewel
                                </Badge>
                              )}
                              {!node.is_entry_point && !node.is_crown_jewel && (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            {node.vulnerabilities?.length > 0 ? (
                              <Badge variant="destructive">
                                {node.vulnerabilities.length}
                              </Badge>
                            ) : (
                              <Badge variant="secondary">0</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge className={getRiskBgColor(node.risk_score)}>
                              {node.risk_score.toFixed(1)}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Simulations Tab */}
          <TabsContent value="simulations" className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium">What-If Simulations</h3>
                <p className="text-sm text-muted-foreground">
                  Test remediation scenarios to see their impact on attack paths
                </p>
              </div>
              <Button size="sm" onClick={() => setIsSimulationDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Simulation
              </Button>
            </div>

            {simulationsLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading simulations...</div>
            ) : !simulationsData?.simulations || simulationsData.simulations.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h4 className="font-medium mb-2">No simulations yet</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create a simulation to test how security changes would affect your attack paths.
                  </p>
                  <Button onClick={() => setIsSimulationDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create First Simulation
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {simulationsData.simulations.map((sim) => (
                  <Card key={sim.id} className={cn(
                    "border-l-4",
                    sim.status === "completed" && sim.risk_reduction_percent && sim.risk_reduction_percent > 0
                      ? "border-l-green-500"
                      : sim.status === "error"
                      ? "border-l-red-500"
                      : "border-l-blue-500"
                  )}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{sim.name}</CardTitle>
                          <Badge variant="outline">
                            {formatLabel(sim.simulation_type)}
                          </Badge>
                          <Badge className={getStatusColor(sim.status)}>
                            {formatLabel(sim.status)}
                          </Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteSimulationMutation.mutate(sim.id)}
                        >
                          <Trash2 className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      </div>
                      {sim.description && (
                        <CardDescription>{sim.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      {sim.status === "completed" && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center p-3 bg-muted rounded-lg">
                              <div className="text-2xl font-bold">{sim.original_paths_count || 0}</div>
                              <div className="text-xs text-muted-foreground">Original Paths</div>
                            </div>
                            <div className="text-center p-3 bg-muted rounded-lg">
                              <div className="text-2xl font-bold text-green-600">{sim.paths_eliminated || 0}</div>
                              <div className="text-xs text-muted-foreground">Paths Eliminated</div>
                            </div>
                            <div className="text-center p-3 bg-muted rounded-lg">
                              <div className="text-2xl font-bold">{sim.resulting_paths_count || 0}</div>
                              <div className="text-xs text-muted-foreground">Resulting Paths</div>
                            </div>
                            <div className="text-center p-3 bg-muted rounded-lg">
                              <div className={cn(
                                "text-2xl font-bold",
                                (sim.risk_reduction_percent || 0) > 0 ? "text-green-600" : "text-gray-600"
                              )}>
                                {sim.risk_reduction_percent?.toFixed(1) || 0}%
                              </div>
                              <div className="text-xs text-muted-foreground">Risk Reduction</div>
                            </div>
                          </div>

                          {sim.recommendation && (
                            <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                              <Zap className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                              <p className="text-sm">{sim.recommendation}</p>
                            </div>
                          )}
                        </div>
                      )}

                      {sim.status === "pending" && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          <span>Simulation in progress...</span>
                        </div>
                      )}

                      {sim.status === "error" && (
                        <div className="flex items-center gap-2 text-red-600">
                          <AlertTriangle className="h-4 w-4" />
                          <span>{sim.recommendation || "Simulation failed"}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Simulation Dialog */}
      <Dialog open={isSimulationDialogOpen} onOpenChange={setIsSimulationDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create What-If Simulation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Simulation Name</Label>
              <Input
                value={newSimulation.name}
                onChange={(e) => setNewSimulation({ ...newSimulation, name: e.target.value })}
                placeholder="e.g., Add MFA to Web Server"
              />
            </div>

            <div className="space-y-2">
              <Label>Description (optional)</Label>
              <Textarea
                value={newSimulation.description}
                onChange={(e) => setNewSimulation({ ...newSimulation, description: e.target.value })}
                placeholder="Describe what you want to simulate..."
              />
            </div>

            <div className="space-y-2">
              <Label>Simulation Type</Label>
              <Select
                value={newSimulation.simulation_type}
                onValueChange={(value) => setNewSimulation({
                  ...newSimulation,
                  simulation_type: value,
                  parameters: {},
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SIMULATION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div>
                        <div className="font-medium">{type.label}</div>
                        <div className="text-xs text-muted-foreground">{type.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Dynamic parameters based on simulation type */}
            {newSimulation.simulation_type === "add_control" && (
              <>
                <div className="space-y-2">
                  <Label>Asset ID</Label>
                  <Input
                    value={(newSimulation.parameters.asset_id as string) || ""}
                    onChange={(e) => setNewSimulation({
                      ...newSimulation,
                      parameters: { ...newSimulation.parameters, asset_id: e.target.value },
                    })}
                    placeholder="Select an asset from the graph"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Control Type</Label>
                  <Select
                    value={(newSimulation.parameters.control_type as string) || "mfa"}
                    onValueChange={(value) => setNewSimulation({
                      ...newSimulation,
                      parameters: { ...newSimulation.parameters, control_type: value },
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CONTROL_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {newSimulation.simulation_type === "segment_network" && (
              <div className="space-y-2">
                <Label>Asset to Isolate</Label>
                <Input
                  value={(newSimulation.parameters.asset_id as string) || ""}
                  onChange={(e) => setNewSimulation({
                    ...newSimulation,
                    parameters: { ...newSimulation.parameters, asset_id: e.target.value },
                  })}
                  placeholder="Asset ID to segment"
                />
              </div>
            )}

            {newSimulation.simulation_type === "patch_vulnerability" && (
              <div className="space-y-2">
                <Label>CVE IDs to Patch (comma-separated)</Label>
                <Input
                  value={(newSimulation.parameters.cve_ids as string[])?.join(", ") || ""}
                  onChange={(e) => setNewSimulation({
                    ...newSimulation,
                    parameters: {
                      ...newSimulation.parameters,
                      cve_ids: e.target.value.split(",").map(s => s.trim()).filter(Boolean),
                    },
                  })}
                  placeholder="CVE-2024-1234, CVE-2024-5678"
                />
              </div>
            )}

            {newSimulation.simulation_type === "compromise_asset" && (
              <div className="space-y-2">
                <Label>Asset to Simulate as Compromised</Label>
                <Input
                  value={(newSimulation.parameters.asset_id as string) || ""}
                  onChange={(e) => setNewSimulation({
                    ...newSimulation,
                    parameters: { ...newSimulation.parameters, asset_id: e.target.value },
                  })}
                  placeholder="Asset ID"
                />
              </div>
            )}

            <Button
              className="w-full"
              onClick={() => createSimulationMutation.mutate(newSimulation)}
              disabled={!newSimulation.name || createSimulationMutation.isPending}
            >
              {createSimulationMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Running Simulation...
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Run Simulation
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Status Update Dialog */}
      <Dialog open={isStatusDialogOpen} onOpenChange={setIsStatusDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Path Status</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>New Status</Label>
              <Select
                value={statusUpdateData.status}
                onValueChange={(value) => setStatusUpdateData({ ...statusUpdateData, status: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {PATH_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {formatLabel(status)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Reason (optional)</Label>
              <Textarea
                value={statusUpdateData.reason}
                onChange={(e) => setStatusUpdateData({ ...statusUpdateData, reason: e.target.value })}
                placeholder="Why is this status being changed?"
              />
            </div>

            <Button
              className="w-full"
              onClick={() => {
                if (selectedPath && statusUpdateData.status) {
                  updatePathStatusMutation.mutate({
                    pathId: selectedPath.id,
                    data: {
                      status: statusUpdateData.status,
                      reason: statusUpdateData.reason || undefined,
                    },
                  });
                }
              }}
              disabled={!statusUpdateData.status || updatePathStatusMutation.isPending}
            >
              {updatePathStatusMutation.isPending ? "Updating..." : "Update Status"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Scale,
  Plus,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Target,
  BarChart3,
  Filter,
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { risksAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
interface RiskStats {
  total_risks: number;
  open_risks: number;
  critical_risks: number;
  high_risks: number;
  overdue_treatments: number;
  risks_needing_review: number;
  total_controls: number;
  effective_controls: number;
  average_risk_score: number | null;
  total_financial_exposure: number | null;
  risks_by_category: Record<string, number>;
  risks_by_status: Record<string, number>;
  risks_by_level: Record<string, number>;
  recent_risks: Risk[];
}

interface Risk {
  id: string;
  risk_id: string;
  title: string;
  description: string | null;
  category: string;
  status: string;
  inherent_likelihood: string | null;
  inherent_impact: string | null;
  inherent_risk_score: number | null;
  inherent_risk_level: string | null;
  residual_risk_score: number | null;
  residual_risk_level: string | null;
  treatment_type: string | null;
  treatment_deadline: string | null;
  risk_owner: string | null;
  department: string | null;
  financial_impact: number | null;
  created_at: string;
  controls: RiskControl[];
  treatment_actions: TreatmentAction[];
}

interface RiskControl {
  id: string;
  control_id: string;
  name: string;
  description: string | null;
  control_type: string;
  status: string;
  effectiveness_rating: number | null;
}

interface TreatmentAction {
  id: string;
  title: string;
  status: string;
  priority: string;
  due_date: string | null;
}

interface RiskListResponse {
  risks: Risk[];
  total: number;
  page: number;
  page_size: number;
}

interface RiskMatrixCell {
  likelihood: string;
  impact: string;
  risk_level: string;
  risk_count: number;
  risks: Array<{ id: string; risk_id: string; title: string }>;
}

interface RiskMatrix {
  cells: RiskMatrixCell[];
  likelihood_levels: string[];
  impact_levels: string[];
}

const CATEGORIES = [
  "operational", "compliance", "strategic", "financial",
  "reputational", "technical", "security", "legal"
];

const LIKELIHOOD_LEVELS = ["rare", "unlikely", "possible", "likely", "almost_certain"];
const IMPACT_LEVELS = ["negligible", "minor", "moderate", "major", "catastrophic"];
const TREATMENT_TYPES = ["mitigate", "accept", "transfer", "avoid"];
const CONTROL_TYPES = ["preventive", "detective", "corrective", "compensating"];

export default function RisksPage() {
  const { token } = useAuthStore();
  const { t } = useTranslations();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [selectedLevel, setSelectedLevel] = useState<string | undefined>();
  const [isAddRiskOpen, setIsAddRiskOpen] = useState(false);
  const [isAddControlOpen, setIsAddControlOpen] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);

  // Form state for new risk
  const [newRisk, setNewRisk] = useState({
    title: "",
    description: "",
    category: "operational",
    inherent_likelihood: "",
    inherent_impact: "",
    treatment_type: "",
    department: "",
    risk_owner: "",
    financial_impact: "",
    tags: [] as string[],
  });

  // Form state for new control
  const [newControl, setNewControl] = useState({
    name: "",
    description: "",
    control_type: "preventive",
    implementation_details: "",
    effectiveness_rating: "",
  });

  // Queries
  const { data: stats, isLoading: statsLoading } = useQuery<RiskStats>({
    queryKey: ["risks", "stats"],
    queryFn: () => risksAPI.getStats(token!) as Promise<RiskStats>,
    enabled: !!token,
  });

  const { data: risksData, isLoading: risksLoading, refetch: refetchRisks } = useQuery<RiskListResponse>({
    queryKey: ["risks", "list", searchQuery, selectedCategory, selectedLevel],
    queryFn: () => risksAPI.listRisks(token!, {
      search: searchQuery || undefined,
      category: selectedCategory,
      risk_level: selectedLevel,
    }) as Promise<RiskListResponse>,
    enabled: !!token,
  });

  const { data: riskMatrix } = useQuery<RiskMatrix>({
    queryKey: ["risks", "matrix"],
    queryFn: () => risksAPI.getRiskMatrix(token!) as Promise<RiskMatrix>,
    enabled: !!token && activeTab === "matrix",
  });

  const { data: controlsData } = useQuery<{ controls: RiskControl[]; total: number }>({
    queryKey: ["risks", "controls"],
    queryFn: () => risksAPI.listControls(token!) as Promise<{ controls: RiskControl[]; total: number }>,
    enabled: !!token && activeTab === "controls",
  });

  // Mutations
  const createRiskMutation = useMutation({
    mutationFn: (data: typeof newRisk) => risksAPI.createRisk(token!, {
      title: data.title,
      description: data.description || undefined,
      category: data.category,
      inherent_likelihood: data.inherent_likelihood || undefined,
      inherent_impact: data.inherent_impact || undefined,
      treatment_type: data.treatment_type || undefined,
      department: data.department || undefined,
      risk_owner: data.risk_owner || undefined,
      financial_impact: data.financial_impact ? parseFloat(data.financial_impact) : undefined,
      tags: data.tags.length > 0 ? data.tags : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risks"] });
      setIsAddRiskOpen(false);
      setNewRisk({
        title: "",
        description: "",
        category: "operational",
        inherent_likelihood: "",
        inherent_impact: "",
        treatment_type: "",
        department: "",
        risk_owner: "",
        financial_impact: "",
        tags: [],
      });
    },
  });

  const createControlMutation = useMutation({
    mutationFn: (data: typeof newControl) => risksAPI.createControl(token!, {
      name: data.name,
      description: data.description || undefined,
      control_type: data.control_type,
      implementation_details: data.implementation_details || undefined,
      effectiveness_rating: data.effectiveness_rating ? parseFloat(data.effectiveness_rating) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risks", "controls"] });
      setIsAddControlOpen(false);
      setNewControl({
        name: "",
        description: "",
        control_type: "preventive",
        implementation_details: "",
        effectiveness_rating: "",
      });
    },
  });

  const deleteRiskMutation = useMutation({
    mutationFn: (id: string) => risksAPI.deleteRisk(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risks"] });
    },
  });

  const getRiskLevelColor = (level: string | null) => {
    switch (level?.toLowerCase()) {
      case "critical": return "bg-red-500 text-white";
      case "high": return "bg-orange-500 text-white";
      case "medium": return "bg-yellow-500 text-black";
      case "low": return "bg-green-500 text-white";
      default: return "bg-gray-500 text-white";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "identified": return "bg-blue-100 text-blue-800";
      case "assessed": return "bg-purple-100 text-purple-800";
      case "treatment_planned": return "bg-yellow-100 text-yellow-800";
      case "treatment_in_progress": return "bg-orange-100 text-orange-800";
      case "mitigated": return "bg-green-100 text-green-800";
      case "accepted": return "bg-gray-100 text-gray-800";
      case "closed": return "bg-gray-200 text-gray-600";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getCategoryLabel = (category: string) => {
    return category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, " ");
  };

  const formatCurrency = (amount: number | null) => {
    if (amount === null) return "-";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={t("risks.title")}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetchRisks()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {t("risks.refresh")}
            </Button>
            <Dialog open={isAddRiskOpen} onOpenChange={setIsAddRiskOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  {t("risks.addRisk")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>{t("risks.addRisk")}</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label>{t("risks.titleLabel")}</Label>
                    <Input
                      value={newRisk.title}
                      onChange={(e) => setNewRisk({ ...newRisk, title: e.target.value })}
                      placeholder={t("risks.riskTitlePlaceholder")}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>{t("risks.descriptionLabel")}</Label>
                    <Textarea
                      value={newRisk.description}
                      onChange={(e) => setNewRisk({ ...newRisk, description: e.target.value })}
                      placeholder={t("risks.describeRiskPlaceholder")}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label>{t("risks.categoryLabel")}</Label>
                      <Select
                        value={newRisk.category}
                        onValueChange={(value) => setNewRisk({ ...newRisk, category: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CATEGORIES.map((cat) => (
                            <SelectItem key={cat} value={cat}>
                              {getCategoryLabel(cat)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.departmentLabel")}</Label>
                      <Input
                        value={newRisk.department}
                        onChange={(e) => setNewRisk({ ...newRisk, department: e.target.value })}
                        placeholder={t("risks.departmentPlaceholder")}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label>{t("risks.likelihoodLabel")}</Label>
                      <Select
                        value={newRisk.inherent_likelihood}
                        onValueChange={(value) => setNewRisk({ ...newRisk, inherent_likelihood: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t("risks.selectLikelihood")} />
                        </SelectTrigger>
                        <SelectContent>
                          {LIKELIHOOD_LEVELS.map((level) => (
                            <SelectItem key={level} value={level}>
                              {level.charAt(0).toUpperCase() + level.slice(1).replace(/_/g, " ")}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.impactLabel")}</Label>
                      <Select
                        value={newRisk.inherent_impact}
                        onValueChange={(value) => setNewRisk({ ...newRisk, inherent_impact: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t("risks.selectImpact")} />
                        </SelectTrigger>
                        <SelectContent>
                          {IMPACT_LEVELS.map((level) => (
                            <SelectItem key={level} value={level}>
                              {level.charAt(0).toUpperCase() + level.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label>{t("risks.treatmentTypeLabel")}</Label>
                      <Select
                        value={newRisk.treatment_type}
                        onValueChange={(value) => setNewRisk({ ...newRisk, treatment_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t("risks.selectTreatment")} />
                        </SelectTrigger>
                        <SelectContent>
                          {TREATMENT_TYPES.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type.charAt(0).toUpperCase() + type.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.financialImpactLabel")}</Label>
                      <Input
                        type="number"
                        value={newRisk.financial_impact}
                        onChange={(e) => setNewRisk({ ...newRisk, financial_impact: e.target.value })}
                        placeholder="0"
                      />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label>{t("risks.riskOwnerLabel")}</Label>
                    <Input
                      value={newRisk.risk_owner}
                      onChange={(e) => setNewRisk({ ...newRisk, risk_owner: e.target.value })}
                      placeholder={t("risks.riskOwnerPlaceholder")}
                    />
                  </div>
                  <Button
                    onClick={() => createRiskMutation.mutate(newRisk)}
                    disabled={!newRisk.title || createRiskMutation.isPending}
                  >
                    {createRiskMutation.isPending ? t("risks.creating") : t("risks.createRisk")}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="dashboard">
              <BarChart3 className="h-4 w-4 mr-2" />
              {t("risks.dashboard")}
            </TabsTrigger>
            <TabsTrigger value="risks">
              <Scale className="h-4 w-4 mr-2" />
              {t("risks.list")}
            </TabsTrigger>
            <TabsTrigger value="matrix">
              <Target className="h-4 w-4 mr-2" />
              {t("risks.matrix")}
            </TabsTrigger>
            <TabsTrigger value="controls">
              <Shield className="h-4 w-4 mr-2" />
              {t("risks.controls")}
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">{t("risks.totalRisks")}</CardTitle>
                  <Scale className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_risks || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {stats?.open_risks || 0} {t("risks.open")}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">{t("risks.criticalRisks")}</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{stats?.critical_risks || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {stats?.high_risks || 0} {t("risks.high")}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">{t("risks.totalControls")}</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_controls || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {stats?.effective_controls || 0} {t("risks.effective")}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">{t("risks.financialExposure")}</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(stats?.total_financial_exposure || null)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {t("risks.avgScore")} {stats?.average_risk_score?.toFixed(1) || "-"}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Alert Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="border-orange-200 bg-orange-50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Clock className="h-4 w-4 text-orange-500" />
                    {t("risks.overdueActions")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-orange-600">
                    {stats?.overdue_treatments || 0}
                  </div>
                </CardContent>
              </Card>

              <Card className="border-blue-200 bg-blue-50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 text-blue-500" />
                    {t("risks.needsReview")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">
                    {stats?.risks_needing_review || 0}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Distribution Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{t("risks.risksByCategory")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {stats?.risks_by_category && Object.entries(stats.risks_by_category).map(([category, count]) => (
                      <div key={category} className="flex items-center justify-between">
                        <span className="text-sm capitalize">{category.replace(/_/g, " ")}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full"
                              style={{ width: `${(count / (stats?.total_risks || 1)) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{t("risks.risksByLevel")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {["critical", "high", "medium", "low"].map((level) => {
                      const count = stats?.risks_by_level?.[level] || 0;
                      return (
                        <div key={level} className="flex items-center justify-between">
                          <Badge className={getRiskLevelColor(level)}>
                            {level.charAt(0).toUpperCase() + level.slice(1)}
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
                                style={{ width: `${(count / (stats?.total_risks || 1)) * 100}%` }}
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
            </div>

            {/* Recent Risks */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">{t("risks.recentRisks")}</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("risks.riskId")}</TableHead>
                      <TableHead>{t("risks.titleHeader")}</TableHead>
                      <TableHead>{t("risks.categoryHeader")}</TableHead>
                      <TableHead>{t("risks.levelHeader")}</TableHead>
                      <TableHead>{t("risks.statusHeader")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stats?.recent_risks?.slice(0, 5).map((risk) => (
                      <TableRow key={risk.id}>
                        <TableCell className="font-mono text-sm">{risk.risk_id}</TableCell>
                        <TableCell>{risk.title}</TableCell>
                        <TableCell className="capitalize">{risk.category}</TableCell>
                        <TableCell>
                          <Badge className={getRiskLevelColor(risk.inherent_risk_level)}>
                            {risk.inherent_risk_level || "N/A"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={getStatusColor(risk.status)}>
                            {risk.status.replace(/_/g, " ")}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Risks List Tab */}
          <TabsContent value="risks" className="space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder={t("risks.searchRisksPlaceholder")}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("risks.allCategories")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t("risks.allCategories")}</SelectItem>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {getCategoryLabel(cat)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("risks.allLevels")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t("risks.allLevels")}</SelectItem>
                  <SelectItem value="critical">{t("risks.critical")}</SelectItem>
                  <SelectItem value="high">{t("risks.high")}</SelectItem>
                  <SelectItem value="medium">{t("risks.medium")}</SelectItem>
                  <SelectItem value="low">{t("risks.low")}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Risks Table */}
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("risks.riskId")}</TableHead>
                      <TableHead>{t("risks.titleHeader")}</TableHead>
                      <TableHead>{t("risks.categoryHeader")}</TableHead>
                      <TableHead>{t("risks.riskLevelHeader")}</TableHead>
                      <TableHead>{t("risks.scoreHeader")}</TableHead>
                      <TableHead>{t("risks.statusHeader")}</TableHead>
                      <TableHead>{t("risks.treatmentHeader")}</TableHead>
                      <TableHead>{t("risks.controlsHeader")}</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {risksLoading ? (
                      <TableRow>
                        <TableCell colSpan={9} className="text-center py-8">
                          {t("risks.loading")}
                        </TableCell>
                      </TableRow>
                    ) : risksData?.risks?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                          {t("risks.noRisks")}
                        </TableCell>
                      </TableRow>
                    ) : (
                      risksData?.risks?.map((risk) => (
                        <TableRow key={risk.id}>
                          <TableCell className="font-mono text-sm">{risk.risk_id}</TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{risk.title}</div>
                              {risk.description && (
                                <div className="text-sm text-muted-foreground truncate max-w-[300px]">
                                  {risk.description}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="capitalize">{risk.category}</TableCell>
                          <TableCell>
                            <Badge className={getRiskLevelColor(risk.inherent_risk_level)}>
                              {risk.inherent_risk_level || "N/A"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {risk.inherent_risk_score?.toFixed(1) || "-"}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={getStatusColor(risk.status)}>
                              {risk.status.replace(/_/g, " ")}
                            </Badge>
                          </TableCell>
                          <TableCell className="capitalize">
                            {risk.treatment_type || "-"}
                          </TableCell>
                          <TableCell>
                            {risk.controls?.length || 0}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => setSelectedRisk(risk)}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  {t("risks.viewDetails")}
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => deleteRiskMutation.mutate(risk.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  {t("common.delete")}
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

          {/* Risk Matrix Tab */}
          <TabsContent value="matrix" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>{t("risks.matrix")}</CardTitle>
              </CardHeader>
              <CardContent>
                {riskMatrix ? (
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr>
                          <th className="p-2 border bg-muted"></th>
                          {IMPACT_LEVELS.map((impact) => (
                            <th key={impact} className="p-2 border bg-muted text-center capitalize">
                              {impact}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[...LIKELIHOOD_LEVELS].reverse().map((likelihood) => (
                          <tr key={likelihood}>
                            <td className="p-2 border bg-muted font-medium capitalize">
                              {likelihood.replace(/_/g, " ")}
                            </td>
                            {IMPACT_LEVELS.map((impact) => {
                              const cell = riskMatrix.cells.find(
                                (c) => c.likelihood === likelihood && c.impact === impact
                              );
                              return (
                                <td
                                  key={`${likelihood}-${impact}`}
                                  className={cn(
                                    "p-4 border text-center cursor-pointer hover:opacity-80 transition-opacity",
                                    cell?.risk_level === "critical" && "bg-red-500 text-white",
                                    cell?.risk_level === "high" && "bg-orange-500 text-white",
                                    cell?.risk_level === "medium" && "bg-yellow-400",
                                    cell?.risk_level === "low" && "bg-green-400"
                                  )}
                                >
                                  <div className="text-2xl font-bold">{cell?.risk_count || 0}</div>
                                  <div className="text-xs mt-1 capitalize">{cell?.risk_level}</div>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <div className="mt-4 flex gap-4 justify-center">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-500 rounded" />
                        <span className="text-sm">{t("risks.legendCritical")}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-orange-500 rounded" />
                        <span className="text-sm">{t("risks.legendHigh")}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-yellow-400 rounded" />
                        <span className="text-sm">{t("risks.legendMedium")}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-400 rounded" />
                        <span className="text-sm">{t("risks.legendLow")}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    {t("risks.loadingRiskMatrix")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Controls Tab */}
          <TabsContent value="controls" className="space-y-4">
            <div className="flex justify-end">
              <Dialog open={isAddControlOpen} onOpenChange={setIsAddControlOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    {t("risks.addControl")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("risks.addControl")}</DialogTitle>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label>{t("risks.nameLabel")}</Label>
                      <Input
                        value={newControl.name}
                        onChange={(e) => setNewControl({ ...newControl, name: e.target.value })}
                        placeholder={t("risks.controlNamePlaceholder")}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.descriptionLabel")}</Label>
                      <Textarea
                        value={newControl.description}
                        onChange={(e) => setNewControl({ ...newControl, description: e.target.value })}
                        placeholder={t("risks.describeControlPlaceholder")}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.controlTypeLabel")}</Label>
                      <Select
                        value={newControl.control_type}
                        onValueChange={(value) => setNewControl({ ...newControl, control_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CONTROL_TYPES.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type.charAt(0).toUpperCase() + type.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.implementationDetailsLabel")}</Label>
                      <Textarea
                        value={newControl.implementation_details}
                        onChange={(e) => setNewControl({ ...newControl, implementation_details: e.target.value })}
                        placeholder={t("risks.implementationPlaceholder")}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label>{t("risks.effectivenessRatingLabel")}</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={newControl.effectiveness_rating}
                        onChange={(e) => setNewControl({ ...newControl, effectiveness_rating: e.target.value })}
                        placeholder={t("risks.effectivenessPlaceholder")}
                      />
                    </div>
                    <Button
                      onClick={() => createControlMutation.mutate(newControl)}
                      disabled={!newControl.name || createControlMutation.isPending}
                    >
                      {createControlMutation.isPending ? t("risks.creating") : t("risks.createControl")}
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
                      <TableHead>{t("risks.controlId")}</TableHead>
                      <TableHead>{t("risks.nameHeader")}</TableHead>
                      <TableHead>{t("risks.typeHeader")}</TableHead>
                      <TableHead>{t("risks.statusHeader")}</TableHead>
                      <TableHead>{t("risks.effectivenessHeader")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {controlsData?.controls?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          {t("risks.noControls")}
                        </TableCell>
                      </TableRow>
                    ) : (
                      controlsData?.controls?.map((control: RiskControl) => (
                        <TableRow key={control.id}>
                          <TableCell className="font-mono text-sm">{control.control_id}</TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{control.name}</div>
                              {control.description && (
                                <div className="text-sm text-muted-foreground truncate max-w-[300px]">
                                  {control.description}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="capitalize">{control.control_type}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className={getStatusColor(control.status)}>
                              {control.status.replace(/_/g, " ")}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {control.effectiveness_rating !== null ? (
                              <div className="flex items-center gap-2">
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div
                                    className={cn(
                                      "h-2 rounded-full",
                                      control.effectiveness_rating >= 70 ? "bg-green-500" :
                                      control.effectiveness_rating >= 40 ? "bg-yellow-500" : "bg-red-500"
                                    )}
                                    style={{ width: `${control.effectiveness_rating}%` }}
                                  />
                                </div>
                                <span className="text-sm">{control.effectiveness_rating}%</span>
                              </div>
                            ) : (
                              "-"
                            )}
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

      {/* Risk Detail Dialog */}
      {selectedRisk && (
        <Dialog open={!!selectedRisk} onOpenChange={() => setSelectedRisk(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <span className="font-mono text-sm text-muted-foreground">{selectedRisk.risk_id}</span>
                {selectedRisk.title}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge className={getRiskLevelColor(selectedRisk.inherent_risk_level)}>
                  {selectedRisk.inherent_risk_level || t("risks.unassessed")}
                </Badge>
                <Badge variant="outline" className={getStatusColor(selectedRisk.status)}>
                  {selectedRisk.status.replace(/_/g, " ")}
                </Badge>
                <Badge variant="outline" className="capitalize">
                  {selectedRisk.category}
                </Badge>
              </div>

              {selectedRisk.description && (
                <div>
                  <Label className="text-muted-foreground">{t("risks.descriptionLabel")}</Label>
                  <p className="mt-1">{selectedRisk.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">{t("risks.inherentScore")}</Label>
                  <p className="text-lg font-semibold">{selectedRisk.inherent_risk_score?.toFixed(1) || "-"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t("risks.residualScore")}</Label>
                  <p className="text-lg font-semibold">{selectedRisk.residual_risk_score?.toFixed(1) || "-"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t("risks.treatment")}</Label>
                  <p className="capitalize">{selectedRisk.treatment_type || "-"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t("risks.financialImpactLabel")}</Label>
                  <p>{formatCurrency(selectedRisk.financial_impact)}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t("risks.departmentLabel")}</Label>
                  <p>{selectedRisk.department || "-"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t("risks.owner")}</Label>
                  <p>{selectedRisk.risk_owner || "-"}</p>
                </div>
              </div>

              {selectedRisk.controls && selectedRisk.controls.length > 0 && (
                <div>
                  <Label className="text-muted-foreground">{t("risks.controlsCount")} ({selectedRisk.controls.length})</Label>
                  <div className="mt-2 space-y-2">
                    {selectedRisk.controls.map((control) => (
                      <div key={control.id} className="flex items-center justify-between p-2 bg-muted rounded">
                        <span>{control.name}</span>
                        <Badge variant="outline" className="capitalize">{control.control_type}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedRisk.treatment_actions && selectedRisk.treatment_actions.length > 0 && (
                <div>
                  <Label className="text-muted-foreground">{t("risks.treatmentActions")} ({selectedRisk.treatment_actions.length})</Label>
                  <div className="mt-2 space-y-2">
                    {selectedRisk.treatment_actions.map((action) => (
                      <div key={action.id} className="flex items-center justify-between p-2 bg-muted rounded">
                        <span>{action.title}</span>
                        <Badge variant="outline" className={getStatusColor(action.status)}>
                          {action.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

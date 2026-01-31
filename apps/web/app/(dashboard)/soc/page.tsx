"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Briefcase,
  BookOpen,
  Clock,
  Plus,
  Search,
  MoreHorizontal,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  User,
  Timer,
  Activity,
  Zap,
  TrendingUp,
  Users,
} from "lucide-react";
import { socAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import {
  useTrend,
  useDistribution,
  useAnalystMetrics,
  useSLACompliance,
} from "@/hooks/useAnalytics";
import {
  TrendLineChart,
  DistributionChart,
  DonutChart,
} from "@/components/dashboard/charts";
import { ChartCard, SLAStatusCard } from "@/components/dashboard/widgets";
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
interface SOCDashboardStats {
  total_alerts_today: number;
  new_alerts: number;
  in_progress_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  open_cases: number;
  escalated_cases: number;
  overdue_cases: number;
  mttd: number | null;
  mttr: number | null;
  alerts_by_severity: Record<string, number>;
  alerts_by_source: Record<string, number>;
  alerts_by_status: Record<string, number>;
  cases_by_priority: Record<string, number>;
  cases_by_status: Record<string, number>;
  playbook_runs_today: number;
  automation_rate: number;
  alerts_per_analyst: Record<string, number>;
}

interface Alert {
  id: string;
  alert_id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  source: string;
  assigned_to: string | null;
  detected_at: string;
  risk_score: number | null;
  mitre_techniques: string[] | null;
}

interface AlertList {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface Case {
  id: string;
  case_number: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  assigned_team: string | null;
  opened_at: string;
  due_date: string | null;
  alert_count: number;
  task_count: number;
}

interface CaseList {
  items: Case[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface Playbook {
  id: string;
  name: string;
  description: string;
  status: string;
  trigger_type: string;
  is_enabled: boolean;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  category: string | null;
}

interface PlaybookList {
  items: Playbook[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const tabs = [
  { id: "dashboard", icon: Activity, labelKey: "soc.dashboard" },
  { id: "alerts", icon: Bell, labelKey: "soc.alerts" },
  { id: "cases", icon: Briefcase, labelKey: "soc.cases" },
  { id: "playbooks", icon: BookOpen, labelKey: "soc.playbooks" },
];

export default function SOCPage() {
  const { t } = useTranslations();
  const { token, user } = useAuthStore();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [isAddAlertOpen, setIsAddAlertOpen] = useState(false);
  const [isAddCaseOpen, setIsAddCaseOpen] = useState(false);

  // Form states
  const [alertForm, setAlertForm] = useState({
    title: "",
    severity: "",
    source: "",
    description: "",
  });
  const [caseForm, setCaseForm] = useState({
    title: "",
    priority: "",
    case_type: "",
    description: "",
  });

  const queryClient = useQueryClient();

  // Dashboard stats
  const { data: stats } = useQuery<SOCDashboardStats>({
    queryKey: ["soc-dashboard"],
    queryFn: () => socAPI.getDashboard(token!) as Promise<SOCDashboardStats>,
    enabled: !!token,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Alerts query
  const { data: alertList, isLoading: alertsLoading } = useQuery<AlertList>({
    queryKey: ["soc-alerts", search, severityFilter, statusFilter],
    queryFn: () =>
      socAPI.listAlerts(token!, {
        search: search || undefined,
        severity: severityFilter !== "all" ? severityFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      }) as Promise<AlertList>,
    enabled: !!token && activeTab === "alerts",
  });

  // Cases query
  const { data: caseList, isLoading: casesLoading } = useQuery<CaseList>({
    queryKey: ["soc-cases", search, statusFilter, priorityFilter],
    queryFn: () =>
      socAPI.listCases(token!, {
        search: search || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        priority: priorityFilter !== "all" ? priorityFilter : undefined,
      }) as Promise<CaseList>,
    enabled: !!token && activeTab === "cases",
  });

  // Playbooks query
  const { data: playbookList, isLoading: playbooksLoading } = useQuery<PlaybookList>({
    queryKey: ["soc-playbooks", search],
    queryFn: () =>
      socAPI.listPlaybooks(token!, {
        search: search || undefined,
      }) as Promise<PlaybookList>,
    enabled: !!token && activeTab === "playbooks",
  });

  // Analytics for charts
  const { data: alertTrend } = useTrend("alerts", "count", 30, "daily");
  const { data: alertDistribution } = useDistribution("alerts", "severity");
  const { data: analystMetrics } = useAnalystMetrics(30);
  const { data: responseSLA } = useSLACompliance("response", 30);

  // Create Alert mutation
  const createAlertMutation = useMutation({
    mutationFn: (data: typeof alertForm) => socAPI.createAlert(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["soc-alerts"] });
      queryClient.invalidateQueries({ queryKey: ["soc-dashboard"] });
      setIsAddAlertOpen(false);
      setAlertForm({ title: "", severity: "", source: "", description: "" });
    },
  });

  // Create Case mutation
  const createCaseMutation = useMutation({
    mutationFn: (data: typeof caseForm) => socAPI.createCase(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["soc-cases"] });
      queryClient.invalidateQueries({ queryKey: ["soc-dashboard"] });
      setIsAddCaseOpen(false);
      setCaseForm({ title: "", priority: "", case_type: "", description: "" });
    },
  });

  const handleCreateAlert = () => {
    if (!alertForm.title) return;
    createAlertMutation.mutate(alertForm);
  };

  const handleCreateCase = () => {
    if (!caseForm.title) return;
    createCaseMutation.mutate(caseForm);
  };

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "destructive",
      medium: "default",
      low: "secondary",
      informational: "outline",
    };
    const colors: Record<string, string> = {
      critical: "bg-red-600",
      high: "bg-orange-500",
      medium: "bg-yellow-500",
      low: "bg-blue-500",
      informational: "bg-gray-500",
    };
    return (
      <Badge className={severity === "critical" || severity === "high" ? colors[severity] : ""} variant={variants[severity] || "default"}>
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      new: "destructive",
      assigned: "default",
      in_progress: "default",
      pending: "secondary",
      resolved: "outline",
      closed: "outline",
      false_positive: "secondary",
      escalated: "destructive",
      open: "destructive",
    };
    return <Badge variant={variants[status] || "default"}>{status.replace(/_/g, " ")}</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "destructive",
      medium: "default",
      low: "secondary",
    };
    return <Badge variant={variants[priority] || "default"}>{priority.toUpperCase()}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{t("soc.title")}</h1>
          <p className="text-muted-foreground">
            {t("soc.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          {activeTab === "alerts" && (
            <Dialog open={isAddAlertOpen} onOpenChange={setIsAddAlertOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("soc.addAlert")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>{t("soc.addAlert")}</DialogTitle>
                  <DialogDescription>
                    {t("soc.createAlertDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="alert-title">{t("soc.alertTitle")}</Label>
                    <Input
                      id="alert-title"
                      placeholder={t("soc.alertTitlePlaceholder")}
                      value={alertForm.title}
                      onChange={(e) => setAlertForm({ ...alertForm, title: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="alert-severity">{t("common.severity")}</Label>
                    <Select
                      value={alertForm.severity}
                      onValueChange={(value) => setAlertForm({ ...alertForm, severity: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t("soc.selectSeverity")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">{t("soc.critical")}</SelectItem>
                        <SelectItem value="high">{t("soc.high")}</SelectItem>
                        <SelectItem value="medium">{t("soc.medium")}</SelectItem>
                        <SelectItem value="low">{t("soc.low")}</SelectItem>
                        <SelectItem value="informational">{t("soc.informational")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="alert-source">{t("soc.source")}</Label>
                    <Select
                      value={alertForm.source}
                      onValueChange={(value) => setAlertForm({ ...alertForm, source: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t("soc.selectSource")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="siem">{t("soc.siem")}</SelectItem>
                        <SelectItem value="edr">{t("soc.edr")}</SelectItem>
                        <SelectItem value="ids">{t("soc.ids")}</SelectItem>
                        <SelectItem value="firewall">{t("soc.firewall")}</SelectItem>
                        <SelectItem value="manual">{t("soc.manual")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="alert-desc">{t("common.description")}</Label>
                    <Textarea
                      id="alert-desc"
                      placeholder={t("soc.describeAlert")}
                      value={alertForm.description}
                      onChange={(e) => setAlertForm({ ...alertForm, description: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddAlertOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                  <Button
                    onClick={handleCreateAlert}
                    disabled={createAlertMutation.isPending || !alertForm.title}
                  >
                    {createAlertMutation.isPending ? t("common.saving") : t("common.save")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          {activeTab === "cases" && (
            <Dialog open={isAddCaseOpen} onOpenChange={setIsAddCaseOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("soc.addCase")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>{t("soc.addCase")}</DialogTitle>
                  <DialogDescription>
                    {t("soc.createCaseDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="case-title">{t("soc.caseTitle")}</Label>
                    <Input
                      id="case-title"
                      placeholder={t("soc.caseTitlePlaceholder")}
                      value={caseForm.title}
                      onChange={(e) => setCaseForm({ ...caseForm, title: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="case-priority">{t("common.priority")}</Label>
                    <Select
                      value={caseForm.priority}
                      onValueChange={(value) => setCaseForm({ ...caseForm, priority: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t("soc.selectPriority")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">{t("soc.priorityCritical")}</SelectItem>
                        <SelectItem value="high">{t("soc.priorityHigh")}</SelectItem>
                        <SelectItem value="medium">{t("soc.priorityMedium")}</SelectItem>
                        <SelectItem value="low">{t("soc.priorityLow")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="case-type">{t("soc.caseType")}</Label>
                    <Select
                      value={caseForm.case_type}
                      onValueChange={(value) => setCaseForm({ ...caseForm, case_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t("soc.selectType")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="malware">{t("soc.malware")}</SelectItem>
                        <SelectItem value="phishing">{t("soc.phishing")}</SelectItem>
                        <SelectItem value="data_breach">{t("soc.dataBreach")}</SelectItem>
                        <SelectItem value="unauthorized_access">{t("soc.unauthorizedAccess")}</SelectItem>
                        <SelectItem value="other">{t("soc.other")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="case-desc">{t("common.description")}</Label>
                    <Textarea
                      id="case-desc"
                      placeholder={t("soc.describeCase")}
                      value={caseForm.description}
                      onChange={(e) => setCaseForm({ ...caseForm, description: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddCaseOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                  <Button
                    onClick={handleCreateCase}
                    disabled={createCaseMutation.isPending || !caseForm.title}
                  >
                    {createCaseMutation.isPending ? t("common.saving") : t("common.save")}
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
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-l-4 border-l-red-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("soc.criticalAlerts")}
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-500">
                  {stats?.critical_alerts || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  +{stats?.high_alerts || 0} {t("soc.highSeverity")}
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-yellow-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("soc.newAlerts")}
                </CardTitle>
                <Bell className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.new_alerts || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.in_progress_alerts || 0} {t("soc.inProgress").toLowerCase()}
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("soc.openCases")}
                </CardTitle>
                <Briefcase className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.open_cases || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.escalated_cases || 0} {t("soc.escalated").toLowerCase()}
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("soc.automationRate")}
                </CardTitle>
                <Zap className="h-4 w-4 text-purple-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((stats?.automation_rate || 0) * 100).toFixed(0)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.playbook_runs_today || 0} {t("soc.playbookRunsToday")}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Response Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{t("soc.mttd")}</CardTitle>
                <Timer className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.mttd ? `${Math.round(stats.mttd / 60)}m` : "N/A"}
                </div>
                <p className="text-xs text-muted-foreground">
                  {t("soc.meanTimeToDetect")}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{t("soc.mttr")}</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.mttr ? `${Math.round(stats.mttr / 60)}m` : "N/A"}
                </div>
                <p className="text-xs text-muted-foreground">
                  {t("soc.meanTimeToRespond")}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{t("soc.alertsToday")}</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_alerts_today || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {t("soc.totalAlertsReceived")}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Alert Trend Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Alert Volume (30 days)" icon={Bell}>
              {alertTrend?.data && (
                <TrendLineChart
                  data={alertTrend.data}
                  height={200}
                  showArea={true}
                />
              )}
            </ChartCard>

            <SLAStatusCard
              title="Response SLA Compliance"
              compliant={responseSLA?.compliant_items || 0}
              total={responseSLA?.total_items || 0}
              breached={responseSLA?.breached_items || 0}
              atRisk={responseSLA?.at_risk_items || 0}
            />
          </div>

          {/* Alerts by Severity and Analyst Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title={t("soc.alertsBySeverity")}>
              {alertDistribution?.data && alertDistribution.data.length > 0 ? (
                <DonutChart
                  data={alertDistribution.data}
                  colorScheme="severity"
                  height={200}
                />
              ) : (
                <div className="flex items-center justify-center h-[200px]">
                  <p className="text-muted-foreground text-sm">{t("soc.noActiveAlerts")}</p>
                </div>
              )}
            </ChartCard>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  {t("soc.analystWorkload")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analystMetrics?.analysts && analystMetrics.analysts.length > 0 ? (
                  <div className="space-y-3">
                    {analystMetrics.analysts.slice(0, 5).map((analyst) => (
                      <div key={analyst.analyst_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4" />
                          <span className="text-sm">{analyst.analyst_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">{analyst.alerts_assigned} alerts</Badge>
                          <Badge
                            variant={analyst.workload_score > 80 ? "destructive" : analyst.workload_score > 50 ? "default" : "outline"}
                          >
                            {analyst.workload_score.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {stats?.alerts_per_analyst && Object.entries(stats.alerts_per_analyst).map(([analyst, count]) => (
                      <div key={analyst} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4" />
                          <span>{analyst}</span>
                        </div>
                        <Badge variant="secondary">{count} {t("soc.alerts").toLowerCase()}</Badge>
                      </div>
                    ))}
                    {(!stats?.alerts_per_analyst || Object.keys(stats.alerts_per_analyst).length === 0) && (
                      <p className="text-muted-foreground text-sm">{t("soc.noAssignments")}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === "alerts" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("soc.searchAlerts")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder={t("common.severity")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("soc.allSeverities")}</SelectItem>
                <SelectItem value="critical">{t("soc.critical")}</SelectItem>
                <SelectItem value="high">{t("soc.high")}</SelectItem>
                <SelectItem value="medium">{t("soc.medium")}</SelectItem>
                <SelectItem value="low">{t("soc.low")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder={t("common.status")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("soc.allStatus")}</SelectItem>
                <SelectItem value="new">{t("soc.new")}</SelectItem>
                <SelectItem value="assigned">{t("soc.assigned")}</SelectItem>
                <SelectItem value="in_progress">{t("soc.inProgress")}</SelectItem>
                <SelectItem value="resolved">{t("soc.resolved")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Alerts Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("soc.alertId")}</TableHead>
                  <TableHead>{t("soc.alertTitle")}</TableHead>
                  <TableHead>{t("common.severity")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("soc.source")}</TableHead>
                  <TableHead>{t("soc.assignedTo")}</TableHead>
                  <TableHead>{t("soc.detected")}</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alertsLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      {t("common.loading")}
                    </TableCell>
                  </TableRow>
                ) : alertList?.items && alertList.items.length > 0 ? (
                  alertList.items.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-mono text-sm">{alert.alert_id}</TableCell>
                      <TableCell>
                        <div className="font-medium">{alert.title}</div>
                        {alert.mitre_techniques && alert.mitre_techniques.length > 0 && (
                          <div className="text-xs text-muted-foreground">
                            {alert.mitre_techniques.slice(0, 2).join(", ")}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
                      <TableCell>{getStatusBadge(alert.status)}</TableCell>
                      <TableCell className="capitalize">{alert.source.replace(/_/g, " ")}</TableCell>
                      <TableCell>{alert.assigned_to || "-"}</TableCell>
                      <TableCell>
                        {new Date(alert.detected_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>{t("common.view")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("soc.assign")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("soc.acknowledge")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("soc.resolve")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("soc.escalate")}</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {t("soc.noAlerts")}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}

      {/* Cases Tab */}
      {activeTab === "cases" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("soc.searchCases")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder={t("common.status")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("soc.allStatus")}</SelectItem>
                <SelectItem value="open">{t("soc.open")}</SelectItem>
                <SelectItem value="in_progress">{t("soc.inProgress")}</SelectItem>
                <SelectItem value="escalated">{t("soc.escalated")}</SelectItem>
                <SelectItem value="resolved">{t("soc.resolved")}</SelectItem>
                <SelectItem value="closed">{t("soc.closed")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder={t("common.priority")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("soc.allPriorities")}</SelectItem>
                <SelectItem value="critical">{t("soc.priorityCritical")}</SelectItem>
                <SelectItem value="high">{t("soc.priorityHigh")}</SelectItem>
                <SelectItem value="medium">{t("soc.priorityMedium")}</SelectItem>
                <SelectItem value="low">{t("soc.priorityLow")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Cases Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("soc.caseNumber")}</TableHead>
                  <TableHead>{t("soc.caseTitle")}</TableHead>
                  <TableHead>{t("common.priority")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("soc.assignedTo")}</TableHead>
                  <TableHead>{t("soc.alerts")}</TableHead>
                  <TableHead>{t("soc.dueDate")}</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {casesLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      {t("common.loading")}
                    </TableCell>
                  </TableRow>
                ) : caseList?.items && caseList.items.length > 0 ? (
                  caseList.items.map((caseItem) => (
                    <TableRow key={caseItem.id}>
                      <TableCell className="font-mono text-sm">{caseItem.case_number}</TableCell>
                      <TableCell>
                        <div className="font-medium">{caseItem.title}</div>
                        {caseItem.assigned_team && (
                          <div className="text-xs text-muted-foreground">
                            Team: {caseItem.assigned_team}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getPriorityBadge(caseItem.priority)}</TableCell>
                      <TableCell>{getStatusBadge(caseItem.status)}</TableCell>
                      <TableCell>{caseItem.assigned_to || "-"}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{caseItem.alert_count} {t("soc.alerts").toLowerCase()}</Badge>
                      </TableCell>
                      <TableCell>
                        {caseItem.due_date
                          ? new Date(caseItem.due_date).toLocaleDateString()
                          : "-"}
                      </TableCell>
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
                            <DropdownMenuItem>{t("soc.escalate")}</DropdownMenuItem>
                            <DropdownMenuItem>{t("soc.resolve")}</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {t("soc.noCases")}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </div>
      )}

      {/* Playbooks Tab */}
      {activeTab === "playbooks" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("soc.searchPlaybooks")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Playbooks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {playbooksLoading ? (
              <p className="col-span-full text-center py-8">{t("common.loading")}</p>
            ) : playbookList?.items && playbookList.items.length > 0 ? (
              playbookList.items.map((playbook) => (
                <Card key={playbook.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{playbook.name}</CardTitle>
                      <Badge variant={playbook.is_enabled ? "default" : "secondary"}>
                        {playbook.is_enabled ? t("soc.active") : t("soc.disabled")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      {playbook.description || t("soc.noDescription")}
                    </p>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {t("soc.trigger")}: {playbook.trigger_type.replace(/_/g, " ")}
                      </span>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span>{playbook.successful_runs}</span>
                        <XCircle className="h-4 w-4 text-red-500" />
                        <span>{playbook.failed_runs}</span>
                      </div>
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        {t("common.view")}
                      </Button>
                      <Button size="sm" className="flex-1">
                        {t("soc.execute")}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="col-span-full text-center py-8 text-muted-foreground">
                {t("soc.noPlaybooks")}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

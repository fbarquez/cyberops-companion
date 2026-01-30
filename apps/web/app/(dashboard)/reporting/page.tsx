"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart3,
  FileText,
  Download,
  Clock,
  Calendar,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Bug,
  Scale,
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
  Plus,
  Play,
  FileSpreadsheet,
  FileJson,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { reportingAPI } from "@/lib/api-client";

interface ExecutiveDashboardStats {
  security_score: number;
  security_score_trend?: string;
  incidents_total: number;
  incidents_open: number;
  incidents_critical: number;
  incidents_mttr_hours?: number;
  alerts_today: number;
  alerts_critical: number;
  cases_open: number;
  cases_escalated: number;
  mttd_minutes?: number;
  mttr_minutes?: number;
  vulnerabilities_total: number;
  vulnerabilities_critical: number;
  vulnerabilities_high: number;
  vulnerabilities_overdue: number;
  patch_compliance_rate?: number;
  risks_total: number;
  risks_critical: number;
  risks_high: number;
  risk_score_average?: number;
  risks_requiring_treatment: number;
  vendors_total: number;
  vendors_high_risk: number;
  assessments_pending: number;
  findings_open: number;
  integrations_active: number;
  integrations_with_errors: number;
  syncs_today: number;
  compliance_score?: number;
  controls_implemented?: number;
  controls_total?: number;
}

interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  report_type: string;
  config?: Record<string, any>;
  supported_formats?: string[];
  is_active: boolean;
  created_at: string;
}

interface GeneratedReport {
  id: string;
  report_id: string;
  name: string;
  description?: string;
  report_type: string;
  status: string;
  format: string;
  period_start?: string;
  period_end?: string;
  file_size_bytes?: number;
  generation_time_seconds?: number;
  generated_at?: string;
  error_message?: string;
  created_at: string;
}

interface ReportSchedule {
  id: string;
  name: string;
  description?: string;
  template_id: string;
  frequency: string;
  recipients: string[];
  is_enabled: boolean;
  last_run_at?: string;
  next_run_at?: string;
  last_status?: string;
  consecutive_failures: number;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function ReportingPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [reportConfig, setReportConfig] = useState({
    format: "pdf",
    period_days: 30,
  });

  // Executive Dashboard
  const { data: dashboardStats } = useQuery({
    queryKey: ["executive-dashboard"],
    queryFn: () => reportingAPI.getExecutiveDashboard(token!) as Promise<ExecutiveDashboardStats>,
    enabled: !!token,
    refetchInterval: 60000,
  });

  // Report Templates
  const { data: templatesData } = useQuery({
    queryKey: ["report-templates"],
    queryFn: () => reportingAPI.listTemplates(token!) as Promise<ReportTemplate[]>,
    enabled: !!token && (activeTab === "templates" || activeTab === "dashboard"),
  });

  // Generated Reports
  const { data: reportsData } = useQuery({
    queryKey: ["generated-reports"],
    queryFn: () => reportingAPI.listReports(token!, { size: 50 }) as Promise<PaginatedResponse<GeneratedReport>>,
    enabled: !!token && activeTab === "reports",
  });

  // Report Schedules
  const { data: schedulesData } = useQuery({
    queryKey: ["report-schedules"],
    queryFn: () => reportingAPI.listSchedules(token!, { size: 50 }) as Promise<PaginatedResponse<ReportSchedule>>,
    enabled: !!token && activeTab === "schedules",
  });

  // Seed templates mutation
  const seedTemplatesMutation = useMutation({
    mutationFn: () => reportingAPI.seedTemplates(token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["report-templates"] });
    },
  });

  // Generate report mutation
  const generateReportMutation = useMutation({
    mutationFn: (data: any) => reportingAPI.generateReport(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["generated-reports"] });
      setIsGenerateOpen(false);
      setSelectedTemplate(null);
    },
  });

  const handleGenerateReport = () => {
    if (!selectedTemplate) return;

    generateReportMutation.mutate({
      template_id: selectedTemplate.id,
      report_type: selectedTemplate.report_type,
      name: `${selectedTemplate.name} - ${new Date().toLocaleDateString()}`,
      format: reportConfig.format,
      period_days: reportConfig.period_days,
    });
  };

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      completed: "default",
      pending: "secondary",
      generating: "secondary",
      failed: "destructive",
      scheduled: "outline",
    };
    return variants[status] || "secondary";
  };

  const getFormatIcon = (format: string) => {
    if (format === "pdf") return FileText;
    if (format === "excel") return FileSpreadsheet;
    if (format === "json") return FileJson;
    return FileText;
  };

  const getTrendIcon = (trend?: string) => {
    if (trend === "up") return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend === "down") return <TrendingDown className="h-4 w-4 text-red-500" />;
    return null;
  };

  const stats = dashboardStats;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("reporting.title")}</h1>
          <p className="text-muted-foreground">
            Executive dashboards, reports, and analytics
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => seedTemplatesMutation.mutate()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Seed Templates
          </Button>
          <Dialog open={isGenerateOpen} onOpenChange={setIsGenerateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                {t("reporting.generateReport")}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t("reporting.generateReport")}</DialogTitle>
                <DialogDescription>
                  Select a template and configure your report.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Report Template</Label>
                  <Select
                    value={selectedTemplate?.id || ""}
                    onValueChange={(id) => {
                      const template = templatesData?.find((t: ReportTemplate) => t.id === id);
                      setSelectedTemplate(template || null);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a template" />
                    </SelectTrigger>
                    <SelectContent>
                      {templatesData?.map((template: ReportTemplate) => (
                        <SelectItem key={template.id} value={template.id}>
                          {template.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Format</Label>
                    <Select
                      value={reportConfig.format}
                      onValueChange={(v) => setReportConfig({ ...reportConfig, format: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">{t("reporting.pdf")}</SelectItem>
                        <SelectItem value="excel">{t("reporting.excel")}</SelectItem>
                        <SelectItem value="csv">{t("reporting.csv")}</SelectItem>
                        <SelectItem value="json">{t("reporting.json")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Period (Days)</Label>
                    <Select
                      value={reportConfig.period_days.toString()}
                      onValueChange={(v) => setReportConfig({ ...reportConfig, period_days: parseInt(v) })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="7">Last 7 days</SelectItem>
                        <SelectItem value="30">Last 30 days</SelectItem>
                        <SelectItem value="90">Last 90 days</SelectItem>
                        <SelectItem value="365">Last year</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsGenerateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleGenerateReport}
                  disabled={!selectedTemplate || generateReportMutation.isPending}
                >
                  {generateReportMutation.isPending ? "Generating..." : t("reporting.generate")}
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
            <BarChart3 className="h-4 w-4" />
            {t("reporting.executiveDashboard")}
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {t("reporting.templates")}
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            {t("reporting.reports")}
          </TabsTrigger>
          <TabsTrigger value="schedules" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {t("reporting.schedules")}
          </TabsTrigger>
        </TabsList>

        {/* Executive Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Security Score */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="lg:col-span-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center justify-between">
                  {t("reporting.securityScore")}
                  {getTrendIcon(stats?.security_score_trend)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center">
                  <div className="relative w-32 h-32">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="12"
                        className="text-muted"
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="12"
                        strokeDasharray={`${(stats?.security_score || 0) * 3.52} 352`}
                        className={
                          (stats?.security_score || 0) >= 80
                            ? "text-green-500"
                            : (stats?.security_score || 0) >= 60
                              ? "text-yellow-500"
                              : "text-red-500"
                        }
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-3xl font-bold">{stats?.security_score || 0}</span>
                    </div>
                  </div>
                </div>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  Overall Security Posture
                </p>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Key Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{stats?.mttd_minutes || 0}</p>
                    <p className="text-xs text-muted-foreground">MTTD (min)</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{stats?.mttr_minutes || 0}</p>
                    <p className="text-xs text-muted-foreground">MTTR (min)</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{stats?.patch_compliance_rate || 0}%</p>
                    <p className="text-xs text-muted-foreground">Patch Compliance</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <p className="text-2xl font-bold">{stats?.compliance_score || 0}%</p>
                    <p className="text-xs text-muted-foreground">Compliance Score</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Incidents & SOC */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("reporting.totalIncidents")}
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.incidents_total || 0}</div>
                <div className="flex gap-2 mt-1">
                  <Badge variant="destructive">{stats?.incidents_critical || 0} critical</Badge>
                  <Badge variant="secondary">{stats?.incidents_open || 0} open</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("reporting.criticalAlerts")}
                </CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.alerts_today || 0}</div>
                <div className="flex gap-2 mt-1">
                  <Badge variant="destructive">{stats?.alerts_critical || 0} critical</Badge>
                  <Badge variant="secondary">{stats?.cases_open || 0} cases</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("reporting.totalVulnerabilities")}
                </CardTitle>
                <Bug className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.vulnerabilities_total || 0}</div>
                <div className="flex gap-2 mt-1">
                  <Badge variant="destructive">{stats?.vulnerabilities_critical || 0} critical</Badge>
                  <Badge variant="secondary">{stats?.vulnerabilities_overdue || 0} overdue</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("reporting.totalRisks")}
                </CardTitle>
                <Scale className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.risks_total || 0}</div>
                <div className="flex gap-2 mt-1">
                  <Badge variant="destructive">{stats?.risks_critical || 0} critical</Badge>
                  <Badge variant="secondary">{stats?.risks_requiring_treatment || 0} treatment</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Third-Party & Integrations */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Third-Party Risk</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.vendors_total || 0} Vendors</div>
                <div className="flex gap-2 mt-1">
                  <Badge variant="destructive">{stats?.vendors_high_risk || 0} high risk</Badge>
                  <Badge variant="secondary">{stats?.assessments_pending || 0} pending</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Integrations</CardTitle>
                <RefreshCw className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.integrations_active || 0} Active</div>
                <div className="flex gap-2 mt-1">
                  {stats?.integrations_with_errors ? (
                    <Badge variant="destructive">{stats.integrations_with_errors} errors</Badge>
                  ) : (
                    <Badge variant="default">All healthy</Badge>
                  )}
                  <Badge variant="secondary">{stats?.syncs_today || 0} syncs</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Compliance</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.compliance_score || 0}%</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {stats?.controls_implemented || 0} / {stats?.controls_total || 0} controls
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templatesData?.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("reporting.noTemplates")}</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => seedTemplatesMutation.mutate()}
                  >
                    Seed Default Templates
                  </Button>
                </CardContent>
              </Card>
            )}
            {templatesData?.map((template: ReportTemplate) => (
              <Card key={template.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <CardDescription className="text-xs">
                    {template.report_type.replace(/_/g, " ").toUpperCase()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">
                    {template.description || "No description"}
                  </p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {template.supported_formats?.map((format) => (
                      <Badge key={format} variant="outline">
                        {format.toUpperCase()}
                      </Badge>
                    ))}
                  </div>
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() => {
                      setSelectedTemplate(template);
                      setIsGenerateOpen(true);
                    }}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Generated Reports Tab */}
        <TabsContent value="reports" className="space-y-4">
          <div className="space-y-3">
            {reportsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Download className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("reporting.noReports")}</p>
                </CardContent>
              </Card>
            )}
            {reportsData?.items?.map((report: GeneratedReport) => {
              const FormatIcon = getFormatIcon(report.format);
              return (
                <Card key={report.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-muted rounded-lg">
                          <FormatIcon className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{report.name}</h3>
                            <Badge variant={getStatusBadgeVariant(report.status)}>
                              {report.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {report.report_id} • {report.report_type.replace(/_/g, " ")}
                          </p>
                          {report.period_start && report.period_end && (
                            <p className="text-xs text-muted-foreground">
                              Period: {new Date(report.period_start).toLocaleDateString()} -{" "}
                              {new Date(report.period_end).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className="flex gap-2">
                          {report.status === "completed" && (
                            <Button variant="outline" size="sm">
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground text-right">
                          {report.generated_at && (
                            <p>Generated: {new Date(report.generated_at).toLocaleString()}</p>
                          )}
                          {report.generation_time_seconds && (
                            <p>Time: {report.generation_time_seconds.toFixed(1)}s</p>
                          )}
                        </div>
                      </div>
                    </div>
                    {report.error_message && (
                      <p className="text-sm text-destructive mt-2 bg-destructive/10 p-2 rounded">
                        {report.error_message}
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Schedules Tab */}
        <TabsContent value="schedules" className="space-y-4">
          <div className="space-y-3">
            {schedulesData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("reporting.noSchedules")}</p>
                </CardContent>
              </Card>
            )}
            {schedulesData?.items?.map((schedule: ReportSchedule) => (
              <Card key={schedule.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-muted rounded-lg">
                        <Clock className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{schedule.name}</h3>
                          {schedule.is_enabled ? (
                            <Badge variant="default">Enabled</Badge>
                          ) : (
                            <Badge variant="secondary">Disabled</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {schedule.frequency} • {schedule.recipients.length} recipients
                        </p>
                        {schedule.description && (
                          <p className="text-xs text-muted-foreground">{schedule.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      {schedule.next_run_at && (
                        <p className="text-muted-foreground">
                          Next: {new Date(schedule.next_run_at).toLocaleString()}
                        </p>
                      )}
                      {schedule.last_run_at && (
                        <p className="text-muted-foreground">
                          Last: {new Date(schedule.last_run_at).toLocaleString()}
                        </p>
                      )}
                      {schedule.consecutive_failures > 0 && (
                        <p className="text-destructive">
                          {schedule.consecutive_failures} consecutive failures
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

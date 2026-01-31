"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Download,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Activity,
  Eye,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { auditAPI } from "@/lib/api-client";
import { formatDistanceToNow, format } from "date-fns";

interface AuditLog {
  id: string;
  user_id?: string;
  user_name?: string;
  user_email?: string;
  action: string;
  action_category?: string;
  resource_type?: string;
  resource_id?: string;
  resource_name?: string;
  description?: string;
  changes_summary?: string;
  ip_address?: string;
  user_agent?: string;
  request_id?: string;
  success: boolean;
  error_message?: string;
  severity: string;
  created_at: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
}

interface AuditStats {
  total_logs: number;
  logs_today: number;
  logs_this_week: number;
  critical_actions: number;
  failed_actions: number;
  active_users_today: number;
  actions_by_type: Record<string, number>;
  actions_by_resource: Record<string, number>;
  actions_by_severity: Record<string, number>;
  top_users: Array<{
    user_id: string;
    name: string;
    email: string;
    action_count: number;
  }>;
  recent_critical: AuditLog[];
}

interface AuditListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface AuditActions {
  actions: Array<{ value: string; label: string; category: string }>;
  categories: Array<{ value: string; label: string }>;
  resource_types: Array<{ value: string; label: string }>;
  severities: Array<{ value: string; label: string }>;
}

export default function AuditPage() {
  const { t } = useTranslations();
  const { token, user } = useAuthStore();
  const isAdmin = user?.role === "admin" || user?.role === "manager";

  // Filter state
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("");
  const [resourceFilter, setResourceFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [successFilter, setSuccessFilter] = useState<string>("");
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");
  const [isExporting, setIsExporting] = useState(false);

  // Detail dialog
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Fetch audit logs
  const { data: logsData, isLoading, refetch } = useQuery({
    queryKey: ["audit-logs", page, search, actionFilter, resourceFilter, severityFilter, successFilter],
    queryFn: () =>
      auditAPI.list(token!, {
        page,
        size: 25,
        search: search || undefined,
        action: actionFilter || undefined,
        resource_type: resourceFilter || undefined,
        severity: severityFilter || undefined,
        success: successFilter ? successFilter === "true" : undefined,
      }) as Promise<AuditListResponse>,
    enabled: !!token,
  });

  // Fetch stats (admin only)
  const { data: stats } = useQuery({
    queryKey: ["audit-stats"],
    queryFn: () => auditAPI.getStats(token!) as Promise<AuditStats>,
    enabled: !!token && isAdmin,
  });

  // Fetch available actions for filters
  const { data: actionsData } = useQuery({
    queryKey: ["audit-actions"],
    queryFn: () => auditAPI.getActions(token!) as Promise<AuditActions>,
    enabled: !!token,
  });

  // Fetch log detail
  const { data: logDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ["audit-log-detail", selectedLog?.id],
    queryFn: () => auditAPI.get(token!, selectedLog!.id) as Promise<AuditLog>,
    enabled: !!token && !!selectedLog,
  });

  // Handle export
  const handleExport = async () => {
    if (!token) return;

    setIsExporting(true);
    try {
      const { blob, filename } = await auditAPI.export(token, {
        format: exportFormat,
        action: actionFilter || undefined,
        resource_type: resourceFilter || undefined,
        severity: severityFilter || undefined,
      });

      // Download file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
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

  // Open log detail
  const openLogDetail = (log: AuditLog) => {
    setSelectedLog(log);
    setIsDetailOpen(true);
  };

  // Get severity badge color
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "critical":
        return <Badge variant="destructive">{t("audit.critical")}</Badge>;
      case "warning":
        return <Badge variant="outline" className="border-yellow-500 text-yellow-600">{t("audit.warning")}</Badge>;
      default:
        return <Badge variant="secondary">{t("audit.info")}</Badge>;
    }
  };

  // Get action badge
  const getActionBadge = (action: string) => {
    const colors: Record<string, string> = {
      create: "bg-green-100 text-green-800",
      update: "bg-blue-100 text-blue-800",
      delete: "bg-red-100 text-red-800",
      login: "bg-purple-100 text-purple-800",
      logout: "bg-gray-100 text-gray-800",
      login_failed: "bg-red-100 text-red-800",
      export: "bg-yellow-100 text-yellow-800",
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[action] || "bg-gray-100 text-gray-800"}`}>
        {action}
      </span>
    );
  };

  // Clear all filters
  const clearFilters = () => {
    setSearch("");
    setActionFilter("");
    setResourceFilter("");
    setSeverityFilter("");
    setSuccessFilter("");
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t("audit.title")}</h1>
          <p className="text-muted-foreground">{t("audit.subtitle")}</p>
        </div>
        {isAdmin && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button disabled={isExporting}>
                <Download className="h-4 w-4 mr-2" />
                {isExporting ? t("audit.exporting") : t("audit.export")}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => { setExportFormat("csv"); handleExport(); }}>
                {t("audit.exportCsv")}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => { setExportFormat("json"); handleExport(); }}>
                {t("audit.exportJson")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Stats Cards (Admin only) */}
      {isAdmin && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("audit.totalLogs")}</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_logs.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                {stats.logs_this_week.toLocaleString()} {t("audit.thisWeek")}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("audit.logsToday")}</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.logs_today}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_users_today} {t("audit.activeUsers")}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("audit.criticalActions")}</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{stats.critical_actions}</div>
              <p className="text-xs text-muted-foreground">{t("audit.requireAttention")}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{t("audit.failedActions")}</CardTitle>
              <XCircle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.failed_actions}</div>
              <p className="text-xs text-muted-foreground">{t("audit.unsuccessfulAttempts")}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="h-5 w-5" />
              {t("audit.filters")}
            </CardTitle>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                {t("audit.clearFilters")}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("audit.searchPlaceholder")}
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="pl-10"
              />
            </div>

            {/* Action filter */}
            <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v); setPage(1); }}>
              <SelectTrigger>
                <SelectValue placeholder={t("audit.allActions")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">{t("audit.allActions")}</SelectItem>
                {actionsData?.actions.map((action) => (
                  <SelectItem key={action.value} value={action.value}>
                    {action.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Resource filter */}
            <Select value={resourceFilter} onValueChange={(v) => { setResourceFilter(v); setPage(1); }}>
              <SelectTrigger>
                <SelectValue placeholder={t("audit.allResources")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">{t("audit.allResources")}</SelectItem>
                {actionsData?.resource_types.map((resource) => (
                  <SelectItem key={resource.value} value={resource.value}>
                    {resource.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Severity filter */}
            <Select value={severityFilter} onValueChange={(v) => { setSeverityFilter(v); setPage(1); }}>
              <SelectTrigger>
                <SelectValue placeholder={t("audit.allSeverities")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">{t("audit.allSeverities")}</SelectItem>
                <SelectItem value="info">{t("audit.info")}</SelectItem>
                <SelectItem value="warning">{t("audit.warning")}</SelectItem>
                <SelectItem value="critical">{t("audit.critical")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t("audit.activityLogs")}</CardTitle>
          <CardDescription>
            {logsData ? `${logsData.total.toLocaleString()} ${t("audit.totalRecords")}` : t("common.loading")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("audit.timestamp")}</TableHead>
                <TableHead>{t("audit.user")}</TableHead>
                <TableHead>{t("audit.action")}</TableHead>
                <TableHead>{t("audit.resource")}</TableHead>
                <TableHead>{t("audit.description")}</TableHead>
                <TableHead>{t("audit.status")}</TableHead>
                <TableHead>{t("audit.severity")}</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    {t("common.loading")}
                  </TableCell>
                </TableRow>
              ) : logsData?.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    {t("audit.noLogs")}
                  </TableCell>
                </TableRow>
              ) : (
                logsData?.items.map((log) => (
                  <TableRow key={log.id} className="cursor-pointer hover:bg-muted/50" onClick={() => openLogDetail(log)}>
                    <TableCell className="font-mono text-sm">
                      <div>{format(new Date(log.created_at), "yyyy-MM-dd")}</div>
                      <div className="text-muted-foreground text-xs">
                        {format(new Date(log.created_at), "HH:mm:ss")}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-medium">{log.user_name || t("audit.system")}</div>
                          <div className="text-xs text-muted-foreground">{log.user_email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{getActionBadge(log.action)}</TableCell>
                    <TableCell>
                      {log.resource_type && (
                        <div>
                          <span className="capitalize">{log.resource_type}</span>
                          {log.resource_name && (
                            <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                              {log.resource_name}
                            </div>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="max-w-[200px] truncate" title={log.description || log.changes_summary}>
                        {log.description || log.changes_summary || "-"}
                      </div>
                    </TableCell>
                    <TableCell>
                      {log.success ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                    </TableCell>
                    <TableCell>{getSeverityBadge(log.severity)}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); openLogDetail(log); }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Pagination */}
          {logsData && logsData.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                {t("audit.page")} {logsData.page} {t("audit.of")} {logsData.pages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(logsData.pages, p + 1))}
                  disabled={page === logsData.pages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Log Detail Dialog */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {t("audit.logDetails")}
            </DialogTitle>
            <DialogDescription>
              {selectedLog && format(new Date(selectedLog.created_at), "PPpp")}
            </DialogDescription>
          </DialogHeader>

          {loadingDetail ? (
            <div className="py-8 text-center">{t("common.loading")}</div>
          ) : logDetail ? (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.user")}</label>
                  <p className="font-medium">{logDetail.user_name || t("audit.system")}</p>
                  <p className="text-sm text-muted-foreground">{logDetail.user_email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.action")}</label>
                  <div className="flex items-center gap-2 mt-1">
                    {getActionBadge(logDetail.action)}
                    {getSeverityBadge(logDetail.severity)}
                  </div>
                </div>
              </div>

              {/* Resource */}
              {logDetail.resource_type && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.resource")}</label>
                  <p>
                    <span className="capitalize">{logDetail.resource_type}</span>
                    {logDetail.resource_id && (
                      <span className="text-muted-foreground ml-2">({logDetail.resource_id})</span>
                    )}
                  </p>
                  {logDetail.resource_name && (
                    <p className="text-sm text-muted-foreground">{logDetail.resource_name}</p>
                  )}
                </div>
              )}

              {/* Description */}
              {logDetail.description && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.description")}</label>
                  <p>{logDetail.description}</p>
                </div>
              )}

              {/* Changes */}
              {logDetail.changes_summary && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.changes")}</label>
                  <p className="text-sm">{logDetail.changes_summary}</p>
                </div>
              )}

              {/* Values */}
              {(logDetail.old_values || logDetail.new_values) && (
                <div className="grid grid-cols-2 gap-4">
                  {logDetail.old_values && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">{t("audit.oldValues")}</label>
                      <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto max-h-32">
                        {JSON.stringify(logDetail.old_values, null, 2)}
                      </pre>
                    </div>
                  )}
                  {logDetail.new_values && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">{t("audit.newValues")}</label>
                      <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto max-h-32">
                        {JSON.stringify(logDetail.new_values, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Request Info */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.ipAddress")}</label>
                  <p className="font-mono text-sm">{logDetail.ip_address || "-"}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.requestId")}</label>
                  <p className="font-mono text-sm">{logDetail.request_id || "-"}</p>
                </div>
              </div>

              {logDetail.user_agent && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">{t("audit.userAgent")}</label>
                  <p className="text-xs text-muted-foreground break-all">{logDetail.user_agent}</p>
                </div>
              )}

              {/* Error */}
              {!logDetail.success && logDetail.error_message && (
                <div className="bg-red-50 border border-red-200 rounded p-3">
                  <label className="text-sm font-medium text-red-800">{t("audit.error")}</label>
                  <p className="text-sm text-red-700">{logDetail.error_message}</p>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

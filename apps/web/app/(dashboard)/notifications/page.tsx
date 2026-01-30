"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  BellOff,
  Check,
  CheckCheck,
  Archive,
  Trash2,
  Settings,
  Webhook,
  AlertTriangle,
  Shield,
  Bug,
  Scale,
  Plug,
  FileText,
  Server,
  Mail,
  Plus,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
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
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { notificationsAPI } from "@/lib/api-client";
import { formatDistanceToNow } from "date-fns";

interface Notification {
  id: string;
  notification_type: string;
  priority: string;
  title: string;
  message?: string;
  entity_type?: string;
  entity_id?: string;
  entity_url?: string;
  data?: Record<string, any>;
  is_read: boolean;
  is_archived: boolean;
  created_at: string;
}

interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

interface NotificationPreference {
  id: string;
  notifications_enabled: boolean;
  email_enabled: boolean;
  email_frequency: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  channel_preferences?: Record<string, string[]>;
  min_priority_email: string;
  min_priority_sms: string;
}

interface Webhook {
  id: string;
  name: string;
  description?: string;
  url: string;
  method: string;
  subscribed_events: string[];
  is_active: boolean;
  last_triggered_at?: string;
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

export default function NotificationsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("notifications");
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [isWebhookDialogOpen, setIsWebhookDialogOpen] = useState(false);
  const [webhookForm, setWebhookForm] = useState({
    name: "",
    description: "",
    url: "",
    method: "POST",
    subscribed_events: [] as string[],
  });

  // Notifications
  const { data: notificationsData, isLoading: loadingNotifications } = useQuery({
    queryKey: ["notifications", showUnreadOnly],
    queryFn: () => notificationsAPI.listNotifications(token!, {
      size: 100,
      unread_only: showUnreadOnly,
    }) as Promise<PaginatedResponse<Notification>>,
    enabled: !!token,
    refetchInterval: 30000,
  });

  // Stats
  const { data: stats } = useQuery({
    queryKey: ["notification-stats"],
    queryFn: () => notificationsAPI.getStats(token!) as Promise<NotificationStats>,
    enabled: !!token,
    refetchInterval: 30000,
  });

  // Preferences
  const { data: preferences } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: () => notificationsAPI.getPreferences(token!) as Promise<NotificationPreference>,
    enabled: !!token && activeTab === "preferences",
  });

  // Webhooks
  const { data: webhooksData } = useQuery({
    queryKey: ["notification-webhooks"],
    queryFn: () => notificationsAPI.listWebhooks(token!, { size: 50 }) as Promise<PaginatedResponse<Webhook>>,
    enabled: !!token && activeTab === "webhooks",
  });

  // Mutations
  const markReadMutation = useMutation({
    mutationFn: (data: { notification_ids?: string[]; mark_all?: boolean }) =>
      notificationsAPI.markAsRead(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => notificationsAPI.archiveNotification(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationsAPI.deleteNotification(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
    },
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: (data: any) => notificationsAPI.updatePreferences(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });

  const createWebhookMutation = useMutation({
    mutationFn: (data: any) => notificationsAPI.createWebhook(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-webhooks"] });
      setIsWebhookDialogOpen(false);
      setWebhookForm({ name: "", description: "", url: "", method: "POST", subscribed_events: [] });
    },
  });

  const deleteWebhookMutation = useMutation({
    mutationFn: (id: string) => notificationsAPI.deleteWebhook(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-webhooks"] });
    },
  });

  const getNotificationIcon = (type: string) => {
    if (type.includes("incident")) return AlertTriangle;
    if (type.includes("alert")) return Shield;
    if (type.includes("vulnerability")) return Bug;
    if (type.includes("risk")) return Scale;
    if (type.includes("integration") || type.includes("sync")) return Plug;
    if (type.includes("report")) return FileText;
    return Bell;
  };

  const getPriorityBadgeVariant = (priority: string): "default" | "secondary" | "destructive" | "outline" => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "destructive",
      medium: "secondary",
      low: "outline",
    };
    return variants[priority] || "secondary";
  };

  const formatNotificationType = (type: string) => {
    return type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  };

  const notifications = notificationsData?.items || [];
  const webhooks = webhooksData?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("notifications.title")}</h1>
          <p className="text-muted-foreground">
            {stats?.unread || 0} unread of {stats?.total || 0} notifications
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => markReadMutation.mutate({ mark_all: true })}
            disabled={!stats?.unread}
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            {t("notifications.markAllRead")}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Unread</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.unread || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.by_priority?.critical || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">High</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.by_priority?.high || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            {t("notifications.all")}
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            {t("notifications.preferences")}
          </TabsTrigger>
          <TabsTrigger value="webhooks" className="flex items-center gap-2">
            <Webhook className="h-4 w-4" />
            {t("notifications.webhooks")}
          </TabsTrigger>
        </TabsList>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={showUnreadOnly}
                onCheckedChange={setShowUnreadOnly}
              />
              <Label>Show unread only</Label>
            </div>
          </div>

          <div className="space-y-2">
            {loadingNotifications ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : notifications.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <BellOff className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("notifications.noNotifications")}</p>
                </CardContent>
              </Card>
            ) : (
              notifications.map((notification) => {
                const Icon = getNotificationIcon(notification.notification_type);
                return (
                  <Card
                    key={notification.id}
                    className={notification.is_read ? "opacity-60" : "border-l-4 border-l-primary"}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg ${notification.is_read ? "bg-muted" : "bg-primary/10"}`}>
                          <Icon className={`h-5 w-5 ${notification.is_read ? "text-muted-foreground" : "text-primary"}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className={`font-medium ${notification.is_read ? "" : "font-semibold"}`}>
                              {notification.title}
                            </h3>
                            <Badge variant={getPriorityBadgeVariant(notification.priority)}>
                              {notification.priority}
                            </Badge>
                          </div>
                          {notification.message && (
                            <p className="text-sm text-muted-foreground mb-2">{notification.message}</p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{formatNotificationType(notification.notification_type)}</span>
                            <span>{formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}</span>
                            {notification.entity_url && (
                              <a
                                href={notification.entity_url}
                                className="flex items-center gap-1 text-primary hover:underline"
                              >
                                View <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          {!notification.is_read && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => markReadMutation.mutate({ notification_ids: [notification.id] })}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => archiveMutation.mutate(notification.id)}
                          >
                            <Archive className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteMutation.mutate(notification.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </div>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Configure how you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base">Enable Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive in-app notifications</p>
                </div>
                <Switch
                  checked={preferences?.notifications_enabled ?? true}
                  onCheckedChange={(checked) =>
                    updatePreferencesMutation.mutate({ notifications_enabled: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base">{t("notifications.emailEnabled")}</Label>
                  <p className="text-sm text-muted-foreground">Receive email notifications</p>
                </div>
                <Switch
                  checked={preferences?.email_enabled ?? true}
                  onCheckedChange={(checked) =>
                    updatePreferencesMutation.mutate({ email_enabled: checked })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>{t("notifications.emailFrequency")}</Label>
                <Select
                  value={preferences?.email_frequency || "instant"}
                  onValueChange={(value) =>
                    updatePreferencesMutation.mutate({ email_frequency: value })
                  }
                >
                  <SelectTrigger className="w-64">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instant">{t("notifications.instant")}</SelectItem>
                    <SelectItem value="hourly">{t("notifications.hourly")}</SelectItem>
                    <SelectItem value="daily">{t("notifications.daily")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base">{t("notifications.quietHoursEnabled")}</Label>
                  <p className="text-sm text-muted-foreground">Mute notifications during specific hours</p>
                </div>
                <Switch
                  checked={preferences?.quiet_hours_enabled ?? false}
                  onCheckedChange={(checked) =>
                    updatePreferencesMutation.mutate({ quiet_hours_enabled: checked })
                  }
                />
              </div>

              {preferences?.quiet_hours_enabled && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("notifications.quietHoursStart")}</Label>
                    <Input
                      type="time"
                      value={preferences?.quiet_hours_start || "22:00"}
                      onChange={(e) =>
                        updatePreferencesMutation.mutate({ quiet_hours_start: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("notifications.quietHoursEnd")}</Label>
                    <Input
                      type="time"
                      value={preferences?.quiet_hours_end || "08:00"}
                      onChange={(e) =>
                        updatePreferencesMutation.mutate({ quiet_hours_end: e.target.value })
                      }
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Priority Thresholds</CardTitle>
              <CardDescription>Set minimum priority for different channels</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Minimum Priority for Email</Label>
                  <Select
                    value={preferences?.min_priority_email || "medium"}
                    onValueChange={(value) =>
                      updatePreferencesMutation.mutate({ min_priority_email: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Minimum Priority for SMS</Label>
                  <Select
                    value={preferences?.min_priority_sms || "critical"}
                    onValueChange={(value) =>
                      updatePreferencesMutation.mutate({ min_priority_sms: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Webhooks Tab */}
        <TabsContent value="webhooks" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isWebhookDialogOpen} onOpenChange={setIsWebhookDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("notifications.addWebhook")}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>{t("notifications.addWebhook")}</DialogTitle>
                  <DialogDescription>
                    Configure a webhook to receive notifications at an external URL.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={webhookForm.name}
                      onChange={(e) => setWebhookForm({ ...webhookForm, name: e.target.value })}
                      placeholder="My Webhook"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={webhookForm.description}
                      onChange={(e) => setWebhookForm({ ...webhookForm, description: e.target.value })}
                      placeholder="Optional description"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("notifications.webhookUrl")}</Label>
                    <Input
                      value={webhookForm.url}
                      onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })}
                      placeholder="https://example.com/webhook"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Method</Label>
                    <Select
                      value={webhookForm.method}
                      onValueChange={(v) => setWebhookForm({ ...webhookForm, method: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="POST">POST</SelectItem>
                        <SelectItem value="PUT">PUT</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsWebhookDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={() => createWebhookMutation.mutate({
                      ...webhookForm,
                      subscribed_events: ["incident_created", "alert_critical"],
                    })}
                    disabled={!webhookForm.name || !webhookForm.url}
                  >
                    Create Webhook
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="space-y-3">
            {webhooks.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Webhook className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("notifications.noWebhooks")}</p>
                </CardContent>
              </Card>
            ) : (
              webhooks.map((webhook) => (
                <Card key={webhook.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-muted rounded-lg">
                          <Webhook className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{webhook.name}</h3>
                            <Badge variant={webhook.is_active ? "default" : "secondary"}>
                              {webhook.is_active ? t("notifications.active") : t("notifications.inactive")}
                            </Badge>
                            {webhook.consecutive_failures > 0 && (
                              <Badge variant="destructive">
                                {webhook.consecutive_failures} failures
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{webhook.url}</p>
                          {webhook.description && (
                            <p className="text-sm text-muted-foreground">{webhook.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <RefreshCw className="h-4 w-4 mr-1" />
                          Test
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteWebhookMutation.mutate(webhook.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

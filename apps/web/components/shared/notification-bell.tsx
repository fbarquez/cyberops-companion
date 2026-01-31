"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, ExternalLink, AlertTriangle, Info, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuthStore } from "@/stores/auth-store";
import { notificationsAPI } from "@/lib/api-client";
import {
  useNotificationWebSocket,
  type NotificationData,
  type NotificationStats,
} from "@/hooks/use-notification-websocket";
import { cn } from "@/lib/utils";

interface Notification {
  id: string;
  notification_type: string;
  priority: string;
  title: string;
  message: string | null;
  entity_type: string | null;
  entity_id: string | null;
  entity_url: string | null;
  is_read: boolean;
  created_at: string;
}

interface NotificationStatsResponse {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

function getPriorityIcon(priority: string) {
  switch (priority) {
    case "critical":
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case "high":
      return <AlertTriangle className="h-4 w-4 text-orange-500" />;
    case "medium":
      return <Info className="h-4 w-4 text-yellow-500" />;
    default:
      return <Info className="h-4 w-4 text-blue-500" />;
  }
}

function getRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

export function NotificationBell() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, isAuthenticated } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);

  // Fetch notification stats
  const { data: stats } = useQuery<NotificationStatsResponse>({
    queryKey: ["notification-stats"],
    queryFn: () => notificationsAPI.getStats(token!) as Promise<NotificationStatsResponse>,
    enabled: !!token && isAuthenticated,
    refetchInterval: 60000, // Fallback polling every minute
  });

  // Fetch recent notifications when dropdown opens
  const { data: notifications } = useQuery<{ items: Notification[] }>({
    queryKey: ["notifications-recent"],
    queryFn: () =>
      notificationsAPI.listNotifications(token!, {
        size: 5,
        unread_only: false,
      }) as Promise<{ items: Notification[] }>,
    enabled: !!token && isAuthenticated && isOpen,
  });

  // Handle new notification from WebSocket
  const handleNewNotification = useCallback(
    (notification: NotificationData) => {
      // Show toast notification
      const toastType =
        notification.priority === "critical" || notification.priority === "high"
          ? "error"
          : "info";

      if (toastType === "error") {
        toast.error(notification.title, {
          description: notification.message || undefined,
          action: notification.entity_url
            ? {
                label: "View",
                onClick: () => router.push(notification.entity_url!),
              }
            : undefined,
        });
      } else {
        toast.info(notification.title, {
          description: notification.message || undefined,
          action: notification.entity_url
            ? {
                label: "View",
                onClick: () => router.push(notification.entity_url!),
              }
            : undefined,
        });
      }

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    [queryClient, router]
  );

  // Handle stats update from WebSocket
  const handleStatsUpdate = useCallback(
    (newStats: NotificationStats) => {
      // Update stats in cache
      queryClient.setQueryData(["notification-stats"], newStats);
    },
    [queryClient]
  );

  // Connect to WebSocket
  const { isConnected } = useNotificationWebSocket({
    onNotification: handleNewNotification,
    onStatsUpdate: handleStatsUpdate,
  });

  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    if (!token) return;

    try {
      await notificationsAPI.markAsRead(token, {
        notification_ids: [notificationId],
      });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    } catch (e) {
      console.error("Failed to mark notification as read:", e);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    if (!token) return;

    try {
      await notificationsAPI.markAsRead(token, { mark_all: true });
      queryClient.invalidateQueries({ queryKey: ["notification-stats"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-recent"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast.success("All notifications marked as read");
    } catch (e) {
      console.error("Failed to mark all as read:", e);
    }
  };

  const unreadCount = stats?.unread || 0;

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
          {/* Connection indicator */}
          <span
            className={cn(
              "absolute bottom-0 right-0 h-2 w-2 rounded-full border border-background",
              isConnected ? "bg-green-500" : "bg-gray-400"
            )}
          />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-1 text-xs"
              onClick={markAllAsRead}
            >
              <Check className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <ScrollArea className="h-[300px]">
          {notifications?.items && notifications.items.length > 0 ? (
            notifications.items.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                className={cn(
                  "flex flex-col items-start p-3 cursor-pointer",
                  !notification.is_read && "bg-muted/50"
                )}
                onClick={() => {
                  if (!notification.is_read) {
                    markAsRead(notification.id);
                  }
                  if (notification.entity_url) {
                    router.push(notification.entity_url);
                  }
                  setIsOpen(false);
                }}
              >
                <div className="flex items-start gap-2 w-full">
                  {getPriorityIcon(notification.priority)}
                  <div className="flex-1 min-w-0">
                    <p
                      className={cn(
                        "text-sm truncate",
                        !notification.is_read && "font-medium"
                      )}
                    >
                      {notification.title}
                    </p>
                    {notification.message && (
                      <p className="text-xs text-muted-foreground truncate mt-0.5">
                        {notification.message}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {getRelativeTime(notification.created_at)}
                    </p>
                  </div>
                  {notification.entity_url && (
                    <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
                  )}
                </div>
              </DropdownMenuItem>
            ))
          ) : (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No notifications
            </div>
          )}
        </ScrollArea>

        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="justify-center text-primary"
          onClick={() => {
            router.push("/notifications");
            setIsOpen(false);
          }}
        >
          View all notifications
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

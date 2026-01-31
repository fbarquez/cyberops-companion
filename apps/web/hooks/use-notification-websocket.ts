"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";

// WebSocket event types
export type NotificationEvent =
  | "notification:new"
  | "notification:read"
  | "notification:deleted"
  | "stats:updated"
  | "connection:established"
  | "connection:error";

export interface NotificationData {
  id: string;
  type: string | null;
  priority: string | null;
  title: string;
  message: string | null;
  entity_type: string | null;
  entity_id: string | null;
  entity_url: string | null;
  is_read: boolean;
  created_at: string | null;
}

export interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface WebSocketMessage {
  event: NotificationEvent;
  data: NotificationData | NotificationStats | Record<string, unknown>;
  timestamp: string;
}

export interface UseNotificationWebSocketOptions {
  onNotification?: (notification: NotificationData) => void;
  onStatsUpdate?: (stats: NotificationStats) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseNotificationWebSocketReturn {
  isConnected: boolean;
  connectionState: "connecting" | "connected" | "disconnected" | "error";
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
}

/**
 * Hook for managing WebSocket connection to receive real-time notifications.
 *
 * @example
 * const { isConnected, lastMessage } = useNotificationWebSocket({
 *   onNotification: (notification) => {
 *     toast.info(notification.title);
 *     queryClient.invalidateQueries(['notifications']);
 *   },
 *   onStatsUpdate: (stats) => {
 *     setUnreadCount(stats.unread);
 *   },
 * });
 */
export function useNotificationWebSocket(
  options: UseNotificationWebSocketOptions = {}
): UseNotificationWebSocketReturn {
  const {
    onNotification,
    onStatsUpdate,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
  } = options;

  const { token, isAuthenticated } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [connectionState, setConnectionState] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("disconnected");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const isConnected = connectionState === "connected";

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    if (!token) return null;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
    const wsHost = apiUrl.replace(/^https?:\/\//, "");

    return `${wsProtocol}://${wsHost}/api/v1/ws/notifications?token=${token}`;
  }, [token]);

  // Handle incoming messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(message);

        switch (message.event) {
          case "notification:new":
            onNotification?.(message.data as NotificationData);
            break;

          case "stats:updated":
            onStatsUpdate?.(message.data as NotificationStats);
            break;

          case "connection:established":
            // Connection confirmed by server
            break;

          default:
            // Handle other events
            break;
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    },
    [onNotification, onStatsUpdate]
  );

  // Start ping interval to keep connection alive
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Ping every 30 seconds
  }, []);

  // Stop ping interval
  const stopPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    const wsUrl = getWebSocketUrl();
    if (!wsUrl || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionState("connecting");

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionState("connected");
        reconnectAttemptsRef.current = 0;
        startPingInterval();
        onConnect?.();
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        setConnectionState("disconnected");
        stopPingInterval();
        onDisconnect?.();

        // Auto reconnect if enabled and not a normal close
        if (
          autoReconnect &&
          event.code !== 1000 &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setConnectionState("error");
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (e) {
      setConnectionState("error");
      console.error("Failed to create WebSocket connection:", e);
    }
  }, [
    getWebSocketUrl,
    handleMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    startPingInterval,
    stopPingInterval,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Stop ping interval
    stopPingInterval();

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected");
      wsRef.current = null;
    }

    setConnectionState("disconnected");
    reconnectAttemptsRef.current = 0;
  }, [stopPingInterval]);

  // Auto-connect when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, token, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    connectionState,
    connect,
    disconnect,
    lastMessage,
  };
}

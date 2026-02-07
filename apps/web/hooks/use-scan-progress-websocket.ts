"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";

// WebSocket event types for scan progress
export type ScanProgressEvent =
  | "scan:started"
  | "scan:progress"
  | "scan:completed"
  | "scan:failed"
  | "scan:cancelled"
  | "connection:established";

export interface ScanProgressData {
  scan_id: string;
  progress_percent: number;
  state: "pending" | "running" | "completed" | "failed" | "cancelled";
  hosts_total: number;
  hosts_completed: number;
  current_host?: string | null;
  message?: string | null;
  error?: string | null;
  total_findings?: number;
  severity_counts?: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

export interface ScanProgressMessage {
  event: ScanProgressEvent;
  data: ScanProgressData;
  timestamp: string;
}

export interface UseScanProgressWebSocketOptions {
  scanId: string;
  onProgress?: (data: ScanProgressData) => void;
  onStarted?: (data: ScanProgressData) => void;
  onCompleted?: (data: ScanProgressData) => void;
  onFailed?: (data: ScanProgressData) => void;
  onCancelled?: (data: ScanProgressData) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  enabled?: boolean;
}

export interface UseScanProgressWebSocketReturn {
  isConnected: boolean;
  connectionState: "connecting" | "connected" | "disconnected" | "error";
  progress: ScanProgressData | null;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for managing WebSocket connection to receive real-time scan progress updates.
 *
 * @example
 * const { isConnected, progress } = useScanProgressWebSocket({
 *   scanId: "scan-123",
 *   onProgress: (data) => {
 *     console.log(`Scan ${data.progress_percent}% complete`);
 *   },
 *   onCompleted: (data) => {
 *     toast.success(`Scan completed with ${data.total_findings} findings`);
 *     queryClient.invalidateQueries(['scan', scanId]);
 *   },
 * });
 */
export function useScanProgressWebSocket(
  options: UseScanProgressWebSocketOptions
): UseScanProgressWebSocketReturn {
  const {
    scanId,
    onProgress,
    onStarted,
    onCompleted,
    onFailed,
    onCancelled,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    enabled = true,
  } = options;

  const { token, isAuthenticated } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [connectionState, setConnectionState] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("disconnected");
  const [progress, setProgress] = useState<ScanProgressData | null>(null);

  const isConnected = connectionState === "connected";

  // Get WebSocket URL for scan progress
  const getWebSocketUrl = useCallback(() => {
    if (!token || !scanId) return null;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
    const wsHost = apiUrl.replace(/^https?:\/\//, "");

    return `${wsProtocol}://${wsHost}/api/v1/ws/scans/${scanId}/progress?token=${token}`;
  }, [token, scanId]);

  // Handle incoming messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: ScanProgressMessage = JSON.parse(event.data);

        // Handle pong responses
        if ((message as unknown as { type: string }).type === "pong") {
          return;
        }

        const eventType = message.event;
        const data = message.data;

        // Update local progress state
        if (data) {
          setProgress(data);
        }

        switch (eventType) {
          case "scan:started":
            onStarted?.(data);
            break;

          case "scan:progress":
            onProgress?.(data);
            break;

          case "scan:completed":
            onCompleted?.(data);
            // Stop reconnecting after completion
            reconnectAttemptsRef.current = maxReconnectAttempts;
            break;

          case "scan:failed":
            onFailed?.(data);
            // Stop reconnecting after failure
            reconnectAttemptsRef.current = maxReconnectAttempts;
            break;

          case "scan:cancelled":
            onCancelled?.(data);
            // Stop reconnecting after cancellation
            reconnectAttemptsRef.current = maxReconnectAttempts;
            break;

          case "connection:established":
            // Connection confirmed by server
            break;

          default:
            break;
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    },
    [onProgress, onStarted, onCompleted, onFailed, onCancelled, maxReconnectAttempts]
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
    }, 30000);
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

      ws.onerror = () => {
        setConnectionState("error");
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

  // Auto-connect when authenticated and enabled
  useEffect(() => {
    if (isAuthenticated && token && enabled && scanId) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, token, enabled, scanId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    connectionState,
    progress,
    connect,
    disconnect,
  };
}

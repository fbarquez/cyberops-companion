"use client";

import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Shield,
  Server,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  Ban,
  Wifi,
  WifiOff,
} from "lucide-react";

import {
  useScanProgressWebSocket,
  ScanProgressData,
} from "@/hooks/use-scan-progress-websocket";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ScanProgressCardProps {
  scanId: string;
  scanName?: string;
  onComplete?: (data: ScanProgressData) => void;
  onCancel?: () => void;
  showCancelButton?: boolean;
  className?: string;
}

const stateConfig = {
  pending: {
    icon: Loader2,
    label: "Pending",
    color: "text-muted-foreground",
    bgColor: "bg-muted",
    badgeVariant: "secondary" as const,
  },
  running: {
    icon: Loader2,
    label: "Scanning",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    badgeVariant: "default" as const,
  },
  completed: {
    icon: CheckCircle2,
    label: "Completed",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    badgeVariant: "default" as const,
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    badgeVariant: "destructive" as const,
  },
  cancelled: {
    icon: Ban,
    label: "Cancelled",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    badgeVariant: "secondary" as const,
  },
};

const severityColors = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-blue-500",
  info: "bg-gray-400",
};

export function ScanProgressCard({
  scanId,
  scanName,
  onComplete,
  onCancel,
  showCancelButton = true,
  className,
}: ScanProgressCardProps) {
  const queryClient = useQueryClient();
  const [isFinished, setIsFinished] = useState(false);

  const { isConnected, connectionState, progress } = useScanProgressWebSocket({
    scanId,
    enabled: !isFinished,
    onStarted: (data) => {
      toast.info(`Scan started: ${scanName || data.scan_id}`);
    },
    onProgress: () => {
      // Progress updates are handled via the progress state
    },
    onCompleted: (data) => {
      setIsFinished(true);
      toast.success(
        `Scan completed! Found ${data.total_findings || 0} vulnerabilities`,
        {
          description: `Critical: ${data.severity_counts?.critical || 0}, High: ${data.severity_counts?.high || 0}`,
        }
      );
      queryClient.invalidateQueries({ queryKey: ["scans"] });
      queryClient.invalidateQueries({ queryKey: ["vulnerabilities"] });
      queryClient.invalidateQueries({ queryKey: ["vuln-stats"] });
      onComplete?.(data);
    },
    onFailed: (data) => {
      setIsFinished(true);
      toast.error("Scan failed", {
        description: data.error || "An unexpected error occurred",
      });
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
    onCancelled: () => {
      setIsFinished(true);
      toast.warning("Scan was cancelled");
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });

  // Get current state configuration
  const currentState = progress?.state || "pending";
  const config = stateConfig[currentState];
  const StateIcon = config.icon;

  // Calculate progress bar color based on state
  const getProgressColor = () => {
    switch (currentState) {
      case "running":
        return "bg-blue-500";
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "cancelled":
        return "bg-orange-500";
      default:
        return "bg-primary";
    }
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">
              {scanName || "Vulnerability Scan"}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {/* Connection indicator */}
            <div className="flex items-center gap-1">
              {isConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="text-xs text-muted-foreground">
                {connectionState === "connecting" ? "Connecting..." : ""}
              </span>
            </div>
            {/* State badge */}
            <Badge variant={config.badgeVariant} className="gap-1">
              <StateIcon
                className={cn(
                  "h-3 w-3",
                  currentState === "running" && "animate-spin"
                )}
              />
              {config.label}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {progress?.message || "Initializing scan..."}
            </span>
            <span className="font-medium">
              {progress?.progress_percent || 0}%
            </span>
          </div>
          <Progress
            value={progress?.progress_percent || 0}
            className="h-2"
            indicatorClassName={getProgressColor()}
          />
        </div>

        {/* Host progress */}
        {(progress?.hosts_total ?? 0) > 0 && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <Server className="h-4 w-4 text-muted-foreground" />
              <span>
                Hosts: {progress?.hosts_completed || 0} / {progress?.hosts_total}
              </span>
            </div>
            {progress?.current_host && (
              <span className="text-muted-foreground">
                Current: {progress.current_host}
              </span>
            )}
          </div>
        )}

        {/* Error message */}
        {currentState === "failed" && progress?.error && (
          <div className="flex items-start gap-2 rounded-md bg-red-500/10 p-3 text-sm text-red-500">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{progress.error}</span>
          </div>
        )}

        {/* Findings summary (when completed) */}
        {currentState === "completed" && progress?.severity_counts && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Findings Summary</span>
              <span className="text-sm text-muted-foreground">
                Total: {progress.total_findings || 0}
              </span>
            </div>
            <div className="flex gap-2">
              {Object.entries(progress.severity_counts).map(([severity, count]) => (
                <div
                  key={severity}
                  className="flex items-center gap-1.5 rounded-md bg-muted px-2 py-1"
                >
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      severityColors[severity as keyof typeof severityColors]
                    )}
                  />
                  <span className="text-xs capitalize">{severity}</span>
                  <span className="text-xs font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cancel button */}
        {showCancelButton &&
          currentState === "running" &&
          onCancel && (
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                className="text-orange-500 hover:text-orange-600"
              >
                <Ban className="h-4 w-4 mr-1" />
                Cancel Scan
              </Button>
            </div>
          )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact version of ScanProgressCard for use in lists or smaller spaces
 */
export function ScanProgressCompact({
  scanId,
  scanName,
  onComplete,
  className,
}: Omit<ScanProgressCardProps, "showCancelButton" | "onCancel">) {
  const queryClient = useQueryClient();
  const [isFinished, setIsFinished] = useState(false);

  const { progress } = useScanProgressWebSocket({
    scanId,
    enabled: !isFinished,
    onCompleted: (data) => {
      setIsFinished(true);
      queryClient.invalidateQueries({ queryKey: ["scans"] });
      onComplete?.(data);
    },
    onFailed: () => {
      setIsFinished(true);
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
    onCancelled: () => {
      setIsFinished(true);
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });

  const currentState = progress?.state || "pending";
  const config = stateConfig[currentState];
  const StateIcon = config.icon;

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <StateIcon
        className={cn(
          "h-4 w-4",
          config.color,
          currentState === "running" && "animate-spin"
        )}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-medium truncate">
            {scanName || "Scan"}
          </span>
          <span className="text-xs text-muted-foreground">
            {progress?.progress_percent || 0}%
          </span>
        </div>
        <Progress
          value={progress?.progress_percent || 0}
          className="h-1.5 mt-1"
        />
      </div>
    </div>
  );
}

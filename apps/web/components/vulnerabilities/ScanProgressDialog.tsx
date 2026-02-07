"use client";

import { useState } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { X } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScanProgressCard } from "./ScanProgressCard";
import { ScanProgressData } from "@/hooks/use-scan-progress-websocket";
import { useAuthStore } from "@/stores/auth-store";

interface ScanProgressDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  scanId: string;
  scanName?: string;
  onComplete?: (data: ScanProgressData) => void;
}

export function ScanProgressDialog({
  open,
  onOpenChange,
  scanId,
  scanName,
  onComplete,
}: ScanProgressDialogProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [isCompleted, setIsCompleted] = useState(false);

  // Cancel scan mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/vulnerabilities/scans/${scanId}/cancel`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to cancel scan");
      }
      return response.json();
    },
    onSuccess: () => {
      toast.info("Scan cancellation requested");
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to cancel scan");
    },
  });

  const handleComplete = (data: ScanProgressData) => {
    setIsCompleted(true);
    onComplete?.(data);
  };

  const handleClose = () => {
    if (isCompleted) {
      onOpenChange(false);
      setIsCompleted(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            Scan Progress
            {isCompleted && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onOpenChange(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </DialogTitle>
        </DialogHeader>

        <ScanProgressCard
          scanId={scanId}
          scanName={scanName}
          onComplete={handleComplete}
          onCancel={() => cancelMutation.mutate()}
          showCancelButton={!isCompleted && !cancelMutation.isPending}
        />

        {isCompleted && (
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <Button
              onClick={() => {
                onOpenChange(false);
                // Navigate to scan results - could emit an event or use router
              }}
            >
              View Results
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * Hook to manage scan progress dialog state
 */
export function useScanProgressDialog() {
  const [dialogState, setDialogState] = useState<{
    open: boolean;
    scanId: string;
    scanName?: string;
  }>({
    open: false,
    scanId: "",
    scanName: undefined,
  });

  const openDialog = (scanId: string, scanName?: string) => {
    setDialogState({ open: true, scanId, scanName });
  };

  const closeDialog = () => {
    setDialogState((prev) => ({ ...prev, open: false }));
  };

  return {
    dialogState,
    openDialog,
    closeDialog,
    setOpen: (open: boolean) =>
      setDialogState((prev) => ({ ...prev, open })),
  };
}

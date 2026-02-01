"use client";

import { useEffect, useState, useCallback } from "react";
import { AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { onRateLimitExceeded, RateLimitInfo } from "@/lib/api-client";
import { Button } from "@/components/ui/button";

interface RateLimitBannerProps {
  className?: string;
}

export function RateLimitBanner({ className }: RateLimitBannerProps) {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [countdown, setCountdown] = useState<number>(0);
  const [dismissed, setDismissed] = useState(false);

  // Subscribe to rate limit events
  useEffect(() => {
    const unsubscribe = onRateLimitExceeded((info) => {
      setRateLimitInfo(info);
      setCountdown(info.retryAfter || 60);
      setDismissed(false);
    });

    return () => unsubscribe();
  }, []);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) {
      setRateLimitInfo(null);
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setRateLimitInfo(null);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
  }, []);

  // Format countdown as mm:ss
  const formatCountdown = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!rateLimitInfo || dismissed) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed top-0 left-0 right-0 z-50 bg-amber-500 text-amber-950 px-4 py-3",
        "shadow-md",
        className
      )}
      role="alert"
    >
      <div className="container mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
            <span className="font-medium">Rate limit exceeded</span>
            <span className="text-sm opacity-90">
              Too many requests. Please wait {formatCountdown(countdown)} before
              trying again.
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-amber-950 hover:bg-amber-600 hover:text-amber-950"
          onClick={handleDismiss}
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Dismiss</span>
        </Button>
      </div>
    </div>
  );
}

// Hook for components that need to handle rate limit state
export function useRateLimitState() {
  const [isRateLimited, setIsRateLimited] = useState(false);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);

  useEffect(() => {
    const unsubscribe = onRateLimitExceeded((info) => {
      setIsRateLimited(true);
      setRetryAfter(info.retryAfter || 60);

      // Auto-reset after retry period
      const timeout = setTimeout(() => {
        setIsRateLimited(false);
        setRetryAfter(null);
      }, (info.retryAfter || 60) * 1000);

      return () => clearTimeout(timeout);
    });

    return () => unsubscribe();
  }, []);

  return { isRateLimited, retryAfter };
}

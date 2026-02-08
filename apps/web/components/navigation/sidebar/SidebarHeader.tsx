"use client";

import { Shield, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";

export function SidebarHeader() {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="flex h-16 items-center border-b px-4">
      <div className="flex items-center gap-3">
        <div className="relative">
          <Shield className="h-8 w-8 text-primary" />
          <Sparkles className="absolute -right-1 -top-1 h-3 w-3 text-primary animate-pulse" />
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col">
            <span className="text-base font-semibold leading-tight">ISORA</span>
            <span className="text-xs text-muted-foreground leading-tight">Risk Assurance</span>
          </div>
        )}
      </div>
    </div>
  );
}

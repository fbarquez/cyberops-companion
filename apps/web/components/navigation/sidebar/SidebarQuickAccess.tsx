"use client";

import Link from "next/link";
import { Clock, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/hooks/use-translations";

export function SidebarQuickAccess() {
  const { sidebarCollapsed, quickAccess, clearQuickAccess, setSidebarOpen } = useUIStore();
  const { t } = useTranslations();

  if (sidebarCollapsed || quickAccess.length === 0) {
    return null;
  }

  return (
    <div className="border-t px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>Recent</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5"
          onClick={clearQuickAccess}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
      <div className="space-y-1">
        {quickAccess.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setSidebarOpen(false)}
            className="block rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground truncate"
          >
            {item.label}
          </Link>
        ))}
      </div>
    </div>
  );
}

"use client";

import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";

interface SidebarNavGroupProps {
  id: string;
  label: string;
  children: React.ReactNode;
}

export function SidebarNavGroup({ id, label, children }: SidebarNavGroupProps) {
  const { sidebarCollapsed, expandedGroups, toggleGroup } = useUIStore();
  const isExpanded = expandedGroups[id] ?? false;

  if (sidebarCollapsed) {
    return <div className="space-y-1 py-1">{children}</div>;
  }

  return (
    <div className="space-y-1">
      <button
        onClick={() => toggleGroup(id)}
        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground"
      >
        <ChevronRight
          className={cn(
            "h-3 w-3 transition-transform duration-200",
            isExpanded && "rotate-90"
          )}
        />
        <span>{label}</span>
      </button>
      <div
        className={cn(
          "overflow-hidden transition-all duration-200",
          isExpanded ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="space-y-1 pl-2">{children}</div>
      </div>
    </div>
  );
}

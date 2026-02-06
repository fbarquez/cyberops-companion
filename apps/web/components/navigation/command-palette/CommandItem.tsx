"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface CommandItemProps {
  icon: LucideIcon;
  label: string;
  description?: string;
  shortcut?: string;
  isActive?: boolean;
  onClick: () => void;
}

export function CommandItem({
  icon: Icon,
  label,
  description,
  shortcut,
  isActive,
  onClick,
}: CommandItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
        isActive
          ? "bg-primary/10 text-primary"
          : "text-foreground hover:bg-accent"
      )}
    >
      <Icon className={cn("h-4 w-4 flex-shrink-0", isActive && "text-primary")} />
      <div className="flex-1 text-left">
        <div className="font-medium">{label}</div>
        {description && (
          <div className="text-xs text-muted-foreground">{description}</div>
        )}
      </div>
      {shortcut && (
        <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
          {shortcut}
        </kbd>
      )}
    </button>
  );
}

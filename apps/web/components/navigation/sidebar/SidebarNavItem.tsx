"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { LucideIcon } from "lucide-react";

interface SidebarNavItemProps {
  href: string;
  icon: LucideIcon;
  label: string;
  badge?: string | number;
  onClick?: () => void;
}

export function SidebarNavItem({
  href,
  icon: Icon,
  label,
  badge,
  onClick,
}: SidebarNavItemProps) {
  const pathname = usePathname();
  const { sidebarCollapsed, addToQuickAccess, setSidebarOpen } = useUIStore();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  const handleClick = () => {
    // Track page visit for quick access
    addToQuickAccess({
      href,
      label,
      icon: Icon.displayName || "FileText",
    });
    // Close mobile sidebar
    setSidebarOpen(false);
    onClick?.();
  };

  return (
    <Link
      href={href}
      onClick={handleClick}
      className={cn(
        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-150",
        isActive
          ? "bg-primary/10 text-primary dark:bg-primary/20"
          : "text-muted-foreground hover:bg-accent hover:text-foreground",
        sidebarCollapsed && "justify-center px-2"
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 flex-shrink-0 transition-colors",
          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
        )}
      />
      {!sidebarCollapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {badge !== undefined && (
            <span
              className={cn(
                "flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-xs font-medium",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {badge}
            </span>
          )}
        </>
      )}
    </Link>
  );
}

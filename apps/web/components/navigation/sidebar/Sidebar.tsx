"use client";

import { ChevronLeft, ChevronRight, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarNav } from "./SidebarNav";
import { SidebarQuickAccess } from "./SidebarQuickAccess";

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebarCollapse } = useUIStore();
  const { logout, user } = useAuthStore();
  const { t } = useTranslations();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col h-screen bg-card border-r transition-all duration-300 ease-in-out",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      <SidebarHeader />
      <SidebarNav />
      <SidebarQuickAccess />

      {/* User Section */}
      <div className="border-t p-3 space-y-2">
        {user && !sidebarCollapsed && (
          <div className="px-3 py-2 text-sm">
            <div className="font-medium truncate">{user.full_name}</div>
            <div className="text-muted-foreground text-xs truncate">
              {user.email}
            </div>
          </div>
        )}

        <div className={cn("flex gap-2", sidebarCollapsed ? "flex-col" : "flex-row")}>
          <Button
            variant="ghost"
            className={cn(
              "flex-1 justify-start",
              sidebarCollapsed && "justify-center px-2"
            )}
            onClick={logout}
          >
            <LogOut className="h-4 w-4" />
            {!sidebarCollapsed && <span className="ml-2">{t("nav.logout")}</span>}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={toggleSidebarCollapse}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </aside>
  );
}

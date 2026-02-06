"use client";

import {
  Home,
  AlertTriangle,
  Bell,
  Radar,
  Bug,
  Scale,
  Route,
  Server,
  Building2,
  ShieldCheck,
  Building,
  Globe,
  RefreshCw,
  FileText,
  GraduationCap,
  BarChart3,
  BookOpen,
  Map,
  Users,
  ClipboardList,
  Plug,
  PlayCircle,
  Sparkles,
} from "lucide-react";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarNavGroup } from "./SidebarNavGroup";
import { useTranslations } from "@/hooks/use-translations";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { useCopilot } from "@/components/copilot/CopilotProvider";

export function SidebarNav() {
  const { t } = useTranslations();
  const { sidebarCollapsed } = useUIStore();
  const { openChat, health } = useCopilot();
  const isConnected = health?.status === "healthy";

  return (
    <nav className="flex-1 space-y-2 overflow-y-auto px-3 py-4">
      {/* Home */}
      <SidebarNavItem href="/home" icon={Home} label={t("nav.home")} />

      {/* Operations */}
      <SidebarNavGroup id="operations" label="Operations">
        <SidebarNavItem href="/incidents" icon={AlertTriangle} label={t("nav.incidents")} />
        <SidebarNavItem href="/soc" icon={Bell} label={t("nav.soc")} />
        <SidebarNavItem href="/threats" icon={Radar} label={t("nav.threats")} />
        <SidebarNavItem href="/vulnerabilities" icon={Bug} label={t("nav.vulnerabilities")} />
      </SidebarNavGroup>

      {/* Security */}
      <SidebarNavGroup id="security" label="Security">
        <SidebarNavItem href="/risks" icon={Scale} label={t("nav.risks")} />
        <SidebarNavItem href="/attack-paths" icon={Route} label={t("nav.attackPaths")} />
        <SidebarNavItem href="/cmdb" icon={Server} label={t("nav.cmdb")} />
        <SidebarNavItem href="/tprm" icon={Building2} label={t("nav.tprm")} />
      </SidebarNavGroup>

      {/* Compliance */}
      <SidebarNavGroup id="compliance" label="Compliance">
        <SidebarNavItem href="/compliance/iso27001" icon={ShieldCheck} label={t("nav.iso27001")} />
        <SidebarNavItem href="/compliance/bsi" icon={Building} label={t("nav.bsi")} />
        <SidebarNavItem href="/compliance/nis2" icon={Globe} label={t("nav.nis2")} />
        <SidebarNavItem href="/bcm" icon={RefreshCw} label={t("nav.bcm")} />
      </SidebarNavGroup>

      {/* Management */}
      <SidebarNavGroup id="management" label="Management">
        <SidebarNavItem href="/documents" icon={FileText} label={t("nav.documents")} />
        <SidebarNavItem href="/training" icon={GraduationCap} label={t("nav.training")} />
        <SidebarNavItem href="/reporting" icon={BarChart3} label={t("nav.reporting")} />
        <SidebarNavItem href="/notifications" icon={Bell} label={t("nav.notifications")} />
      </SidebarNavGroup>

      {/* Tools */}
      <SidebarNavGroup id="tools" label="Tools">
        <SidebarNavItem href="/tools/playbook" icon={BookOpen} label={t("nav.playbook")} />
        <SidebarNavItem href="/tools/templates" icon={FileText} label={t("nav.templates")} />
        <SidebarNavItem href="/tools/lessons" icon={GraduationCap} label={t("nav.lessons")} />
        <SidebarNavItem href="/tools/navigator" icon={Map} label={t("nav.navigator")} />
      </SidebarNavGroup>

      {/* Administration */}
      <SidebarNavGroup id="administration" label="Administration">
        <SidebarNavItem href="/users" icon={Users} label={t("nav.users")} />
        <SidebarNavItem href="/audit" icon={ClipboardList} label={t("nav.audit")} />
        <SidebarNavItem href="/integrations" icon={Plug} label={t("nav.integrations")} />
        <SidebarNavItem href="/simulation" icon={PlayCircle} label={t("nav.simulation")} />
      </SidebarNavGroup>

      {/* Copilot - Special Entry */}
      <div className="pt-4 mt-4 border-t">
        <button
          onClick={openChat}
          className={cn(
            "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-150",
            "bg-gradient-to-r from-primary/5 to-primary/10 hover:from-primary/10 hover:to-primary/20",
            "text-primary border border-primary/20 hover:border-primary/40",
            sidebarCollapsed && "justify-center px-2"
          )}
        >
          <div className="relative">
            <Sparkles className="h-4 w-4" />
            {isConnected && (
              <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            )}
          </div>
          {!sidebarCollapsed && (
            <>
              <span className="flex-1 text-left">AI Copilot</span>
              <span className="text-xs opacity-60">⌘K</span>
            </>
          )}
        </button>
      </div>
    </nav>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  AlertTriangle,
  PlayCircle,
  BookOpen,
  FileText,
  GraduationCap,
  Map,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield,
  Crosshair,
  Users,
  Target,
  Radar,
  Bug,
  Scale,
  Server,
  Bell,
  Building2,
  Plug,
  BarChart3,
  ClipboardList,
  ShieldCheck,
  RefreshCw,
  Route,
  Building,
  Globe,
  Landmark,
  FileCheck,
  TestTube,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/incidents", icon: AlertTriangle, labelKey: "nav.incidents" },
  { href: "/soc", icon: Bell, labelKey: "nav.soc" },
  { href: "/threats", icon: Radar, labelKey: "nav.threats" },
  { href: "/vulnerabilities", icon: Bug, labelKey: "nav.vulnerabilities" },
  { href: "/risks", icon: Scale, labelKey: "nav.risks" },
  { href: "/attack-paths", icon: Route, labelKey: "nav.attackPaths" },
  { href: "/cmdb", icon: Server, labelKey: "nav.cmdb" },
  { href: "/tprm", icon: Building2, labelKey: "nav.tprm" },
  { href: "/compliance", icon: Scale, labelKey: "nav.complianceHub" },
  {
    label: "Regulatory",
    labelKey: "nav.regulatory",
    children: [
      { href: "/compliance/regulatory/nis2", icon: Globe, labelKey: "nav.nis2" },
      { href: "/compliance/regulatory/dora", icon: Landmark, labelKey: "nav.dora" },
    ],
  },
  {
    label: "Frameworks",
    labelKey: "nav.frameworks",
    children: [
      { href: "/compliance/frameworks/iso27001", icon: ShieldCheck, labelKey: "nav.iso27001" },
      { href: "/compliance/frameworks/bsi", icon: Building, labelKey: "nav.bsi" },
    ],
  },
  {
    label: "Assurance",
    labelKey: "nav.assurance",
    children: [
      { href: "/compliance/assurance", icon: FileCheck, labelKey: "nav.assuranceHub" },
      { href: "/compliance/assurance/evidence", icon: FileText, labelKey: "nav.evidence" },
      { href: "/compliance/assurance/testing", icon: TestTube, labelKey: "nav.testing" },
      { href: "/compliance/assurance/audits", icon: ClipboardList, labelKey: "nav.audits" },
      { href: "/compliance/assurance/bcm", icon: RefreshCw, labelKey: "nav.bcm" },
      { href: "/compliance/assurance/incidents", icon: AlertTriangle, labelKey: "nav.incidentsShort" },
    ],
  },
  { href: "/documents", icon: FileText, labelKey: "nav.documents" },
  { href: "/training", icon: GraduationCap, labelKey: "nav.training" },
  { href: "/integrations", icon: Plug, labelKey: "nav.integrations" },
  { href: "/reporting", icon: BarChart3, labelKey: "nav.reporting" },
  { href: "/notifications", icon: Bell, labelKey: "nav.notifications" },
  { href: "/users", icon: Users, labelKey: "nav.users" },
  { href: "/audit", icon: ClipboardList, labelKey: "nav.audit" },
  { href: "/simulation", icon: PlayCircle, labelKey: "nav.simulation" },
  {
    label: "Tools",
    labelKey: "nav.tools",
    children: [
      { href: "/tools/playbook", icon: BookOpen, labelKey: "nav.playbook" },
      { href: "/tools/templates", icon: FileText, labelKey: "nav.templates" },
      { href: "/tools/lessons", icon: GraduationCap, labelKey: "nav.lessons" },
      { href: "/tools/navigator", icon: Map, labelKey: "nav.navigator" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslations();
  const { sidebarCollapsed, toggleSidebarCollapse } = useUIStore();
  const { logout, user } = useAuthStore();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col h-screen bg-card border-r transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b">
        <Shield className="h-8 w-8 text-primary flex-shrink-0" />
        {!sidebarCollapsed && (
          <span className="ml-2 text-lg font-semibold">ISORA</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) =>
          item.children ? (
            <div key={item.labelKey} className="space-y-1">
              {!sidebarCollapsed && (
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3">
                  {t(item.labelKey)}
                </span>
              )}
              {item.children.map((child) => (
                <NavItem
                  key={child.href}
                  href={child.href}
                  icon={child.icon}
                  label={t(child.labelKey)}
                  isActive={pathname.startsWith(child.href)}
                  collapsed={sidebarCollapsed}
                />
              ))}
            </div>
          ) : (
            <NavItem
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={t(item.labelKey)}
              isActive={pathname.startsWith(item.href)}
              collapsed={sidebarCollapsed}
            />
          )
        )}
      </nav>

      {/* User & Settings */}
      <div className="p-4 border-t space-y-2">
        {user && !sidebarCollapsed && (
          <div className="px-3 py-2 text-sm">
            <div className="font-medium truncate">{user.full_name}</div>
            <div className="text-muted-foreground text-xs truncate">
              {user.email}
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          className={cn(
            "w-full justify-start",
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
          className="w-full"
          onClick={toggleSidebarCollapse}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}

function NavItem({
  href,
  icon: Icon,
  label,
  isActive,
  collapsed,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  isActive: boolean;
  collapsed: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
        collapsed && "justify-center px-2"
      )}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      {!collapsed && <span className="ml-2">{label}</span>}
    </Link>
  );
}

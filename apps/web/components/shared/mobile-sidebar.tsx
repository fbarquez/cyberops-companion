"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  Landmark,
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
  LogOut,
  Shield,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { useCopilot } from "@/components/copilot/CopilotProvider";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  labelKey: string;
}

interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    id: "operations",
    label: "Operations",
    items: [
      { href: "/incidents", icon: AlertTriangle, labelKey: "nav.incidents" },
      { href: "/soc", icon: Bell, labelKey: "nav.soc" },
      { href: "/threats", icon: Radar, labelKey: "nav.threats" },
      { href: "/vulnerabilities", icon: Bug, labelKey: "nav.vulnerabilities" },
    ],
  },
  {
    id: "security",
    label: "Security",
    items: [
      { href: "/risks", icon: Scale, labelKey: "nav.risks" },
      { href: "/attack-paths", icon: Route, labelKey: "nav.attackPaths" },
      { href: "/cmdb", icon: Server, labelKey: "nav.cmdb" },
      { href: "/tprm", icon: Building2, labelKey: "nav.tprm" },
    ],
  },
  {
    id: "compliance",
    label: "Compliance",
    items: [
      { href: "/compliance", icon: Scale, labelKey: "nav.complianceHub" },
      { href: "/compliance/regulatory/nis2", icon: Globe, labelKey: "nav.nis2" },
      { href: "/compliance/regulatory/dora", icon: Landmark, labelKey: "nav.dora" },
      { href: "/compliance/frameworks/iso27001", icon: ShieldCheck, labelKey: "nav.iso27001" },
      { href: "/compliance/frameworks/bsi", icon: Building, labelKey: "nav.bsi" },
      { href: "/bcm", icon: RefreshCw, labelKey: "nav.bcm" },
    ],
  },
  {
    id: "management",
    label: "Management",
    items: [
      { href: "/documents", icon: FileText, labelKey: "nav.documents" },
      { href: "/training", icon: GraduationCap, labelKey: "nav.training" },
      { href: "/reporting", icon: BarChart3, labelKey: "nav.reporting" },
      { href: "/notifications", icon: Bell, labelKey: "nav.notifications" },
    ],
  },
  {
    id: "tools",
    label: "Tools",
    items: [
      { href: "/tools/playbook", icon: BookOpen, labelKey: "nav.playbook" },
      { href: "/tools/templates", icon: FileText, labelKey: "nav.templates" },
      { href: "/tools/lessons", icon: GraduationCap, labelKey: "nav.lessons" },
      { href: "/tools/navigator", icon: Map, labelKey: "nav.navigator" },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    items: [
      { href: "/users", icon: Users, labelKey: "nav.users" },
      { href: "/audit", icon: ClipboardList, labelKey: "nav.audit" },
      { href: "/integrations", icon: Plug, labelKey: "nav.integrations" },
      { href: "/simulation", icon: PlayCircle, labelKey: "nav.simulation" },
    ],
  },
];

export function MobileSidebar() {
  const pathname = usePathname();
  const { t } = useTranslations();
  const { sidebarOpen, setSidebarOpen, expandedGroups, toggleGroup } = useUIStore();
  const { logout, user } = useAuthStore();
  const { openChat, health } = useCopilot();
  const isConnected = health?.status === "healthy";

  const handleNavClick = () => {
    setSidebarOpen(false);
  };

  const handleCopilotClick = () => {
    openChat();
    setSidebarOpen(false);
  };

  return (
    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <SheetContent side="left" className="w-72 p-0 flex flex-col">
        {/* Logo */}
        <SheetHeader className="flex flex-row items-center h-16 px-4 border-b">
          <div className="relative">
            <Shield className="h-8 w-8 text-primary flex-shrink-0" />
            <Sparkles className="absolute -right-1 -top-1 h-3 w-3 text-primary animate-pulse" />
          </div>
          <SheetTitle className="ml-2">
            <div className="flex flex-col">
              <span className="text-base font-semibold leading-tight">ISORA</span>
              <span className="text-xs text-muted-foreground leading-tight">Risk Assurance</span>
            </div>
          </SheetTitle>
        </SheetHeader>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-2">
          {/* Home */}
          <MobileNavItem
            href="/home"
            icon={Home}
            label={t("nav.home")}
            isActive={pathname === "/home"}
            onClick={handleNavClick}
          />

          {/* Nav Groups */}
          {navGroups.map((group) => (
            <MobileNavGroup
              key={group.id}
              id={group.id}
              label={group.label}
              isExpanded={expandedGroups[group.id] ?? false}
              onToggle={() => toggleGroup(group.id)}
            >
              {group.items.map((item) => (
                <MobileNavItem
                  key={item.href}
                  href={item.href}
                  icon={item.icon}
                  label={t(item.labelKey)}
                  isActive={pathname === item.href || pathname.startsWith(`${item.href}/`)}
                  onClick={handleNavClick}
                />
              ))}
            </MobileNavGroup>
          ))}

          {/* Copilot Button */}
          <div className="pt-4 mt-4 border-t">
            <button
              onClick={handleCopilotClick}
              className={cn(
                "group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-150",
                "bg-gradient-to-r from-primary/5 to-primary/10 hover:from-primary/10 hover:to-primary/20",
                "text-primary border border-primary/20 hover:border-primary/40"
              )}
            >
              <div className="relative">
                <Sparkles className="h-4 w-4" />
                {isConnected && (
                  <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                )}
              </div>
              <span className="flex-1 text-left">AI Copilot</span>
            </button>
          </div>
        </nav>

        {/* User & Settings */}
        <div className="p-3 border-t bg-background">
          {user && (
            <div className="px-3 py-2 text-sm mb-2">
              <div className="font-medium truncate">{user.full_name}</div>
              <div className="text-muted-foreground text-xs truncate">
                {user.email}
              </div>
            </div>
          )}

          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={() => {
              logout();
              setSidebarOpen(false);
            }}
          >
            <LogOut className="h-4 w-4" />
            <span className="ml-2">{t("nav.logout")}</span>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function MobileNavGroup({
  id,
  label,
  isExpanded,
  onToggle,
  children,
}: {
  id: string;
  label: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <button
        onClick={onToggle}
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
          isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="space-y-1 pl-2">{children}</div>
      </div>
    </div>
  );
}

function MobileNavItem({
  href,
  icon: Icon,
  label,
  isActive,
  onClick,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={cn(
        "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-150",
        isActive
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-accent hover:text-foreground"
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 flex-shrink-0 transition-colors",
          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
        )}
      />
      <span>{label}</span>
    </Link>
  );
}

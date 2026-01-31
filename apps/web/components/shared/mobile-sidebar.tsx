"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  PlayCircle,
  BookOpen,
  FileText,
  GraduationCap,
  Map,
  LogOut,
  Shield,
  Users,
  Radar,
  Bug,
  Scale,
  Server,
  Bell,
  Building2,
  Plug,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

const navItems = [
  { href: "/incidents", icon: AlertTriangle, labelKey: "nav.incidents" },
  { href: "/soc", icon: Bell, labelKey: "nav.soc" },
  { href: "/threats", icon: Radar, labelKey: "nav.threats" },
  { href: "/vulnerabilities", icon: Bug, labelKey: "nav.vulnerabilities" },
  { href: "/risks", icon: Scale, labelKey: "nav.risks" },
  { href: "/cmdb", icon: Server, labelKey: "nav.cmdb" },
  { href: "/tprm", icon: Building2, labelKey: "nav.tprm" },
  { href: "/integrations", icon: Plug, labelKey: "nav.integrations" },
  { href: "/reporting", icon: BarChart3, labelKey: "nav.reporting" },
  { href: "/notifications", icon: Bell, labelKey: "nav.notifications" },
  { href: "/users", icon: Users, labelKey: "nav.users" },
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

export function MobileSidebar() {
  const pathname = usePathname();
  const { t } = useTranslations();
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { logout, user } = useAuthStore();

  const handleNavClick = () => {
    setSidebarOpen(false);
  };

  return (
    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <SheetContent side="left" className="w-64 p-0">
        {/* Logo */}
        <SheetHeader className="flex flex-row items-center h-16 px-4 border-b">
          <Shield className="h-8 w-8 text-primary flex-shrink-0" />
          <SheetTitle className="ml-2 text-lg font-semibold">
            CyberOps Companion
          </SheetTitle>
        </SheetHeader>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto max-h-[calc(100vh-180px)]">
          {navItems.map((item) =>
            item.children ? (
              <div key={item.labelKey} className="space-y-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3">
                  {t(item.labelKey)}
                </span>
                {item.children.map((child) => (
                  <MobileNavItem
                    key={child.href}
                    href={child.href}
                    icon={child.icon}
                    label={t(child.labelKey)}
                    isActive={pathname.startsWith(child.href)}
                    onClick={handleNavClick}
                  />
                ))}
              </div>
            ) : (
              <MobileNavItem
                key={item.href}
                href={item.href}
                icon={item.icon}
                label={t(item.labelKey)}
                isActive={pathname.startsWith(item.href)}
                onClick={handleNavClick}
              />
            )
          )}
        </nav>

        {/* User & Settings */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-background">
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
        "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      <span className="ml-2">{label}</span>
    </Link>
  );
}

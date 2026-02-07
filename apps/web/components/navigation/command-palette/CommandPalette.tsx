"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
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
  Plus,
  Search as SearchIcon,
  Clock,
  Zap,
  LucideIcon,
} from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useUIStore } from "@/stores/ui-store";
import { useTranslations } from "@/hooks/use-translations";
import { CommandSearch } from "./CommandSearch";
import { CommandGroup } from "./CommandGroup";
import { CommandItem } from "./CommandItem";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  keywords?: string[];
}

interface ActionItem {
  id: string;
  label: string;
  description?: string;
  icon: LucideIcon;
  action: () => void;
  keywords?: string[];
}

const navigationItems: NavigationItem[] = [
  { id: "home", label: "Home", href: "/home", icon: Home, keywords: ["dashboard", "main"] },
  { id: "incidents", label: "Incidents", href: "/incidents", icon: AlertTriangle, keywords: ["security", "breach", "alert"] },
  { id: "soc", label: "SOC", href: "/soc", icon: Bell, keywords: ["security", "operations", "center", "monitoring"] },
  { id: "threats", label: "Threat Intel", href: "/threats", icon: Radar, keywords: ["intelligence", "ioc", "threat"] },
  { id: "vulnerabilities", label: "Vulnerabilities", href: "/vulnerabilities", icon: Bug, keywords: ["cve", "weakness", "scan"] },
  { id: "risks", label: "Risk Register", href: "/risks", icon: Scale, keywords: ["assessment", "risk"] },
  { id: "attack-paths", label: "Attack Paths", href: "/attack-paths", icon: Route, keywords: ["visualization", "attack"] },
  { id: "cmdb", label: "CMDB", href: "/cmdb", icon: Server, keywords: ["assets", "configuration", "inventory"] },
  { id: "tprm", label: "Third-Party Risk", href: "/tprm", icon: Building2, keywords: ["vendor", "supplier", "risk"] },
  { id: "iso27001", label: "ISO 27001", href: "/compliance/iso27001", icon: ShieldCheck, keywords: ["compliance", "standard"] },
  { id: "bsi", label: "BSI IT-Grundschutz", href: "/compliance/bsi", icon: Building, keywords: ["compliance", "german"] },
  { id: "nis2", label: "NIS2 Directive", href: "/compliance/nis2", icon: Globe, keywords: ["compliance", "eu", "directive"] },
  { id: "bcm", label: "Business Continuity", href: "/bcm", icon: RefreshCw, keywords: ["disaster", "recovery", "bcp"] },
  { id: "documents", label: "Documents & Policies", href: "/documents", icon: FileText, keywords: ["policy", "procedure"] },
  { id: "training", label: "Training", href: "/training", icon: GraduationCap, keywords: ["learning", "awareness"] },
  { id: "reporting", label: "Reporting", href: "/reporting", icon: BarChart3, keywords: ["reports", "analytics"] },
  { id: "notifications", label: "Notifications", href: "/notifications", icon: Bell, keywords: ["alerts", "messages"] },
  { id: "playbook", label: "Playbook Generator", href: "/tools/playbook", icon: BookOpen, keywords: ["automation", "runbook"] },
  { id: "templates", label: "Communication Templates", href: "/tools/templates", icon: FileText, keywords: ["email", "notification"] },
  { id: "lessons", label: "Lessons Learned", href: "/tools/lessons", icon: GraduationCap, keywords: ["retrospective", "improvement"] },
  { id: "navigator", label: "MITRE Navigator", href: "/tools/navigator", icon: Map, keywords: ["att&ck", "tactics", "techniques"] },
  { id: "users", label: "User Management", href: "/users", icon: Users, keywords: ["admin", "permissions"] },
  { id: "audit", label: "Audit Logs", href: "/audit", icon: ClipboardList, keywords: ["logging", "activity"] },
  { id: "integrations", label: "Integrations", href: "/integrations", icon: Plug, keywords: ["api", "connect"] },
  { id: "simulation", label: "Simulation", href: "/simulation", icon: PlayCircle, keywords: ["test", "exercise", "tabletop"] },
];

export function CommandPalette() {
  const router = useRouter();
  const { t } = useTranslations();
  const { commandPaletteOpen, setCommandPaletteOpen, quickAccess } = useUIStore();
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Actions
  const actionItems: ActionItem[] = useMemo(
    () => [
      {
        id: "new-incident",
        label: "New Incident",
        description: "Create a new security incident",
        icon: Plus,
        action: () => {
          router.push("/incidents?action=new");
          setCommandPaletteOpen(false);
        },
        keywords: ["create", "add", "incident"],
      },
      {
        id: "generate-report",
        label: "Generate Report",
        description: "Create a new report",
        icon: BarChart3,
        action: () => {
          router.push("/reporting");
          setCommandPaletteOpen(false);
        },
        keywords: ["create", "report", "analytics"],
      },
    ],
    [router, setCommandPaletteOpen]
  );

  // Filter results based on search
  const filteredNavigation = useMemo(() => {
    if (!search) return navigationItems.slice(0, 6);
    const searchLower = search.toLowerCase();
    return navigationItems.filter(
      (item) =>
        item.label.toLowerCase().includes(searchLower) ||
        item.keywords?.some((k) => k.includes(searchLower))
    );
  }, [search]);

  const filteredActions = useMemo(() => {
    if (!search) return actionItems;
    const searchLower = search.toLowerCase();
    return actionItems.filter(
      (item) =>
        item.label.toLowerCase().includes(searchLower) ||
        item.description?.toLowerCase().includes(searchLower) ||
        item.keywords?.some((k) => k.includes(searchLower))
    );
  }, [search, actionItems]);

  // Build flat list for keyboard navigation
  const allItems = useMemo(() => {
    const items: { type: "nav" | "action" | "recent"; item: NavigationItem | ActionItem }[] = [];

    if (quickAccess.length > 0 && !search) {
      quickAccess.slice(0, 3).forEach((qa) => {
        const navItem = navigationItems.find((n) => n.href === qa.href);
        if (navItem) {
          items.push({ type: "recent", item: navItem });
        }
      });
    }

    filteredActions.forEach((item) => items.push({ type: "action", item }));
    filteredNavigation.forEach((item) => items.push({ type: "nav", item }));

    return items;
  }, [quickAccess, search, filteredActions, filteredNavigation]);

  // Reset selection when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((i) => Math.min(i + 1, allItems.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          const selected = allItems[selectedIndex];
          if (selected) {
            if (selected.type === "action") {
              (selected.item as ActionItem).action();
            } else {
              router.push((selected.item as NavigationItem).href);
              setCommandPaletteOpen(false);
            }
          }
          break;
      }
    },
    [allItems, selectedIndex, router, setCommandPaletteOpen]
  );

  // Reset on close
  useEffect(() => {
    if (!commandPaletteOpen) {
      setSearch("");
      setSelectedIndex(0);
    }
  }, [commandPaletteOpen]);

  let currentIndex = -1;

  return (
    <Dialog open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen}>
      <DialogContent
        className="max-w-xl p-0 gap-0 overflow-hidden"
        onKeyDown={handleKeyDown}
      >
        <VisuallyHidden>
          <DialogTitle>Command Palette</DialogTitle>
        </VisuallyHidden>
        <CommandSearch
          value={search}
          onChange={setSearch}
          placeholder="Search commands and pages..."
        />

        <div className="max-h-[400px] overflow-y-auto">
          {/* Recent Pages */}
          {quickAccess.length > 0 && !search && (
            <CommandGroup label="Recent">
              {quickAccess.slice(0, 3).map((qa) => {
                const navItem = navigationItems.find((n) => n.href === qa.href);
                if (!navItem) return null;
                currentIndex++;
                const index = currentIndex;
                return (
                  <CommandItem
                    key={`recent-${qa.href}`}
                    icon={navItem.icon}
                    label={navItem.label}
                    isActive={selectedIndex === index}
                    onClick={() => {
                      router.push(qa.href);
                      setCommandPaletteOpen(false);
                    }}
                  />
                );
              })}
            </CommandGroup>
          )}

          {/* Actions */}
          {filteredActions.length > 0 && (
            <CommandGroup label="Actions">
              {filteredActions.map((item) => {
                currentIndex++;
                const index = currentIndex;
                return (
                  <CommandItem
                    key={item.id}
                    icon={item.icon}
                    label={item.label}
                    description={item.description}
                    isActive={selectedIndex === index}
                    onClick={item.action}
                  />
                );
              })}
            </CommandGroup>
          )}

          {/* Navigation */}
          {filteredNavigation.length > 0 && (
            <CommandGroup label="Navigation">
              {filteredNavigation.map((item) => {
                currentIndex++;
                const index = currentIndex;
                return (
                  <CommandItem
                    key={item.id}
                    icon={item.icon}
                    label={item.label}
                    isActive={selectedIndex === index}
                    onClick={() => {
                      router.push(item.href);
                      setCommandPaletteOpen(false);
                    }}
                  />
                );
              })}
            </CommandGroup>
          )}

          {/* No results */}
          {search && filteredNavigation.length === 0 && filteredActions.length === 0 && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No results found.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-center border-t px-4 py-2 text-xs text-muted-foreground">
          <div className="flex gap-4">
            <span>
              <kbd className="rounded border bg-muted px-1.5 py-0.5 font-mono">↑↓</kbd> Navigate
            </span>
            <span>
              <kbd className="rounded border bg-muted px-1.5 py-0.5 font-mono">↵</kbd> Select
            </span>
            <span>
              <kbd className="rounded border bg-muted px-1.5 py-0.5 font-mono">esc</kbd> Close
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Radar,
  FileText,
  Bell,
  Bot,
  Sparkles,
  LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCopilot } from "@/components/copilot/CopilotProvider";
import { useTranslations } from "@/hooks/use-translations";

interface QuickAction {
  id: string;
  label: string;
  icon: LucideIcon;
  secondaryIcon?: LucideIcon;
  href?: string;
  onClick?: () => void;
  variant?: "default" | "primary";
}

export function QuickActionBar() {
  const router = useRouter();
  const { openChat } = useCopilot();
  const { t } = useTranslations();

  const actions: QuickAction[] = [
    {
      id: "new-incident",
      label: "New Incident",
      icon: AlertTriangle,
      href: "/incidents?action=new",
    },
    {
      id: "run-scan",
      label: "Run Scan",
      icon: Radar,
      href: "/vulnerabilities?action=scan",
    },
    {
      id: "generate-report",
      label: "Generate Report",
      icon: FileText,
      href: "/reporting",
    },
    {
      id: "view-alerts",
      label: "View Alerts",
      icon: Bell,
      href: "/soc",
    },
    {
      id: "ask-copilot",
      label: "Ask Copilot",
      icon: Bot,
      secondaryIcon: Sparkles,
      onClick: openChat,
      variant: "primary",
    },
  ];

  const handleAction = (action: QuickAction) => {
    if (action.onClick) {
      action.onClick();
    } else if (action.href) {
      router.push(action.href);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((action) => (
        <button
          key={action.id}
          onClick={() => handleAction(action)}
          className={cn(
            "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all duration-150",
            "border shadow-sm hover:shadow-md",
            action.variant === "primary"
              ? "bg-primary text-primary-foreground border-primary hover:bg-primary/90"
              : "bg-card text-foreground border-border hover:bg-accent hover:border-accent"
          )}
        >
          <div className="relative">
            <action.icon className="h-4 w-4" />
            {action.secondaryIcon && (
              <action.secondaryIcon className="absolute -right-1 -top-1 h-2.5 w-2.5" />
            )}
          </div>
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}

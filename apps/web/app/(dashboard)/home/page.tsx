"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Shield,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AskAnythingBar } from "@/components/dashboard/ask-bar";
import { QuickActionBar } from "@/components/dashboard/quick-actions";
import { useTranslations } from "@/hooks/use-translations";
import { useAuthStore } from "@/stores/auth-store";

interface DashboardStats {
  openIncidents: number;
  criticalAlerts: number;
  pendingTasks: number;
  complianceScore: number;
}

export default function HomePage() {
  const { t } = useTranslations();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats>({
    openIncidents: 0,
    criticalAlerts: 0,
    pendingTasks: 0,
    complianceScore: 0,
  });

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="Home" />

      <div className="flex-1 overflow-y-auto">
        <div className="container max-w-6xl mx-auto p-6 space-y-8">
          {/* Welcome Section */}
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">
              {getGreeting()}, {user?.full_name?.split(" ")[0] || "there"}
            </h1>
            <p className="text-muted-foreground">
              Here&apos;s what&apos;s happening with your security operations today.
            </p>
          </div>

          {/* Ask Anything Bar */}
          <AskAnythingBar />

          {/* Quick Actions */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Quick Actions
            </h2>
            <QuickActionBar />
          </div>

          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Open Incidents"
              value={stats.openIncidents}
              icon={AlertTriangle}
              description="Active security incidents"
              trend={{ value: 12, direction: "down" }}
              href="/incidents"
            />
            <StatsCard
              title="Critical Alerts"
              value={stats.criticalAlerts}
              icon={AlertCircle}
              description="Requires immediate attention"
              trend={{ value: 5, direction: "up" }}
              href="/soc"
              variant="danger"
            />
            <StatsCard
              title="Pending Tasks"
              value={stats.pendingTasks}
              icon={Clock}
              description="Awaiting completion"
              href="/notifications"
            />
            <StatsCard
              title="Compliance Score"
              value={`${stats.complianceScore}%`}
              icon={Shield}
              description="Overall compliance status"
              trend={{ value: 3, direction: "up" }}
              href="/compliance/iso27001"
              variant="success"
            />
          </div>

          {/* Recent Activity & Tasks */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Recent Activity */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <ActivityItem
                    icon={AlertTriangle}
                    title="New incident reported"
                    description="Suspicious login activity detected"
                    time="2 hours ago"
                    variant="warning"
                  />
                  <ActivityItem
                    icon={CheckCircle2}
                    title="Compliance control updated"
                    description="ISO 27001 A.5.1.1 marked as compliant"
                    time="4 hours ago"
                    variant="success"
                  />
                  <ActivityItem
                    icon={FileText}
                    title="Report generated"
                    description="Monthly security report exported"
                    time="Yesterday"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Security Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Mean Time to Detect</span>
                    <span className="text-sm font-medium">4.2 hours</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Mean Time to Respond</span>
                    <span className="text-sm font-medium">12.5 hours</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Incidents This Month</span>
                    <span className="text-sm font-medium">23</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Resolved This Month</span>
                    <span className="text-sm font-medium">19</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Active Threat Actors</span>
                    <span className="text-sm font-medium">7</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  trend?: { value: number; direction: "up" | "down" };
  href?: string;
  variant?: "default" | "danger" | "success";
}

function StatsCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  href,
  variant = "default",
}: StatsCardProps) {
  const variantStyles = {
    default: "text-muted-foreground",
    danger: "text-destructive",
    success: "text-green-600 dark:text-green-500",
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <Icon className={`h-5 w-5 ${variantStyles[variant]}`} />
          {trend && (
            <span
              className={`text-xs font-medium ${
                trend.direction === "up" ? "text-green-600" : "text-destructive"
              }`}
            >
              {trend.direction === "up" ? "+" : "-"}{trend.value}%
            </span>
          )}
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">{title}</p>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActivityItemProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  time: string;
  variant?: "default" | "warning" | "success";
}

function ActivityItem({
  icon: Icon,
  title,
  description,
  time,
  variant = "default",
}: ActivityItemProps) {
  const variantStyles = {
    default: "bg-muted text-muted-foreground",
    warning: "bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-500",
    success: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-500",
  };

  return (
    <div className="flex items-start gap-3">
      <div className={`p-2 rounded-lg ${variantStyles[variant]}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{title}</p>
        <p className="text-xs text-muted-foreground truncate">{description}</p>
      </div>
      <span className="text-xs text-muted-foreground whitespace-nowrap">{time}</span>
    </div>
  );
}

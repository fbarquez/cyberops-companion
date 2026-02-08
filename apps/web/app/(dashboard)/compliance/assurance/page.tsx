"use client";

import Link from "next/link";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  FileCheck,
  FileText,
  TestTube,
  ClipboardCheck,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  Link2,
} from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";

const assuranceModules = [
  {
    id: "evidence",
    name: "Evidence Management",
    nameDE: "Nachweismanagement",
    description: "Collect, organize, and link compliance evidence to controls",
    descriptionDE: "Nachweise sammeln, organisieren und mit Kontrollen verknüpfen",
    icon: FileText,
    href: "/compliance/assurance/evidence",
    color: "from-blue-500 to-blue-600",
    stats: { total: 156, linked: 142, pending: 14 },
  },
  {
    id: "testing",
    name: "Security Testing",
    nameDE: "Sicherheitstests",
    description: "Vulnerability assessments, penetration tests, TLPT",
    descriptionDE: "Schwachstellenbewertungen, Penetrationstests, TLPT",
    icon: TestTube,
    href: "/compliance/assurance/testing",
    color: "from-orange-500 to-orange-600",
    stats: { total: 24, passed: 18, failed: 6 },
  },
  {
    id: "audits",
    name: "Audit Management",
    nameDE: "Audit-Management",
    description: "Plan, execute, and track internal and external audits",
    descriptionDE: "Interne und externe Audits planen, durchführen und verfolgen",
    icon: ClipboardCheck,
    href: "/compliance/assurance/audits",
    color: "from-purple-500 to-purple-600",
    stats: { total: 8, completed: 5, inProgress: 2, planned: 1 },
  },
  {
    id: "bcm",
    name: "BCM & Resilience",
    nameDE: "BCM & Resilienz",
    description: "Business continuity, BIA, recovery plans, exercises",
    descriptionDE: "Business Continuity, BIA, Wiederherstellungspläne, Übungen",
    icon: RefreshCw,
    href: "/compliance/assurance/bcm",
    color: "from-green-500 to-green-600",
    stats: { plans: 12, exercises: 4, lastTest: "2024-01" },
  },
  {
    id: "incidents",
    name: "Incident Management",
    nameDE: "Vorfallsmanagement",
    description: "Security incidents, breach reporting, lessons learned",
    descriptionDE: "Sicherheitsvorfälle, Meldungen, Lessons Learned",
    icon: AlertTriangle,
    href: "/compliance/assurance/incidents",
    color: "from-red-500 to-red-600",
    stats: { open: 3, resolved: 47, avgResolution: "4.2h" },
  },
  {
    id: "bridge",
    name: "ISMS ↔ SOC Bridge",
    nameDE: "ISMS ↔ SOC Brücke",
    description: "Auto-link operations to controls, measure effectiveness",
    descriptionDE: "Operationen automatisch mit Kontrollen verknüpfen, Wirksamkeit messen",
    icon: Link2,
    href: "/compliance/assurance/bridge",
    color: "from-indigo-500 to-indigo-600",
    stats: { linked: 1247, controls: 93, score: 87 },
  },
];

export default function AssuranceLayerPage() {
  const { t } = useTranslations();

  return (
    <div className="flex flex-col h-full">
      <Header title="Layer C: Assurance & Evidence">
        <Link href="/compliance">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Hub
          </Button>
        </Link>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {/* Info Banner */}
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 border-green-200 dark:border-green-800">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <FileCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100">
                  Operational & Evidence Layer
                </h3>
                <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                  This is where audits are won or lost. Collect evidence, execute tests,
                  manage audits, ensure resilience, and handle incidents. All proof of
                  compliance lives here.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Question */}
        <div className="text-center py-4">
          <p className="text-lg text-muted-foreground">
            <span className="font-semibold text-foreground">"Can I prove compliance to BaFin/BSI/auditors?"</span>
          </p>
        </div>

        {/* Assurance Modules Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {assuranceModules.map((module) => (
            <AssuranceModuleCard key={module.id} module={module} />
          ))}
        </div>

        {/* Compliance Readiness Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Audit Readiness Overview</CardTitle>
            <CardDescription>
              How prepared are you for the next audit?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <ReadinessItem
                label="Evidence Coverage"
                value={91}
                icon={FileText}
                status="good"
              />
              <ReadinessItem
                label="Testing Complete"
                value={75}
                icon={TestTube}
                status="warning"
              />
              <ReadinessItem
                label="Audit Findings Closed"
                value={88}
                icon={ClipboardCheck}
                status="good"
              />
              <ReadinessItem
                label="BCM Exercises Current"
                value={100}
                icon={RefreshCw}
                status="good"
              />
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Link href="/compliance/assurance/evidence">
                <Button variant="outline" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Upload Evidence
                </Button>
              </Link>
              <Link href="/compliance/assurance/testing">
                <Button variant="outline" size="sm">
                  <TestTube className="h-4 w-4 mr-2" />
                  Schedule Test
                </Button>
              </Link>
              <Link href="/compliance/assurance/audits">
                <Button variant="outline" size="sm">
                  <ClipboardCheck className="h-4 w-4 mr-2" />
                  Plan Audit
                </Button>
              </Link>
              <Link href="/compliance/assurance/incidents">
                <Button variant="outline" size="sm">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Report Incident
                </Button>
              </Link>
              <Link href="/compliance/assurance/bridge">
                <Button variant="outline" size="sm">
                  <Link2 className="h-4 w-4 mr-2" />
                  View Evidence Bridge
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AssuranceModuleCard({
  module,
}: {
  module: typeof assuranceModules[0];
}) {
  const Icon = module.icon;

  return (
    <Link href={module.href}>
      <Card className="hover:shadow-md transition-all h-full">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className={`p-2 rounded-lg bg-gradient-to-br ${module.color} text-white`}>
              <Icon className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </div>
          <CardTitle className="text-base mt-3">{module.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">{module.description}</p>
          <div className="flex flex-wrap gap-2">
            {module.id === "evidence" && (
              <>
                <Badge variant="outline" className="text-xs">
                  {module.stats.linked}/{module.stats.total} linked
                </Badge>
                {module.stats.pending > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {module.stats.pending} pending
                  </Badge>
                )}
              </>
            )}
            {module.id === "testing" && (
              <>
                <Badge variant="outline" className="text-xs text-green-600">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  {module.stats.passed} passed
                </Badge>
                {module.stats.failed > 0 && (
                  <Badge variant="outline" className="text-xs text-red-600">
                    <XCircle className="h-3 w-3 mr-1" />
                    {module.stats.failed} failed
                  </Badge>
                )}
              </>
            )}
            {module.id === "audits" && (
              <>
                <Badge variant="outline" className="text-xs">
                  {module.stats.completed} completed
                </Badge>
                {module.stats.inProgress > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    <Clock className="h-3 w-3 mr-1" />
                    {module.stats.inProgress} in progress
                  </Badge>
                )}
              </>
            )}
            {module.id === "bcm" && (
              <>
                <Badge variant="outline" className="text-xs">
                  {module.stats.plans} plans
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {module.stats.exercises} exercises
                </Badge>
              </>
            )}
            {module.id === "incidents" && (
              <>
                {module.stats.open > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {module.stats.open} open
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  {module.stats.resolved} resolved
                </Badge>
              </>
            )}
            {module.id === "bridge" && (
              <>
                <Badge variant="outline" className="text-xs">
                  {module.stats.linked} linked
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {module.stats.controls} controls
                </Badge>
                <Badge variant="outline" className="text-xs text-green-600">
                  {module.stats.score}% effective
                </Badge>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function ReadinessItem({
  label,
  value,
  icon: Icon,
  status,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  status: "good" | "warning" | "critical";
}) {
  const statusColors = {
    good: "text-green-600",
    warning: "text-yellow-600",
    critical: "text-red-600",
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className={`text-sm font-bold ${statusColors[status]}`}>{value}%</span>
      </div>
      <Progress value={value} className="h-2" />
    </div>
  );
}

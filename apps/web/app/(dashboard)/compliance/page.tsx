"use client";

import Link from "next/link";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Scale,
  Shield,
  FileCheck,
  Building2,
  Globe,
  Landmark,
  Car,
  Factory,
  Lock,
  ShieldCheck,
  Building,
  Server,
  BarChart3,
  ClipboardCheck,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Layers,
  FileText,
  TestTube,
} from "lucide-react";
import { useTranslations } from "@/hooks/use-translations";

// Layer A - Regulatory (What must I comply with?)
const regulatoryFrameworks = [
  {
    id: "nis2",
    name: "NIS2",
    fullName: "NIS2 Directive",
    description: "EU Network and Information Security Directive for critical infrastructure",
    icon: Globe,
    href: "/compliance/regulatory/nis2",
    status: "active",
    region: "EU",
    color: "from-blue-500 to-blue-600",
  },
  {
    id: "dora",
    name: "DORA",
    fullName: "Digital Operational Resilience Act",
    description: "EU regulation for ICT risk management in financial sector",
    icon: Landmark,
    href: "/compliance/regulatory/dora",
    status: "active",
    region: "EU",
    color: "from-indigo-500 to-indigo-600",
  },
  {
    id: "tisax",
    name: "TISAX",
    fullName: "Trusted Information Security Assessment Exchange",
    description: "Automotive industry security assessment standard",
    icon: Car,
    href: "/compliance/regulatory/tisax",
    status: "coming_soon",
    region: "DE/Auto",
    color: "from-orange-500 to-orange-600",
  },
  {
    id: "kritis",
    name: "KRITIS",
    fullName: "Kritische Infrastrukturen",
    description: "German critical infrastructure protection regulation",
    icon: Factory,
    href: "/compliance/regulatory/kritis",
    status: "coming_soon",
    region: "DE",
    color: "from-red-500 to-red-600",
  },
  {
    id: "gdpr",
    name: "GDPR",
    fullName: "General Data Protection Regulation",
    description: "EU data protection and privacy regulation",
    icon: Lock,
    href: "/compliance/regulatory/gdpr",
    status: "coming_soon",
    region: "EU",
    color: "from-green-500 to-green-600",
  },
];

// Layer B - Implementation Frameworks (How do I implement it?)
const implementationFrameworks = [
  {
    id: "iso27001",
    name: "ISO 27001",
    fullName: "ISO/IEC 27001:2022",
    description: "International standard for information security management systems",
    icon: ShieldCheck,
    href: "/compliance/frameworks/iso27001",
    status: "active",
    type: "International",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    id: "bsi",
    name: "BSI IT-Grundschutz",
    fullName: "BSI IT-Grundschutz Kompendium",
    description: "German federal methodology for IT security",
    icon: Building,
    href: "/compliance/frameworks/bsi",
    status: "active",
    type: "DE",
    color: "from-amber-500 to-amber-600",
  },
  {
    id: "nist",
    name: "NIST CSF",
    fullName: "NIST Cybersecurity Framework",
    description: "US framework for managing cybersecurity risk",
    icon: Server,
    href: "/compliance/frameworks/nist",
    status: "coming_soon",
    type: "US",
    color: "from-cyan-500 to-cyan-600",
  },
  {
    id: "cobit",
    name: "COBIT",
    fullName: "Control Objectives for IT",
    description: "IT governance and management framework",
    icon: BarChart3,
    href: "/compliance/frameworks/cobit",
    status: "coming_soon",
    type: "International",
    color: "from-purple-500 to-purple-600",
  },
];

// Layer C - Assurance (Can I prove compliance?)
const assuranceModules = [
  {
    id: "evidence",
    name: "Evidence Management",
    description: "Collect, organize, and link compliance evidence",
    icon: FileText,
    href: "/compliance/assurance/evidence",
    status: "active",
  },
  {
    id: "audit",
    name: "Audit Management",
    description: "Plan, execute, and track internal and external audits",
    icon: ClipboardCheck,
    href: "/compliance/assurance/audits",
    status: "active",
  },
  {
    id: "testing",
    name: "Security Testing",
    description: "Vulnerability assessments, penetration tests, TLPT",
    icon: TestTube,
    href: "/compliance/assurance/testing",
    status: "active",
  },
  {
    id: "bcm",
    name: "BCM & Resilience",
    description: "Business continuity, BIA, recovery plans, exercises",
    icon: RefreshCw,
    href: "/compliance/assurance/bcm",
    status: "active",
  },
  {
    id: "incidents",
    name: "Incident Management",
    description: "Security incidents, breach reporting, lessons learned",
    icon: AlertTriangle,
    href: "/compliance/assurance/incidents",
    status: "active",
  },
];

// 4 Functional Pillars
const functionalPillars = [
  {
    id: "compliance",
    name: "Compliance Management",
    question: "What does the regulator require from MY company?",
    icon: Scale,
    color: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  },
  {
    id: "risk",
    name: "Risk Management",
    question: "Where is my greatest exposure?",
    icon: AlertTriangle,
    href: "/risks",
    color: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  },
  {
    id: "bcm",
    name: "BCM & Resilience",
    question: "Can I continue operating after an incident?",
    icon: RefreshCw,
    href: "/bcm",
    color: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  },
  {
    id: "assurance",
    name: "Assurance",
    question: "Can I demonstrate it to BaFin/BSI/auditors?",
    icon: FileCheck,
    href: "/audit",
    color: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  },
];

export default function ComplianceHubPage() {
  const { t } = useTranslations();

  return (
    <div className="flex flex-col h-full">
      <Header title="Compliance Hub">
        <Badge variant="outline" className="text-xs">
          German Enterprise Model
        </Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-8">
        {/* 4 Pillars Overview */}
        <section>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Functional Pillars
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {functionalPillars.map((pillar) => (
              <Card key={pillar.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className={`inline-flex p-2 rounded-lg ${pillar.color} mb-3`}>
                    <pillar.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-medium mb-1">{pillar.name}</h3>
                  <p className="text-sm text-muted-foreground">{pillar.question}</p>
                  {pillar.href && (
                    <Link href={pillar.href}>
                      <Button variant="ghost" size="sm" className="mt-2 -ml-2">
                        Open <ArrowRight className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Layer A - Regulatory */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <Scale className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Layer A: Regulatory</h2>
              <p className="text-sm text-muted-foreground">What must I comply with? — The language of the regulator</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {regulatoryFrameworks.map((framework) => (
              <FrameworkCard key={framework.id} framework={framework} />
            ))}
          </div>
        </section>

        {/* Layer B - Implementation */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Layer B: Implementation Frameworks</h2>
              <p className="text-sm text-muted-foreground">How do I implement it? — Control catalogs, policies, processes</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {implementationFrameworks.map((framework) => (
              <FrameworkCard key={framework.id} framework={framework} showType />
            ))}
          </div>
        </section>

        {/* Layer C - Assurance */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <FileCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Layer C: Operational & Evidence</h2>
              <p className="text-sm text-muted-foreground">Can I prove compliance? — Where audits are won or lost</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {assuranceModules.map((module) => (
              <Link key={module.id} href={module.href}>
                <Card className="hover:shadow-md transition-shadow h-full">
                  <CardContent className="p-4">
                    <div className="inline-flex p-2 bg-gray-100 dark:bg-gray-800 rounded-lg mb-3">
                      <module.icon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                    </div>
                    <h3 className="font-medium mb-1">{module.name}</h3>
                    <p className="text-sm text-muted-foreground">{module.description}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        {/* Cross-Mapping Info */}
        <section>
          <Card className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 border-slate-200 dark:border-slate-700">
            <CardContent className="py-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-white dark:bg-slate-800 rounded-lg shadow-sm">
                  <Layers className="h-6 w-6 text-slate-600 dark:text-slate-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    Automatic Cross-Mapping
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                    Controls are automatically mapped across frameworks. Implementing ISO 27001 A.5.1
                    satisfies requirements in NIS2 Art. 21, DORA Art. 5, and BSI ORP.1.
                    Evidence collected for one framework is reused across all applicable regulations.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">NIS2 ↔ ISO 27001</Badge>
                    <Badge variant="outline">DORA ↔ ISO 27001</Badge>
                    <Badge variant="outline">BSI ↔ ISO 27001</Badge>
                    <Badge variant="outline">KRITIS ↔ NIS2</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}

function FrameworkCard({
  framework,
  showType = false
}: {
  framework: {
    id: string;
    name: string;
    fullName: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    href: string;
    status: string;
    region?: string;
    type?: string;
    color: string;
  };
  showType?: boolean;
}) {
  const Icon = framework.icon;
  const isActive = framework.status === "active";

  const cardContent = (
    <Card className={`hover:shadow-md transition-all h-full ${!isActive ? 'opacity-75' : ''}`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className={`p-2 rounded-lg bg-gradient-to-br ${framework.color} text-white`}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex gap-2">
            {(framework.region || framework.type) && (
              <Badge variant="outline" className="text-xs">
                {showType ? framework.type : framework.region}
              </Badge>
            )}
            {!isActive && (
              <Badge variant="secondary" className="text-xs">
                Coming Soon
              </Badge>
            )}
          </div>
        </div>
        <CardTitle className="text-base mt-3">{framework.name}</CardTitle>
        <CardDescription className="text-xs">{framework.fullName}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{framework.description}</p>
        {isActive && (
          <Button variant="ghost" size="sm" className="mt-3 -ml-2">
            Open <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  );

  if (isActive) {
    return <Link href={framework.href}>{cardContent}</Link>;
  }

  return cardContent;
}

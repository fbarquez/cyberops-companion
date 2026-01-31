"use client";

import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Bug,
  Shield,
  Building2,
  FileCheck,
  Server,
  Target,
  Link2,
  BarChart3,
  ArrowRight,
  ArrowLeft,
  Check,
} from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { cn } from "@/lib/utils";

interface ModulesStepProps {
  onNext: () => void;
  onBack: () => void;
}

const modules = [
  {
    id: "incidents",
    icon: AlertTriangle,
    name: "Incident Response",
    description: "Manage security incidents end-to-end",
    recommended: true,
  },
  {
    id: "soc",
    icon: Shield,
    name: "SOC Operations",
    description: "Alert triage and case management",
    recommended: true,
  },
  {
    id: "vulnerabilities",
    icon: Bug,
    name: "Vulnerability Management",
    description: "Track and remediate vulnerabilities",
    recommended: true,
  },
  {
    id: "risks",
    icon: Target,
    name: "Risk Management",
    description: "Assess and mitigate risks",
    recommended: false,
  },
  {
    id: "tprm",
    icon: Building2,
    name: "Third-Party Risk",
    description: "Vendor security assessments",
    recommended: false,
  },
  {
    id: "compliance",
    icon: FileCheck,
    name: "Compliance",
    description: "Framework mapping and audits",
    recommended: false,
  },
  {
    id: "cmdb",
    icon: Server,
    name: "CMDB",
    description: "Asset inventory management",
    recommended: false,
  },
  {
    id: "threats",
    icon: Target,
    name: "Threat Intelligence",
    description: "MITRE ATT&CK and IOCs",
    recommended: false,
  },
  {
    id: "integrations",
    icon: Link2,
    name: "Integrations",
    description: "Connect external tools",
    recommended: false,
  },
  {
    id: "reporting",
    icon: BarChart3,
    name: "Reporting",
    description: "Dashboards and reports",
    recommended: true,
  },
];

export function ModulesStep({ onNext, onBack }: ModulesStepProps) {
  const { data, updateData } = useOnboardingStore();

  const toggleModule = (moduleId: string) => {
    const selected = data.selectedModules.includes(moduleId)
      ? data.selectedModules.filter((id) => id !== moduleId)
      : [...data.selectedModules, moduleId];
    updateData({ selectedModules: selected });
  };

  const selectRecommended = () => {
    const recommended = modules.filter((m) => m.recommended).map((m) => m.id);
    updateData({ selectedModules: recommended });
  };

  const selectAll = () => {
    updateData({ selectedModules: modules.map((m) => m.id) });
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Choose your modules</h2>
        <p className="text-muted-foreground">
          Select the security modules you want to use. You can change this later.
        </p>
      </div>

      <div className="flex justify-center gap-4 mb-6">
        <Button variant="outline" size="sm" onClick={selectRecommended}>
          Select Recommended
        </Button>
        <Button variant="outline" size="sm" onClick={selectAll}>
          Select All
        </Button>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        {modules.map((module) => {
          const isSelected = data.selectedModules.includes(module.id);
          return (
            <button
              key={module.id}
              onClick={() => toggleModule(module.id)}
              className={cn(
                "flex items-start gap-4 p-4 rounded-lg border text-left transition-all",
                isSelected
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : "border-border hover:border-primary/50"
              )}
            >
              <div
                className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center shrink-0",
                  isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                )}
              >
                {isSelected ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <module.icon className="h-5 w-5" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{module.name}</span>
                  {module.recommended && (
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                      Recommended
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {module.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <p className="text-center text-sm text-muted-foreground mt-4">
        {data.selectedModules.length} module{data.selectedModules.length !== 1 ? "s" : ""} selected
      </p>

      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={onNext} disabled={data.selectedModules.length === 0}>
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

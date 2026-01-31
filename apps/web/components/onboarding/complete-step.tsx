"use client";

import { Button } from "@/components/ui/button";
import { CheckCircle2, ArrowRight, Rocket, PartyPopper } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";

interface CompleteStepProps {
  onComplete: () => void;
}

export function CompleteStep({ onComplete }: CompleteStepProps) {
  const { data } = useOnboardingStore();

  const quickActions = [
    {
      title: "Create your first incident",
      description: "Start tracking a security event",
      href: "/incidents/new",
    },
    {
      title: "Import vulnerabilities",
      description: "Upload scan results from your tools",
      href: "/vulnerabilities",
    },
    {
      title: "Set up integrations",
      description: "Connect your existing security stack",
      href: "/integrations",
    },
    {
      title: "Invite team members",
      description: "Collaborate with your security team",
      href: "/users",
    },
  ];

  return (
    <div className="max-w-lg mx-auto text-center">
      <div className="mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 mb-6">
          <CheckCircle2 className="h-10 w-10 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold mb-4">You're all set!</h1>
        <p className="text-lg text-muted-foreground">
          Your CyberOps Companion account is ready. Let's secure your organization!
        </p>
      </div>

      <div className="bg-muted/50 rounded-lg p-6 mb-8 text-left">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Rocket className="h-5 w-5 text-primary" />
          Quick Start Actions
        </h3>
        <div className="space-y-3">
          {quickActions.map((action, index) => (
            <a
              key={index}
              href={action.href}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <div>
                <div className="font-medium">{action.title}</div>
                <div className="text-sm text-muted-foreground">
                  {action.description}
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>

      <div className="text-sm text-muted-foreground mb-6">
        <p>
          <strong>Organization:</strong> {data.organizationName}
        </p>
        <p>
          <strong>Modules enabled:</strong> {data.selectedModules.length}
        </p>
      </div>

      <Button size="lg" onClick={onComplete} className="px-8">
        Go to Dashboard
        <ArrowRight className="ml-2 h-5 w-5" />
      </Button>
    </div>
  );
}

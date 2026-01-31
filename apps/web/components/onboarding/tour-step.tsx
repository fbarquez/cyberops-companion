"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  BarChart3,
  Bell,
  Search,
  Users,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TourStepProps {
  onNext: () => void;
  onBack: () => void;
}

const features = [
  {
    icon: AlertTriangle,
    title: "Incident Management",
    description:
      "Create and track incidents through the complete lifecycle. Use phases, checklists, and decisions to maintain control.",
    tip: "Pro tip: Use keyboard shortcuts (Ctrl+K) to quickly create new incidents.",
  },
  {
    icon: BarChart3,
    title: "Real-time Dashboard",
    description:
      "Get instant visibility into your security posture with executive dashboards and customizable widgets.",
    tip: "Pro tip: Pin your most important metrics to the main dashboard.",
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description:
      "Stay informed with in-app, email, and webhook notifications. Configure alerts based on severity and type.",
    tip: "Pro tip: Set up Slack/Teams webhooks for team-wide alerts.",
  },
  {
    icon: Search,
    title: "Powerful Search",
    description:
      "Find anything instantly with global search. Filter by type, date, severity, and more.",
    tip: "Pro tip: Use Ctrl+/ to open search from anywhere.",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description:
      "Assign tasks, share evidence, and collaborate with your team in real-time on incidents.",
    tip: "Pro tip: @mention team members in comments to notify them.",
  },
  {
    icon: Zap,
    title: "Integrations",
    description:
      "Connect your existing tools - SIEM, ticketing, SOAR, and more. Automate workflows across platforms.",
    tip: "Pro tip: Start with your most critical integration first.",
  },
];

export function TourStep({ onNext, onBack }: TourStepProps) {
  const [activeFeature, setActiveFeature] = useState(0);

  const nextFeature = () => {
    if (activeFeature < features.length - 1) {
      setActiveFeature(activeFeature + 1);
    } else {
      onNext();
    }
  };

  const prevFeature = () => {
    if (activeFeature > 0) {
      setActiveFeature(activeFeature - 1);
    } else {
      onBack();
    }
  };

  const feature = features[activeFeature];

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Quick Platform Tour</h2>
        <p className="text-muted-foreground">
          Learn about key features to get the most out of CyberOps Companion
        </p>
      </div>

      {/* Progress dots */}
      <div className="flex justify-center gap-2 mb-8">
        {features.map((_, index) => (
          <button
            key={index}
            onClick={() => setActiveFeature(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-all",
              index === activeFeature
                ? "w-8 bg-primary"
                : index < activeFeature
                ? "bg-primary/50"
                : "bg-muted"
            )}
          />
        ))}
      </div>

      {/* Feature card */}
      <div className="bg-card border rounded-xl p-8 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6">
          <feature.icon className="h-8 w-8 text-primary" />
        </div>

        <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
        <p className="text-muted-foreground mb-6">{feature.description}</p>

        <div className="bg-muted/50 rounded-lg p-4 text-sm">
          <span className="font-medium text-primary">💡 {feature.tip}</span>
        </div>
      </div>

      {/* Feature navigation */}
      <div className="flex justify-center gap-2 mt-6">
        {features.map((f, index) => (
          <button
            key={index}
            onClick={() => setActiveFeature(index)}
            className={cn(
              "p-2 rounded-lg transition-all",
              index === activeFeature
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            )}
          >
            <f.icon className="h-5 w-5" />
          </button>
        ))}
      </div>

      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={prevFeature}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          {activeFeature === 0 ? "Back" : "Previous"}
        </Button>
        <Button onClick={nextFeature}>
          {activeFeature === features.length - 1 ? "Finish Tour" : "Next"}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      <p className="text-center text-sm text-muted-foreground mt-4">
        {activeFeature + 1} of {features.length}
      </p>
    </div>
  );
}

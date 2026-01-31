"use client";

import { Button } from "@/components/ui/button";
import { Shield, ArrowRight, Sparkles } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  const { user } = useAuthStore();
  const firstName = user?.full_name?.split(" ")[0] || "there";

  return (
    <div className="text-center max-w-lg mx-auto">
      <div className="mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary/10 mb-6">
          <Shield className="h-10 w-10 text-primary" />
        </div>
        <h1 className="text-3xl font-bold mb-4">
          Welcome, {firstName}! <Sparkles className="inline h-8 w-8 text-yellow-500" />
        </h1>
        <p className="text-lg text-muted-foreground">
          Let's get your security operations platform set up in just a few steps.
        </p>
      </div>

      <div className="bg-muted/50 rounded-lg p-6 mb-8 text-left">
        <h3 className="font-semibold mb-4">Here's what we'll cover:</h3>
        <ul className="space-y-3">
          <li className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-medium">1</div>
            <span>Set up your organization profile</span>
          </li>
          <li className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-medium">2</div>
            <span>Choose your security modules</span>
          </li>
          <li className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-medium">3</div>
            <span>Quick tour of key features</span>
          </li>
        </ul>
      </div>

      <Button size="lg" onClick={onNext} className="px-8">
        Let's Get Started
        <ArrowRight className="ml-2 h-5 w-5" />
      </Button>

      <p className="mt-4 text-sm text-muted-foreground">
        This will only take about 2 minutes
      </p>
    </div>
  );
}

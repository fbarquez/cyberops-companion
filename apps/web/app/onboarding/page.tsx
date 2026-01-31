"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import {
  WelcomeStep,
  OrganizationStep,
  ModulesStep,
  TourStep,
  CompleteStep,
} from "@/components/onboarding";
import { cn } from "@/lib/utils";

const TOTAL_STEPS = 5;

export default function OnboardingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, loadUser } = useAuthStore();
  const {
    currentStep,
    isComplete,
    nextStep,
    prevStep,
    completeOnboarding,
  } = useOnboardingStore();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    // If onboarding is already complete, redirect to dashboard
    if (isComplete) {
      router.push("/incidents");
    }
  }, [isComplete, router]);

  const handleComplete = () => {
    completeOnboarding();
    router.push("/incidents");
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse flex items-center gap-2">
          <Shield className="h-8 w-8 text-primary" />
          <span className="text-lg font-medium">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">CyberOps Companion</span>
          </div>

          {/* Progress indicator */}
          <div className="hidden sm:flex items-center gap-2">
            {Array.from({ length: TOTAL_STEPS }).map((_, index) => (
              <div
                key={index}
                className={cn(
                  "h-2 rounded-full transition-all",
                  index + 1 === currentStep
                    ? "w-8 bg-primary"
                    : index + 1 < currentStep
                    ? "w-2 bg-primary"
                    : "w-2 bg-muted"
                )}
              />
            ))}
          </div>

          <div className="text-sm text-muted-foreground">
            Step {currentStep} of {TOTAL_STEPS}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-12">
        {currentStep === 1 && <WelcomeStep onNext={nextStep} />}
        {currentStep === 2 && (
          <OrganizationStep onNext={nextStep} onBack={prevStep} />
        )}
        {currentStep === 3 && (
          <ModulesStep onNext={nextStep} onBack={prevStep} />
        )}
        {currentStep === 4 && (
          <TourStep onNext={nextStep} onBack={prevStep} />
        )}
        {currentStep === 5 && <CompleteStep onComplete={handleComplete} />}
      </main>
    </div>
  );
}

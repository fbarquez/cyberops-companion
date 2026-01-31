"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface OnboardingData {
  // Step 2: Organization
  organizationName: string;
  organizationSize: string;
  industry: string;
  jobTitle: string;

  // Step 3: Modules
  selectedModules: string[];

  // Completion
  completedAt: string | null;
}

interface OnboardingState {
  currentStep: number;
  data: OnboardingData;
  isComplete: boolean;

  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  updateData: (data: Partial<OnboardingData>) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
}

const initialData: OnboardingData = {
  organizationName: "",
  organizationSize: "",
  industry: "",
  jobTitle: "",
  selectedModules: [],
  completedAt: null,
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      currentStep: 1,
      data: initialData,
      isComplete: false,

      setStep: (step) => set({ currentStep: step }),

      nextStep: () => set((state) => ({ currentStep: state.currentStep + 1 })),

      prevStep: () => set((state) => ({ currentStep: Math.max(1, state.currentStep - 1) })),

      updateData: (newData) =>
        set((state) => ({
          data: { ...state.data, ...newData },
        })),

      completeOnboarding: () =>
        set((state) => ({
          isComplete: true,
          data: { ...state.data, completedAt: new Date().toISOString() },
        })),

      resetOnboarding: () =>
        set({
          currentStep: 1,
          data: initialData,
          isComplete: false,
        }),
    }),
    {
      name: "onboarding-storage",
    }
  )
);

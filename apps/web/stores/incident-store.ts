"use client";

import { create } from "zustand";
import { Incident, PhaseProgress, IRPhase } from "@/types";

interface IncidentState {
  currentIncident: Incident | null;
  phaseProgress: PhaseProgress[];
  isLoading: boolean;

  setIncident: (incident: Incident | null) => void;
  updateIncident: (updates: Partial<Incident>) => void;
  setPhaseProgress: (progress: PhaseProgress[]) => void;
  updatePhaseProgress: (phase: IRPhase, updates: Partial<PhaseProgress>) => void;
  reset: () => void;
}

export const useIncidentStore = create<IncidentState>((set) => ({
  currentIncident: null,
  phaseProgress: [],
  isLoading: false,

  setIncident: (incident) => set({ currentIncident: incident }),

  updateIncident: (updates) =>
    set((state) => ({
      currentIncident: state.currentIncident
        ? { ...state.currentIncident, ...updates }
        : null,
    })),

  setPhaseProgress: (progress) => set({ phaseProgress: progress }),

  updatePhaseProgress: (phase, updates) =>
    set((state) => ({
      phaseProgress: state.phaseProgress.map((p) =>
        p.phase === phase ? { ...p, ...updates } : p
      ),
    })),

  reset: () =>
    set({
      currentIncident: null,
      phaseProgress: [],
      isLoading: false,
    }),
}));

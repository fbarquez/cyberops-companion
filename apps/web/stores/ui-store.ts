"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

type Language = "de" | "en";
type Theme = "light" | "dark" | "system";

interface UIState {
  language: Language;
  theme: Theme;
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;

  setLanguage: (lang: Language) => void;
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapse: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      language: "en",
      theme: "system",
      sidebarOpen: true,
      sidebarCollapsed: false,

      setLanguage: (language) => set({ language }),
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      toggleSidebarCollapse: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: "ui-storage",
    }
  )
);

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

type Language = "de" | "en";
type Theme = "light" | "dark" | "system";

interface QuickAccessItem {
  href: string;
  label: string;
  icon: string;
  visitedAt: number;
}

interface UIState {
  language: Language;
  theme: Theme;
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;

  // Command palette state
  commandPaletteOpen: boolean;

  // Sidebar navigation groups expanded state
  expandedGroups: Record<string, boolean>;

  // Quick access (recent pages)
  quickAccess: QuickAccessItem[];

  // Actions
  setLanguage: (lang: Language) => void;
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapse: () => void;

  // Command palette actions
  setCommandPaletteOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;

  // Sidebar group actions
  toggleGroup: (groupId: string) => void;
  setGroupExpanded: (groupId: string, expanded: boolean) => void;

  // Quick access actions
  addToQuickAccess: (item: Omit<QuickAccessItem, 'visitedAt'>) => void;
  clearQuickAccess: () => void;
}

const MAX_QUICK_ACCESS_ITEMS = 5;

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      language: "en",
      theme: "system",
      sidebarOpen: true,
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      expandedGroups: {
        operations: true,
        security: true,
        compliance: false,
        management: false,
        tools: false,
        administration: false,
      },
      quickAccess: [],

      setLanguage: (language) => set({ language }),
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      toggleSidebarCollapse: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
      toggleCommandPalette: () =>
        set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),

      toggleGroup: (groupId) =>
        set((state) => ({
          expandedGroups: {
            ...state.expandedGroups,
            [groupId]: !state.expandedGroups[groupId],
          },
        })),

      setGroupExpanded: (groupId, expanded) =>
        set((state) => ({
          expandedGroups: {
            ...state.expandedGroups,
            [groupId]: expanded,
          },
        })),

      addToQuickAccess: (item) =>
        set((state) => {
          const newItem = { ...item, visitedAt: Date.now() };
          const filtered = state.quickAccess.filter((i) => i.href !== item.href);
          const updated = [newItem, ...filtered].slice(0, MAX_QUICK_ACCESS_ITEMS);
          return { quickAccess: updated };
        }),

      clearQuickAccess: () => set({ quickAccess: [] }),
    }),
    {
      name: "ui-storage",
    }
  )
);

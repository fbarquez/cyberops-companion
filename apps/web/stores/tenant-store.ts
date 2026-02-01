"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { saveTokens } from "@/lib/auth";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  status: string;
  plan: string;
  logo_url?: string;
  org_role: string;
  is_default: boolean;
  joined_at: string;
}

interface TenantState {
  currentTenant: Organization | null;
  availableTenants: Organization[];
  isLoading: boolean;

  setCurrentTenant: (tenant: Organization | null) => void;
  setAvailableTenants: (tenants: Organization[]) => void;
  switchTenant: (tenantId: string) => Promise<void>;
  loadTenants: (token: string) => Promise<void>;
  clearTenants: () => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      currentTenant: null,
      availableTenants: [],
      isLoading: false,

      setCurrentTenant: (tenant) => set({ currentTenant: tenant }),

      setAvailableTenants: (tenants) => {
        set({ availableTenants: tenants });
        // Set current tenant to default or first available
        const current = get().currentTenant;
        if (!current && tenants.length > 0) {
          const defaultTenant = tenants.find((t) => t.is_default) || tenants[0];
          set({ currentTenant: defaultTenant });
        }
      },

      switchTenant: async (tenantId: string) => {
        set({ isLoading: true });
        try {
          const token = localStorage.getItem("access_token");
          if (!token) throw new Error("Not authenticated");

          const response = await fetch(`${API_BASE_URL}/api/v1/organizations/switch`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ tenant_id: tenantId }),
          });

          if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Failed to switch tenant" }));
            throw new Error(error.detail);
          }

          const tokens = await response.json();
          saveTokens(tokens);

          // Find the new current tenant
          const tenants = get().availableTenants;
          const newTenant = tenants.find((t) => t.id === tenantId);
          if (newTenant) {
            set({ currentTenant: newTenant, isLoading: false });
          }

          // Reload the page to refresh all data with new tenant context
          window.location.reload();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      loadTenants: async (token: string) => {
        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/organizations/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error("Failed to load organizations");
          }

          const data = await response.json();
          const tenants = data.organizations || [];

          set({ availableTenants: tenants, isLoading: false });

          // Set current tenant if not already set
          const current = get().currentTenant;
          if (!current && tenants.length > 0) {
            const defaultTenant = tenants.find((t: Organization) => t.is_default) || tenants[0];
            set({ currentTenant: defaultTenant });
          }
        } catch (error) {
          set({ isLoading: false });
          console.error("Failed to load tenants:", error);
        }
      },

      clearTenants: () => {
        set({
          currentTenant: null,
          availableTenants: [],
        });
      },
    }),
    {
      name: "tenant-storage",
      partialize: (state) => ({
        currentTenant: state.currentTenant,
      }),
    }
  )
);

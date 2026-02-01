"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/types";
import { authAPI, ssoAPI, SSOCallbackResponse } from "@/lib/api-client";
import { saveTokens, clearTokens, getTokens, isTokenExpired } from "@/lib/auth";
import { useTenantStore } from "./tenant-store";

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  ssoProvider: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  loginWithSSO: (provider: string, code: string, state: string) => Promise<SSOCallbackResponse>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoading: false,
      isAuthenticated: false,
      ssoProvider: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const tokens = await authAPI.login(email, password);
          saveTokens(tokens);

          const user = await authAPI.me(tokens.access_token);

          set({
            user: user as User,
            token: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Load user's organizations/tenants
          await useTenantStore.getState().loadTenants(tokens.access_token);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true });
        try {
          await authAPI.register({ email, password, full_name: fullName });
          // Auto login after registration
          await get().login(email, password);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      loginWithSSO: async (provider: string, code: string, state: string) => {
        set({ isLoading: true });
        try {
          const response = await ssoAPI.callback(provider, code, state);
          saveTokens({
            access_token: response.access_token,
            refresh_token: response.refresh_token,
          });

          set({
            user: {
              id: response.user.id,
              email: response.user.email,
              full_name: response.user.full_name,
              role: response.user.role,
              is_active: true,
            } as User,
            token: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            ssoProvider: response.user.sso_provider || provider,
          });

          // Load user's organizations/tenants
          await useTenantStore.getState().loadTenants(response.access_token);

          return response;
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        clearTokens();
        useTenantStore.getState().clearTenants();
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          ssoProvider: null,
        });
      },

      refreshAuth: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          get().logout();
          return;
        }

        try {
          const tokens = await authAPI.refresh(refreshToken);
          saveTokens(tokens);

          set({
            token: tokens.access_token,
            refreshToken: tokens.refresh_token,
          });
        } catch {
          get().logout();
        }
      },

      loadUser: async () => {
        const tokens = getTokens();
        if (!tokens) return;

        if (isTokenExpired(tokens.access_token)) {
          if (tokens.refresh_token && !isTokenExpired(tokens.refresh_token)) {
            await get().refreshAuth();
          } else {
            get().logout();
            return;
          }
        }

        try {
          const user = await authAPI.me(tokens.access_token);
          set({
            user: user as User,
            token: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
          });

          // Load user's organizations/tenants
          await useTenantStore.getState().loadTenants(tokens.access_token);
        } catch {
          get().logout();
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
      }),
    }
  )
);

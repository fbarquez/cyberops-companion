"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/types";
import { authAPI } from "@/lib/api-client";
import { saveTokens, clearTokens, getTokens, isTokenExpired } from "@/lib/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
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

      logout: () => {
        clearTokens();
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
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

import { decodeJwt } from "jose";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "lead" | "analyst";
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

const TOKEN_KEY = "ir_companion_tokens";

export function saveTokens(tokens: AuthTokens): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  }
}

export function getTokens(): AuthTokens | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(TOKEN_KEY);
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

export function clearTokens(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeJwt(token);
    if (!decoded.exp) return true;
    // Add 30 second buffer
    return decoded.exp * 1000 < Date.now() + 30000;
  } catch {
    return true;
  }
}

export function hasRole(user: User | null, requiredRole: string): boolean {
  if (!user) return false;
  const roleHierarchy: Record<string, number> = {
    admin: 4,
    manager: 3,
    lead: 2,
    analyst: 1,
  };
  return (roleHierarchy[user.role] || 0) >= (roleHierarchy[requiredRole] || 0);
}

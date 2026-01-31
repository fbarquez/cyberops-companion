import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string, locale: string = "en"): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString(locale === "de" ? "de-DE" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`;
}

export function truncateHash(hash: string, length: number = 8): string {
  if (hash.length <= length * 2) return hash;
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: "bg-severity-critical",
    high: "bg-severity-high",
    medium: "bg-severity-medium",
    low: "bg-severity-low",
    informational: "bg-severity-info",
  };
  return colors[severity] || "bg-gray-500";
}

export function getPhaseColor(phase: string): string {
  const colors: Record<string, string> = {
    detection: "bg-phase-detection",
    analysis: "bg-phase-analysis",
    containment: "bg-phase-containment",
    eradication: "bg-phase-eradication",
    recovery: "bg-phase-recovery",
    post_incident: "bg-phase-post_incident",
  };
  return colors[phase] || "bg-gray-500";
}

export function getPhaseIndex(phase: string): number {
  const phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"];
  return phases.indexOf(phase);
}

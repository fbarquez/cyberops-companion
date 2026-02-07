"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type ThreatLevel = "critical" | "high" | "medium" | "low" | "unknown";
type Motivation = "financial" | "espionage" | "hacktivism" | "destruction" | "unknown";
type Sophistication = "apt" | "organized_crime" | "script_kiddie" | "insider" | "unknown";

const threatLevelVariants: Record<ThreatLevel, "destructive" | "default" | "secondary" | "outline"> = {
  critical: "destructive",
  high: "destructive",
  medium: "default",
  low: "secondary",
  unknown: "outline",
};

const motivationColors: Record<Motivation, string> = {
  financial: "bg-green-500/10 text-green-700 border-green-500/20",
  espionage: "bg-purple-500/10 text-purple-700 border-purple-500/20",
  hacktivism: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  destruction: "bg-red-500/10 text-red-700 border-red-500/20",
  unknown: "bg-gray-500/10 text-gray-700 border-gray-500/20",
};

const sophisticationColors: Record<Sophistication, string> = {
  apt: "bg-red-500/10 text-red-700 border-red-500/20",
  organized_crime: "bg-orange-500/10 text-orange-700 border-orange-500/20",
  script_kiddie: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
  insider: "bg-purple-500/10 text-purple-700 border-purple-500/20",
  unknown: "bg-gray-500/10 text-gray-700 border-gray-500/20",
};

const motivationLabels: Record<Motivation, string> = {
  financial: "Financial",
  espionage: "Espionage",
  hacktivism: "Hacktivism",
  destruction: "Destruction",
  unknown: "Unknown",
};

const sophisticationLabels: Record<Sophistication, string> = {
  apt: "APT",
  organized_crime: "Organized Crime",
  script_kiddie: "Script Kiddie",
  insider: "Insider",
  unknown: "Unknown",
};

export function ThreatLevelBadge({ level, className }: { level: ThreatLevel; className?: string }) {
  return (
    <Badge variant={threatLevelVariants[level] || "outline"} className={className}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  );
}

export function MotivationBadge({ motivation, className }: { motivation: Motivation; className?: string }) {
  return (
    <Badge
      variant="outline"
      className={cn(motivationColors[motivation] || motivationColors.unknown, className)}
    >
      {motivationLabels[motivation] || motivation}
    </Badge>
  );
}

export function SophisticationBadge({ sophistication, className }: { sophistication: Sophistication; className?: string }) {
  return (
    <Badge
      variant="outline"
      className={cn(sophisticationColors[sophistication] || sophisticationColors.unknown, className)}
    >
      {sophisticationLabels[sophistication] || sophistication}
    </Badge>
  );
}

export function ActiveStatusBadge({ isActive, className }: { isActive: boolean; className?: string }) {
  return (
    <Badge
      variant={isActive ? "default" : "secondary"}
      className={cn(
        isActive ? "bg-green-500/10 text-green-700 border-green-500/20" : "",
        className
      )}
    >
      {isActive ? "Active" : "Inactive"}
    </Badge>
  );
}

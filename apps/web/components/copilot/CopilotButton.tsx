"use client";

import { Bot, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotOptional } from "./CopilotProvider";
import { cn } from "@/lib/utils";

interface CopilotButtonProps {
  className?: string;
}

export function CopilotButton({ className }: CopilotButtonProps) {
  const copilot = useCopilotOptional();

  if (!copilot) return null;

  const { isOpen, toggleChat, health } = copilot;

  // Don't show button if copilot is completely disabled
  if (health?.status === "disabled") return null;

  const isConfigured = health?.status === "healthy";

  return (
    <Button
      onClick={toggleChat}
      size="lg"
      className={cn(
        "fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50",
        "transition-all duration-200 hover:scale-110",
        isOpen
          ? "bg-gray-600 hover:bg-gray-700"
          : isConfigured
          ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
          : "bg-gray-400 hover:bg-gray-500",
        className
      )}
      title={isConfigured ? "AI Copilot" : "AI Copilot (not configured)"}
    >
      {isOpen ? (
        <X className="h-6 w-6 text-white" />
      ) : (
        <Bot className="h-6 w-6 text-white" />
      )}

      {/* Pulse animation when healthy */}
      {isConfigured && !isOpen && (
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-green-500"></span>
        </span>
      )}
    </Button>
  );
}

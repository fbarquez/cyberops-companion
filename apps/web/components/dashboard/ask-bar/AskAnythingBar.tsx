"use client";

import { useState } from "react";
import { Sparkles, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useCopilot } from "@/components/copilot/CopilotProvider";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const AI_MODELS = [
  { id: "groq:llama-3.3-70b-versatile", label: "Llama 3.3 70B", provider: "Groq" },
  { id: "groq:llama-3.1-8b-instant", label: "Llama 3.1 8B", provider: "Groq" },
  { id: "gemini:gemini-2.0-flash", label: "Gemini 2.0 Flash", provider: "Gemini" },
  { id: "gemini:gemini-1.5-pro", label: "Gemini 1.5 Pro", provider: "Gemini" },
  { id: "openai:gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { id: "openai:gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
];

export function AskAnythingBar() {
  const { setCommandPaletteOpen } = useUIStore();
  const { openChat, sendMessage, selectedModel, setSelectedModel, availableProviders } = useCopilot();
  const [query, setQuery] = useState("");

  const currentModel = AI_MODELS.find((m) => m.id === selectedModel) || AI_MODELS[0];

  // Filter models by available providers
  const availableModels = AI_MODELS.filter((model) => {
    const provider = model.id.split(":")[0];
    return availableProviders.includes(provider);
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      openChat();
      sendMessage(query);
      setQuery("");
    }
  };

  const handleBarClick = () => {
    setCommandPaletteOpen(true);
  };

  return (
    <div className="w-full">
      <div
        onClick={handleBarClick}
        className={cn(
          "flex items-center gap-3 rounded-xl border bg-card p-4 cursor-pointer",
          "shadow-sm hover:shadow-md transition-all duration-200",
          "hover:border-primary/50 group"
        )}
      >
        {/* Sparkle Icon */}
        <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
          <Sparkles className="h-5 w-5" />
        </div>

        {/* Input Area */}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground">Ask anything...</div>
          <div className="text-xs text-muted-foreground">
            Search commands, navigate, or get AI assistance
          </div>
        </div>

        {/* Model Selector */}
        <DropdownMenu>
          <DropdownMenuTrigger
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-2 rounded-lg border bg-muted/50 px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <span className="hidden sm:inline">{currentModel.provider}:</span>
            <span>{currentModel.label}</span>
            <ChevronDown className="h-3 w-3" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {availableModels.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => setSelectedModel(model.id)}
                className={cn(
                  "flex items-center justify-between",
                  model.id === selectedModel && "bg-primary/10"
                )}
              >
                <span>{model.label}</span>
                <span className="text-xs text-muted-foreground">{model.provider}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Keyboard Hint */}
        <kbd className="hidden md:inline-flex h-7 items-center gap-1 rounded-md border bg-muted px-2 font-mono text-xs font-medium text-muted-foreground">
          <span className="text-base">⌘</span>K
        </kbd>
      </div>
    </div>
  );
}

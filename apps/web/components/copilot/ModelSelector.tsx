"use client";

import { useState } from "react";
import { ChevronDown, Zap, Brain, Sparkles, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  category: "fast" | "versatile" | "powerful";
  description: string;
  isPro?: boolean;
  icon?: string;
}

export const AI_MODELS: AIModel[] = [
  // Fast and cost-efficient
  {
    id: "groq:llama-3.3-70b-versatile",
    name: "Llama 3.3 70B",
    provider: "Groq",
    category: "fast",
    description: "Fast and free",
  },
  {
    id: "groq:llama-3.1-8b-instant",
    name: "Llama 3.1 8B",
    provider: "Groq",
    category: "fast",
    description: "Ultra fast responses",
  },
  {
    id: "gemini:gemini-2.0-flash",
    name: "Gemini 2.0 Flash",
    provider: "Google",
    category: "fast",
    description: "Quick and efficient",
  },
  // Versatile and highly intelligent
  {
    id: "groq:mixtral-8x7b-32768",
    name: "Mixtral 8x7B",
    provider: "Groq",
    category: "versatile",
    description: "Balanced performance",
  },
  {
    id: "openai:gpt-4o-mini",
    name: "GPT-4o Mini",
    provider: "OpenAI",
    category: "versatile",
    description: "Smart and affordable",
    isPro: true,
  },
  {
    id: "anthropic:claude-3-haiku-20240307",
    name: "Claude 3 Haiku",
    provider: "Anthropic",
    category: "versatile",
    description: "Fast and intelligent",
    isPro: true,
  },
  // Most powerful
  {
    id: "openai:gpt-4o",
    name: "GPT-4o",
    provider: "OpenAI",
    category: "powerful",
    description: "Highly capable",
    isPro: true,
  },
  {
    id: "anthropic:claude-3-5-sonnet-20241022",
    name: "Claude 3.5 Sonnet",
    provider: "Anthropic",
    category: "powerful",
    description: "Excellent reasoning",
    isPro: true,
  },
  {
    id: "openai:gpt-4-turbo",
    name: "GPT-4 Turbo",
    provider: "OpenAI",
    category: "powerful",
    description: "Most capable GPT-4",
    isPro: true,
  },
];

const CATEGORIES = [
  { id: "fast", label: "Fast & Free", icon: Zap, color: "text-green-500" },
  { id: "versatile", label: "Versatile", icon: Brain, color: "text-blue-500" },
  { id: "powerful", label: "Most Powerful", icon: Sparkles, color: "text-purple-500" },
];

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  availableProviders?: string[];
}

export function ModelSelector({
  selectedModel,
  onModelChange,
  availableProviders = ["groq"]
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const currentModel = AI_MODELS.find((m) => m.id === selectedModel) || AI_MODELS[0];

  const isModelAvailable = (model: AIModel) => {
    const provider = model.id.split(":")[0];
    return availableProviders.includes(provider) || !model.isPro;
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded-md text-xs",
          "bg-white/10 hover:bg-white/20 transition-colors",
          "text-white/90 hover:text-white"
        )}
      >
        <span className="font-medium truncate max-w-[100px]">{currentModel.name}</span>
        <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-50"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute top-full right-0 mt-1 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden">
            <div className="p-2 border-b border-gray-700">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                Models
              </span>
            </div>

            <div className="max-h-80 overflow-y-auto">
              {CATEGORIES.map((category) => {
                const CategoryIcon = category.icon;
                const models = AI_MODELS.filter((m) => m.category === category.id);

                return (
                  <div key={category.id} className="py-1">
                    {/* Category Header */}
                    <div className="flex items-center gap-2 px-3 py-1.5">
                      <CategoryIcon className={cn("h-3.5 w-3.5", category.color)} />
                      <span className="text-xs font-medium text-gray-400">
                        {category.label}
                      </span>
                    </div>

                    {/* Models */}
                    {models.map((model) => {
                      const isAvailable = isModelAvailable(model);
                      const isSelected = model.id === selectedModel;

                      return (
                        <button
                          key={model.id}
                          onClick={() => {
                            if (isAvailable) {
                              onModelChange(model.id);
                              setIsOpen(false);
                            }
                          }}
                          disabled={!isAvailable}
                          className={cn(
                            "w-full flex items-center justify-between px-3 py-2 text-left",
                            "transition-colors",
                            isSelected
                              ? "bg-violet-600/20 text-white"
                              : isAvailable
                              ? "hover:bg-gray-800 text-gray-300 hover:text-white"
                              : "opacity-50 cursor-not-allowed text-gray-500"
                          )}
                        >
                          <div className="flex items-center gap-2">
                            {isSelected && (
                              <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                            )}
                            <div className={cn(!isSelected && "ml-3.5")}>
                              <div className="flex items-center gap-1.5">
                                <span className="text-sm font-medium">{model.name}</span>
                                {model.isPro && !isAvailable && (
                                  <Lock className="h-3 w-3 text-gray-500" />
                                )}
                              </div>
                              <span className="text-xs text-gray-500">{model.provider}</span>
                            </div>
                          </div>

                          {model.isPro && (
                            <span className={cn(
                              "text-[10px] px-1.5 py-0.5 rounded",
                              isAvailable
                                ? "bg-violet-500/20 text-violet-300"
                                : "bg-gray-700 text-gray-500"
                            )}>
                              PRO
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                );
              })}
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-gray-700 bg-gray-800/50">
              <p className="text-[10px] text-gray-500 text-center">
                PRO models require API key in settings
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

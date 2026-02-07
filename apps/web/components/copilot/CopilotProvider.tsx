"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";

// Types
export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}

export interface CopilotHealth {
  status: "healthy" | "not_configured" | "disabled" | "unhealthy";
  provider: string | null;
  model: string | null;
  message: string;
}

export interface CopilotContextType {
  // State
  isOpen: boolean;
  messages: CopilotMessage[];
  isLoading: boolean;
  health: CopilotHealth | null;
  context: string | null;
  selectedModel: string;
  availableProviders: string[];

  // Actions
  openChat: () => void;
  closeChat: () => void;
  toggleChat: () => void;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
  setContext: (context: string | null) => void;
  setSelectedModel: (model: string) => void;
  checkHealth: () => Promise<void>;

  // Specialized actions
  analyzeIncident: (incidentId: string) => Promise<void>;
  explainControl: (framework: string, controlId: string, controlTitle: string) => Promise<void>;
  suggestRemediation: (framework: string, gap: any) => Promise<void>;
}

const CopilotContext = createContext<CopilotContextType | null>(null);

export function useCopilot() {
  const context = useContext(CopilotContext);
  if (!context) {
    throw new Error("useCopilot must be used within CopilotProvider");
  }
  return context;
}

// Optional hook that doesn't throw if not in provider
export function useCopilotOptional() {
  return useContext(CopilotContext);
}

interface CopilotProviderProps {
  children: React.ReactNode;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DEFAULT_MODEL = "groq:llama-3.3-70b-versatile";
const DEFAULT_PROVIDERS = ["groq", "gemini", "openai"];

export function CopilotProvider({ children }: CopilotProviderProps) {
  const { token } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<CopilotHealth | null>(null);
  const [context, setContext] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>(DEFAULT_MODEL);
  const [availableProviders, setAvailableProviders] = useState<string[]>(DEFAULT_PROVIDERS);

  // Generate unique ID
  const generateId = () => `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Check health on mount
  const checkHealth = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/copilot/health`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (error) {
      console.error("Failed to check copilot health:", error);
    }
  }, [token]);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Open/close/toggle
  const openChat = useCallback(() => setIsOpen(true), []);
  const closeChat = useCallback(() => setIsOpen(false), []);
  const toggleChat = useCallback(() => setIsOpen((prev) => !prev), []);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Send message
  const sendMessage = useCallback(
    async (message: string) => {
      if (!token || !message.trim()) return;

      // Add user message
      const userMessage: CopilotMessage = {
        id: generateId(),
        role: "user",
        content: message,
        timestamp: new Date(),
      };

      // Add placeholder for assistant response
      const assistantMessage: CopilotMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        // Build history (exclude loading messages)
        const history = messages
          .filter((m) => !m.isLoading && !m.error)
          .map((m) => ({ role: m.role, content: m.content }));

        const response = await fetch(`${API_URL}/api/v1/copilot/chat`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            history: history.slice(-10), // Last 10 messages for context
            context,
          }),
        });

        const data = await response.json();

        // Update assistant message with response
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: data.content || data.error || "No response received",
                  isLoading: false,
                  error: data.error,
                }
              : m
          )
        );
      } catch (error) {
        // Update with error
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: "Failed to get response. Please try again.",
                  isLoading: false,
                  error: "Connection error",
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [token, messages, context]
  );

  // Analyze incident
  const analyzeIncident = useCallback(
    async (incidentId: string) => {
      if (!token) return;

      openChat();

      const userMessage: CopilotMessage = {
        id: generateId(),
        role: "user",
        content: `Analyze incident ${incidentId}`,
        timestamp: new Date(),
      };

      const assistantMessage: CopilotMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        const response = await fetch(`${API_URL}/api/v1/copilot/analyze-incident`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ incident_id: incidentId }),
        });

        const data = await response.json();

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: data.content || data.error || "No response received",
                  isLoading: false,
                  error: data.error,
                }
              : m
          )
        );
      } catch (error) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: "Failed to analyze incident.",
                  isLoading: false,
                  error: "Connection error",
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [token, openChat]
  );

  // Explain control
  const explainControl = useCallback(
    async (framework: string, controlId: string, controlTitle: string) => {
      if (!token) return;

      openChat();

      const userMessage: CopilotMessage = {
        id: generateId(),
        role: "user",
        content: `Explain ${framework} control ${controlId}: ${controlTitle}`,
        timestamp: new Date(),
      };

      const assistantMessage: CopilotMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        const response = await fetch(`${API_URL}/api/v1/copilot/explain-control`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            framework,
            control_id: controlId,
            control_title: controlTitle,
          }),
        });

        const data = await response.json();

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: data.content || data.error || "No response received",
                  isLoading: false,
                  error: data.error,
                }
              : m
          )
        );
      } catch (error) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: "Failed to explain control.",
                  isLoading: false,
                  error: "Connection error",
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [token, openChat]
  );

  // Suggest remediation
  const suggestRemediation = useCallback(
    async (framework: string, gap: any) => {
      if (!token) return;

      openChat();

      const userMessage: CopilotMessage = {
        id: generateId(),
        role: "user",
        content: `Suggest remediation for ${framework} gap: ${gap.control_id || gap.measure_id}`,
        timestamp: new Date(),
      };

      const assistantMessage: CopilotMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      try {
        const response = await fetch(`${API_URL}/api/v1/copilot/suggest-remediation`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ framework, gap }),
        });

        const data = await response.json();

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: data.content || data.error || "No response received",
                  isLoading: false,
                  error: data.error,
                }
              : m
          )
        );
      } catch (error) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content: "Failed to suggest remediation.",
                  isLoading: false,
                  error: "Connection error",
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [token, openChat]
  );

  const value: CopilotContextType = {
    isOpen,
    messages,
    isLoading,
    health,
    context,
    selectedModel,
    availableProviders,
    openChat,
    closeChat,
    toggleChat,
    sendMessage,
    clearMessages,
    setContext,
    setSelectedModel,
    checkHealth,
    analyzeIncident,
    explainControl,
    suggestRemediation,
  };

  return <CopilotContext.Provider value={value}>{children}</CopilotContext.Provider>;
}

"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Bot, User, AlertCircle, Loader2, Sparkles, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCopilot, CopilotMessage } from "./CopilotProvider";
import { cn } from "@/lib/utils";

interface CopilotChatProps {
  className?: string;
}

export function CopilotChat({ className }: CopilotChatProps) {
  const { messages, isLoading, health, sendMessage, clearMessages, isOpen } = useCopilot();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input;
    setInput("");
    await sendMessage(message);
  };

  const isConfigured = health?.status === "healthy";

  // Don't render if not open
  if (!isOpen) return null;

  return (
    <div
      className={cn(
        "fixed bottom-24 right-6 w-96 h-[500px] bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col z-50",
        "transition-all duration-200",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-t-lg">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-white" />
          <span className="font-semibold text-white">AI Copilot</span>
          {health?.provider && (
            <span className="text-xs text-white/70 bg-white/20 px-2 py-0.5 rounded-full">
              {health.provider}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-white hover:bg-white/20"
            onClick={clearMessages}
            title="Clear chat"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {!isConfigured && (
          <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-amber-800 dark:text-amber-200">
                  AI Copilot not configured
                </p>
                <p className="text-amber-700 dark:text-amber-300 mt-1">
                  {health?.message || "Install Ollama or configure a cloud AI provider in settings."}
                </p>
              </div>
            </div>
          </div>
        )}

        {messages.length === 0 && isConfigured && (
          <div className="text-center py-8">
            <Sparkles className="h-12 w-12 mx-auto text-violet-400 mb-4" />
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              How can I help you?
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              I can assist with incident analysis, compliance guidance, and security operations.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                "Explain BSI DER.2.1",
                "NIS2 requirements",
                "Analyze an incident",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="text-xs px-3 py-1.5 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full hover:bg-violet-200 dark:hover:bg-violet-900/50 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>
      </ScrollArea>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-gray-200 dark:border-gray-700"
      >
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isConfigured ? "Ask anything..." : "Copilot not configured"}
            disabled={!isConfigured || isLoading}
            className="flex-1"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!isConfigured || isLoading || !input.trim()}
            className="bg-violet-600 hover:bg-violet-700"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: CopilotMessage }) {
  const isUser = message.role === "user";
  const isError = !!message.error;

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser
            ? "bg-gray-200 dark:bg-gray-700"
            : isError
            ? "bg-red-100 dark:bg-red-900/30"
            : "bg-violet-100 dark:bg-violet-900/30"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
        ) : (
          <Bot
            className={cn(
              "h-4 w-4",
              isError
                ? "text-red-600 dark:text-red-400"
                : "text-violet-600 dark:text-violet-400"
            )}
          />
        )}
      </div>

      {/* Message */}
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-3 py-2",
          isUser
            ? "bg-violet-600 text-white"
            : isError
            ? "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800"
            : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        )}
      >
        {message.isLoading ? (
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        ) : (
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useCallback } from "react";
import { useUIStore } from "@/stores/ui-store";

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  action: () => void;
  preventDefault?: boolean;
}

export function useKeyboardShortcut(config: ShortcutConfig) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const { key, ctrl, meta, shift, action, preventDefault = true } = config;

      const isCtrlOrMeta = ctrl || meta;
      const ctrlMetaPressed = event.ctrlKey || event.metaKey;

      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        (isCtrlOrMeta ? ctrlMetaPressed : !ctrlMetaPressed) &&
        (shift ? event.shiftKey : !event.shiftKey)
      ) {
        if (preventDefault) {
          event.preventDefault();
        }
        action();
      }
    },
    [config]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

export function useCommandPaletteShortcut() {
  const { toggleCommandPalette, setCommandPaletteOpen } = useUIStore();

  // Cmd+K or Ctrl+K to toggle
  useKeyboardShortcut({
    key: "k",
    meta: true,
    action: toggleCommandPalette,
  });

  // Escape to close
  useKeyboardShortcut({
    key: "Escape",
    action: () => setCommandPaletteOpen(false),
    preventDefault: false,
  });
}

export function useGlobalShortcuts() {
  const { toggleSidebarCollapse } = useUIStore();

  // Cmd+B to toggle sidebar
  useKeyboardShortcut({
    key: "b",
    meta: true,
    action: toggleSidebarCollapse,
  });
}

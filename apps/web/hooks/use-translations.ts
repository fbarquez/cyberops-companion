"use client";

import { useUIStore } from "@/stores/ui-store";
import { t, TranslationKey } from "@/i18n/translations";

export function useTranslations() {
  const language = useUIStore((state) => state.language);

  return {
    t: (key: string) => t(key, language),
    language,
  };
}

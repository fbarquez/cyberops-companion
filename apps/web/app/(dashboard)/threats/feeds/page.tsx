"use client";

import { Header } from "@/components/shared/header";
import { useTranslations } from "@/hooks/use-translations";
import { FeedsList } from "@/components/threats/FeedsList";

export default function FeedsPage() {
  const { t } = useTranslations();

  return (
    <div className="flex flex-col h-full">
      <Header title="Threat Intelligence Feeds" />

      <div className="p-6 space-y-6 overflow-y-auto">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Manage Feeds</h2>
          <p className="text-muted-foreground">
            Configure threat intelligence feeds to automatically import IOCs from MISP, OTX, VirusTotal, and other sources.
          </p>
        </div>

        <FeedsList />
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { EvidenceBridgeDashboard } from "@/components/compliance/EvidenceBridgeDashboard";

export default function EvidenceBridgePage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="ISMS ↔ SOC Evidence Bridge">
        <Link href="/compliance/assurance">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Assurance
          </Button>
        </Link>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <EvidenceBridgeDashboard />
      </div>
    </div>
  );
}

"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Factory, ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";

export default function KRITISPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="KRITIS Compliance">
        <Badge variant="secondary">Coming Soon</Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mb-6">
              <Factory className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>

            <h2 className="text-2xl font-bold mb-2">KRITIS</h2>
            <p className="text-lg text-muted-foreground mb-4">
              Kritische Infrastrukturen (Critical Infrastructure Protection)
            </p>

            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">What is KRITIS?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                KRITIS is the German regulation for critical infrastructure protection,
                mandated by the BSI-Gesetz (BSI Act) and IT-Sicherheitsgesetz 2.0.
                It applies to operators of critical infrastructure in Germany.
              </p>

              <h3 className="font-semibold mb-2">KRITIS Sectors</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Energy (Energie)</li>
                <li>• Water (Wasser)</li>
                <li>• Food (Ernährung)</li>
                <li>• IT & Telecommunications</li>
                <li>• Health (Gesundheit)</li>
                <li>• Finance & Insurance</li>
                <li>• Transport & Traffic</li>
                <li>• Municipal Waste Management</li>
              </ul>

              <h3 className="font-semibold mt-4 mb-2">Key Features (Coming)</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Sector-specific requirements</li>
                <li>• BSI registration management</li>
                <li>• Incident reporting to BSI</li>
                <li>• Audit preparation (§8a)</li>
                <li>• Cross-mapping to NIS2</li>
              </ul>
            </div>

            <div className="flex gap-3 justify-center">
              <Link href="/compliance">
                <Button variant="outline">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Hub
                </Button>
              </Link>
              <Button disabled>
                <Bell className="h-4 w-4 mr-2" />
                Notify Me
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

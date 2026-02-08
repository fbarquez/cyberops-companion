"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BarChart3, ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";

export default function COBITPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="COBIT Framework">
        <Badge variant="secondary">Coming Soon</Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mb-6">
              <BarChart3 className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            </div>

            <h2 className="text-2xl font-bold mb-2">COBIT 2019</h2>
            <p className="text-lg text-muted-foreground mb-4">
              Control Objectives for Information and Related Technologies
            </p>

            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">What is COBIT?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                COBIT is a framework for IT governance and management, developed by ISACA.
                It helps organizations develop, organize, and implement strategies around
                IT governance and management.
              </p>

              <h3 className="font-semibold mb-2">Governance Objectives</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• <strong>EDM</strong> - Evaluate, Direct and Monitor</li>
                <li>• <strong>APO</strong> - Align, Plan and Organize</li>
                <li>• <strong>BAI</strong> - Build, Acquire and Implement</li>
                <li>• <strong>DSS</strong> - Deliver, Service and Support</li>
                <li>• <strong>MEA</strong> - Monitor, Evaluate and Assess</li>
              </ul>

              <h3 className="font-semibold mt-4 mb-2">Key Features (Coming)</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• COBIT 2019 assessment</li>
                <li>• Capability levels (0-5)</li>
                <li>• Design factors analysis</li>
                <li>• Focus area selection</li>
                <li>• Cross-mapping to ISO 27001, ITIL</li>
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

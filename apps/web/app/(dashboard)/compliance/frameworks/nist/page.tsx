"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Server, ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";

export default function NISTPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="NIST Cybersecurity Framework">
        <Badge variant="secondary">Coming Soon</Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 bg-cyan-100 dark:bg-cyan-900 rounded-full flex items-center justify-center mb-6">
              <Server className="h-8 w-8 text-cyan-600 dark:text-cyan-400" />
            </div>

            <h2 className="text-2xl font-bold mb-2">NIST CSF</h2>
            <p className="text-lg text-muted-foreground mb-4">
              NIST Cybersecurity Framework 2.0
            </p>

            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">What is NIST CSF?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                The NIST Cybersecurity Framework provides a policy framework of computer security
                guidance for organizations to assess and improve their ability to prevent, detect,
                and respond to cyber attacks.
              </p>

              <h3 className="font-semibold mb-2">Core Functions</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• <strong>Govern</strong> - Cybersecurity risk management strategy</li>
                <li>• <strong>Identify</strong> - Asset management, risk assessment</li>
                <li>• <strong>Protect</strong> - Access control, awareness, data security</li>
                <li>• <strong>Detect</strong> - Anomalies, continuous monitoring</li>
                <li>• <strong>Respond</strong> - Response planning, communications</li>
                <li>• <strong>Recover</strong> - Recovery planning, improvements</li>
              </ul>

              <h3 className="font-semibold mt-4 mb-2">Key Features (Coming)</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• NIST CSF 2.0 assessment</li>
                <li>• Implementation tiers (1-4)</li>
                <li>• Profile creation (Current/Target)</li>
                <li>• Subcategory evaluation</li>
                <li>• Cross-mapping to ISO 27001, CIS</li>
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

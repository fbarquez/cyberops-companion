"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Car, ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";

export default function TISAXPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="TISAX Assessment">
        <Badge variant="secondary">Coming Soon</Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center mb-6">
              <Car className="h-8 w-8 text-orange-600 dark:text-orange-400" />
            </div>

            <h2 className="text-2xl font-bold mb-2">TISAX</h2>
            <p className="text-lg text-muted-foreground mb-4">
              Trusted Information Security Assessment Exchange
            </p>

            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">What is TISAX?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                TISAX is a standard for information security in the automotive industry,
                developed by the German Association of the Automotive Industry (VDA).
                It enables companies to share assessment results across the supply chain.
              </p>

              <h3 className="font-semibold mb-2">Key Features (Coming)</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• VDA ISA catalog assessment (v5.1/v6)</li>
                <li>• Assessment Level 1, 2, 3 support</li>
                <li>• Prototype protection module</li>
                <li>• Data protection module</li>
                <li>• Cross-mapping to ISO 27001</li>
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

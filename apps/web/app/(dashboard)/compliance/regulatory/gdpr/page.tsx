"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Lock, ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";

export default function GDPRPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="GDPR Compliance">
        <Badge variant="secondary">Coming Soon</Badge>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-6">
              <Lock className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>

            <h2 className="text-2xl font-bold mb-2">GDPR</h2>
            <p className="text-lg text-muted-foreground mb-4">
              General Data Protection Regulation (EU 2016/679)
            </p>

            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">What is GDPR?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                The General Data Protection Regulation is the EU's data protection and privacy
                regulation. It applies to all organizations processing personal data of EU residents.
              </p>

              <h3 className="font-semibold mb-2">Key Areas</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Lawful basis for processing (Art. 6)</li>
                <li>• Data subject rights (Art. 12-23)</li>
                <li>• Data protection by design (Art. 25)</li>
                <li>• Data breach notification (Art. 33-34)</li>
                <li>• Data Protection Impact Assessment (Art. 35)</li>
                <li>• International transfers (Art. 44-49)</li>
              </ul>

              <h3 className="font-semibold mt-4 mb-2">Key Features (Coming)</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Processing activity register (Art. 30)</li>
                <li>• DPIA management</li>
                <li>• Data subject request tracking</li>
                <li>• Consent management</li>
                <li>• Breach notification workflow</li>
                <li>• Cross-mapping to ISO 27701</li>
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

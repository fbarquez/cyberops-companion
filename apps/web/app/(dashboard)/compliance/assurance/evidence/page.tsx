"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  FileText,
  ArrowLeft,
  Upload,
  Link as LinkIcon,
  CheckCircle,
  Clock,
  Filter,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

// This page provides a compliance-focused view of evidence management
// linking to the main evidence module with compliance context

const evidenceByFramework = [
  { framework: "ISO 27001", total: 93, linked: 89, coverage: 96 },
  { framework: "NIS2", total: 45, linked: 41, coverage: 91 },
  { framework: "DORA", total: 28, linked: 24, coverage: 86 },
  { framework: "BSI", total: 67, linked: 58, coverage: 87 },
];

const recentEvidence = [
  { id: "1", name: "Information Security Policy v3.2", type: "Policy", linkedTo: "ISO 27001 A.5.1", date: "2024-01-15" },
  { id: "2", name: "Penetration Test Report Q4", type: "Report", linkedTo: "DORA Art. 26", date: "2024-01-10" },
  { id: "3", name: "Access Control Procedure", type: "Procedure", linkedTo: "ISO 27001 A.9.1", date: "2024-01-08" },
  { id: "4", name: "Incident Response Plan", type: "Plan", linkedTo: "NIS2 Art. 21", date: "2024-01-05" },
];

export default function EvidencePage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="Evidence Management">
        <div className="flex gap-2">
          <Link href="/compliance/assurance">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <Link href="/evidence">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Full Module
            </Button>
          </Link>
        </div>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Evidence</p>
                  <p className="text-2xl font-bold">156</p>
                </div>
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Linked to Controls</p>
                  <p className="text-2xl font-bold text-green-600">142</p>
                </div>
                <LinkIcon className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Pending Review</p>
                  <p className="text-2xl font-bold text-yellow-600">14</p>
                </div>
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Coverage</p>
                  <p className="text-2xl font-bold">91%</p>
                </div>
                <CheckCircle className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Evidence by Framework */}
        <Card>
          <CardHeader>
            <CardTitle>Evidence Coverage by Framework</CardTitle>
            <CardDescription>
              How well are your controls covered with evidence?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {evidenceByFramework.map((fw) => (
              <div key={fw.framework} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{fw.framework}</span>
                  <span className="text-sm text-muted-foreground">
                    {fw.linked}/{fw.total} controls ({fw.coverage}%)
                  </span>
                </div>
                <Progress value={fw.coverage} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Evidence */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Evidence</CardTitle>
              <CardDescription>Recently uploaded or updated evidence</CardDescription>
            </div>
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Evidence
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentEvidence.map((evidence) => (
                <div
                  key={evidence.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{evidence.name}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline" className="text-xs">{evidence.type}</Badge>
                        <span>→</span>
                        <span>{evidence.linkedTo}</span>
                      </div>
                    </div>
                  </div>
                  <span className="text-sm text-muted-foreground">{evidence.date}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="flex gap-2">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filter by Framework
          </Button>
          <Button variant="outline">
            <LinkIcon className="h-4 w-4 mr-2" />
            Link Evidence to Control
          </Button>
          <Link href="/evidence">
            <Button>
              Open Full Evidence Manager
              <ExternalLink className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

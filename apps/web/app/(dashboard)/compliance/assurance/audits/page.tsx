"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  ClipboardCheck,
  ArrowLeft,
  Plus,
  CheckCircle,
  Clock,
  Calendar,
  AlertTriangle,
  FileText,
  ExternalLink,
  User,
} from "lucide-react";
import Link from "next/link";

const audits = [
  {
    id: "1",
    name: "ISO 27001 Surveillance Audit",
    type: "External",
    auditor: "TÜV Rheinland",
    status: "completed",
    date: "2024-01-08",
    findings: { major: 0, minor: 2, observations: 5 },
    framework: "ISO 27001",
  },
  {
    id: "2",
    name: "DORA Readiness Assessment",
    type: "Internal",
    auditor: "Internal Audit Team",
    status: "in_progress",
    date: "2024-01-15",
    findings: { major: 1, minor: 3, observations: 8 },
    framework: "DORA",
  },
  {
    id: "3",
    name: "NIS2 Gap Analysis",
    type: "External",
    auditor: "KPMG",
    status: "completed",
    date: "2023-12-20",
    findings: { major: 0, minor: 4, observations: 12 },
    framework: "NIS2",
  },
  {
    id: "4",
    name: "BSI IT-Grundschutz Check",
    type: "Internal",
    auditor: "Internal Audit Team",
    status: "planned",
    date: "2024-02-01",
    findings: { major: 0, minor: 0, observations: 0 },
    framework: "BSI",
  },
];

const openFindings = [
  { id: "F-001", title: "Missing MFA for admin accounts", severity: "Major", audit: "DORA Readiness", dueDate: "2024-01-30", status: "in_progress" },
  { id: "F-002", title: "Incomplete asset inventory", severity: "Minor", audit: "ISO 27001 Surveillance", dueDate: "2024-02-15", status: "open" },
  { id: "F-003", title: "Outdated security policies", severity: "Minor", audit: "ISO 27001 Surveillance", dueDate: "2024-02-28", status: "open" },
];

export default function AuditsPage() {
  const statusColors = {
    completed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
    in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
    planned: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100",
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="Audit Management">
        <div className="flex gap-2">
          <Link href="/compliance/assurance">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <Link href="/audit">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Audit Logs
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
                  <p className="text-sm text-muted-foreground">Total Audits</p>
                  <p className="text-2xl font-bold">8</p>
                </div>
                <ClipboardCheck className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold text-green-600">5</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">In Progress</p>
                  <p className="text-2xl font-bold text-blue-600">2</p>
                </div>
                <Clock className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Open Findings</p>
                  <p className="text-2xl font-bold text-yellow-600">3</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Audits List */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Audits</CardTitle>
              <CardDescription>Internal and external compliance audits</CardDescription>
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Plan Audit
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {audits.map((audit) => (
              <div key={audit.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <ClipboardCheck className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="font-medium">{audit.name}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <Badge variant="outline">{audit.framework}</Badge>
                      <span className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {audit.auditor}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {audit.date}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge className={statusColors[audit.status as keyof typeof statusColors]}>
                    {audit.status === "completed" && <CheckCircle className="h-3 w-3 mr-1" />}
                    {audit.status === "in_progress" && <Clock className="h-3 w-3 mr-1" />}
                    {audit.status === "planned" && <Calendar className="h-3 w-3 mr-1" />}
                    {audit.status.replace("_", " ")}
                  </Badge>
                  {audit.status !== "planned" && (
                    <div className="text-right text-xs text-muted-foreground">
                      <div>{audit.findings.major} major</div>
                      <div>{audit.findings.minor} minor</div>
                    </div>
                  )}
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Open Findings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Open Findings (CAPA)
            </CardTitle>
            <CardDescription>Corrective and preventive actions required</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {openFindings.map((finding) => (
                <div key={finding.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant={finding.severity === "Major" ? "destructive" : "secondary"}>
                      {finding.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">{finding.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {finding.audit} • Due: {finding.dueDate}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline">{finding.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

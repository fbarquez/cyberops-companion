"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  TestTube,
  ArrowLeft,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  Shield,
  Bug,
  ExternalLink,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";

const testTypes = [
  {
    id: "vuln-scan",
    name: "Vulnerability Scans",
    description: "Automated vulnerability assessments",
    frequency: "Weekly",
    lastRun: "2024-01-14",
    status: "passed",
    findings: 12,
    critical: 0,
  },
  {
    id: "pentest",
    name: "Penetration Tests",
    description: "Manual security testing by experts",
    frequency: "Quarterly",
    lastRun: "2024-01-10",
    status: "findings",
    findings: 5,
    critical: 1,
  },
  {
    id: "tlpt",
    name: "TLPT (Threat-Led Penetration Testing)",
    description: "Advanced testing required by DORA Art. 26",
    frequency: "Annually",
    lastRun: "2023-11-15",
    status: "passed",
    findings: 3,
    critical: 0,
  },
  {
    id: "redteam",
    name: "Red Team Exercises",
    description: "Adversary simulation exercises",
    frequency: "Annually",
    lastRun: "2023-09-20",
    status: "passed",
    findings: 8,
    critical: 0,
  },
];

const upcomingTests = [
  { name: "Q1 Penetration Test", type: "Pentest", date: "2024-02-15", scope: "External perimeter" },
  { name: "Monthly Vuln Scan", type: "Vuln Scan", date: "2024-01-21", scope: "All systems" },
  { name: "Social Engineering Test", type: "Phishing", date: "2024-02-01", scope: "All employees" },
];

export default function TestingPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="Security Testing">
        <div className="flex gap-2">
          <Link href="/compliance/assurance">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <Link href="/vulnerabilities">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Vulnerability Scanner
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
                  <p className="text-sm text-muted-foreground">Tests This Year</p>
                  <p className="text-2xl font-bold">24</p>
                </div>
                <TestTube className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Passed</p>
                  <p className="text-2xl font-bold text-green-600">18</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">With Findings</p>
                  <p className="text-2xl font-bold text-yellow-600">6</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Open Critical</p>
                  <p className="text-2xl font-bold text-red-600">1</p>
                </div>
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* DORA Compliance Note */}
        <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950 dark:to-purple-950 border-indigo-200">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
                <Shield className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h3 className="font-semibold text-indigo-900 dark:text-indigo-100">
                  DORA Art. 24-27: Digital Resilience Testing
                </h3>
                <p className="text-sm text-indigo-700 dark:text-indigo-300 mt-1">
                  Financial entities must establish testing programs including vulnerability assessments,
                  network security testing, and for significant entities, Threat-Led Penetration Testing (TLPT)
                  at least every 3 years.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Test Types */}
        <Card>
          <CardHeader>
            <CardTitle>Testing Programs</CardTitle>
            <CardDescription>Active security testing programs and their status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {testTypes.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${
                    test.status === "passed" ? "bg-green-100 dark:bg-green-900" :
                    test.status === "findings" ? "bg-yellow-100 dark:bg-yellow-900" :
                    "bg-gray-100 dark:bg-gray-900"
                  }`}>
                    <TestTube className={`h-5 w-5 ${
                      test.status === "passed" ? "text-green-600" :
                      test.status === "findings" ? "text-yellow-600" :
                      "text-gray-600"
                    }`} />
                  </div>
                  <div>
                    <p className="font-medium">{test.name}</p>
                    <p className="text-sm text-muted-foreground">{test.description}</p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {test.frequency}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Last: {test.lastRun}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      {test.critical > 0 ? (
                        <Badge variant="destructive">{test.critical} critical</Badge>
                      ) : (
                        <Badge variant="outline" className="text-green-600">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Passed
                        </Badge>
                      )}
                    </div>
                    {test.findings > 0 && (
                      <span className="text-xs text-muted-foreground">
                        {test.findings} total findings
                      </span>
                    )}
                  </div>
                  <Button variant="ghost" size="sm">
                    View Report
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Upcoming Tests */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Upcoming Tests</CardTitle>
              <CardDescription>Scheduled security testing activities</CardDescription>
            </div>
            <Button>
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Test
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingTests.map((test, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{test.name}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{test.type}</Badge>
                        <span>{test.scope}</span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary">{test.date}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

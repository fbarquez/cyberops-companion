"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  ArrowLeft,
  Plus,
  CheckCircle,
  Clock,
  Calendar,
  FileText,
  ExternalLink,
  Send,
  AlertCircle,
  XCircle,
  Timer,
  Building,
} from "lucide-react";
import Link from "next/link";

const recentIncidents = [
  {
    id: "INC-2024-001",
    title: "Phishing Campaign Detected",
    severity: "High",
    status: "resolved",
    detected: "2024-01-14 09:30",
    resolved: "2024-01-14 14:45",
    reportedToAuthority: true,
  },
  {
    id: "INC-2024-002",
    title: "Unauthorized Access Attempt",
    severity: "Medium",
    status: "investigating",
    detected: "2024-01-15 11:20",
    resolved: null,
    reportedToAuthority: false,
  },
  {
    id: "INC-2023-047",
    title: "DDoS Attack on Customer Portal",
    severity: "Critical",
    status: "resolved",
    detected: "2023-12-28 03:15",
    resolved: "2023-12-28 05:30",
    reportedToAuthority: true,
  },
];

const regulatoryReports = [
  { id: "1", incident: "INC-2024-001", authority: "BSI", type: "NIS2 Notification", status: "submitted", date: "2024-01-14" },
  { id: "2", incident: "INC-2023-047", authority: "BaFin", type: "DORA Major Incident", status: "final", date: "2023-12-28" },
  { id: "3", incident: "INC-2023-047", authority: "BSI", type: "KRITIS Report", status: "final", date: "2023-12-28" },
];

const lessonsLearned = [
  { incident: "INC-2023-047", finding: "Need faster DDoS mitigation activation", action: "Automated DDoS detection & response", status: "implemented" },
  { incident: "INC-2024-001", finding: "Email filtering gaps for new phishing techniques", action: "Update email security rules", status: "in_progress" },
];

export default function IncidentsPage() {
  const severityColors = {
    Critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
    High: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100",
    Medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
    Low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="Incident Management">
        <div className="flex gap-2">
          <Link href="/compliance/assurance">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <Link href="/incidents">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Full Incidents Module
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
                  <p className="text-sm text-muted-foreground">Open Incidents</p>
                  <p className="text-2xl font-bold text-yellow-600">3</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Resolved (YTD)</p>
                  <p className="text-2xl font-bold text-green-600">47</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Resolution</p>
                  <p className="text-2xl font-bold">4.2h</p>
                </div>
                <Timer className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Reported to Authorities</p>
                  <p className="text-2xl font-bold">5</p>
                </div>
                <Building className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Regulatory Note */}
        <Card className="bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 border-red-200">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  Incident Reporting Requirements
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  <strong>NIS2:</strong> Early warning within 24h, full notification within 72h, final report within 1 month.<br/>
                  <strong>DORA:</strong> Initial notification same day, intermediate within 72h, final within 1 month for major incidents.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Incidents */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Security Incidents</CardTitle>
              <CardDescription>Latest security incidents and their status</CardDescription>
            </div>
            <Link href="/incidents">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Report Incident
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentIncidents.map((incident) => (
              <div key={incident.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${
                    incident.status === "resolved" ? "bg-green-100 dark:bg-green-900" :
                    "bg-yellow-100 dark:bg-yellow-900"
                  }`}>
                    {incident.status === "resolved" ? (
                      <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-muted-foreground">{incident.id}</span>
                      <Badge className={severityColors[incident.severity as keyof typeof severityColors]}>
                        {incident.severity}
                      </Badge>
                    </div>
                    <p className="font-medium">{incident.title}</p>
                    <p className="text-xs text-muted-foreground">
                      Detected: {incident.detected}
                      {incident.resolved && ` • Resolved: ${incident.resolved}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {incident.reportedToAuthority && (
                    <Badge variant="outline" className="text-blue-600">
                      <Send className="h-3 w-3 mr-1" />
                      Reported
                    </Badge>
                  )}
                  <Button variant="ghost" size="sm">View</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Regulatory Reports */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5" />
              Regulatory Notifications
            </CardTitle>
            <CardDescription>Incident reports submitted to authorities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {regulatoryReports.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Building className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{report.type}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{report.incident}</span>
                        <span>→</span>
                        <Badge variant="outline">{report.authority}</Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">{report.date}</span>
                    <Badge variant={report.status === "final" ? "default" : "secondary"}>
                      {report.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Lessons Learned */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Lessons Learned
            </CardTitle>
            <CardDescription>Improvements from incident post-mortems</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {lessonsLearned.map((lesson, index) => (
                <div key={index} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm text-muted-foreground">{lesson.incident}</span>
                    <Badge variant={lesson.status === "implemented" ? "default" : "secondary"}>
                      {lesson.status === "implemented" && <CheckCircle className="h-3 w-3 mr-1" />}
                      {lesson.status === "in_progress" && <Clock className="h-3 w-3 mr-1" />}
                      {lesson.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <p className="text-sm"><strong>Finding:</strong> {lesson.finding}</p>
                  <p className="text-sm text-muted-foreground"><strong>Action:</strong> {lesson.action}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

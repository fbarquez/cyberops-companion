"use client";

import { Header } from "@/components/shared/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  RefreshCw,
  ArrowLeft,
  Plus,
  CheckCircle,
  Clock,
  Calendar,
  AlertTriangle,
  FileText,
  ExternalLink,
  Play,
  Target,
  Timer,
} from "lucide-react";
import Link from "next/link";

const bcPlans = [
  { id: "1", name: "IT Disaster Recovery Plan", scope: "IT Systems", rto: "4h", rpo: "1h", lastTested: "2024-01-10", status: "current" },
  { id: "2", name: "Data Center Failover", scope: "Primary DC", rto: "2h", rpo: "15min", lastTested: "2023-12-15", status: "current" },
  { id: "3", name: "Ransomware Response Plan", scope: "All Systems", rto: "24h", rpo: "4h", lastTested: "2023-11-20", status: "current" },
  { id: "4", name: "Payment Systems Recovery", scope: "Payment Processing", rto: "1h", rpo: "0", lastTested: "2024-01-05", status: "current" },
];

const criticalProcesses = [
  { name: "Payment Processing", rto: "1h", rpo: "0", impact: "Critical", status: "protected" },
  { name: "Customer Portal", rto: "4h", rpo: "1h", impact: "High", status: "protected" },
  { name: "Core Banking", rto: "2h", rpo: "15min", impact: "Critical", status: "protected" },
  { name: "Trading Platform", rto: "30min", rpo: "0", impact: "Critical", status: "protected" },
];

const exercises = [
  { id: "1", name: "Tabletop Exercise: Ransomware", type: "Tabletop", date: "2024-01-15", status: "completed", participants: 12 },
  { id: "2", name: "DR Failover Test", type: "Technical", date: "2024-01-10", status: "completed", participants: 8 },
  { id: "3", name: "Crisis Communication Drill", type: "Functional", date: "2024-02-01", status: "planned", participants: 15 },
];

export default function BCMPage() {
  return (
    <div className="flex flex-col h-full">
      <Header title="BCM & Resilience">
        <div className="flex gap-2">
          <Link href="/compliance/assurance">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <Link href="/bcm">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Full BCM Module
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
                  <p className="text-sm text-muted-foreground">BC Plans</p>
                  <p className="text-2xl font-bold">12</p>
                </div>
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Critical Processes</p>
                  <p className="text-2xl font-bold">8</p>
                </div>
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Exercises YTD</p>
                  <p className="text-2xl font-bold text-green-600">4</p>
                </div>
                <Play className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg RTO</p>
                  <p className="text-2xl font-bold">4.2h</p>
                </div>
                <Timer className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* DORA Note */}
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 border-green-200">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <RefreshCw className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100">
                  DORA Art. 11-12: Response & Recovery
                </h3>
                <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                  Financial entities must have comprehensive ICT business continuity policies,
                  response and recovery plans, and conduct regular testing including
                  crisis communication procedures.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Critical Processes */}
        <Card>
          <CardHeader>
            <CardTitle>Critical Business Processes</CardTitle>
            <CardDescription>Business Impact Analysis (BIA) results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {criticalProcesses.map((process, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant={process.impact === "Critical" ? "destructive" : "secondary"}>
                      {process.impact}
                    </Badge>
                    <span className="font-medium">{process.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right text-sm">
                      <div className="text-muted-foreground">RTO: <span className="font-medium text-foreground">{process.rto}</span></div>
                      <div className="text-muted-foreground">RPO: <span className="font-medium text-foreground">{process.rpo}</span></div>
                    </div>
                    <Badge variant="outline" className="text-green-600">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      {process.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* BC Plans */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Business Continuity Plans</CardTitle>
              <CardDescription>Recovery plans for critical systems</CardDescription>
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Plan
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {bcPlans.map((plan) => (
              <div key={plan.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{plan.name}</p>
                    <p className="text-xs text-muted-foreground">{plan.scope}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right text-xs text-muted-foreground">
                    <div>RTO: {plan.rto} | RPO: {plan.rpo}</div>
                    <div>Last tested: {plan.lastTested}</div>
                  </div>
                  <Button variant="ghost" size="sm">View</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Exercises */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Resilience Exercises</CardTitle>
              <CardDescription>Testing and validation activities</CardDescription>
            </div>
            <Button>
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Exercise
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {exercises.map((exercise) => (
                <div key={exercise.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Play className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{exercise.name}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{exercise.type}</Badge>
                        <span>{exercise.participants} participants</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">{exercise.date}</span>
                    <Badge variant={exercise.status === "completed" ? "default" : "secondary"}>
                      {exercise.status === "completed" && <CheckCircle className="h-3 w-3 mr-1" />}
                      {exercise.status === "planned" && <Calendar className="h-3 w-3 mr-1" />}
                      {exercise.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

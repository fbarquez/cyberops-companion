"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ShieldQuestion,
  TrendingUp,
  Download,
  FileText,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";

interface BSIDashboardProps {
  schutzbedarf: string;
}

interface CategoryScore {
  kategorie: string;
  name_de: string;
  total: number;
  compliant: number;
  partial: number;
  gap: number;
  not_applicable: number;
  not_evaluated: number;
  score_percent: number;
}

interface ComplianceOverview {
  overall_score_percent: number;
  total: number;
  compliant: number;
  partial: number;
  gap: number;
  not_applicable: number;
  not_evaluated: number;
  by_kategorie: CategoryScore[];
}

const KATEGORIE_NAMES: Record<string, string> = {
  ISMS: "Sicherheitsmanagement",
  ORP: "Organisation & Personal",
  CON: "Konzeption & Vorgehensweise",
  OPS: "Betrieb",
  DER: "Detektion & Reaktion",
  APP: "Anwendungen",
  SYS: "IT-Systeme",
  NET: "Netze & Kommunikation",
  INF: "Infrastruktur",
  IND: "Industrielle IT",
};

export function BSIDashboard({ schutzbedarf }: BSIDashboardProps) {
  const { token } = useAuthStore();

  const { data: overview, isLoading } = useQuery<ComplianceOverview>({
    queryKey: ["bsi-compliance-overview", schutzbedarf],
    queryFn: async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/v1/bsi/grundschutz/compliance/overview?schutzbedarf=${schutzbedarf}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.json();
    },
    enabled: !!token,
  });

  const [isExportingPdf, setIsExportingPdf] = React.useState(false);

  const exportReport = async (format: "json" | "csv") => {
    if (!overview) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === "json") {
      content = JSON.stringify(overview, null, 2);
      filename = `bsi-compliance-report-${schutzbedarf}-${new Date().toISOString().split("T")[0]}.json`;
      mimeType = "application/json";
    } else {
      // CSV export
      const headers = ["Kategorie", "Name", "Total", "Compliant", "Partial", "Gap", "N/A", "Open", "Score %"];
      const rows = overview.by_kategorie.map((k) => [
        k.kategorie,
        KATEGORIE_NAMES[k.kategorie] || k.name_de,
        k.total,
        k.compliant,
        k.partial,
        k.gap,
        k.not_applicable,
        k.not_evaluated,
        k.score_percent,
      ]);
      content = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      filename = `bsi-compliance-report-${schutzbedarf}-${new Date().toISOString().split("T")[0]}.csv`;
      mimeType = "text/csv";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPdfReport = async () => {
    setIsExportingPdf(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/v1/reports/bsi/compliance?schutzbedarf=${schutzbedarf}&classification=Vertraulich`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate PDF");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `BSI_Compliance_Report_${schutzbedarf}_${new Date().toISOString().split("T")[0]}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("PDF export failed:", error);
      alert("PDF export failed. Please ensure LaTeX is installed on the server.");
    } finally {
      setIsExportingPdf(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-muted rounded-lg" />
        ))}
      </div>
    );
  }

  if (!overview) return null;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    if (score >= 40) return "text-orange-600";
    return "text-red-600";
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    if (score >= 40) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
            <TrendingUp className={`h-4 w-4 ${getScoreColor(overview.overall_score_percent)}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${getScoreColor(overview.overall_score_percent)}`}>
              {overview.overall_score_percent}%
            </div>
            <Progress
              value={overview.overall_score_percent}
              className="mt-2 h-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <ShieldCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{overview.compliant}</div>
            <p className="text-xs text-muted-foreground">
              {((overview.compliant / overview.total) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Partial</CardTitle>
            <ShieldAlert className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{overview.partial}</div>
            <p className="text-xs text-muted-foreground">
              {((overview.partial / overview.total) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gaps</CardTitle>
            <ShieldX className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{overview.gap}</div>
            <p className="text-xs text-muted-foreground">
              {((overview.gap / overview.total) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Not Evaluated</CardTitle>
            <ShieldQuestion className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-500">{overview.not_evaluated}</div>
            <p className="text-xs text-muted-foreground">
              {((overview.not_evaluated / overview.total) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Export Buttons */}
      <div className="flex gap-2">
        <Button
          variant="default"
          size="sm"
          onClick={exportPdfReport}
          disabled={isExportingPdf}
        >
          {isExportingPdf ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <FileText className="h-4 w-4 mr-2" />
          )}
          Export PDF (DIN 5008)
        </Button>
        <Button variant="outline" size="sm" onClick={() => exportReport("csv")}>
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
        <Button variant="outline" size="sm" onClick={() => exportReport("json")}>
          <FileText className="h-4 w-4 mr-2" />
          Export JSON
        </Button>
      </div>

      {/* Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance by Category</CardTitle>
          <CardDescription>
            Breakdown of compliance status across all BSI IT-Grundschutz categories
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {overview.by_kategorie?.map((kategorie) => (
              <div key={kategorie.kategorie} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono">
                      {kategorie.kategorie}
                    </Badge>
                    <span className="text-sm font-medium">
                      {KATEGORIE_NAMES[kategorie.kategorie] || kategorie.name_de}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-muted-foreground">
                      {kategorie.compliant + kategorie.partial}/{kategorie.total - kategorie.not_applicable}
                    </span>
                    <span className={`font-bold ${getScoreColor(kategorie.score_percent)}`}>
                      {kategorie.score_percent}%
                    </span>
                  </div>
                </div>
                <div className="flex h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="bg-green-500 transition-all"
                    style={{
                      width: `${(kategorie.compliant / kategorie.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-yellow-500 transition-all"
                    style={{
                      width: `${(kategorie.partial / kategorie.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500 transition-all"
                    style={{
                      width: `${(kategorie.gap / kategorie.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-gray-300 transition-all"
                    style={{
                      width: `${(kategorie.not_evaluated / kategorie.total) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    {kategorie.compliant} Compliant
                  </span>
                  <span className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-yellow-500" />
                    {kategorie.partial} Partial
                  </span>
                  <span className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                    {kategorie.gap} Gap
                  </span>
                  <span className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-gray-300" />
                    {kategorie.not_evaluated} Open
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Schutzbedarf: {schutzbedarf.charAt(0).toUpperCase() + schutzbedarf.slice(1)}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Basis</span>
              <p className="text-muted-foreground text-xs">
                Minimum requirements for basic protection
              </p>
            </div>
            <div>
              <span className="font-medium">Standard</span>
              <p className="text-muted-foreground text-xs">
                Normal protection level for typical business data
              </p>
            </div>
            <div>
              <span className="font-medium">Hoch</span>
              <p className="text-muted-foreground text-xs">
                High protection for sensitive or critical data
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  FileText,
  Download,
  FileJson,
  FileCode,
  CheckCircle,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { cn } from "@/lib/utils";

interface ExportOption {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  formats: string[];
}

const exportOptions: ExportOption[] = [
  {
    id: "full_report",
    name: "Full Incident Report",
    description: "Complete incident documentation including all phases, evidence, and decisions",
    icon: FileText,
    formats: ["pdf", "markdown", "docx"],
  },
  {
    id: "executive_summary",
    name: "Executive Summary",
    description: "High-level overview for management and stakeholders",
    icon: FileText,
    formats: ["pdf", "markdown"],
  },
  {
    id: "evidence_chain",
    name: "Evidence Chain",
    description: "Forensic evidence log with hash verification",
    icon: FileJson,
    formats: ["json", "markdown", "csv"],
  },
  {
    id: "timeline",
    name: "Incident Timeline",
    description: "Chronological view of all incident events",
    icon: FileCode,
    formats: ["json", "csv"],
  },
  {
    id: "compliance_report",
    name: "Compliance Report",
    description: "Framework compliance validation results",
    icon: FileText,
    formats: ["pdf", "json"],
  },
];

export default function ExportPage() {
  const params = useParams();
  const incidentId = params.id as string;
  const { t } = useTranslations();
  const [selectedExport, setSelectedExport] = useState<string>("full_report");
  const [selectedFormat, setSelectedFormat] = useState<string>("pdf");
  const [includeHashes, setIncludeHashes] = useState(true);
  const [includeRawData, setIncludeRawData] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const currentOption = exportOptions.find((o) => o.id === selectedExport);

  const handleExport = async () => {
    setIsExporting(true);
    // Simulate export
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsExporting(false);
    // In real implementation, would trigger download
    alert("Export completed! Download would start here.");
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={t("incidents.export")} backHref={`/incidents/${incidentId}`} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Export Type Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Export Type</CardTitle>
            <CardDescription>
              Select the type of export you want to generate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {exportOptions.map((option) => (
                <ExportOptionCard
                  key={option.id}
                  option={option}
                  isSelected={selectedExport === option.id}
                  onSelect={() => {
                    setSelectedExport(option.id);
                    setSelectedFormat(option.formats[0]);
                  }}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Format Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Output Format</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {currentOption?.formats.map((format) => (
                <Button
                  key={format}
                  variant={selectedFormat === format ? "default" : "outline"}
                  onClick={() => setSelectedFormat(format)}
                >
                  .{format.toUpperCase()}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Options */}
        <Card>
          <CardHeader>
            <CardTitle>Export Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Checkbox
                id="includeHashes"
                checked={includeHashes}
                onCheckedChange={(checked) => setIncludeHashes(!!checked)}
              />
              <Label htmlFor="includeHashes" className="cursor-pointer">
                Include cryptographic hashes for evidence verification
              </Label>
            </div>

            <div className="flex items-center gap-3">
              <Checkbox
                id="includeRawData"
                checked={includeRawData}
                onCheckedChange={(checked) => setIncludeRawData(!!checked)}
              />
              <Label htmlFor="includeRawData" className="cursor-pointer">
                Include raw JSON data (for technical analysis)
              </Label>
            </div>
          </CardContent>
        </Card>

        {/* Export Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Export Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Export Type:</span>
                <span className="font-medium">{currentOption?.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Format:</span>
                <Badge>.{selectedFormat.toUpperCase()}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Include Hashes:</span>
                <span>{includeHashes ? "Yes" : "No"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Include Raw Data:</span>
                <span>{includeRawData ? "Yes" : "No"}</span>
              </div>
            </div>

            <Button
              className="w-full mt-4"
              onClick={handleExport}
              disabled={isExporting}
            >
              {isExporting ? (
                <>
                  <span className="animate-spin mr-2">&#8987;</span>
                  Generating Export...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Generate & Download
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Recent Exports */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Exports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <RecentExportItem
                name="Full Incident Report"
                format="PDF"
                date="2024-01-15 14:30"
                size="2.4 MB"
              />
              <RecentExportItem
                name="Evidence Chain"
                format="JSON"
                date="2024-01-15 10:15"
                size="156 KB"
              />
              <RecentExportItem
                name="Executive Summary"
                format="Markdown"
                date="2024-01-14 16:45"
                size="45 KB"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ExportOptionCard({
  option,
  isSelected,
  onSelect,
}: {
  option: ExportOption;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const Icon = option.icon;

  return (
    <Card
      className={cn(
        "cursor-pointer transition-colors",
        isSelected && "border-primary bg-primary/5"
      )}
      onClick={onSelect}
    >
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <Icon className="h-8 w-8 text-primary flex-shrink-0" />
          <div className="space-y-1 flex-1">
            <div className="flex items-center justify-between">
              <p className="font-medium">{option.name}</p>
              {isSelected && (
                <CheckCircle className="h-5 w-5 text-primary" />
              )}
            </div>
            <p className="text-sm text-muted-foreground">{option.description}</p>
            <div className="flex gap-1 mt-2">
              {option.formats.map((f) => (
                <Badge key={f} variant="outline" className="text-xs">
                  .{f}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RecentExportItem({
  name,
  format,
  date,
  size,
}: {
  name: string;
  format: string;
  date: string;
  size: string;
}) {
  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
      <div className="flex items-center gap-3">
        <FileText className="h-5 w-5 text-muted-foreground" />
        <div>
          <p className="font-medium">{name}</p>
          <p className="text-sm text-muted-foreground">
            {format} - {date}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{size}</span>
        <Button variant="ghost" size="icon">
          <Download className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// Simple checkbox for this page
function Checkbox({
  id,
  checked,
  onCheckedChange,
}: {
  id: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      className="h-4 w-4 rounded border-input accent-primary"
    />
  );
}

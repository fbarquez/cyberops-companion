"use client";

import { useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Shield,
  Check,
  X,
  AlertCircle,
  MinusCircle,
  HelpCircle,
  Upload,
  Paperclip,
  Calendar,
  FileText,
  Loader2,
  Trash2,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { bsiGrundschutzAPI, BSIAnforderung } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const TYP_LABELS: Record<string, { label: string; color: string; description: string }> = {
  MUSS: {
    label: "MUSS",
    color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-300",
    description: "Pflichtanforderung (Basis-Absicherung)",
  },
  SOLLTE: {
    label: "SOLLTE",
    color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 border-yellow-300",
    description: "Empfohlene Anforderung (Standard-Absicherung)",
  },
  KANN: {
    label: "KANN",
    color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-300",
    description: "Optionale Anforderung (Erhohter Schutzbedarf)",
  },
};

const STATUS_OPTIONS = [
  { value: "not_evaluated", label: "Nicht bewertet", icon: HelpCircle, color: "text-gray-500" },
  { value: "compliant", label: "Erfuellt", icon: Check, color: "text-green-500" },
  { value: "partial", label: "Teilweise", icon: MinusCircle, color: "text-yellow-500" },
  { value: "gap", label: "Luecke", icon: X, color: "text-red-500" },
  { value: "not_applicable", label: "N/A", icon: AlertCircle, color: "text-gray-400" },
];

export default function BausteinDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const bausteinId = decodeURIComponent(params.id as string);

  const [schutzbedarf, setSchutzbedarf] = useState<string>("standard");
  const [selectedAnforderung, setSelectedAnforderung] = useState<BSIAnforderung | null>(null);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<string>("not_evaluated");
  const [notes, setNotes] = useState<string>("");
  const [dueDate, setDueDate] = useState<string>("");
  const [remediationPlan, setRemediationPlan] = useState<string>("");
  const [evidenceFiles, setEvidenceFiles] = useState<File[]>([]);
  const [isUploadingEvidence, setIsUploadingEvidence] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Bulk update state
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [bulkStatus, setBulkStatus] = useState<string>("not_evaluated");

  // Fetch Baustein with Anforderungen
  const { data, isLoading, error } = useQuery({
    queryKey: ["bsi-baustein", bausteinId, schutzbedarf],
    queryFn: () => bsiGrundschutzAPI.getBaustein(token!, bausteinId, schutzbedarf),
    enabled: !!token && !!bausteinId,
  });

  // Fetch compliance score
  const { data: scoreData, refetch: refetchScore } = useQuery({
    queryKey: ["bsi-baustein-score", bausteinId, schutzbedarf],
    queryFn: () =>
      bsiGrundschutzAPI.getBausteinScore(token!, bausteinId, { schutzbedarf }),
    enabled: !!token && !!bausteinId,
  });

  // Update compliance status mutation
  const updateStatusMutation = useMutation({
    mutationFn: (data: {
      anforderung_id: string;
      status: string;
      notes?: string;
      due_date?: string;
      remediation_plan?: string;
    }) => bsiGrundschutzAPI.updateComplianceStatus(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bsi-baustein-score", bausteinId] });
      toast.success("Status aktualisiert");
      setStatusDialogOpen(false);
      setSelectedAnforderung(null);
      setEvidenceFiles([]);
      setDueDate("");
      setRemediationPlan("");
      refetchScore();
    },
    onError: () => {
      toast.error("Fehler beim Aktualisieren");
    },
  });

  // Bulk update mutation
  const bulkUpdateMutation = useMutation({
    mutationFn: async (data: { anforderung_ids: string[]; status: string }) => {
      // Update each item sequentially
      for (const id of data.anforderung_ids) {
        await bsiGrundschutzAPI.updateComplianceStatus(token!, {
          anforderung_id: id,
          status: data.status,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bsi-baustein-score", bausteinId] });
      toast.success(`${selectedItems.size} Anforderungen aktualisiert`);
      setBulkDialogOpen(false);
      setSelectedItems(new Set());
      refetchScore();
    },
    onError: () => {
      toast.error("Fehler beim Bulk-Update");
    },
  });

  if (isLoading) return <PageLoading />;

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <h2 className="text-xl font-semibold mb-2">Baustein nicht gefunden</h2>
        <Button onClick={() => router.back()}>Zurueck</Button>
      </div>
    );
  }

  const { baustein, anforderungen, anforderungen_count } = data;

  // Group Anforderungen by type
  const anforderungenByTyp = {
    MUSS: anforderungen.filter((a) => a.typ === "MUSS"),
    SOLLTE: anforderungen.filter((a) => a.typ === "SOLLTE"),
    KANN: anforderungen.filter((a) => a.typ === "KANN"),
  };

  const handleStatusUpdate = async () => {
    if (!selectedAnforderung) return;

    // First handle evidence upload if there are files
    if (evidenceFiles.length > 0) {
      setIsUploadingEvidence(true);
      // Note: In a real implementation, you would upload files to the server here
      // For now, we'll just simulate the upload
      await new Promise((resolve) => setTimeout(resolve, 500));
      setIsUploadingEvidence(false);
      toast.success(`${evidenceFiles.length} Evidenz-Datei(en) hochgeladen`);
    }

    updateStatusMutation.mutate({
      anforderung_id: selectedAnforderung.anforderung_id,
      status: newStatus,
      notes: notes || undefined,
      due_date: dueDate || undefined,
      remediation_plan: remediationPlan || undefined,
    });
  };

  const handleBulkUpdate = () => {
    if (selectedItems.size === 0) return;
    bulkUpdateMutation.mutate({
      anforderung_ids: Array.from(selectedItems),
      status: bulkStatus,
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      setEvidenceFiles((prev) => [...prev, ...Array.from(files)]);
    }
  };

  const removeFile = (index: number) => {
    setEvidenceFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleItemSelection = (id: string) => {
    setSelectedItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleSelectAll = (anforderungen: BSIAnforderung[]) => {
    if (selectedItems.size === anforderungen.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(anforderungen.map((a) => a.anforderung_id)));
    }
  };

  const openStatusDialog = (anforderung: BSIAnforderung) => {
    setSelectedAnforderung(anforderung);
    setNewStatus("not_evaluated");
    setNotes("");
    setDueDate("");
    setRemediationPlan("");
    setEvidenceFiles([]);
    setStatusDialogOpen(true);
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={`${baustein.baustein_id} - ${baustein.titel}`}
        backHref="/compliance/frameworks/bsi"
      >
        <Select value={schutzbedarf} onValueChange={setSchutzbedarf}>
          <SelectTrigger className="w-40">
            <Shield className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="basis">Basis</SelectItem>
            <SelectItem value="standard">Standard</SelectItem>
            <SelectItem value="hoch">Hoch</SelectItem>
          </SelectContent>
        </Select>
      </Header>

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {/* Overview Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Anforderungen</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{anforderungen_count.total}</div>
              <div className="text-xs text-muted-foreground mt-1">
                {anforderungen_count.muss} MUSS, {anforderungen_count.sollte} SOLLTE,{" "}
                {anforderungen_count.kann} KANN
              </div>
            </CardContent>
          </Card>

          {scoreData && (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{scoreData.score_percent}%</div>
                  <Progress value={scoreData.score_percent} className="h-2 mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-green-600">Erfuellt</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{scoreData.compliant}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    + {scoreData.partial} teilweise
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-red-600">Luecken</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{scoreData.gap}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {scoreData.not_evaluated} nicht bewertet
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Description */}
        {baustein.beschreibung && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Beschreibung</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{baustein.beschreibung}</p>
            </CardContent>
          </Card>
        )}

        {/* Anforderungen Tabs */}
        <Tabs defaultValue="all" className="space-y-4">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="all">
                Alle ({anforderungen.length})
              </TabsTrigger>
              <TabsTrigger value="MUSS" className="text-red-600">
                MUSS ({anforderungenByTyp.MUSS.length})
              </TabsTrigger>
              <TabsTrigger value="SOLLTE" className="text-yellow-600">
                SOLLTE ({anforderungenByTyp.SOLLTE.length})
              </TabsTrigger>
              <TabsTrigger value="KANN" className="text-blue-600">
                KANN ({anforderungenByTyp.KANN.length})
              </TabsTrigger>
            </TabsList>

            {/* Bulk Actions */}
            {selectedItems.size > 0 && (
              <div className="flex items-center gap-2">
                <Badge variant="secondary">
                  {selectedItems.size} ausgewaehlt
                </Badge>
                <Button
                  size="sm"
                  onClick={() => setBulkDialogOpen(true)}
                >
                  Status aktualisieren
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedItems(new Set())}
                >
                  Auswahl aufheben
                </Button>
              </div>
            )}
          </div>

          <TabsContent value="all">
            <AnforderungenList
              anforderungen={anforderungen}
              onStatusClick={openStatusDialog}
              selectedItems={selectedItems}
              onToggleSelection={toggleItemSelection}
              onSelectAll={() => toggleSelectAll(anforderungen)}
            />
          </TabsContent>

          {["MUSS", "SOLLTE", "KANN"].map((typ) => (
            <TabsContent key={typ} value={typ}>
              <AnforderungenList
                anforderungen={anforderungenByTyp[typ as keyof typeof anforderungenByTyp]}
                onStatusClick={openStatusDialog}
                selectedItems={selectedItems}
                onToggleSelection={toggleItemSelection}
                onSelectAll={() => toggleSelectAll(anforderungenByTyp[typ as keyof typeof anforderungenByTyp])}
              />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Status Update Dialog */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Compliance Status aktualisieren</DialogTitle>
            <DialogDescription>
              {selectedAnforderung?.anforderung_id} - {selectedAnforderung?.titel}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      <div className="flex items-center gap-2">
                        <opt.icon className={cn("h-4 w-4", opt.color)} />
                        {opt.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Notizen</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optionale Anmerkungen..."
                rows={3}
              />
            </div>

            {/* Remediation section - shown for gaps and partial */}
            {(newStatus === "gap" || newStatus === "partial") && (
              <>
                <div className="space-y-2">
                  <Label>Faelligkeitsdatum</Label>
                  <Input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Massnahmenplan</Label>
                  <Textarea
                    value={remediationPlan}
                    onChange={(e) => setRemediationPlan(e.target.value)}
                    placeholder="Beschreiben Sie die geplanten Massnahmen zur Behebung..."
                    rows={3}
                  />
                </div>
              </>
            )}

            {/* Evidence upload section */}
            <div className="space-y-2">
              <Label>Evidenz hochladen</Label>
              <div className="border-2 border-dashed rounded-lg p-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                  multiple
                  accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.xlsx,.xls"
                />
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="h-4 w-4 mr-2" />
                    Dateien auswaehlen
                  </Button>
                  <p className="text-xs text-muted-foreground">
                    PDF, Word, Excel, Bilder (max. 10MB)
                  </p>
                </div>
              </div>

              {evidenceFiles.length > 0 && (
                <div className="space-y-2 mt-2">
                  {evidenceFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-muted rounded"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm truncate max-w-[200px]">
                          {file.name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleStatusUpdate}
              disabled={updateStatusMutation.isPending || isUploadingEvidence}
            >
              {updateStatusMutation.isPending || isUploadingEvidence ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Speichere...
                </>
              ) : (
                "Speichern"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Update Dialog */}
      <Dialog open={bulkDialogOpen} onOpenChange={setBulkDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sammelaktualisierung</DialogTitle>
            <DialogDescription>
              {selectedItems.size} Anforderungen werden aktualisiert
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Neuer Status fuer alle</Label>
              <Select value={bulkStatus} onValueChange={setBulkStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      <div className="flex items-center gap-2">
                        <opt.icon className={cn("h-4 w-4", opt.color)} />
                        {opt.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleBulkUpdate}
              disabled={bulkUpdateMutation.isPending}
            >
              {bulkUpdateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Aktualisiere...
                </>
              ) : (
                `${selectedItems.size} aktualisieren`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AnforderungenList({
  anforderungen,
  onStatusClick,
  selectedItems,
  onToggleSelection,
  onSelectAll,
}: {
  anforderungen: BSIAnforderung[];
  onStatusClick: (a: BSIAnforderung) => void;
  selectedItems: Set<string>;
  onToggleSelection: (id: string) => void;
  onSelectAll: () => void;
}) {
  if (anforderungen.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        Keine Anforderungen in dieser Kategorie.
      </div>
    );
  }

  const allSelected = anforderungen.every((a) => selectedItems.has(a.anforderung_id));
  const someSelected = anforderungen.some((a) => selectedItems.has(a.anforderung_id));

  return (
    <div className="space-y-2">
      {/* Select all header */}
      <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-lg">
        <Checkbox
          checked={allSelected}
          onCheckedChange={onSelectAll}
          className="data-[state=indeterminate]:bg-primary"
          {...(someSelected && !allSelected ? { "data-state": "indeterminate" } : {})}
        />
        <span className="text-sm text-muted-foreground">
          Alle auswaehlen ({anforderungen.length})
        </span>
      </div>

      <Accordion type="multiple" className="space-y-2">
        {anforderungen.map((anf) => (
          <AccordionItem
            key={anf.id}
            value={anf.id}
            className="border rounded-lg px-4"
          >
            <div className="flex items-center gap-2">
              <Checkbox
                checked={selectedItems.has(anf.anforderung_id)}
                onCheckedChange={() => onToggleSelection(anf.anforderung_id)}
                onClick={(e) => e.stopPropagation()}
                className="shrink-0"
              />
              <AccordionTrigger className="hover:no-underline flex-1">
                <div className="flex items-center gap-3 text-left">
                  <Badge
                    variant="outline"
                    className={cn("shrink-0", TYP_LABELS[anf.typ]?.color)}
                  >
                    {anf.typ}
                  </Badge>
                  <div>
                    <div className="font-medium text-sm">{anf.anforderung_id}</div>
                    <div className="text-sm text-muted-foreground line-clamp-1">
                      {anf.titel}
                    </div>
                  </div>
                </div>
              </AccordionTrigger>
            </div>
            <AccordionContent className="pt-2 pl-8">
              <div className="space-y-4">
                {anf.beschreibung && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">Beschreibung</h4>
                    <p className="text-sm text-muted-foreground">{anf.beschreibung}</p>
                  </div>
                )}

                {anf.umsetzungshinweise && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">Umsetzungshinweise</h4>
                    <p className="text-sm text-muted-foreground">
                      {anf.umsetzungshinweise}
                    </p>
                  </div>
                )}

                {anf.cross_references && Object.keys(anf.cross_references).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">Querverweise</h4>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(anf.cross_references).map(([framework, refs]) =>
                        (refs as string[]).map((ref) => (
                          <Badge key={`${framework}-${ref}`} variant="secondary" className="text-xs">
                            {framework}: {ref}
                          </Badge>
                        ))
                      )}
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-2 border-t">
                  <Button size="sm" onClick={() => onStatusClick(anf)}>
                    Status setzen
                  </Button>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}

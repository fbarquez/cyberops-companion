"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Shield,
  Check,
  X,
  AlertCircle,
  MinusCircle,
  HelpCircle,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
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
    mutationFn: (data: { anforderung_id: string; status: string; notes?: string }) =>
      bsiGrundschutzAPI.updateComplianceStatus(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bsi-baustein-score", bausteinId] });
      toast.success("Status aktualisiert");
      setStatusDialogOpen(false);
      setSelectedAnforderung(null);
      refetchScore();
    },
    onError: () => {
      toast.error("Fehler beim Aktualisieren");
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

  const handleStatusUpdate = () => {
    if (!selectedAnforderung) return;
    updateStatusMutation.mutate({
      anforderung_id: selectedAnforderung.anforderung_id,
      status: newStatus,
      notes: notes || undefined,
    });
  };

  const openStatusDialog = (anforderung: BSIAnforderung) => {
    setSelectedAnforderung(anforderung);
    setNewStatus("not_evaluated");
    setNotes("");
    setStatusDialogOpen(true);
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={`${baustein.baustein_id} - ${baustein.titel}`}
        backHref="/compliance/bsi"
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

          <TabsContent value="all">
            <AnforderungenList
              anforderungen={anforderungen}
              onStatusClick={openStatusDialog}
            />
          </TabsContent>

          {["MUSS", "SOLLTE", "KANN"].map((typ) => (
            <TabsContent key={typ} value={typ}>
              <AnforderungenList
                anforderungen={anforderungenByTyp[typ as keyof typeof anforderungenByTyp]}
                onStatusClick={openStatusDialog}
              />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Status Update Dialog */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Compliance Status aktualisieren</DialogTitle>
            <DialogDescription>
              {selectedAnforderung?.anforderung_id} - {selectedAnforderung?.titel}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
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
              <label className="text-sm font-medium">Notizen</label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optionale Anmerkungen..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleStatusUpdate}
              disabled={updateStatusMutation.isPending}
            >
              {updateStatusMutation.isPending ? "Speichere..." : "Speichern"}
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
}: {
  anforderungen: BSIAnforderung[];
  onStatusClick: (a: BSIAnforderung) => void;
}) {
  if (anforderungen.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        Keine Anforderungen in dieser Kategorie.
      </div>
    );
  }

  return (
    <Accordion type="multiple" className="space-y-2">
      {anforderungen.map((anf) => (
        <AccordionItem
          key={anf.id}
          value={anf.id}
          className="border rounded-lg px-4"
        >
          <AccordionTrigger className="hover:no-underline">
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
          <AccordionContent className="pt-2">
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
  );
}

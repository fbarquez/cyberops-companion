"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  FileText,
  Plus,
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  Archive,
  FileCheck,
  Users,
  Eye,
  Edit,
  MoreVertical,
  RefreshCw,
  TrendingUp,
  ClipboardList,
  BookOpen,
  FileQuestion,
  FilePlus,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { documentsAPI } from "@/lib/api-client";

interface DashboardStats {
  total_documents: number;
  documents_by_category: Record<string, number>;
  documents_by_status: Record<string, number>;
  draft_documents: number;
  pending_review: number;
  published_documents: number;
  archived_documents: number;
  documents_due_for_review: number;
  documents_overdue_review: number;
  pending_my_approval: number;
  pending_my_acknowledgment: number;
  acknowledgment_compliance_rate: number;
  documents_requiring_acknowledgment: number;
  acknowledgments_pending: number;
  acknowledgments_overdue: number;
}

interface Document {
  id: string;
  document_id: string;
  title: string;
  description?: string;
  category: string;
  status: string;
  current_version: string;
  owner_id: string;
  owner_name?: string;
  department?: string;
  next_review_date?: string;
  published_at?: string;
  created_at: string;
  frameworks: string[];
  control_references: string[];
  requires_acknowledgment: boolean;
  acknowledgment_stats?: {
    total: number;
    acknowledged: number;
    pending: number;
    overdue: number;
  };
  pending_approvals?: number;
}

interface DocumentListResponse {
  items: Document[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface PendingApprovalItem {
  document_id: string;
  document_title: string;
  document_category: string;
  current_version: string;
  approval_id: string;
  requested_at: string;
}

interface PendingAcknowledgmentItem {
  document_id: string;
  document_title: string;
  document_category: string;
  current_version: string;
  acknowledgment_id: string;
  due_date: string;
  is_overdue: boolean;
}

export default function DocumentsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("all");
  const [category, setCategory] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newDocument, setNewDocument] = useState({
    title: "",
    description: "",
    category: "policy",
    department: "",
    review_frequency_days: 365,
    requires_acknowledgment: false,
  });

  // Dashboard stats
  const { data: dashboardData } = useQuery({
    queryKey: ["documents-dashboard"],
    queryFn: () => documentsAPI.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
    refetchInterval: 60000,
  });

  // Documents list
  const { data: documentsData, refetch: refetchDocuments } = useQuery({
    queryKey: ["documents-list", category, status, searchQuery, activeTab],
    queryFn: () =>
      documentsAPI.list(token!, {
        category: category !== "all" ? category : undefined,
        status: activeTab === "pending-review" ? "pending_review" : (status !== "all" ? status : undefined),
        search: searchQuery || undefined,
        size: 50,
      }) as Promise<DocumentListResponse>,
    enabled: !!token,
  });

  // Pending approvals for current user
  const { data: pendingApprovals } = useQuery({
    queryKey: ["documents-pending-approvals"],
    queryFn: () =>
      documentsAPI.getMyPendingApprovals(token!) as Promise<{
        items: PendingApprovalItem[];
        total: number;
      }>,
    enabled: !!token && activeTab === "my-approvals",
  });

  // Pending acknowledgments for current user
  const { data: pendingAcknowledgments } = useQuery({
    queryKey: ["documents-pending-acknowledgments"],
    queryFn: () =>
      documentsAPI.getMyPendingAcknowledgments(token!) as Promise<{
        items: PendingAcknowledgmentItem[];
        total: number;
        overdue: number;
      }>,
    enabled: !!token && activeTab === "my-acknowledgments",
  });

  // Create document mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newDocument) =>
      documentsAPI.create(token!, data),
    onSuccess: () => {
      setIsCreateOpen(false);
      setNewDocument({
        title: "",
        description: "",
        category: "policy",
        department: "",
        review_frequency_days: 365,
        requires_acknowledgment: false,
      });
      refetchDocuments();
      queryClient.invalidateQueries({ queryKey: ["documents-dashboard"] });
    },
  });

  // Acknowledge mutation
  const acknowledgeMutation = useMutation({
    mutationFn: (documentId: string) =>
      documentsAPI.acknowledge(token!, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents-pending-acknowledgments"] });
      queryClient.invalidateQueries({ queryKey: ["documents-dashboard"] });
    },
  });

  const handleCreateDocument = () => {
    if (!newDocument.title) return;
    createMutation.mutate(newDocument);
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      published: "default",
      approved: "default",
      draft: "secondary",
      pending_review: "secondary",
      under_revision: "outline",
      archived: "destructive",
    };
    return variants[status] || "secondary";
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, typeof FileText> = {
      policy: BookOpen,
      procedure: ClipboardList,
      standard: FileCheck,
      guideline: FileQuestion,
      form: FilePlus,
      manual: BookOpen,
    };
    const Icon = icons[category] || FileText;
    return <Icon className="h-4 w-4" />;
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      policy: t("documents.categoryPolicy"),
      procedure: t("documents.categoryProcedure"),
      standard: t("documents.categoryStandard"),
      guideline: t("documents.categoryGuideline"),
      form: t("documents.categoryForm"),
      record: t("documents.categoryRecord"),
      manual: t("documents.categoryManual"),
      instruction: t("documents.categoryInstruction"),
    };
    return labels[category] || category;
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      draft: t("documents.statusDraft"),
      pending_review: t("documents.statusPendingReview"),
      approved: t("documents.statusApproved"),
      published: t("documents.statusPublished"),
      under_revision: t("documents.statusUnderRevision"),
      archived: t("documents.statusArchived"),
    };
    return labels[status] || status;
  };

  const stats = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("documents.title")}</h1>
          <p className="text-muted-foreground">{t("documents.subtitle")}</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t("documents.newDocument")}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t("documents.createDocument")}</DialogTitle>
              <DialogDescription>
                {t("documents.createDescription")}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="title">{t("documents.documentTitle")}</Label>
                <Input
                  id="title"
                  value={newDocument.title}
                  onChange={(e) =>
                    setNewDocument({ ...newDocument, title: e.target.value })
                  }
                  placeholder={t("documents.titlePlaceholder")}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">{t("documents.category")}</Label>
                  <Select
                    value={newDocument.category}
                    onValueChange={(v) =>
                      setNewDocument({ ...newDocument, category: v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="policy">{t("documents.categoryPolicy")}</SelectItem>
                      <SelectItem value="procedure">{t("documents.categoryProcedure")}</SelectItem>
                      <SelectItem value="standard">{t("documents.categoryStandard")}</SelectItem>
                      <SelectItem value="guideline">{t("documents.categoryGuideline")}</SelectItem>
                      <SelectItem value="form">{t("documents.categoryForm")}</SelectItem>
                      <SelectItem value="manual">{t("documents.categoryManual")}</SelectItem>
                      <SelectItem value="instruction">{t("documents.categoryInstruction")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">{t("documents.department")}</Label>
                  <Input
                    id="department"
                    value={newDocument.department}
                    onChange={(e) =>
                      setNewDocument({ ...newDocument, department: e.target.value })
                    }
                    placeholder={t("documents.departmentPlaceholder")}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">{t("documents.description")}</Label>
                <Textarea
                  id="description"
                  value={newDocument.description}
                  onChange={(e) =>
                    setNewDocument({ ...newDocument, description: e.target.value })
                  }
                  placeholder={t("documents.descriptionPlaceholder")}
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="review">{t("documents.reviewCycle")}</Label>
                  <Select
                    value={newDocument.review_frequency_days.toString()}
                    onValueChange={(v) =>
                      setNewDocument({ ...newDocument, review_frequency_days: parseInt(v) })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="90">{t("documents.quarterly")}</SelectItem>
                      <SelectItem value="180">{t("documents.semiAnnual")}</SelectItem>
                      <SelectItem value="365">{t("documents.annual")}</SelectItem>
                      <SelectItem value="730">{t("documents.biennial")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>{t("documents.requiresAck")}</Label>
                  <Select
                    value={newDocument.requires_acknowledgment ? "yes" : "no"}
                    onValueChange={(v) =>
                      setNewDocument({ ...newDocument, requires_acknowledgment: v === "yes" })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="no">{t("common.no")}</SelectItem>
                      <SelectItem value="yes">{t("common.yes")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                {t("common.cancel")}
              </Button>
              <Button
                onClick={handleCreateDocument}
                disabled={!newDocument.title || createMutation.isPending}
              >
                {createMutation.isPending ? t("common.creating") : t("documents.create")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              {t("documents.totalDocuments")}
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_documents || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.published_documents || 0} {t("documents.published")}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              {t("documents.pendingMyAction")}
            </CardTitle>
            <Clock className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(stats?.pending_my_approval || 0) + (stats?.pending_my_acknowledgment || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.pending_my_approval || 0} {t("documents.approvals")}, {stats?.pending_my_acknowledgment || 0} {t("documents.acknowledgments")}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              {t("documents.reviewsDue")}
            </CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.documents_due_for_review || 0}
            </div>
            <p className="text-xs text-destructive">
              {stats?.documents_overdue_review || 0} {t("documents.overdue")}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              {t("documents.ackCompliance")}
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.acknowledgment_compliance_rate || 0}%
            </div>
            <Progress
              value={stats?.acknowledgment_compliance_rate || 0}
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {t("documents.allDocuments")}
          </TabsTrigger>
          <TabsTrigger value="pending-review" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            {t("documents.pendingReview")}
            {(stats?.pending_review || 0) > 0 && (
              <Badge variant="secondary" className="ml-1">
                {stats?.pending_review}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="my-approvals" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            {t("documents.myApprovals")}
            {(stats?.pending_my_approval || 0) > 0 && (
              <Badge variant="destructive" className="ml-1">
                {stats?.pending_my_approval}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="my-acknowledgments" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            {t("documents.myAcknowledgments")}
            {(stats?.pending_my_acknowledgment || 0) > 0 && (
              <Badge variant="destructive" className="ml-1">
                {stats?.pending_my_acknowledgment}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* All Documents Tab */}
        <TabsContent value="all" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t("documents.searchPlaceholder")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder={t("documents.category")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("documents.allCategories")}</SelectItem>
                <SelectItem value="policy">{t("documents.categoryPolicy")}</SelectItem>
                <SelectItem value="procedure">{t("documents.categoryProcedure")}</SelectItem>
                <SelectItem value="standard">{t("documents.categoryStandard")}</SelectItem>
                <SelectItem value="guideline">{t("documents.categoryGuideline")}</SelectItem>
                <SelectItem value="form">{t("documents.categoryForm")}</SelectItem>
                <SelectItem value="manual">{t("documents.categoryManual")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t("documents.status")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("documents.allStatuses")}</SelectItem>
                <SelectItem value="draft">{t("documents.statusDraft")}</SelectItem>
                <SelectItem value="pending_review">{t("documents.statusPendingReview")}</SelectItem>
                <SelectItem value="approved">{t("documents.statusApproved")}</SelectItem>
                <SelectItem value="published">{t("documents.statusPublished")}</SelectItem>
                <SelectItem value="archived">{t("documents.statusArchived")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Documents List */}
          <div className="grid gap-4">
            {documentsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("documents.noDocuments")}</p>
                </CardContent>
              </Card>
            )}
            {documentsData?.items?.map((doc) => (
              <Card
                key={doc.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/documents/${doc.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {getCategoryIcon(doc.category)}
                        <h3 className="font-semibold">{doc.title}</h3>
                        <Badge variant="outline">{doc.document_id}</Badge>
                        <Badge variant="outline">v{doc.current_version}</Badge>
                        <Badge variant={getStatusBadgeVariant(doc.status)}>
                          {getStatusLabel(doc.status)}
                        </Badge>
                      </div>
                      {doc.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {doc.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-2 mt-2">
                        <Badge variant="secondary">
                          {getCategoryLabel(doc.category)}
                        </Badge>
                        {doc.frameworks?.map((fw) => (
                          <Badge key={fw} variant="outline">
                            {fw}
                          </Badge>
                        ))}
                        {doc.requires_acknowledgment && doc.acknowledgment_stats && (
                          <Badge
                            variant={
                              doc.acknowledgment_stats.overdue > 0
                                ? "destructive"
                                : "outline"
                            }
                          >
                            {doc.acknowledgment_stats.acknowledged}/
                            {doc.acknowledgment_stats.total} {t("documents.acknowledged")}
                          </Badge>
                        )}
                        {doc.pending_approvals && doc.pending_approvals > 0 && (
                          <Badge variant="secondary">
                            {doc.pending_approvals} {t("documents.pendingApprovals")}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/documents/${doc.id}`);
                          }}>
                            <Eye className="h-4 w-4 mr-2" />
                            {t("common.view")}
                          </DropdownMenuItem>
                          {doc.status === "draft" && (
                            <DropdownMenuItem onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/documents/${doc.id}?edit=true`);
                            }}>
                              <Edit className="h-4 w-4 mr-2" />
                              {t("common.edit")}
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              // Archive action
                            }}
                            className="text-destructive"
                          >
                            <Archive className="h-4 w-4 mr-2" />
                            {t("documents.archive")}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      {doc.next_review_date && (
                        <p className="text-xs text-muted-foreground">
                          {t("documents.nextReview")}: {new Date(doc.next_review_date).toLocaleDateString()}
                        </p>
                      )}
                      {doc.owner_name && (
                        <p className="text-xs text-muted-foreground">
                          {t("documents.owner")}: {doc.owner_name}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Pending Review Tab */}
        <TabsContent value="pending-review" className="space-y-4">
          <div className="grid gap-4">
            {documentsData?.items?.filter(d => d.status === "pending_review").length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("documents.noPendingReview")}</p>
                </CardContent>
              </Card>
            )}
            {documentsData?.items?.filter(d => d.status === "pending_review").map((doc) => (
              <Card
                key={doc.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/documents/${doc.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(doc.category)}
                        <h3 className="font-semibold">{doc.title}</h3>
                        <Badge variant="outline">{doc.document_id}</Badge>
                        <Badge variant="secondary">v{doc.current_version}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {getCategoryLabel(doc.category)}
                        {doc.pending_approvals && ` - ${doc.pending_approvals} ${t("documents.approvalsRemaining")}`}
                      </p>
                    </div>
                    <Button size="sm" onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/documents/${doc.id}?tab=approvals`);
                    }}>
                      {t("documents.review")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* My Approvals Tab */}
        <TabsContent value="my-approvals" className="space-y-4">
          <div className="grid gap-4">
            {pendingApprovals?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <CheckCircle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("documents.noApprovalsRequired")}</p>
                </CardContent>
              </Card>
            )}
            {pendingApprovals?.items?.map((item) => (
              <Card
                key={item.approval_id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/documents/${item.document_id}?tab=approvals`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(item.document_category)}
                        <h3 className="font-semibold">{item.document_title}</h3>
                        <Badge variant="outline">v{item.current_version}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {getCategoryLabel(item.document_category)} - {t("documents.requestedAt")} {new Date(item.requested_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/documents/${item.document_id}`);
                        }}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        {t("common.view")}
                      </Button>
                      <Button size="sm">
                        {t("documents.approveOrReject")}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* My Acknowledgments Tab */}
        <TabsContent value="my-acknowledgments" className="space-y-4">
          <div className="grid gap-4">
            {pendingAcknowledgments?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Users className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("documents.noAcknowledgmentsRequired")}</p>
                </CardContent>
              </Card>
            )}
            {pendingAcknowledgments?.items?.map((item) => (
              <Card
                key={item.acknowledgment_id}
                className={`hover:shadow-md transition-shadow ${
                  item.is_overdue ? "border-destructive" : ""
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(item.document_category)}
                        <h3 className="font-semibold">{item.document_title}</h3>
                        <Badge variant="outline">v{item.current_version}</Badge>
                        {item.is_overdue && (
                          <Badge variant="destructive">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            {t("documents.overdue")}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {getCategoryLabel(item.document_category)} - {t("documents.dueBy")} {new Date(item.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => router.push(`/documents/${item.document_id}`)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        {t("documents.readDocument")}
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => acknowledgeMutation.mutate(item.document_id)}
                        disabled={acknowledgeMutation.isPending}
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        {t("documents.acknowledge")}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

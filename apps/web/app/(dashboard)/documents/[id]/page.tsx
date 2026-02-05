"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Users,
  History,
  Send,
  Save,
  MoreVertical,
  Edit,
  Archive,
  RefreshCw,
  Eye,
  Calendar,
  User,
  Building,
  Tag,
  Link2,
  MessageSquare,
  Bell,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { documentsAPI } from "@/lib/api-client";

interface DocumentDetail {
  id: string;
  document_id: string;
  title: string;
  description?: string;
  category: string;
  status: string;
  current_version: string;
  content?: string;
  owner_id: string;
  owner_name?: string;
  department?: string;
  review_frequency_days?: number;
  last_review_date?: string;
  next_review_date?: string;
  frameworks: string[];
  control_references: string[];
  requires_acknowledgment: boolean;
  acknowledgment_due_days: number;
  approval_type: string;
  tags: string[];
  published_at?: string;
  published_by?: string;
  created_at: string;
  updated_at?: string;
  versions?: Version[];
  current_approval_chain?: Approval[];
  recent_reviews?: Review[];
}

interface Version {
  id: string;
  version_number: string;
  version_type: string;
  change_summary: string;
  change_details?: string;
  is_current: boolean;
  is_published: boolean;
  created_at: string;
  created_by?: string;
  published_at?: string;
  has_content: boolean;
}

interface Approval {
  id: string;
  approver_id: string;
  approver_name?: string;
  approval_order: number;
  status: string;
  decision_at?: string;
  comments?: string;
  created_at: string;
}

interface Acknowledgment {
  id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
  status: string;
  due_date: string;
  acknowledged_at?: string;
  decline_reason?: string;
  reminder_count: number;
  is_overdue: boolean;
}

interface AcknowledgmentList {
  items: Acknowledgment[];
  total: number;
  acknowledged: number;
  pending: number;
  overdue: number;
  declined: number;
  compliance_percentage: number;
}

interface Review {
  id: string;
  review_date: string;
  reviewer_id: string;
  reviewer_name?: string;
  outcome: string;
  review_notes?: string;
  action_items?: any[];
  next_review_date: string;
}

export default function DocumentDetailPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const documentId = params.id as string;
  const initialTab = searchParams.get("tab") || "content";
  const isEditMode = searchParams.get("edit") === "true";

  const [activeTab, setActiveTab] = useState(initialTab);
  const [isEditing, setIsEditing] = useState(isEditMode);
  const [editedContent, setEditedContent] = useState("");
  const [isSubmitDialogOpen, setIsSubmitDialogOpen] = useState(false);
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [approvalComments, setApprovalComments] = useState("");
  const [rejectComments, setRejectComments] = useState("");
  const [selectedApprovers, setSelectedApprovers] = useState<string[]>([]);

  // Fetch document detail
  const { data: document, isLoading } = useQuery({
    queryKey: ["document-detail", documentId],
    queryFn: () => documentsAPI.get(token!, documentId) as Promise<DocumentDetail>,
    enabled: !!token && !!documentId,
  });

  // Fetch acknowledgments
  const { data: acknowledgments } = useQuery({
    queryKey: ["document-acknowledgments", documentId],
    queryFn: () => documentsAPI.listAcknowledgments(token!, documentId) as Promise<AcknowledgmentList>,
    enabled: !!token && !!documentId && activeTab === "acknowledgments",
  });

  // Fetch versions
  const { data: versions } = useQuery({
    queryKey: ["document-versions", documentId],
    queryFn: () => documentsAPI.listVersions(token!, documentId) as Promise<{ items: Version[]; total: number }>,
    enabled: !!token && !!documentId && activeTab === "versions",
  });

  // Fetch reviews
  const { data: reviews } = useQuery({
    queryKey: ["document-reviews", documentId],
    queryFn: () => documentsAPI.listReviews(token!, documentId) as Promise<{ items: Review[]; total: number }>,
    enabled: !!token && !!documentId && activeTab === "reviews",
  });

  // Update content mutation
  const updateMutation = useMutation({
    mutationFn: (data: { content: string }) =>
      documentsAPI.update(token!, documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
      setIsEditing(false);
    },
  });

  // Submit for review mutation
  const submitMutation = useMutation({
    mutationFn: (data: { approvers: { user_id: string; approval_order: number }[] }) =>
      documentsAPI.submitForReview(token!, documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
      setIsSubmitDialogOpen(false);
    },
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (comments?: string) =>
      documentsAPI.approve(token!, documentId, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
      setIsApproveDialogOpen(false);
      setApprovalComments("");
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (comments: string) =>
      documentsAPI.reject(token!, documentId, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
      setIsRejectDialogOpen(false);
      setRejectComments("");
    },
  });

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: () => documentsAPI.publish(token!, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
    },
  });

  // Archive mutation
  const archiveMutation = useMutation({
    mutationFn: () => documentsAPI.archive(token!, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-detail", documentId] });
      router.push("/documents");
    },
  });

  // Send reminder mutation
  const reminderMutation = useMutation({
    mutationFn: (ackId: string) =>
      documentsAPI.sendAcknowledgmentReminder(token!, ackId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-acknowledgments", documentId] });
    },
  });

  useEffect(() => {
    if (document?.content) {
      setEditedContent(document.content);
    }
  }, [document]);

  const handleSaveContent = () => {
    updateMutation.mutate({ content: editedContent });
  };

  const handleSubmitForReview = () => {
    const approvers = selectedApprovers.map((userId, index) => ({
      user_id: userId,
      approval_order: index + 1,
    }));
    submitMutation.mutate({ approvers });
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      published: "default",
      approved: "default",
      draft: "secondary",
      pending_review: "secondary",
      pending: "secondary",
      under_revision: "outline",
      archived: "destructive",
      rejected: "destructive",
      acknowledged: "default",
      declined: "destructive",
      expired: "destructive",
    };
    return variants[status] || "secondary";
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      draft: t("documents.statusDraft"),
      pending_review: t("documents.statusPendingReview"),
      approved: t("documents.statusApproved"),
      published: t("documents.statusPublished"),
      under_revision: t("documents.statusUnderRevision"),
      archived: t("documents.statusArchived"),
      pending: t("documents.statusPending"),
      rejected: t("documents.statusRejected"),
      acknowledged: t("documents.statusAcknowledged"),
      declined: t("documents.statusDeclined"),
      expired: t("documents.statusExpired"),
      changes_requested: t("documents.statusChangesRequested"),
    };
    return labels[status] || status;
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

  const getReviewOutcomeLabel = (outcome: string) => {
    const labels: Record<string, string> = {
      no_changes: t("documents.outcomeNoChanges"),
      minor_update: t("documents.outcomeMinorUpdate"),
      major_revision: t("documents.outcomeMajorRevision"),
      retire: t("documents.outcomeRetire"),
    };
    return labels[outcome] || outcome;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">{t("documents.notFound")}</p>
        <Button variant="link" onClick={() => router.push("/documents")}>
          {t("documents.backToList")}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => router.push("/documents")}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold">{document.title}</h1>
                <Badge variant="outline">{document.document_id}</Badge>
                <Badge variant="outline">v{document.current_version}</Badge>
                <Badge variant={getStatusBadgeVariant(document.status)}>
                  {getStatusLabel(document.status)}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {getCategoryLabel(document.category)}
                {document.department && ` - ${document.department}`}
                {document.updated_at && ` - ${t("documents.lastUpdated")} ${new Date(document.updated_at).toLocaleDateString()}`}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Workflow actions based on status */}
          {document.status === "draft" && (
            <>
              {!isEditing ? (
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  {t("common.edit")}
                </Button>
              ) : (
                <Button onClick={handleSaveContent} disabled={updateMutation.isPending}>
                  <Save className="h-4 w-4 mr-2" />
                  {t("common.save")}
                </Button>
              )}
              <Dialog open={isSubmitDialogOpen} onOpenChange={setIsSubmitDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Send className="h-4 w-4 mr-2" />
                    {t("documents.submitForReview")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("documents.submitForReview")}</DialogTitle>
                    <DialogDescription>
                      {t("documents.submitDescription")}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>{t("documents.selectApprovers")}</Label>
                      <p className="text-sm text-muted-foreground">
                        {t("documents.approverNote")}
                      </p>
                      {/* Simplified approver input */}
                      <Input
                        placeholder={t("documents.approverIdPlaceholder")}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            const value = (e.target as HTMLInputElement).value.trim();
                            if (value && !selectedApprovers.includes(value)) {
                              setSelectedApprovers([...selectedApprovers, value]);
                              (e.target as HTMLInputElement).value = "";
                            }
                          }
                        }}
                      />
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedApprovers.map((id, index) => (
                          <Badge key={id} variant="secondary" className="cursor-pointer" onClick={() =>
                            setSelectedApprovers(selectedApprovers.filter(a => a !== id))
                          }>
                            {index + 1}. {id} <XCircle className="h-3 w-3 ml-1" />
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsSubmitDialogOpen(false)}>
                      {t("common.cancel")}
                    </Button>
                    <Button
                      onClick={handleSubmitForReview}
                      disabled={selectedApprovers.length === 0 || submitMutation.isPending}
                    >
                      {t("documents.submit")}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </>
          )}

          {document.status === "pending_review" && (
            <>
              <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="default">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {t("documents.approve")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("documents.approveDocument")}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>{t("documents.comments")}</Label>
                      <Textarea
                        value={approvalComments}
                        onChange={(e) => setApprovalComments(e.target.value)}
                        placeholder={t("documents.approvalCommentsPlaceholder")}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>
                      {t("common.cancel")}
                    </Button>
                    <Button onClick={() => approveMutation.mutate(approvalComments)} disabled={approveMutation.isPending}>
                      {t("documents.approve")}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="destructive">
                    <XCircle className="h-4 w-4 mr-2" />
                    {t("documents.reject")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("documents.rejectDocument")}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>{t("documents.rejectReason")}</Label>
                      <Textarea
                        value={rejectComments}
                        onChange={(e) => setRejectComments(e.target.value)}
                        placeholder={t("documents.rejectReasonPlaceholder")}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsRejectDialogOpen(false)}>
                      {t("common.cancel")}
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => rejectMutation.mutate(rejectComments)}
                      disabled={!rejectComments || rejectMutation.isPending}
                    >
                      {t("documents.reject")}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </>
          )}

          {document.status === "approved" && (
            <Button onClick={() => publishMutation.mutate()} disabled={publishMutation.isPending}>
              <Send className="h-4 w-4 mr-2" />
              {t("documents.publish")}
            </Button>
          )}

          {/* Dropdown for more actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setActiveTab("versions")}>
                <History className="h-4 w-4 mr-2" />
                {t("documents.viewHistory")}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => archiveMutation.mutate()}
                className="text-destructive"
              >
                <Archive className="h-4 w-4 mr-2" />
                {t("documents.archive")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="content" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {t("documents.content")}
          </TabsTrigger>
          <TabsTrigger value="versions" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            {t("documents.versions")}
          </TabsTrigger>
          <TabsTrigger value="approvals" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            {t("documents.approvals")}
          </TabsTrigger>
          {document.requires_acknowledgment && (
            <TabsTrigger value="acknowledgments" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              {t("documents.acknowledgments")}
            </TabsTrigger>
          )}
          <TabsTrigger value="reviews" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            {t("documents.reviews")}
          </TabsTrigger>
        </TabsList>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-3">
              <Card>
                <CardContent className="p-6">
                  {isEditing ? (
                    <Textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="min-h-[500px] font-mono"
                      placeholder={t("documents.contentPlaceholder")}
                    />
                  ) : (
                    <div className="prose dark:prose-invert max-w-none">
                      {document.content ? (
                        <ReactMarkdown>{document.content}</ReactMarkdown>
                      ) : (
                        <p className="text-muted-foreground italic">
                          {t("documents.noContent")}
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Metadata */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">{t("documents.metadata")}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">{t("documents.owner")}:</span>
                    <span>{document.owner_name || document.owner_id}</span>
                  </div>
                  {document.department && (
                    <div className="flex items-center gap-2 text-sm">
                      <Building className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">{t("documents.department")}:</span>
                      <span>{document.department}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">{t("documents.created")}:</span>
                    <span>{new Date(document.created_at).toLocaleDateString()}</span>
                  </div>
                  {document.published_at && (
                    <div className="flex items-center gap-2 text-sm">
                      <Send className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">{t("documents.published")}:</span>
                      <span>{new Date(document.published_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Review Cycle */}
              {document.review_frequency_days && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">{t("documents.reviewCycle")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <RefreshCw className="h-4 w-4 text-muted-foreground" />
                      <span>
                        {document.review_frequency_days === 365
                          ? t("documents.annual")
                          : document.review_frequency_days === 180
                          ? t("documents.semiAnnual")
                          : document.review_frequency_days === 90
                          ? t("documents.quarterly")
                          : `${document.review_frequency_days} ${t("documents.days")}`}
                      </span>
                    </div>
                    {document.next_review_date && (
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">{t("documents.nextReview")}:</span>
                        <span>{new Date(document.next_review_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Frameworks & Controls */}
              {(document.frameworks?.length > 0 || document.control_references?.length > 0) && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">{t("documents.compliance")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {document.frameworks?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {document.frameworks.map((fw) => (
                          <Badge key={fw} variant="outline" className="text-xs">
                            <Link2 className="h-3 w-3 mr-1" />
                            {fw}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {document.control_references?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {document.control_references.map((ref) => (
                          <Badge key={ref} variant="secondary" className="text-xs">
                            {ref}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Tags */}
              {document.tags?.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">{t("documents.tags")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {document.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("documents.versionHistory")}</CardTitle>
              <CardDescription>
                {t("documents.versionHistoryDescription")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("documents.version")}</TableHead>
                    <TableHead>{t("documents.type")}</TableHead>
                    <TableHead>{t("documents.changeSummary")}</TableHead>
                    <TableHead>{t("documents.date")}</TableHead>
                    <TableHead>{t("documents.status")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {versions?.items?.map((version) => (
                    <TableRow key={version.id}>
                      <TableCell className="font-medium">
                        v{version.version_number}
                        {version.is_current && (
                          <Badge variant="default" className="ml-2">
                            {t("documents.current")}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{version.version_type}</Badge>
                      </TableCell>
                      <TableCell>{version.change_summary}</TableCell>
                      <TableCell>{new Date(version.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {version.is_published ? (
                          <Badge variant="default">{t("documents.published")}</Badge>
                        ) : (
                          <Badge variant="secondary">{t("documents.draft")}</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!versions?.items?.length && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        {t("documents.noVersions")}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Approvals Tab */}
        <TabsContent value="approvals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("documents.approvalChain")}</CardTitle>
              <CardDescription>
                {document.approval_type === "sequential"
                  ? t("documents.sequentialApproval")
                  : t("documents.parallelApproval")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {document.current_approval_chain?.map((approval, index) => (
                  <div
                    key={approval.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-sm font-medium">
                        {approval.approval_order}
                      </div>
                      <div>
                        <p className="font-medium">
                          {approval.approver_name || approval.approver_id}
                        </p>
                        {approval.comments && (
                          <p className="text-sm text-muted-foreground flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" />
                            {approval.comments}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusBadgeVariant(approval.status)}>
                        {getStatusLabel(approval.status)}
                      </Badge>
                      {approval.decision_at && (
                        <span className="text-sm text-muted-foreground">
                          {new Date(approval.decision_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {!document.current_approval_chain?.length && (
                  <p className="text-center text-muted-foreground py-8">
                    {t("documents.noApprovals")}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Acknowledgments Tab */}
        {document.requires_acknowledgment && (
          <TabsContent value="acknowledgments" className="space-y-4">
            {/* Progress */}
            <Card>
              <CardHeader>
                <CardTitle>{t("documents.acknowledgmentProgress")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>
                      {acknowledgments?.acknowledged || 0} / {acknowledgments?.total || 0} {t("documents.usersAcknowledged")}
                    </span>
                    <span className="font-medium">
                      {acknowledgments?.compliance_percentage || 0}%
                    </span>
                  </div>
                  <Progress value={acknowledgments?.compliance_percentage || 0} />
                  <div className="flex flex-wrap gap-4 text-sm">
                    <Badge variant="default">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      {acknowledgments?.acknowledged || 0} {t("documents.acknowledged")}
                    </Badge>
                    <Badge variant="secondary">
                      <Clock className="h-3 w-3 mr-1" />
                      {acknowledgments?.pending || 0} {t("documents.pending")}
                    </Badge>
                    <Badge variant="destructive">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      {acknowledgments?.overdue || 0} {t("documents.overdue")}
                    </Badge>
                    {(acknowledgments?.declined || 0) > 0 && (
                      <Badge variant="outline">
                        <XCircle className="h-3 w-3 mr-1" />
                        {acknowledgments?.declined} {t("documents.declined")}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Acknowledgments Table */}
            <Card>
              <CardHeader>
                <CardTitle>{t("documents.acknowledgmentDetails")}</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("documents.user")}</TableHead>
                      <TableHead>{t("documents.status")}</TableHead>
                      <TableHead>{t("documents.dueDate")}</TableHead>
                      <TableHead>{t("documents.acknowledgedAt")}</TableHead>
                      <TableHead>{t("documents.actions")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {acknowledgments?.items?.map((ack) => (
                      <TableRow key={ack.id} className={ack.is_overdue ? "bg-destructive/5" : ""}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{ack.user_name || ack.user_id}</p>
                            {ack.user_email && (
                              <p className="text-sm text-muted-foreground">{ack.user_email}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(ack.status)}>
                            {ack.is_overdue && ack.status === "pending" ? (
                              <AlertCircle className="h-3 w-3 mr-1" />
                            ) : null}
                            {getStatusLabel(ack.status)}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(ack.due_date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          {ack.acknowledged_at
                            ? new Date(ack.acknowledged_at).toLocaleDateString()
                            : "-"}
                        </TableCell>
                        <TableCell>
                          {ack.status === "pending" && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => reminderMutation.mutate(ack.id)}
                              disabled={reminderMutation.isPending}
                            >
                              <Bell className="h-4 w-4 mr-1" />
                              {t("documents.sendReminder")}
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {!acknowledgments?.items?.length && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground">
                          {t("documents.noAcknowledgments")}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Reviews Tab */}
        <TabsContent value="reviews" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("documents.reviewHistory")}</CardTitle>
              <CardDescription>
                {t("documents.reviewHistoryDescription")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("documents.reviewDate")}</TableHead>
                    <TableHead>{t("documents.reviewer")}</TableHead>
                    <TableHead>{t("documents.outcome")}</TableHead>
                    <TableHead>{t("documents.notes")}</TableHead>
                    <TableHead>{t("documents.nextReview")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reviews?.items?.map((review) => (
                    <TableRow key={review.id}>
                      <TableCell>{new Date(review.review_date).toLocaleDateString()}</TableCell>
                      <TableCell>{review.reviewer_name || review.reviewer_id}</TableCell>
                      <TableCell>
                        <Badge variant={
                          review.outcome === "no_changes" ? "default" :
                          review.outcome === "retire" ? "destructive" : "secondary"
                        }>
                          {getReviewOutcomeLabel(review.outcome)}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {review.review_notes || "-"}
                      </TableCell>
                      <TableCell>{new Date(review.next_review_date).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))}
                  {!reviews?.items?.length && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        {t("documents.noReviews")}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

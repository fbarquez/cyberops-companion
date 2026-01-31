"use client";

import { useCallback, useState, useRef } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  File,
  X,
  Download,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  Shield,
  MoreVertical,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useAttachments,
  Attachment,
  AttachmentCategory,
  AttachmentEntityType,
  UploadProgress,
} from "@/hooks/use-attachments";
import { useTranslations } from "@/hooks/use-translations";
import { ConfirmDialog } from "./form-dialog";

const CATEGORY_LABELS: Record<AttachmentCategory, string> = {
  evidence: "Evidence",
  screenshot: "Screenshot",
  log_file: "Log File",
  document: "Document",
  report: "Report",
  pcap: "Network Capture",
  memory_dump: "Memory Dump",
  malware_sample: "Malware Sample",
  other: "Other",
};

const CATEGORY_COLORS: Record<AttachmentCategory, string> = {
  evidence: "bg-blue-500",
  screenshot: "bg-purple-500",
  log_file: "bg-green-500",
  document: "bg-orange-500",
  report: "bg-yellow-500",
  pcap: "bg-cyan-500",
  memory_dump: "bg-red-500",
  malware_sample: "bg-rose-700",
  other: "bg-gray-500",
};

interface FileUploadProps {
  entityType: AttachmentEntityType;
  entityId: string;
  onUploadComplete?: (attachment: Attachment) => void;
  onDeleteComplete?: (attachmentId: string) => void;
  maxFiles?: number;
  maxSizeMB?: number;
  acceptedTypes?: string[];
  showList?: boolean;
  compact?: boolean;
  className?: string;
}

export function FileUpload({
  entityType,
  entityId,
  onUploadComplete,
  onDeleteComplete,
  maxFiles = 10,
  maxSizeMB = 50,
  acceptedTypes,
  showList = true,
  compact = false,
  className,
}: FileUploadProps) {
  const { t } = useTranslations();
  const [selectedCategory, setSelectedCategory] =
    useState<AttachmentCategory>("other");
  const [description, setDescription] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [attachmentToDelete, setAttachmentToDelete] = useState<string | null>(
    null
  );
  const initialized = useRef(false);

  const {
    attachments,
    isLoading,
    isUploading,
    uploadQueue,
    fetchAttachments,
    uploadFile,
    downloadFile,
    deleteAttachment,
    verifyIntegrity,
  } = useAttachments({
    entityType,
    entityId,
    onUploadComplete,
    onDeleteComplete,
  });

  // Fetch attachments on mount
  if (!initialized.current) {
    initialized.current = true;
    fetchAttachments();
  }

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        await uploadFile(file, selectedCategory, description || undefined);
      }
      setDescription("");
    },
    [uploadFile, selectedCategory, description]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      maxFiles,
      maxSize: maxSizeMB * 1024 * 1024,
      accept: acceptedTypes
        ? acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {})
        : undefined,
    });

  const handleDelete = (id: string) => {
    setAttachmentToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (attachmentToDelete) {
      await deleteAttachment(attachmentToDelete);
      setAttachmentToDelete(null);
    }
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) return "image";
    if (contentType.startsWith("video/")) return "video";
    if (contentType.includes("pdf")) return "pdf";
    if (contentType.includes("zip") || contentType.includes("compressed"))
      return "archive";
    return "file";
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (compact) {
    return (
      <div className={cn("space-y-2", className)}>
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors",
            isDragActive && "border-primary bg-primary/5",
            isDragReject && "border-destructive bg-destructive/5",
            !isDragActive && !isDragReject && "border-muted-foreground/25 hover:border-primary/50"
          )}
        >
          <input {...getInputProps()} />
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Upload className="h-4 w-4" />
            <span>Drop files or click to upload</span>
          </div>
        </div>

        {uploadQueue.length > 0 && (
          <div className="space-y-1">
            {uploadQueue.map((item, i) => (
              <UploadProgressItem key={i} item={item} />
            ))}
          </div>
        )}

        {showList && attachments.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {attachments.length} file(s) attached
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Upload Area */}
      <div className="space-y-3">
        <div className="flex gap-3">
          <Select
            value={selectedCategory}
            onValueChange={(v) => setSelectedCategory(v as AttachmentCategory)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="flex-1"
          />
        </div>

        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            isDragActive && "border-primary bg-primary/5",
            isDragReject && "border-destructive bg-destructive/5",
            !isDragActive &&
              !isDragReject &&
              "border-muted-foreground/25 hover:border-primary/50"
          )}
        >
          <input {...getInputProps()} />
          <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
          {isDragActive ? (
            <p className="text-primary">Drop files here...</p>
          ) : (
            <div className="space-y-1">
              <p className="text-muted-foreground">
                Drag & drop files here, or click to select
              </p>
              <p className="text-xs text-muted-foreground/60">
                Max {maxSizeMB}MB per file, up to {maxFiles} files
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Progress */}
      {uploadQueue.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Uploading</h4>
          {uploadQueue.map((item, i) => (
            <UploadProgressItem key={i} item={item} />
          ))}
        </div>
      )}

      {/* Attachments List */}
      {showList && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">
              Attachments ({attachments.length})
            </h4>
            {isLoading && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>

          {attachments.length === 0 && !isLoading ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No attachments yet
            </div>
          ) : (
            <div className="space-y-2">
              {attachments.map((attachment) => (
                <AttachmentItem
                  key={attachment.id}
                  attachment={attachment}
                  onDownload={() => downloadFile(attachment.id)}
                  onDelete={() => handleDelete(attachment.id)}
                  onVerify={() => verifyIntegrity(attachment.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Attachment"
        description="Are you sure you want to delete this attachment? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={confirmDelete}
        destructive
      />
    </div>
  );
}

function UploadProgressItem({ item }: { item: UploadProgress }) {
  return (
    <div className="flex items-center gap-3 p-2 bg-muted/50 rounded-lg">
      <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm truncate">{item.file.name}</p>
        <Progress value={item.progress} className="h-1 mt-1" />
      </div>
      <div className="flex-shrink-0">
        {item.status === "uploading" && (
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        )}
        {item.status === "success" && (
          <CheckCircle className="h-4 w-4 text-green-500" />
        )}
        {item.status === "error" && (
          <AlertCircle className="h-4 w-4 text-destructive" />
        )}
      </div>
    </div>
  );
}

interface AttachmentItemProps {
  attachment: Attachment;
  onDownload: () => void;
  onDelete: () => void;
  onVerify: () => void;
}

function AttachmentItem({
  attachment,
  onDownload,
  onDelete,
  onVerify,
}: AttachmentItemProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-card border rounded-lg hover:bg-muted/50 transition-colors">
      <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{attachment.filename}</p>
          <Badge
            variant="secondary"
            className={cn(
              "text-xs text-white",
              CATEGORY_COLORS[attachment.category]
            )}
          >
            {CATEGORY_LABELS[attachment.category]}
          </Badge>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
          <span>{attachment.file_size_human}</span>
          <span>{formatDate(attachment.uploaded_at)}</span>
          <span>{attachment.download_count} downloads</span>
        </div>
        {attachment.description && (
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {attachment.description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={onDownload}
          title="Download"
        >
          <Download className="h-4 w-4" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onVerify}>
              <Shield className="h-4 w-4 mr-2" />
              Verify Integrity
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onDelete} className="text-destructive">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export { CATEGORY_LABELS, CATEGORY_COLORS };

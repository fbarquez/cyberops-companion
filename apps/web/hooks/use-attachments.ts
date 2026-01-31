"use client";

import { useState, useCallback } from "react";
import { useAuthStore } from "@/stores/auth";
import { attachmentsAPI } from "@/lib/api-client";
import { toast } from "sonner";
import { useTranslation } from "@/i18n/client";

export type AttachmentCategory =
  | "evidence"
  | "screenshot"
  | "log_file"
  | "document"
  | "report"
  | "pcap"
  | "memory_dump"
  | "malware_sample"
  | "other";

export type AttachmentEntityType =
  | "incident"
  | "vulnerability"
  | "case"
  | "alert"
  | "risk"
  | "vendor"
  | "asset"
  | "evidence"
  | "report"
  | "general";

export interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  file_size_human: string;
  file_hash: string;
  category: AttachmentCategory;
  description: string | null;
  entity_type: AttachmentEntityType;
  entity_id: string;
  uploaded_by: string;
  uploaded_at: string;
  download_count: number;
  last_downloaded_at: string | null;
}

export interface UploadProgress {
  file: File;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
  attachment?: Attachment;
}

interface UseAttachmentsOptions {
  entityType: AttachmentEntityType;
  entityId: string;
  onUploadComplete?: (attachment: Attachment) => void;
  onDeleteComplete?: (attachmentId: string) => void;
}

export function useAttachments(options: UseAttachmentsOptions) {
  const { entityType, entityId, onUploadComplete, onDeleteComplete } = options;
  const { t } = useTranslation();
  const token = useAuthStore((state) => state.token);

  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<UploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const fetchAttachments = useCallback(
    async (category?: AttachmentCategory) => {
      if (!token) return;

      setIsLoading(true);
      try {
        const response = await attachmentsAPI.list(
          token,
          entityType,
          entityId,
          category
        );
        setAttachments(response.items || []);
      } catch (error: any) {
        toast.error(error.message || "Failed to load attachments");
      } finally {
        setIsLoading(false);
      }
    },
    [token, entityType, entityId]
  );

  const uploadFile = useCallback(
    async (
      file: File,
      category: AttachmentCategory = "other",
      description?: string
    ) => {
      if (!token) return null;

      const uploadProgress: UploadProgress = {
        file,
        progress: 0,
        status: "pending",
      };

      setUploadQueue((prev) => [...prev, uploadProgress]);
      setIsUploading(true);

      try {
        // Update status to uploading
        setUploadQueue((prev) =>
          prev.map((p) =>
            p.file === file ? { ...p, status: "uploading", progress: 50 } : p
          )
        );

        const response = await attachmentsAPI.upload(
          token,
          entityType,
          entityId,
          file,
          category,
          description
        );

        // Update status to success
        setUploadQueue((prev) =>
          prev.map((p) =>
            p.file === file
              ? { ...p, status: "success", progress: 100, attachment: response.attachment }
              : p
          )
        );

        // Add to attachments list
        setAttachments((prev) => [response.attachment, ...prev]);
        onUploadComplete?.(response.attachment);

        toast.success(`${file.name} uploaded successfully`);
        return response.attachment;
      } catch (error: any) {
        setUploadQueue((prev) =>
          prev.map((p) =>
            p.file === file
              ? { ...p, status: "error", error: error.message }
              : p
          )
        );
        toast.error(error.message || `Failed to upload ${file.name}`);
        return null;
      } finally {
        setIsUploading(false);
        // Remove from queue after a delay
        setTimeout(() => {
          setUploadQueue((prev) => prev.filter((p) => p.file !== file));
        }, 3000);
      }
    },
    [token, entityType, entityId, onUploadComplete]
  );

  const uploadFiles = useCallback(
    async (
      files: File[],
      category: AttachmentCategory = "other",
      description?: string
    ) => {
      const results: (Attachment | null)[] = [];
      for (const file of files) {
        const result = await uploadFile(file, category, description);
        results.push(result);
      }
      return results.filter((r): r is Attachment => r !== null);
    },
    [uploadFile]
  );

  const downloadFile = useCallback(
    async (attachmentId: string) => {
      if (!token) return;

      try {
        const { blob, filename } = await attachmentsAPI.download(
          token,
          attachmentId
        );

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Update download count locally
        setAttachments((prev) =>
          prev.map((a) =>
            a.id === attachmentId
              ? { ...a, download_count: a.download_count + 1 }
              : a
          )
        );
      } catch (error: any) {
        toast.error(error.message || "Failed to download file");
      }
    },
    [token]
  );

  const deleteAttachment = useCallback(
    async (attachmentId: string, permanent = false) => {
      if (!token) return;

      try {
        await attachmentsAPI.delete(token, attachmentId, permanent);
        setAttachments((prev) => prev.filter((a) => a.id !== attachmentId));
        onDeleteComplete?.(attachmentId);
        toast.success("Attachment deleted");
      } catch (error: any) {
        toast.error(error.message || "Failed to delete attachment");
      }
    },
    [token, onDeleteComplete]
  );

  const verifyIntegrity = useCallback(
    async (attachmentId: string) => {
      if (!token) return null;

      try {
        const result = await attachmentsAPI.verify(token, attachmentId);
        if (result.is_valid) {
          toast.success("File integrity verified");
        } else {
          toast.error(`Integrity check failed: ${result.message}`);
        }
        return result;
      } catch (error: any) {
        toast.error(error.message || "Failed to verify file integrity");
        return null;
      }
    },
    [token]
  );

  const clearUploadQueue = useCallback(() => {
    setUploadQueue([]);
  }, []);

  return {
    attachments,
    isLoading,
    isUploading,
    uploadQueue,
    fetchAttachments,
    uploadFile,
    uploadFiles,
    downloadFile,
    deleteAttachment,
    verifyIntegrity,
    clearUploadQueue,
  };
}

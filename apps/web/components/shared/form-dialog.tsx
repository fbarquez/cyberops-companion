"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DialogSize = "sm" | "md" | "lg" | "xl" | "full";

const sizeClasses: Record<DialogSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-2xl max-h-[90vh] overflow-y-auto",
  full: "max-w-4xl max-h-[90vh] overflow-y-auto",
};

interface FormDialogProps {
  /** Controlled open state */
  open: boolean;
  /** Callback when open state changes */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Dialog description (recommended for accessibility) */
  description?: string;
  /** Dialog size preset */
  size?: DialogSize;
  /** Form content */
  children: React.ReactNode;
  /** Submit button text */
  submitLabel?: string;
  /** Submit button text when loading */
  submitLoadingLabel?: string;
  /** Cancel button text */
  cancelLabel?: string;
  /** Loading state */
  isLoading?: boolean;
  /** Disable submit button */
  isSubmitDisabled?: boolean;
  /** Submit handler */
  onSubmit: () => void;
  /** Cancel handler (defaults to closing dialog) */
  onCancel?: () => void;
  /** Use destructive variant for submit button */
  destructive?: boolean;
  /** Optional trigger element (for uncontrolled usage) */
  trigger?: React.ReactNode;
  /** Additional class for DialogContent */
  className?: string;
}

/**
 * Standardized form dialog component.
 * Provides consistent structure, sizing, and behavior for all modal forms.
 *
 * @example
 * <FormDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   title="Add New Item"
 *   description="Fill in the details below."
 *   size="lg"
 *   isLoading={isPending}
 *   onSubmit={handleSubmit}
 * >
 *   <FormField label="Name" {...register("name")} />
 *   <FormField label="Description" type="textarea" {...register("description")} />
 * </FormDialog>
 */
export function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  size = "md",
  children,
  submitLabel = "Save",
  submitLoadingLabel = "Saving...",
  cancelLabel = "Cancel",
  isLoading = false,
  isSubmitDisabled = false,
  onSubmit,
  onCancel,
  destructive = false,
  trigger,
  className,
}: FormDialogProps) {
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onOpenChange(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent className={cn(sizeClasses[size], className)}>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            {description && (
              <DialogDescription>{description}</DialogDescription>
            )}
          </DialogHeader>

          <div className="py-4 space-y-4">{children}</div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isLoading}
            >
              {cancelLabel}
            </Button>
            <Button
              type="submit"
              variant={destructive ? "destructive" : "default"}
              disabled={isLoading || isSubmitDisabled}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {submitLoadingLabel}
                </>
              ) : (
                submitLabel
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  confirmLoadingLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel?: () => void;
  destructive?: boolean;
}

/**
 * Confirmation dialog for dangerous actions (delete, etc.)
 *
 * @example
 * <ConfirmDialog
 *   open={isDeleteOpen}
 *   onOpenChange={setIsDeleteOpen}
 *   title="Delete Item"
 *   description="Are you sure? This action cannot be undone."
 *   confirmLabel="Delete"
 *   destructive
 *   isLoading={isDeleting}
 *   onConfirm={handleDelete}
 * />
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  confirmLoadingLabel = "Processing...",
  cancelLabel = "Cancel",
  isLoading = false,
  onConfirm,
  onCancel,
  destructive = false,
}: ConfirmDialogProps) {
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={destructive ? "destructive" : "default"}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {confirmLoadingLabel}
              </>
            ) : (
              confirmLabel
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

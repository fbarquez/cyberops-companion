"use client";

import * as React from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface FormFieldBaseProps {
  label: string;
  error?: string;
  required?: boolean;
  description?: string;
  className?: string;
}

interface FormInputFieldProps
  extends FormFieldBaseProps,
    Omit<React.InputHTMLAttributes<HTMLInputElement>, "className"> {
  type?: "input";
}

interface FormTextareaFieldProps
  extends FormFieldBaseProps,
    Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> {
  type: "textarea";
  rows?: number;
}

interface FormSelectFieldProps extends FormFieldBaseProps {
  type: "select";
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  options: Array<{ value: string; label: string }>;
  disabled?: boolean;
}

export type FormFieldProps =
  | FormInputFieldProps
  | FormTextareaFieldProps
  | FormSelectFieldProps;

/**
 * Unified form field component with label, input, and error display.
 * Supports input, textarea, and select types.
 *
 * @example
 * // Input field
 * <FormField
 *   label="Email"
 *   type="input"
 *   placeholder="user@example.com"
 *   error={errors.email?.message}
 *   {...register("email")}
 * />
 *
 * @example
 * // Select field
 * <FormField
 *   type="select"
 *   label="Status"
 *   value={status}
 *   onValueChange={setStatus}
 *   options={[
 *     { value: "active", label: "Active" },
 *     { value: "inactive", label: "Inactive" },
 *   ]}
 * />
 *
 * @example
 * // Textarea field
 * <FormField
 *   type="textarea"
 *   label="Description"
 *   rows={4}
 *   error={errors.description?.message}
 *   {...register("description")}
 * />
 */
const FormField = React.forwardRef<
  HTMLInputElement | HTMLTextAreaElement | HTMLButtonElement,
  FormFieldProps
>((props, ref) => {
  const { label, error, required, description, className, type = "input" } = props;
  const id = React.useId();

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id} className="flex items-center gap-1">
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>

      {type === "input" && (
        <Input
          id={id}
          ref={ref as React.Ref<HTMLInputElement>}
          className={cn(error && "border-destructive focus-visible:ring-destructive")}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          {...(props as FormInputFieldProps)}
        />
      )}

      {type === "textarea" && (
        <Textarea
          id={id}
          ref={ref as React.Ref<HTMLTextAreaElement>}
          className={cn(error && "border-destructive focus-visible:ring-destructive")}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          rows={(props as FormTextareaFieldProps).rows || 3}
          {...(props as FormTextareaFieldProps)}
        />
      )}

      {type === "select" && (() => {
        const selectProps = props as FormSelectFieldProps;
        return (
          <Select
            value={selectProps.value}
            onValueChange={selectProps.onValueChange}
            disabled={selectProps.disabled}
          >
            <SelectTrigger
              id={id}
              className={cn(error && "border-destructive focus:ring-destructive")}
              aria-invalid={!!error}
            >
              <SelectValue placeholder={selectProps.placeholder || "Select..."} />
            </SelectTrigger>
            <SelectContent>
              {selectProps.options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      })()}

      {description && !error && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}

      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});
FormField.displayName = "FormField";

export { FormField };

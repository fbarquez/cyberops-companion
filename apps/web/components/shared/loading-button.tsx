"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface LoadingButtonProps extends ButtonProps {
  isLoading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
}

/**
 * Button with built-in loading state.
 * Shows a spinner and optional loading text when isLoading is true.
 *
 * @example
 * <LoadingButton
 *   isLoading={isPending}
 *   loadingText="Creating..."
 *   icon={<Plus className="h-4 w-4" />}
 * >
 *   Create Item
 * </LoadingButton>
 */
const LoadingButton = React.forwardRef<HTMLButtonElement, LoadingButtonProps>(
  ({
    children,
    isLoading = false,
    loadingText,
    icon,
    disabled,
    className,
    ...props
  }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(className)}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            {loadingText || children}
          </>
        ) : (
          <>
            {icon && <span className="mr-2">{icon}</span>}
            {children}
          </>
        )}
      </Button>
    );
  }
);
LoadingButton.displayName = "LoadingButton";

export { LoadingButton };

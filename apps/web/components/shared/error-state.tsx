import { cn } from "@/lib/utils";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "An error occurred while loading data. Please try again.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
    >
      <div className="rounded-full bg-destructive/10 p-4 mb-4">
        <AlertTriangle className="h-8 w-8 text-destructive" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}

interface TableErrorStateProps {
  colSpan?: number;
  message?: string;
  onRetry?: () => void;
}

export function TableErrorState({
  colSpan = 8,
  message = "Failed to load data",
  onRetry,
}: TableErrorStateProps) {
  return (
    <tr>
      <td colSpan={colSpan} className="text-center py-8">
        <div className="flex flex-col items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-destructive" />
          <span className="text-muted-foreground">{message}</span>
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm" className="mt-2">
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

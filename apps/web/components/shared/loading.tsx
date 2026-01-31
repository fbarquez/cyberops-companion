import { cn } from "@/lib/utils";
import { TableCell, TableRow } from "@/components/ui/table";

interface LoadingProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  text?: string;
}

/**
 * Skeleton component for loading placeholders
 */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
    />
  );
}

export function Loading({ className, size = "md", text }: LoadingProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  return (
    <div className={cn("flex flex-col items-center justify-center gap-2", className)}>
      <div
        className={cn(
          "animate-spin rounded-full border-2 border-primary border-t-transparent",
          sizeClasses[size]
        )}
      />
      {text && <span className="text-sm text-muted-foreground">{text}</span>}
    </div>
  );
}

export function PageLoading() {
  return (
    <div className="flex items-center justify-center h-full min-h-[400px]">
      <Loading size="lg" text="Loading..." />
    </div>
  );
}

export function CardLoading() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loading size="md" />
    </div>
  );
}

export function TableLoading({ colSpan = 8 }: { colSpan?: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="text-center py-8">
        <Loading size="sm" text="Loading..." />
      </td>
    </tr>
  );
}

interface TableSkeletonProps {
  columns: number;
  rows?: number;
  /** Column widths as Tailwind classes, e.g., ["w-[200px]", "w-[100px]", "flex-1"] */
  columnWidths?: string[];
}

/**
 * Skeleton loading state for tables.
 * Shows animated placeholder rows while data is loading.
 *
 * @example
 * {isLoading ? (
 *   <TableSkeleton columns={5} rows={5} />
 * ) : (
 *   data.map(item => <TableRow>...</TableRow>)
 * )}
 */
export function TableSkeleton({
  columns,
  rows = 5,
  columnWidths,
}: TableSkeletonProps) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <TableRow key={rowIndex}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <TableCell key={colIndex}>
              <Skeleton
                className={cn(
                  "h-4",
                  columnWidths?.[colIndex] || "w-full"
                )}
              />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

/**
 * Skeleton for card content
 */
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3 p-4">
      <Skeleton className="h-5 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}

/**
 * Skeleton for stat cards (used in dashboards)
 */
export function StatCardSkeleton() {
  return (
    <div className="p-6 space-y-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}

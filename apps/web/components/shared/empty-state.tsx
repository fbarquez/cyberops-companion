import { cn } from "@/lib/utils";
import { LucideIcon, Inbox, Plus, Search, FileX, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
    >
      <div className="rounded-full bg-muted p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
          {description}
        </p>
      )}
      {action && (
        <Button onClick={action.onClick} className="mt-4">
          {action.label}
        </Button>
      )}
    </div>
  );
}

interface TableEmptyStateProps {
  colSpan?: number;
  icon?: LucideIcon;
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Empty state for tables. Shows a centered message with optional icon and action.
 *
 * @example
 * <TableEmptyState
 *   colSpan={5}
 *   icon={Search}
 *   title="No results found"
 *   description="Try adjusting your search filters"
 * />
 */
export function TableEmptyState({
  colSpan = 8,
  icon: Icon = Inbox,
  title = "No data yet",
  description,
  action,
}: TableEmptyStateProps) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan} className="h-[200px]">
        <div className="flex flex-col items-center justify-center text-center py-8">
          <div className="rounded-full bg-muted p-3 mb-3">
            <Icon className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="font-medium text-muted-foreground">{title}</p>
          {description && (
            <p className="text-sm text-muted-foreground/70 mt-1 max-w-xs">
              {description}
            </p>
          )}
          {action && (
            <Button size="sm" onClick={action.onClick} className="mt-3">
              <Plus className="h-4 w-4 mr-2" />
              {action.label}
            </Button>
          )}
        </div>
      </TableCell>
    </TableRow>
  );
}

// ============================================================================
// Preset Empty States for common scenarios
// ============================================================================

/**
 * Empty state when no items exist yet (creation scenario)
 */
export function NoItemsEmptyState({
  itemName,
  onAdd,
  className,
}: {
  itemName: string;
  onAdd?: () => void;
  className?: string;
}) {
  return (
    <EmptyState
      icon={Inbox}
      title={`No ${itemName} yet`}
      description={`Get started by creating your first ${itemName.toLowerCase()}.`}
      action={onAdd ? { label: `Add ${itemName}`, onClick: onAdd } : undefined}
      className={className}
    />
  );
}

/**
 * Empty state when search/filter returns no results
 */
export function NoResultsEmptyState({
  className,
  onClear,
}: {
  className?: string;
  onClear?: () => void;
}) {
  return (
    <EmptyState
      icon={Search}
      title="No results found"
      description="Try adjusting your search or filter criteria."
      action={onClear ? { label: "Clear filters", onClick: onClear } : undefined}
      className={className}
    />
  );
}

/**
 * Empty state for errors
 */
export function ErrorEmptyState({
  message = "Something went wrong",
  onRetry,
  className,
}: {
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <EmptyState
      icon={AlertCircle}
      title="Error"
      description={message}
      action={onRetry ? { label: "Try again", onClick: onRetry } : undefined}
      className={className}
    />
  );
}

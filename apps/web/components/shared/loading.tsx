import { cn } from "@/lib/utils";

interface LoadingProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  text?: string;
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

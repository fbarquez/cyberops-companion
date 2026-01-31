"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface Column<T> {
  key: string;
  header: string;
  cell: (item: T) => React.ReactNode;
  className?: string;
  hideOnMobile?: boolean;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: Column<T>[];
  mobileCard: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  loading?: boolean;
  loadingMessage?: string;
  className?: string;
}

export function ResponsiveTable<T>({
  data,
  columns,
  mobileCard,
  keyExtractor,
  emptyMessage = "No data available",
  loading = false,
  loadingMessage = "Loading...",
  className,
}: ResponsiveTableProps<T>) {
  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {loadingMessage}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Desktop: Standard table */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              {columns
                .filter((col) => !col.hideOnMobile)
                .map((column) => (
                  <TableHead key={column.key} className={column.className}>
                    {column.header}
                  </TableHead>
                ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => (
              <TableRow key={keyExtractor(item)}>
                {columns
                  .filter((col) => !col.hideOnMobile)
                  .map((column) => (
                    <TableCell key={column.key} className={column.className}>
                      {column.cell(item)}
                    </TableCell>
                  ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile: Card stack */}
      <div className="md:hidden space-y-3">
        {data.map((item, index) => (
          <Card key={keyExtractor(item)} className="overflow-hidden">
            <CardContent className="p-4">
              {mobileCard(item, index)}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Helper component for mobile card rows
interface MobileCardRowProps {
  label: string;
  children: React.ReactNode;
  className?: string;
}

export function MobileCardRow({ label, children, className }: MobileCardRowProps) {
  return (
    <div className={cn("flex items-center justify-between py-1", className)}>
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{children}</span>
    </div>
  );
}

// Helper component for mobile card header
interface MobileCardHeaderProps {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export function MobileCardHeader({ title, subtitle, badge, actions }: MobileCardHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium truncate">{title}</span>
          {badge}
        </div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1 truncate">{subtitle}</p>
        )}
      </div>
      {actions && <div className="ml-2 flex-shrink-0">{actions}</div>}
    </div>
  );
}

// Simple wrapper for tables that just need horizontal scroll on mobile
interface ScrollableTableProps {
  children: React.ReactNode;
  className?: string;
}

export function ScrollableTable({ children, className }: ScrollableTableProps) {
  return (
    <div className={cn("overflow-x-auto -mx-4 md:mx-0", className)}>
      <div className="min-w-[600px] md:min-w-0 px-4 md:px-0">
        {children}
      </div>
    </div>
  );
}

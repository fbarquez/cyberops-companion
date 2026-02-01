"use client";

import { Building2, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTenantStore, Organization } from "@/stores/tenant-store";
import { cn } from "@/lib/utils";

interface TenantSelectorProps {
  className?: string;
}

export function TenantSelector({ className }: TenantSelectorProps) {
  const { currentTenant, availableTenants, switchTenant, isLoading } = useTenantStore();

  // Don't render if user has only one organization
  if (availableTenants.length <= 1) {
    return null;
  }

  const handleSwitch = async (tenant: Organization) => {
    if (tenant.id === currentTenant?.id) return;
    try {
      await switchTenant(tenant.id);
    } catch (error) {
      console.error("Failed to switch tenant:", error);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn("gap-2 max-w-[200px]", className)}
          disabled={isLoading}
        >
          <Building2 className="h-4 w-4 flex-shrink-0" />
          <span className="truncate hidden sm:inline">
            {currentTenant?.name || "Select Organization"}
          </span>
          <ChevronDown className="h-3 w-3 flex-shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[240px]">
        <DropdownMenuLabel>Switch Organization</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {availableTenants.map((tenant) => (
          <DropdownMenuItem
            key={tenant.id}
            onClick={() => handleSwitch(tenant)}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex flex-col">
              <span className="font-medium">{tenant.name}</span>
              <span className="text-xs text-muted-foreground capitalize">
                {tenant.org_role}
              </span>
            </div>
            {currentTenant?.id === tenant.id && (
              <Check className="h-4 w-4 text-primary" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

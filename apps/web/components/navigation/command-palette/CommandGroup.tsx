"use client";

interface CommandGroupProps {
  label: string;
  children: React.ReactNode;
}

export function CommandGroup({ label, children }: CommandGroupProps) {
  return (
    <div className="py-2">
      <div className="px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

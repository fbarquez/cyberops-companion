"use client";

import { Search } from "lucide-react";

interface CommandSearchProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function CommandSearch({ value, onChange, placeholder = "Search..." }: CommandSearchProps) {
  return (
    <div className="flex items-center border-b px-4 py-3">
      <Search className="mr-3 h-4 w-4 text-muted-foreground" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        autoFocus
      />
      <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
        ESC
      </kbd>
    </div>
  );
}

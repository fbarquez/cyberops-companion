"use client";

import { useRouter } from "next/navigation";
import { Moon, Sun, Globe, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUIStore } from "@/stores/ui-store";

interface HeaderProps {
  title?: string;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  backHref?: string;
}

export function Header({ title, children, actions, backHref }: HeaderProps) {
  const router = useRouter();
  const { theme, setTheme, language, setLanguage } = useUIStore();

  return (
    <header className="flex items-center justify-between h-16 px-6 border-b bg-card">
      <div className="flex items-center gap-4">
        {backHref && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(backHref)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
        )}
        {title && <h1 className="text-xl font-semibold">{title}</h1>}
      </div>

      <div className="flex items-center gap-4">
        {/* Page-specific actions */}
        {actions || children}

        {/* Language Switcher */}
        <Select value={language} onValueChange={(v) => setLanguage(v as "en" | "de")}>
          <SelectTrigger className="w-24">
            <Globe className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="en">EN</SelectItem>
            <SelectItem value="de">DE</SelectItem>
          </SelectContent>
        </Select>

        {/* Theme Switcher */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </header>
  );
}

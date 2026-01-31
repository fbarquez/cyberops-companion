"use client";

import { useRouter } from "next/navigation";
import { Moon, Sun, Globe, ArrowLeft, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUIStore } from "@/stores/ui-store";
import { NotificationBell } from "./notification-bell";

interface HeaderProps {
  title?: string;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  backHref?: string;
}

export function Header({ title, children, actions, backHref }: HeaderProps) {
  const router = useRouter();
  const { theme, setTheme, language, setLanguage, setSidebarOpen } = useUIStore();

  return (
    <header className="flex items-center justify-between h-14 md:h-16 px-4 md:px-6 border-b bg-card">
      <div className="flex items-center gap-2 md:gap-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {backHref && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(backHref)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
        )}
        {title && (
          <h1 className="text-lg md:text-xl font-semibold truncate max-w-[150px] sm:max-w-none">
            {title}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        {/* Page-specific actions - hidden on mobile for cleaner UI */}
        <div className="hidden sm:flex items-center gap-2">
          {actions || children}
        </div>

        {/* Notification Bell */}
        <NotificationBell />

        {/* Language Switcher - icon only on mobile */}
        <Select value={language} onValueChange={(v) => setLanguage(v as "en" | "de")}>
          <SelectTrigger className="w-10 md:w-24">
            <Globe className="h-4 w-4 md:mr-2" />
            <span className="hidden md:inline">
              <SelectValue />
            </span>
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

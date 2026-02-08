"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Shield,
  Menu,
  X,
  Github
} from "lucide-react";

export function LandingNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">ISORA</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#modules" className="text-muted-foreground hover:text-foreground transition-colors">
              Module
            </Link>
            <Link href="https://github.com/fbarquez/cyberops-companion" target="_blank" className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1">
              <Github className="h-4 w-4" />
              GitHub
            </Link>
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Button variant="ghost" asChild>
              <Link href="/login">Anmelden</Link>
            </Button>
            <Button asChild>
              <Link href="/register">Kostenlos starten</Link>
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <div className="flex flex-col gap-4">
              <Link
                href="#features"
                className="text-muted-foreground hover:text-foreground transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Features
              </Link>
              <Link
                href="#modules"
                className="text-muted-foreground hover:text-foreground transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Module
              </Link>
              <Link
                href="https://github.com/fbarquez/cyberops-companion"
                target="_blank"
                className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Github className="h-4 w-4" />
                GitHub
              </Link>
              <div className="flex flex-col gap-2 pt-4 border-t">
                <Button variant="outline" asChild className="w-full">
                  <Link href="/login">Anmelden</Link>
                </Button>
                <Button asChild className="w-full">
                  <Link href="/register">Kostenlos starten</Link>
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

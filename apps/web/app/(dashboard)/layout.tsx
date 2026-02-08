"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar } from "@/components/navigation/sidebar";
import { MobileSidebar } from "@/components/shared/mobile-sidebar";
import { CommandPalette } from "@/components/navigation/command-palette";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { PageLoading } from "@/components/shared/loading";
import { CopilotProvider } from "@/components/copilot/CopilotProvider";
import { CopilotButton } from "@/components/copilot/CopilotButton";
import { CopilotChat } from "@/components/copilot/CopilotChat";
import { useCommandPaletteShortcut, useGlobalShortcuts } from "@/hooks/useKeyboardShortcuts";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, loadUser } = useAuthStore();
  const { isComplete: isOnboardingComplete } = useOnboardingStore();

  // Check if we're on the onboarding page
  const isOnboardingPage = pathname === "/onboarding";

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    // Redirect to onboarding if not complete (only for authenticated users)
    // But don't redirect if we're already on the onboarding page
    if (!isLoading && isAuthenticated && !isOnboardingComplete && !isOnboardingPage) {
      router.push("/onboarding");
    }
  }, [isAuthenticated, isLoading, isOnboardingComplete, isOnboardingPage, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <PageLoading />
      </div>
    );
  }

  // Allow onboarding page to render even if onboarding is not complete
  if (isOnboardingPage) {
    return (
      <div className="min-h-screen bg-background">
        {children}
      </div>
    );
  }

  // Show loading while checking onboarding status for other pages
  if (!isOnboardingComplete) {
    return (
      <div className="flex items-center justify-center h-screen">
        <PageLoading />
      </div>
    );
  }

  return (
    <CopilotProvider>
      <DashboardContent>{children}</DashboardContent>
    </CopilotProvider>
  );
}

function DashboardContent({ children }: { children: React.ReactNode }) {
  // Initialize keyboard shortcuts
  useCommandPaletteShortcut();
  useGlobalShortcuts();

  return (
    <>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <MobileSidebar />
        <main className="flex-1 overflow-y-auto bg-background w-full">
          {children}
        </main>
      </div>
      {/* Command Palette */}
      <CommandPalette />
      {/* AI Copilot - Outside the overflow container for proper fixed positioning */}
      <CopilotButton />
      <CopilotChat />
    </>
  );
}

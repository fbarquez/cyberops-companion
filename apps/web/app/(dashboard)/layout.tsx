"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/shared/sidebar";
import { MobileSidebar } from "@/components/shared/mobile-sidebar";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { PageLoading } from "@/components/shared/loading";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isLoading, loadUser } = useAuthStore();
  const { isComplete: isOnboardingComplete } = useOnboardingStore();

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
    if (!isLoading && isAuthenticated && !isOnboardingComplete) {
      router.push("/onboarding");
    }
  }, [isAuthenticated, isLoading, isOnboardingComplete, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <PageLoading />
      </div>
    );
  }

  // Show loading while checking onboarding status
  if (!isOnboardingComplete) {
    return (
      <div className="flex items-center justify-center h-screen">
        <PageLoading />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <MobileSidebar />
      <main className="flex-1 overflow-y-auto bg-background w-full">
        {children}
      </main>
    </div>
  );
}

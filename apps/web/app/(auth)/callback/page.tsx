"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Shield, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ssoAPI } from "@/lib/api-client";
import { saveTokens } from "@/lib/auth";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useTranslations();
  const { loadUser } = useAuthStore();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");
  const [isNewUser, setIsNewUser] = useState(false);

  useEffect(() => {
    handleCallback();
  }, [searchParams]);

  const handleCallback = async () => {
    try {
      // Get OAuth parameters from URL
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      // Check for OAuth error
      if (error) {
        throw new Error(errorDescription || error);
      }

      // Validate required parameters
      if (!code || !state) {
        throw new Error(t("auth.ssoMissingParams"));
      }

      // Validate state matches what we stored
      const storedState = sessionStorage.getItem("sso_state");
      const storedProvider = sessionStorage.getItem("sso_provider");

      if (state !== storedState) {
        throw new Error(t("auth.ssoInvalidState"));
      }

      if (!storedProvider) {
        throw new Error(t("auth.ssoMissingProvider"));
      }

      // Clear stored state
      sessionStorage.removeItem("sso_state");
      sessionStorage.removeItem("sso_provider");

      // Exchange code for tokens
      const response = await ssoAPI.callback(storedProvider, code, state);

      // Save tokens
      saveTokens({
        access_token: response.access_token,
        refresh_token: response.refresh_token,
      });

      // Load user into store
      await loadUser();

      // Set success state
      setIsNewUser(response.user.is_new_user);
      setStatus("success");
      setMessage(
        response.user.is_new_user
          ? t("auth.ssoWelcomeNew", { name: response.user.full_name })
          : t("auth.ssoWelcomeBack", { name: response.user.full_name })
      );

      // Redirect after brief delay
      setTimeout(() => {
        router.push(response.user.is_new_user ? "/onboarding" : "/incidents");
      }, 1500);
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || t("auth.ssoError"));
    }
  };

  const handleRetry = () => {
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Shield className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl">{t("app.title")}</CardTitle>
          <CardDescription>
            {status === "loading" && t("auth.ssoProcessing")}
            {status === "success" && t("auth.ssoSuccess")}
            {status === "error" && t("auth.ssoFailed")}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-4">
          {status === "loading" && (
            <>
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground text-center">
                {t("auth.ssoVerifying")}
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="h-8 w-8 text-green-500" />
              <p className="text-sm text-center">{message}</p>
              <p className="text-xs text-muted-foreground">
                {t("auth.ssoRedirecting")}
              </p>
            </>
          )}

          {status === "error" && (
            <>
              <AlertCircle className="h-8 w-8 text-destructive" />
              <p className="text-sm text-center text-destructive">{message}</p>
              <Button onClick={handleRetry} className="mt-4">
                {t("auth.backToLogin")}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { incidentsAPI } from "@/lib/api-client";

const incidentSchema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().optional(),
  severity: z.enum(["critical", "high", "medium", "low", "informational"]),
  detection_source: z
    .enum([
      "user_report",
      "edr_alert",
      "siem_alert",
      "anomaly_detection",
      "external_notification",
      "scheduled_scan",
      "other",
    ])
    .optional(),
  initial_indicator: z.string().optional(),
  analyst_name: z.string().optional(),
  analyst_email: z.string().email().optional().or(z.literal("")),
});

type IncidentFormData = z.infer<typeof incidentSchema>;

export default function NewIncidentPage() {
  const router = useRouter();
  const { t } = useTranslations();
  const { token, user } = useAuthStore();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<IncidentFormData>({
    resolver: zodResolver(incidentSchema),
    defaultValues: {
      severity: "medium",
      analyst_name: user?.full_name,
      analyst_email: user?.email,
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: IncidentFormData) => incidentsAPI.create(token!, data),
    onSuccess: (data: any) => {
      router.push(`/incidents/${data.id}`);
    },
  });

  const onSubmit = (data: IncidentFormData) => {
    createMutation.mutate(data);
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={t("incidents.create")} />

      <div className="p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>{t("incidents.details")}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  {...register("title")}
                  placeholder="Brief description of the incident"
                />
                {errors.title && (
                  <p className="text-sm text-destructive">{errors.title.message}</p>
                )}
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  {...register("description")}
                  placeholder="Detailed description of the incident"
                  rows={4}
                />
              </div>

              {/* Severity */}
              <div className="space-y-2">
                <Label>Severity *</Label>
                <Select
                  value={watch("severity")}
                  onValueChange={(v) => setValue("severity", v as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="critical">{t("severity.critical")}</SelectItem>
                    <SelectItem value="high">{t("severity.high")}</SelectItem>
                    <SelectItem value="medium">{t("severity.medium")}</SelectItem>
                    <SelectItem value="low">{t("severity.low")}</SelectItem>
                    <SelectItem value="informational">
                      {t("severity.informational")}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Detection Source */}
              <div className="space-y-2">
                <Label>Detection Source</Label>
                <Select
                  value={watch("detection_source") || ""}
                  onValueChange={(v) => setValue("detection_source", v as any)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select detection source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user_report">User Report</SelectItem>
                    <SelectItem value="edr_alert">EDR Alert</SelectItem>
                    <SelectItem value="siem_alert">SIEM Alert</SelectItem>
                    <SelectItem value="anomaly_detection">Anomaly Detection</SelectItem>
                    <SelectItem value="external_notification">
                      External Notification
                    </SelectItem>
                    <SelectItem value="scheduled_scan">Scheduled Scan</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Initial Indicator */}
              <div className="space-y-2">
                <Label htmlFor="initial_indicator">Initial Indicator</Label>
                <Textarea
                  id="initial_indicator"
                  {...register("initial_indicator")}
                  placeholder="Initial indicators of compromise (IOCs)"
                  rows={2}
                />
              </div>

              {/* Analyst Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="analyst_name">Analyst Name</Label>
                  <Input id="analyst_name" {...register("analyst_name")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="analyst_email">Analyst Email</Label>
                  <Input
                    id="analyst_email"
                    type="email"
                    {...register("analyst_email")}
                  />
                </div>
              </div>

              {/* Submit */}
              <div className="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                >
                  {t("common.cancel")}
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? t("common.loading") : t("incidents.create")}
                </Button>
              </div>

              {createMutation.isError && (
                <p className="text-sm text-destructive">
                  {t("common.error")}
                </p>
              )}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

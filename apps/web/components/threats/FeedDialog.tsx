"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { threatsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type { ThreatFeed } from "./FeedsList";

interface FeedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  feed: ThreatFeed | null;
  mode: "create" | "edit";
}

const feedTypeOptions = [
  { value: "misp", label: "MISP", placeholder: "https://misp.example.com" },
  { value: "otx", label: "AlienVault OTX", placeholder: "https://otx.alienvault.com" },
  { value: "virustotal", label: "VirusTotal", placeholder: "https://www.virustotal.com" },
  { value: "opencti", label: "OpenCTI", placeholder: "https://opencti.example.com" },
  { value: "taxii", label: "TAXII", placeholder: "https://taxii.example.com" },
];

const syncIntervalOptions = [
  { value: 15, label: "Every 15 minutes" },
  { value: 30, label: "Every 30 minutes" },
  { value: 60, label: "Every hour" },
  { value: 120, label: "Every 2 hours" },
  { value: 360, label: "Every 6 hours" },
  { value: 720, label: "Every 12 hours" },
  { value: 1440, label: "Every 24 hours" },
];

export function FeedDialog({ open, onOpenChange, feed, mode }: FeedDialogProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    name: "",
    feed_type: "misp",
    base_url: "",
    api_key: "",
    enabled: true,
    sync_interval_minutes: 60,
    verify_ssl: true,
  });

  useEffect(() => {
    if (feed && mode === "edit") {
      setFormData({
        name: feed.name,
        feed_type: feed.feed_type,
        base_url: feed.base_url || "",
        api_key: "", // Don't prefill API key for security
        enabled: feed.enabled,
        sync_interval_minutes: feed.sync_interval_minutes,
        verify_ssl: true,
      });
    } else {
      setFormData({
        name: "",
        feed_type: "misp",
        base_url: "",
        api_key: "",
        enabled: true,
        sync_interval_minutes: 60,
        verify_ssl: true,
      });
    }
  }, [feed, mode, open]);

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      threatsAPI.createFeed(token!, {
        name: data.name,
        feed_type: data.feed_type,
        base_url: data.base_url || undefined,
        enabled: data.enabled,
        sync_interval_minutes: data.sync_interval_minutes,
        config: {
          api_key: data.api_key || undefined,
          verify_ssl: data.verify_ssl,
        },
      }),
    onSuccess: () => {
      toast.success("Feed created successfully");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create feed");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      threatsAPI.updateFeed(token!, feed!.id, {
        name: data.name,
        base_url: data.base_url || undefined,
        enabled: data.enabled,
        sync_interval_minutes: data.sync_interval_minutes,
        config: {
          ...(data.api_key ? { api_key: data.api_key } : {}),
          verify_ssl: data.verify_ssl,
        },
      }),
    onSuccess: () => {
      toast.success("Feed updated successfully");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update feed");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error("Name is required");
      return;
    }

    if (mode === "create") {
      createMutation.mutate(formData);
    } else {
      updateMutation.mutate(formData);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const selectedFeedType = feedTypeOptions.find(f => f.value === formData.feed_type);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {mode === "create" ? "Add Threat Feed" : "Edit Threat Feed"}
            </DialogTitle>
            <DialogDescription>
              {mode === "create"
                ? "Configure a new threat intelligence feed to automatically import IOCs."
                : "Update the feed configuration."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="My MISP Feed"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            {/* Feed Type */}
            <div className="space-y-2">
              <Label htmlFor="feed_type">Feed Type</Label>
              <Select
                value={formData.feed_type}
                onValueChange={(value) => setFormData({ ...formData, feed_type: value })}
                disabled={mode === "edit"}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select feed type" />
                </SelectTrigger>
                <SelectContent>
                  {feedTypeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {mode === "edit" && (
                <p className="text-xs text-muted-foreground">
                  Feed type cannot be changed after creation
                </p>
              )}
            </div>

            {/* Base URL */}
            <div className="space-y-2">
              <Label htmlFor="base_url">Base URL</Label>
              <Input
                id="base_url"
                placeholder={selectedFeedType?.placeholder || "https://..."}
                value={formData.base_url}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              />
            </div>

            {/* API Key */}
            <div className="space-y-2">
              <Label htmlFor="api_key">
                API Key {mode === "edit" && "(leave empty to keep current)"}
              </Label>
              <Input
                id="api_key"
                type="password"
                placeholder={mode === "edit" ? "********" : "Enter API key"}
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              />
            </div>

            {/* Sync Interval */}
            <div className="space-y-2">
              <Label htmlFor="sync_interval">Sync Interval</Label>
              <Select
                value={formData.sync_interval_minutes.toString()}
                onValueChange={(value) => setFormData({ ...formData, sync_interval_minutes: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select interval" />
                </SelectTrigger>
                <SelectContent>
                  {syncIntervalOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value.toString()}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* SSL Verification */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Verify SSL</Label>
                <p className="text-xs text-muted-foreground">
                  Verify SSL certificates when connecting
                </p>
              </div>
              <Switch
                checked={formData.verify_ssl}
                onCheckedChange={(checked) => setFormData({ ...formData, verify_ssl: checked })}
              />
            </div>

            {/* Enabled */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enabled</Label>
                <p className="text-xs text-muted-foreground">
                  Enable automatic synchronization
                </p>
              </div>
              <Switch
                checked={formData.enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading
                ? mode === "create"
                  ? "Creating..."
                  : "Saving..."
                : mode === "create"
                ? "Create Feed"
                : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

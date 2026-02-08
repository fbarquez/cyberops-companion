"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Rss,
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Pencil,
  Trash2,
  Play,
  Zap,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { threatsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { FeedDialog } from "./FeedDialog";

export interface ThreatFeed {
  id: string;
  name: string;
  feed_type: "misp" | "otx" | "virustotal" | "opencti" | "taxii";
  base_url?: string;
  enabled: boolean;
  sync_interval_minutes: number;
  last_sync?: string;
  last_sync_count?: number;
  last_sync_status?: "success" | "failed" | "in_progress";
  last_error?: string;
  total_iocs_imported: number;
  created_at: string;
  updated_at: string;
}

const feedTypeLabels: Record<string, string> = {
  misp: "MISP",
  otx: "AlienVault OTX",
  virustotal: "VirusTotal",
  opencti: "OpenCTI",
  taxii: "TAXII",
};

const feedTypeColors: Record<string, string> = {
  misp: "bg-blue-500",
  otx: "bg-green-500",
  virustotal: "bg-purple-500",
  opencti: "bg-orange-500",
  taxii: "bg-cyan-500",
};

export function FeedsList() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [enabledFilter, setEnabledFilter] = useState<string>("all");
  const [showFeedDialog, setShowFeedDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [selectedFeed, setSelectedFeed] = useState<ThreatFeed | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [feedToDelete, setFeedToDelete] = useState<ThreatFeed | null>(null);
  const [syncingFeedId, setSyncingFeedId] = useState<string | null>(null);
  const [testingFeedId, setTestingFeedId] = useState<string | null>(null);

  const { data: feedsData, isLoading, refetch } = useQuery({
    queryKey: ["feeds", searchTerm, typeFilter, enabledFilter],
    queryFn: () =>
      threatsAPI.listFeeds(token!, {
        search: searchTerm || undefined,
        feed_type: typeFilter !== "all" ? typeFilter : undefined,
        enabled: enabledFilter !== "all" ? enabledFilter === "enabled" : undefined,
      }) as Promise<{ feeds: ThreatFeed[]; total: number }>,
    enabled: !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => threatsAPI.deleteFeed(token!, id),
    onSuccess: () => {
      toast.success("Feed deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      setDeleteDialogOpen(false);
      setFeedToDelete(null);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to delete feed");
    },
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => threatsAPI.syncFeed(token!, id),
    onMutate: (id) => {
      setSyncingFeedId(id);
    },
    onSuccess: (data: any) => {
      toast.success(`Sync completed: ${data.iocs_new || 0} new IOCs imported`);
      queryClient.invalidateQueries({ queryKey: ["feeds"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Sync failed");
    },
    onSettled: () => {
      setSyncingFeedId(null);
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => threatsAPI.testFeedConnection(token!, id),
    onMutate: (id) => {
      setTestingFeedId(id);
    },
    onSuccess: (data: any) => {
      if (data.success) {
        toast.success("Connection test successful");
      } else {
        toast.error(`Connection test failed: ${data.error || "Unknown error"}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.message || "Connection test failed");
    },
    onSettled: () => {
      setTestingFeedId(null);
    },
  });

  const handleCreateClick = () => {
    setDialogMode("create");
    setSelectedFeed(null);
    setShowFeedDialog(true);
  };

  const handleEditClick = (feed: ThreatFeed) => {
    setDialogMode("edit");
    setSelectedFeed(feed);
    setShowFeedDialog(true);
  };

  const handleDeleteClick = (feed: ThreatFeed) => {
    setFeedToDelete(feed);
    setDeleteDialogOpen(true);
  };

  const handleSyncClick = (feed: ThreatFeed) => {
    syncMutation.mutate(feed.id);
  };

  const handleTestClick = (feed: ThreatFeed) => {
    testMutation.mutate(feed.id);
  };

  const formatLastSync = (dateString?: string) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const feeds = feedsData?.feeds || [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search feeds..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Feed Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="misp">MISP</SelectItem>
            <SelectItem value="otx">AlienVault OTX</SelectItem>
            <SelectItem value="virustotal">VirusTotal</SelectItem>
            <SelectItem value="opencti">OpenCTI</SelectItem>
            <SelectItem value="taxii">TAXII</SelectItem>
          </SelectContent>
        </Select>
        <Select value={enabledFilter} onValueChange={setEnabledFilter}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="enabled">Enabled</SelectItem>
            <SelectItem value="disabled">Disabled</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="icon" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button onClick={handleCreateClick}>
          <Plus className="h-4 w-4 mr-2" />
          Add Feed
        </Button>
      </div>

      {/* Feeds List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading feeds...</div>
          ) : feeds.length > 0 ? (
            <div className="divide-y">
              {feeds.map((feed) => (
                <div
                  key={feed.id}
                  className="flex items-center justify-between p-4 hover:bg-muted/50"
                >
                  <div className="flex items-center gap-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-full ${feedTypeColors[feed.feed_type] || "bg-gray-500"}`}>
                      <Rss className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {feed.name}
                        <Badge variant="outline" className="text-xs">
                          {feedTypeLabels[feed.feed_type] || feed.feed_type.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                        {feed.base_url && (
                          <span className="truncate max-w-[200px]">{feed.base_url}</span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Every {feed.sync_interval_minutes}m
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Last Sync Status */}
                    <div className="text-right min-w-[120px]">
                      <div className="flex items-center gap-1 justify-end text-sm">
                        {feed.last_sync_status === "success" && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {feed.last_sync_status === "failed" && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <XCircle className="h-4 w-4 text-red-500" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{feed.last_error || "Sync failed"}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        {feed.last_sync_status === "in_progress" && (
                          <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                        )}
                        <span>{formatLastSync(feed.last_sync)}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {feed.total_iocs_imported.toLocaleString()} IOCs total
                      </div>
                    </div>

                    {/* Enabled Badge */}
                    <Badge variant={feed.enabled ? "default" : "secondary"}>
                      {feed.enabled ? "Enabled" : "Disabled"}
                    </Badge>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-1">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleSyncClick(feed)}
                              disabled={syncingFeedId === feed.id || !feed.enabled}
                            >
                              {syncingFeedId === feed.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Sync Now</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleTestClick(feed)}
                              disabled={testingFeedId === feed.id}
                            >
                              {testingFeedId === feed.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Zap className="h-4 w-4" />
                              )}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Test Connection</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditClick(feed)}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDeleteClick(feed)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              <Rss className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No threat feeds configured</p>
              <p className="text-sm mt-1">Add a feed to start importing IOCs automatically</p>
              <Button className="mt-4" variant="outline" onClick={handleCreateClick}>
                <Plus className="h-4 w-4 mr-2" />
                Add Threat Feed
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Feed Dialog */}
      <FeedDialog
        open={showFeedDialog}
        onOpenChange={setShowFeedDialog}
        feed={selectedFeed}
        mode={dialogMode}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Threat Feed</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{feedToDelete?.name}"? This will stop automatic syncing but won't delete imported IOCs.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => feedToDelete && deleteMutation.mutate(feedToDelete.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

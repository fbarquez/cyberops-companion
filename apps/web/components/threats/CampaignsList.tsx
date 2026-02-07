"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Target,
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
  Link2,
  Users,
  Calendar,
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
import { toast } from "sonner";
import { threatsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { ThreatLevelBadge, ActiveStatusBadge } from "./ThreatBadges";
import { CampaignDialog } from "./CampaignDialog";

interface Campaign {
  id: string;
  name: string;
  campaign_type?: string;
  threat_level: "critical" | "high" | "medium" | "low" | "unknown";
  description?: string;
  objectives?: string;
  target_sectors: string[];
  target_countries: string[];
  mitre_techniques: string[];
  attack_vectors: string[];
  malware_used: string[];
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  ioc_count: number;
  actor_count: number;
  created_at: string;
}

const CAMPAIGN_TYPES = [
  { value: "phishing", label: "Phishing" },
  { value: "ransomware", label: "Ransomware" },
  { value: "data_exfiltration", label: "Data Exfiltration" },
  { value: "espionage", label: "Espionage" },
  { value: "ddos", label: "DDoS" },
  { value: "supply_chain", label: "Supply Chain" },
  { value: "credential_theft", label: "Credential Theft" },
  { value: "malware_distribution", label: "Malware Distribution" },
];

function formatDate(dateString?: string): string {
  if (!dateString) return "-";
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function getCampaignTypeLabel(type?: string): string {
  if (!type) return "Unknown";
  const found = CAMPAIGN_TYPES.find((t) => t.value === type);
  return found ? found.label : type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

export function CampaignsList() {
  const { token } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [showCampaignDialog, setShowCampaignDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [campaignToDelete, setCampaignToDelete] = useState<Campaign | null>(null);

  const { data: campaignsData, isLoading, refetch } = useQuery({
    queryKey: ["campaigns", searchTerm, typeFilter, activeFilter],
    queryFn: () =>
      threatsAPI.listCampaigns(token!, {
        search: searchTerm || undefined,
        campaign_type: typeFilter !== "all" ? typeFilter : undefined,
        is_active: activeFilter !== "all" ? activeFilter === "active" : undefined,
      }) as Promise<{ campaigns: Campaign[]; total: number }>,
    enabled: !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/threats/campaigns/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      }),
    onSuccess: () => {
      toast.success("Campaign deleted");
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      setDeleteDialogOpen(false);
      setCampaignToDelete(null);
    },
    onError: () => {
      toast.error("Failed to delete campaign");
    },
  });

  const handleCreateClick = () => {
    setDialogMode("create");
    setSelectedCampaign(null);
    setShowCampaignDialog(true);
  };

  const handleEditClick = (campaign: Campaign) => {
    setDialogMode("edit");
    setSelectedCampaign(campaign);
    setShowCampaignDialog(true);
  };

  const handleDeleteClick = (campaign: Campaign) => {
    setCampaignToDelete(campaign);
    setDeleteDialogOpen(true);
  };

  const handleViewClick = (campaign: Campaign) => {
    router.push(`/threats/campaigns/${campaign.id}`);
  };

  const campaigns = campaignsData?.campaigns || [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Campaign Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {CAMPAIGN_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={activeFilter} onValueChange={setActiveFilter}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="icon" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button onClick={handleCreateClick}>
          <Plus className="h-4 w-4 mr-2" />
          Add Campaign
        </Button>
      </div>

      {/* Campaigns List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading campaigns...</div>
          ) : campaigns.length > 0 ? (
            <div className="divide-y">
              {campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="flex items-center justify-between p-4 hover:bg-muted/50 cursor-pointer"
                  onClick={() => handleViewClick(campaign)}
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      <Target className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {campaign.name}
                        {campaign.campaign_type && (
                          <Badge variant="outline" className="text-xs">
                            {getCampaignTypeLabel(campaign.campaign_type)}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(campaign.start_date)}
                          {campaign.end_date && ` - ${formatDate(campaign.end_date)}`}
                        </span>
                        {campaign.attack_vectors.length > 0 && (
                          <span className="flex items-center gap-1">
                            {campaign.attack_vectors.slice(0, 2).map((v) => (
                              <Badge key={v} variant="secondary" className="text-xs">
                                {v}
                              </Badge>
                            ))}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <ThreatLevelBadge level={campaign.threat_level} />

                    <div className="text-right text-sm text-muted-foreground min-w-[100px]">
                      <div className="flex items-center gap-1 justify-end">
                        <Users className="h-3 w-3" />
                        {campaign.actor_count} Actors
                      </div>
                      <div className="flex items-center gap-1 justify-end">
                        <Link2 className="h-3 w-3" />
                        {campaign.ioc_count} IOCs
                      </div>
                    </div>

                    <ActiveStatusBadge isActive={campaign.is_active} />

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewClick(campaign); }}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleEditClick(campaign); }}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={(e) => { e.stopPropagation(); handleDeleteClick(campaign); }}
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
              <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No campaigns found</p>
              <Button className="mt-4" variant="outline" onClick={handleCreateClick}>
                <Plus className="h-4 w-4 mr-2" />
                Add Campaign
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Campaign Dialog */}
      <CampaignDialog
        open={showCampaignDialog}
        onOpenChange={setShowCampaignDialog}
        campaign={selectedCampaign}
        mode={dialogMode}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Campaign</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{campaignToDelete?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => campaignToDelete && deleteMutation.mutate(campaignToDelete.id)}
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

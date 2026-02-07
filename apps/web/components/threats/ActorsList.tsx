"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  Users,
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
  Link2,
  Globe,
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
import {
  ThreatLevelBadge,
  MotivationBadge,
  SophisticationBadge,
  ActiveStatusBadge,
} from "./ThreatBadges";
import { ActorDialog } from "./ActorDialog";

interface ThreatActor {
  id: string;
  name: string;
  aliases: string[];
  motivation: "financial" | "espionage" | "hacktivism" | "destruction" | "unknown";
  sophistication: "apt" | "organized_crime" | "script_kiddie" | "insider" | "unknown";
  threat_level: "critical" | "high" | "medium" | "low" | "unknown";
  description?: string;
  country_of_origin?: string;
  target_sectors: string[];
  target_countries: string[];
  mitre_techniques: string[];
  tools_used: string[];
  first_seen?: string;
  last_seen?: string;
  is_active: boolean;
  ioc_count: number;
  campaign_count: number;
  created_at: string;
}

export function ActorsList() {
  const { token } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [motivationFilter, setMotivationFilter] = useState<string>("all");
  const [sophisticationFilter, setSophisticationFilter] = useState<string>("all");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [showActorDialog, setShowActorDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [selectedActor, setSelectedActor] = useState<ThreatActor | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actorToDelete, setActorToDelete] = useState<ThreatActor | null>(null);

  const { data: actorsData, isLoading, refetch } = useQuery({
    queryKey: ["actors", searchTerm, motivationFilter, sophisticationFilter, activeFilter],
    queryFn: () =>
      threatsAPI.listActors(token!, {
        search: searchTerm || undefined,
        motivation: motivationFilter !== "all" ? motivationFilter : undefined,
        sophistication: sophisticationFilter !== "all" ? sophisticationFilter : undefined,
        is_active: activeFilter !== "all" ? activeFilter === "active" : undefined,
      }) as Promise<{ actors: ThreatActor[]; total: number }>,
    enabled: !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/threats/actors/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      }),
    onSuccess: () => {
      toast.success("Threat actor deleted");
      queryClient.invalidateQueries({ queryKey: ["actors"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      setDeleteDialogOpen(false);
      setActorToDelete(null);
    },
    onError: () => {
      toast.error("Failed to delete threat actor");
    },
  });

  const handleCreateClick = () => {
    setDialogMode("create");
    setSelectedActor(null);
    setShowActorDialog(true);
  };

  const handleEditClick = (actor: ThreatActor) => {
    setDialogMode("edit");
    setSelectedActor(actor);
    setShowActorDialog(true);
  };

  const handleDeleteClick = (actor: ThreatActor) => {
    setActorToDelete(actor);
    setDeleteDialogOpen(true);
  };

  const handleViewClick = (actor: ThreatActor) => {
    router.push(`/threats/actors/${actor.id}`);
  };

  const actors = actorsData?.actors || [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search actors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        <Select value={motivationFilter} onValueChange={setMotivationFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Motivation" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Motivations</SelectItem>
            <SelectItem value="financial">Financial</SelectItem>
            <SelectItem value="espionage">Espionage</SelectItem>
            <SelectItem value="hacktivism">Hacktivism</SelectItem>
            <SelectItem value="destruction">Destruction</SelectItem>
            <SelectItem value="unknown">Unknown</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sophisticationFilter} onValueChange={setSophisticationFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Sophistication" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Levels</SelectItem>
            <SelectItem value="apt">APT</SelectItem>
            <SelectItem value="organized_crime">Organized Crime</SelectItem>
            <SelectItem value="script_kiddie">Script Kiddie</SelectItem>
            <SelectItem value="insider">Insider</SelectItem>
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
          Add Actor
        </Button>
      </div>

      {/* Actors List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading actors...</div>
          ) : actors.length > 0 ? (
            <div className="divide-y">
              {actors.map((actor) => (
                <div
                  key={actor.id}
                  className="flex items-center justify-between p-4 hover:bg-muted/50 cursor-pointer"
                  onClick={() => handleViewClick(actor)}
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      <Users className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {actor.name}
                        {actor.country_of_origin && (
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Globe className="h-3 w-3" />
                            {actor.country_of_origin}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {actor.aliases.slice(0, 2).map((alias) => (
                          <Badge key={alias} variant="outline" className="text-xs">
                            {alias}
                          </Badge>
                        ))}
                        {actor.aliases.length > 2 && (
                          <span className="text-xs text-muted-foreground">
                            +{actor.aliases.length - 2} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <MotivationBadge motivation={actor.motivation} />
                      <SophisticationBadge sophistication={actor.sophistication} />
                      <ThreatLevelBadge level={actor.threat_level} />
                    </div>

                    <div className="text-right text-sm text-muted-foreground min-w-[100px]">
                      <div className="flex items-center gap-1 justify-end">
                        <Link2 className="h-3 w-3" />
                        {actor.ioc_count} IOCs
                      </div>
                      <div>{actor.campaign_count} Campaigns</div>
                    </div>

                    <ActiveStatusBadge isActive={actor.is_active} />

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewClick(actor); }}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleEditClick(actor); }}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={(e) => { e.stopPropagation(); handleDeleteClick(actor); }}
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
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No threat actors found</p>
              <Button className="mt-4" variant="outline" onClick={handleCreateClick}>
                <Plus className="h-4 w-4 mr-2" />
                Add Threat Actor
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actor Dialog */}
      <ActorDialog
        open={showActorDialog}
        onOpenChange={setShowActorDialog}
        actor={selectedActor}
        mode={dialogMode}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Threat Actor</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{actorToDelete?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => actorToDelete && deleteMutation.mutate(actorToDelete.id)}
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

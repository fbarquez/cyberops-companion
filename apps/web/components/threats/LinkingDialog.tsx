"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, ChevronsUpDown, Link2, Users, Target } from "lucide-react";
import { toast } from "sonner";
import { threatsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

interface LinkingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  iocId: string;
  iocValue: string;
}

interface ThreatActor {
  id: string;
  name: string;
}

interface Campaign {
  id: string;
  name: string;
}

export function LinkingDialog({ open, onOpenChange, iocId, iocValue }: LinkingDialogProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("actors");
  const [selectedActorId, setSelectedActorId] = useState<string | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [actorPopoverOpen, setActorPopoverOpen] = useState(false);
  const [campaignPopoverOpen, setCampaignPopoverOpen] = useState(false);

  // Fetch actors
  const { data: actorsData } = useQuery({
    queryKey: ["actors-list"],
    queryFn: () => threatsAPI.listActors(token!) as Promise<{ actors: ThreatActor[]; total: number }>,
    enabled: !!token && open,
  });

  // Fetch campaigns
  const { data: campaignsData } = useQuery({
    queryKey: ["campaigns-list"],
    queryFn: () => threatsAPI.listCampaigns(token!) as Promise<{ campaigns: Campaign[]; total: number }>,
    enabled: !!token && open,
  });

  const actors = actorsData?.actors || [];
  const campaigns = campaignsData?.campaigns || [];

  // Link to Actor mutation
  const linkToActorMutation = useMutation({
    mutationFn: (actorId: string) => threatsAPI.linkIOCToActor(token!, actorId, iocId),
    onSuccess: () => {
      toast.success("IOC linked to threat actor successfully");
      queryClient.invalidateQueries({ queryKey: ["actors"] });
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
      setSelectedActorId(null);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to link IOC to actor");
    },
  });

  // Link to Campaign mutation
  const linkToCampaignMutation = useMutation({
    mutationFn: (campaignId: string) => threatsAPI.linkIOCToCampaign(token!, campaignId, iocId),
    onSuccess: () => {
      toast.success("IOC linked to campaign successfully");
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["iocs"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
      setSelectedCampaignId(null);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to link IOC to campaign");
    },
  });

  const handleLink = () => {
    if (activeTab === "actors" && selectedActorId) {
      linkToActorMutation.mutate(selectedActorId);
    } else if (activeTab === "campaigns" && selectedCampaignId) {
      linkToCampaignMutation.mutate(selectedCampaignId);
    }
  };

  const isPending = linkToActorMutation.isPending || linkToCampaignMutation.isPending;
  const selectedActor = actors.find((a) => a.id === selectedActorId);
  const selectedCampaign = campaigns.find((c) => c.id === selectedCampaignId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Link2 className="h-5 w-5" />
            Link IOC
          </DialogTitle>
          <DialogDescription>
            Link this IOC to a threat actor or campaign.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="mb-4 p-3 bg-muted rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">IOC Value</div>
            <div className="font-mono text-sm truncate">{iocValue}</div>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="actors" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Actor
              </TabsTrigger>
              <TabsTrigger value="campaigns" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Campaign
              </TabsTrigger>
            </TabsList>

            <TabsContent value="actors" className="mt-4">
              {actors.length > 0 ? (
                <Popover open={actorPopoverOpen} onOpenChange={setActorPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={actorPopoverOpen}
                      className="w-full justify-between"
                    >
                      {selectedActor ? selectedActor.name : "Select a threat actor..."}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-full p-0">
                    <Command>
                      <CommandInput placeholder="Search actors..." />
                      <CommandList>
                        <CommandEmpty>No actors found.</CommandEmpty>
                        <CommandGroup>
                          {actors.map((actor) => (
                            <CommandItem
                              key={actor.id}
                              value={actor.name}
                              onSelect={() => {
                                setSelectedActorId(actor.id);
                                setActorPopoverOpen(false);
                              }}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  selectedActorId === actor.id ? "opacity-100" : "opacity-0"
                                )}
                              />
                              {actor.name}
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No threat actors available.</p>
                  <p className="text-xs">Create a threat actor first to link IOCs.</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="campaigns" className="mt-4">
              {campaigns.length > 0 ? (
                <Popover open={campaignPopoverOpen} onOpenChange={setCampaignPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={campaignPopoverOpen}
                      className="w-full justify-between"
                    >
                      {selectedCampaign ? selectedCampaign.name : "Select a campaign..."}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-full p-0">
                    <Command>
                      <CommandInput placeholder="Search campaigns..." />
                      <CommandList>
                        <CommandEmpty>No campaigns found.</CommandEmpty>
                        <CommandGroup>
                          {campaigns.map((campaign) => (
                            <CommandItem
                              key={campaign.id}
                              value={campaign.name}
                              onSelect={() => {
                                setSelectedCampaignId(campaign.id);
                                setCampaignPopoverOpen(false);
                              }}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  selectedCampaignId === campaign.id ? "opacity-100" : "opacity-0"
                                )}
                              />
                              {campaign.name}
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No campaigns available.</p>
                  <p className="text-xs">Create a campaign first to link IOCs.</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleLink}
            disabled={
              isPending ||
              (activeTab === "actors" && !selectedActorId) ||
              (activeTab === "campaigns" && !selectedCampaignId)
            }
          >
            {isPending ? "Linking..." : "Link IOC"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

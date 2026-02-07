"use client";

import { useState, useEffect } from "react";
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
import { Badge } from "@/components/ui/badge";
import { X, Check, ChevronsUpDown } from "lucide-react";
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
import { cn } from "@/lib/utils";

interface Campaign {
  id: string;
  name: string;
  campaign_type?: string;
  threat_level: string;
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
}

interface ThreatActor {
  id: string;
  name: string;
}

interface CampaignDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  campaign?: Campaign | null;
  mode: "create" | "edit";
}

const CAMPAIGN_TYPES = [
  "Phishing", "Ransomware", "Data Exfiltration", "Espionage",
  "DDoS", "Supply Chain", "Credential Theft", "Malware Distribution"
];

const ATTACK_VECTORS = [
  "Email", "Web", "USB", "Network", "Social Engineering",
  "Watering Hole", "Supply Chain", "Insider"
];

const SECTORS = [
  "Finance", "Healthcare", "Technology", "Government", "Energy",
  "Manufacturing", "Retail", "Education", "Telecommunications", "Defense"
];

export function CampaignDialog({ open, onOpenChange, campaign, mode }: CampaignDialogProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [actorPopoverOpen, setActorPopoverOpen] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    campaign_type: "",
    description: "",
    objectives: "",
    target_sectors: [] as string[],
    target_countries: [] as string[],
    mitre_techniques: [] as string[],
    attack_vectors: [] as string[],
    malware_used: [] as string[],
    start_date: "",
    end_date: "",
    is_active: true,
    actor_ids: [] as string[],
  });

  const [techniqueInput, setTechniqueInput] = useState("");
  const [malwareInput, setMalwareInput] = useState("");
  const [countryInput, setCountryInput] = useState("");

  // Fetch available actors for linking
  const { data: actorsData } = useQuery({
    queryKey: ["actors-list"],
    queryFn: () => threatsAPI.listActors(token!) as Promise<{ actors: ThreatActor[]; total: number }>,
    enabled: !!token && open,
  });

  const actors = actorsData?.actors || [];

  useEffect(() => {
    if (campaign && mode === "edit") {
      setFormData({
        name: campaign.name,
        campaign_type: campaign.campaign_type || "",
        description: campaign.description || "",
        objectives: campaign.objectives || "",
        target_sectors: campaign.target_sectors || [],
        target_countries: campaign.target_countries || [],
        mitre_techniques: campaign.mitre_techniques || [],
        attack_vectors: campaign.attack_vectors || [],
        malware_used: campaign.malware_used || [],
        start_date: campaign.start_date ? campaign.start_date.split("T")[0] : "",
        end_date: campaign.end_date ? campaign.end_date.split("T")[0] : "",
        is_active: campaign.is_active,
        actor_ids: [],
      });
    } else {
      setFormData({
        name: "",
        campaign_type: "",
        description: "",
        objectives: "",
        target_sectors: [],
        target_countries: [],
        mitre_techniques: [],
        attack_vectors: [],
        malware_used: [],
        start_date: "",
        end_date: "",
        is_active: true,
        actor_ids: [],
      });
    }
  }, [campaign, mode, open]);

  const createMutation = useMutation({
    mutationFn: (data: any) => threatsAPI.createCampaign(token!, data),
    onSuccess: () => {
      toast.success("Campaign created successfully");
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create campaign");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => threatsAPI.updateCampaign(token!, campaign!.id, data),
    onSuccess: () => {
      toast.success("Campaign updated successfully");
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update campaign");
    },
  });

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error("Name is required");
      return;
    }

    const submitData = {
      ...formData,
      start_date: formData.start_date ? new Date(formData.start_date).toISOString() : undefined,
      end_date: formData.end_date ? new Date(formData.end_date).toISOString() : undefined,
    };

    if (mode === "create") {
      createMutation.mutate(submitData);
    } else {
      updateMutation.mutate(submitData);
    }
  };

  const addToList = (
    list: string[],
    value: string,
    setter: (list: string[]) => void,
    inputSetter: (v: string) => void
  ) => {
    const trimmed = value.trim();
    if (trimmed && !list.includes(trimmed)) {
      setter([...list, trimmed]);
    }
    inputSetter("");
  };

  const removeFromList = (list: string[], value: string, setter: (list: string[]) => void) => {
    setter(list.filter((item) => item !== value));
  };

  const toggleInList = (list: string[], value: string, setter: (list: string[]) => void) => {
    if (list.includes(value)) {
      setter(list.filter((item) => item !== value));
    } else {
      setter([...list, value]);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create Campaign" : "Edit Campaign"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a new threat campaign to track coordinated attack activities."
              : "Update the campaign information."}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Name */}
          <div className="grid gap-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Operation Aurora, SolarWinds Attack"
            />
          </div>

          {/* Campaign Type */}
          <div className="grid gap-2">
            <Label>Campaign Type</Label>
            <Select
              value={formData.campaign_type}
              onValueChange={(v) => setFormData({ ...formData, campaign_type: v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select campaign type" />
              </SelectTrigger>
              <SelectContent>
                {CAMPAIGN_TYPES.map((type) => (
                  <SelectItem key={type} value={type.toLowerCase().replace(/ /g, "_")}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the campaign's scope, impact, and notable characteristics..."
              rows={3}
            />
          </div>

          {/* Objectives */}
          <div className="grid gap-2">
            <Label htmlFor="objectives">Objectives</Label>
            <Textarea
              id="objectives"
              value={formData.objectives}
              onChange={(e) => setFormData({ ...formData, objectives: e.target.value })}
              placeholder="What are the campaign's goals?"
              rows={2}
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="start_date">Start Date</Label>
              <Input
                id="start_date"
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="end_date">End Date</Label>
              <Input
                id="end_date"
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              />
            </div>
          </div>

          {/* Associated Actors */}
          {mode === "create" && actors.length > 0 && (
            <div className="grid gap-2">
              <Label>Associated Threat Actors</Label>
              <Popover open={actorPopoverOpen} onOpenChange={setActorPopoverOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={actorPopoverOpen}
                    className="justify-between"
                  >
                    {formData.actor_ids.length > 0
                      ? `${formData.actor_ids.length} actor(s) selected`
                      : "Select actors..."}
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
                              toggleInList(
                                formData.actor_ids,
                                actor.id,
                                (list) => setFormData({ ...formData, actor_ids: list })
                              );
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                formData.actor_ids.includes(actor.id) ? "opacity-100" : "opacity-0"
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
              {formData.actor_ids.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {formData.actor_ids.map((id) => {
                    const actor = actors.find((a) => a.id === id);
                    return actor ? (
                      <Badge key={id} variant="secondary" className="gap-1">
                        {actor.name}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() =>
                            removeFromList(
                              formData.actor_ids,
                              id,
                              (list) => setFormData({ ...formData, actor_ids: list })
                            )
                          }
                        />
                      </Badge>
                    ) : null;
                  })}
                </div>
              )}
            </div>
          )}

          {/* Attack Vectors */}
          <div className="grid gap-2">
            <Label>Attack Vectors</Label>
            <div className="flex flex-wrap gap-2">
              {ATTACK_VECTORS.map((vector) => (
                <Badge
                  key={vector}
                  variant={formData.attack_vectors.includes(vector.toLowerCase()) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => {
                    toggleInList(
                      formData.attack_vectors,
                      vector.toLowerCase(),
                      (list) => setFormData({ ...formData, attack_vectors: list })
                    );
                  }}
                >
                  {vector}
                </Badge>
              ))}
            </div>
          </div>

          {/* Target Sectors */}
          <div className="grid gap-2">
            <Label>Target Sectors</Label>
            <div className="flex flex-wrap gap-2">
              {SECTORS.map((sector) => (
                <Badge
                  key={sector}
                  variant={formData.target_sectors.includes(sector) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => {
                    toggleInList(
                      formData.target_sectors,
                      sector,
                      (list) => setFormData({ ...formData, target_sectors: list })
                    );
                  }}
                >
                  {sector}
                </Badge>
              ))}
            </div>
          </div>

          {/* Target Countries */}
          <div className="grid gap-2">
            <Label>Target Countries</Label>
            <div className="flex gap-2">
              <Input
                value={countryInput}
                onChange={(e) => setCountryInput(e.target.value)}
                placeholder="Add country and press Enter"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      formData.target_countries,
                      countryInput,
                      (list) => setFormData({ ...formData, target_countries: list }),
                      setCountryInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  addToList(
                    formData.target_countries,
                    countryInput,
                    (list) => setFormData({ ...formData, target_countries: list }),
                    setCountryInput
                  )
                }
              >
                Add
              </Button>
            </div>
            {formData.target_countries.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.target_countries.map((country) => (
                  <Badge key={country} variant="secondary" className="gap-1">
                    {country}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() =>
                        removeFromList(
                          formData.target_countries,
                          country,
                          (list) => setFormData({ ...formData, target_countries: list })
                        )
                      }
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* MITRE Techniques */}
          <div className="grid gap-2">
            <Label>MITRE ATT&CK Techniques</Label>
            <div className="flex gap-2">
              <Input
                value={techniqueInput}
                onChange={(e) => setTechniqueInput(e.target.value)}
                placeholder="e.g., T1566, T1059.001"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      formData.mitre_techniques,
                      techniqueInput,
                      (list) => setFormData({ ...formData, mitre_techniques: list }),
                      setTechniqueInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  addToList(
                    formData.mitre_techniques,
                    techniqueInput,
                    (list) => setFormData({ ...formData, mitre_techniques: list }),
                    setTechniqueInput
                  )
                }
              >
                Add
              </Button>
            </div>
            {formData.mitre_techniques.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.mitre_techniques.map((tech) => (
                  <Badge key={tech} variant="secondary" className="gap-1 font-mono">
                    {tech}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() =>
                        removeFromList(
                          formData.mitre_techniques,
                          tech,
                          (list) => setFormData({ ...formData, mitre_techniques: list })
                        )
                      }
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Malware Used */}
          <div className="grid gap-2">
            <Label>Malware Used</Label>
            <div className="flex gap-2">
              <Input
                value={malwareInput}
                onChange={(e) => setMalwareInput(e.target.value)}
                placeholder="e.g., Emotet, TrickBot"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      formData.malware_used,
                      malwareInput,
                      (list) => setFormData({ ...formData, malware_used: list }),
                      setMalwareInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  addToList(
                    formData.malware_used,
                    malwareInput,
                    (list) => setFormData({ ...formData, malware_used: list }),
                    setMalwareInput
                  )
                }
              >
                Add
              </Button>
            </div>
            {formData.malware_used.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.malware_used.map((malware) => (
                  <Badge key={malware} variant="secondary" className="gap-1">
                    {malware}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() =>
                        removeFromList(
                          formData.malware_used,
                          malware,
                          (list) => setFormData({ ...formData, malware_used: list })
                        )
                      }
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Active Status */}
          {mode === "edit" && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4"
              />
              <Label htmlFor="is_active">Active campaign</Label>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending}>
            {isPending
              ? mode === "create"
                ? "Creating..."
                : "Updating..."
              : mode === "create"
              ? "Create Campaign"
              : "Update Campaign"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

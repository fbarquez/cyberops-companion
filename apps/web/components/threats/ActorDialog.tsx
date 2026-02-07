"use client";

import { useState, useEffect } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import { toast } from "sonner";
import { threatsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";

interface ThreatActor {
  id: string;
  name: string;
  aliases: string[];
  motivation: string;
  sophistication: string;
  threat_level: string;
  description?: string;
  country_of_origin?: string;
  target_sectors: string[];
  target_countries: string[];
  mitre_techniques: string[];
  tools_used: string[];
  first_seen?: string;
  last_seen?: string;
  is_active: boolean;
}

interface ActorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  actor?: ThreatActor | null;
  mode: "create" | "edit";
}

const MOTIVATIONS = [
  { value: "financial", label: "Financial" },
  { value: "espionage", label: "Espionage" },
  { value: "hacktivism", label: "Hacktivism" },
  { value: "destruction", label: "Destruction" },
  { value: "unknown", label: "Unknown" },
];

const SOPHISTICATIONS = [
  { value: "apt", label: "APT" },
  { value: "organized_crime", label: "Organized Crime" },
  { value: "script_kiddie", label: "Script Kiddie" },
  { value: "insider", label: "Insider" },
  { value: "unknown", label: "Unknown" },
];

const SECTORS = [
  "Finance", "Healthcare", "Technology", "Government", "Energy",
  "Manufacturing", "Retail", "Education", "Telecommunications", "Defense"
];

export function ActorDialog({ open, onOpenChange, actor, mode }: ActorDialogProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    name: "",
    aliases: [] as string[],
    motivation: "unknown",
    sophistication: "unknown",
    description: "",
    country_of_origin: "",
    target_sectors: [] as string[],
    target_countries: [] as string[],
    mitre_techniques: [] as string[],
    tools_used: [] as string[],
    is_active: true,
  });

  const [aliasInput, setAliasInput] = useState("");
  const [techniqueInput, setTechniqueInput] = useState("");
  const [toolInput, setToolInput] = useState("");
  const [countryInput, setCountryInput] = useState("");

  useEffect(() => {
    if (actor && mode === "edit") {
      setFormData({
        name: actor.name,
        aliases: actor.aliases || [],
        motivation: actor.motivation || "unknown",
        sophistication: actor.sophistication || "unknown",
        description: actor.description || "",
        country_of_origin: actor.country_of_origin || "",
        target_sectors: actor.target_sectors || [],
        target_countries: actor.target_countries || [],
        mitre_techniques: actor.mitre_techniques || [],
        tools_used: actor.tools_used || [],
        is_active: actor.is_active,
      });
    } else {
      setFormData({
        name: "",
        aliases: [],
        motivation: "unknown",
        sophistication: "unknown",
        description: "",
        country_of_origin: "",
        target_sectors: [],
        target_countries: [],
        mitre_techniques: [],
        tools_used: [],
        is_active: true,
      });
    }
  }, [actor, mode, open]);

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => threatsAPI.createActor(token!, data),
    onSuccess: () => {
      toast.success("Threat actor created successfully");
      queryClient.invalidateQueries({ queryKey: ["actors"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create threat actor");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => threatsAPI.updateActor(token!, actor!.id, data),
    onSuccess: () => {
      toast.success("Threat actor updated successfully");
      queryClient.invalidateQueries({ queryKey: ["actors"] });
      queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update threat actor");
    },
  });

  const handleSubmit = () => {
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

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create Threat Actor" : "Edit Threat Actor"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a new threat actor to track adversary activity."
              : "Update the threat actor information."}
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
              placeholder="e.g., APT29, Lazarus Group"
            />
          </div>

          {/* Aliases */}
          <div className="grid gap-2">
            <Label>Aliases</Label>
            <div className="flex gap-2">
              <Input
                value={aliasInput}
                onChange={(e) => setAliasInput(e.target.value)}
                placeholder="Add alias and press Enter"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      formData.aliases,
                      aliasInput,
                      (list) => setFormData({ ...formData, aliases: list }),
                      setAliasInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  addToList(
                    formData.aliases,
                    aliasInput,
                    (list) => setFormData({ ...formData, aliases: list }),
                    setAliasInput
                  )
                }
              >
                Add
              </Button>
            </div>
            {formData.aliases.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.aliases.map((alias) => (
                  <Badge key={alias} variant="secondary" className="gap-1">
                    {alias}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() =>
                        removeFromList(
                          formData.aliases,
                          alias,
                          (list) => setFormData({ ...formData, aliases: list })
                        )
                      }
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Motivation & Sophistication */}
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>Motivation</Label>
              <Select
                value={formData.motivation}
                onValueChange={(v) => setFormData({ ...formData, motivation: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MOTIVATIONS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Sophistication</Label>
              <Select
                value={formData.sophistication}
                onValueChange={(v) => setFormData({ ...formData, sophistication: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SOPHISTICATIONS.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Description */}
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the threat actor's history, tactics, and notable activities..."
              rows={3}
            />
          </div>

          {/* Country of Origin */}
          <div className="grid gap-2">
            <Label htmlFor="country">Country of Origin</Label>
            <Input
              id="country"
              value={formData.country_of_origin}
              onChange={(e) => setFormData({ ...formData, country_of_origin: e.target.value })}
              placeholder="e.g., Russia, China, North Korea"
            />
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
                    if (formData.target_sectors.includes(sector)) {
                      setFormData({
                        ...formData,
                        target_sectors: formData.target_sectors.filter((s) => s !== sector),
                      });
                    } else {
                      setFormData({
                        ...formData,
                        target_sectors: [...formData.target_sectors, sector],
                      });
                    }
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

          {/* Tools Used */}
          <div className="grid gap-2">
            <Label>Tools Used</Label>
            <div className="flex gap-2">
              <Input
                value={toolInput}
                onChange={(e) => setToolInput(e.target.value)}
                placeholder="e.g., Cobalt Strike, Mimikatz"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      formData.tools_used,
                      toolInput,
                      (list) => setFormData({ ...formData, tools_used: list }),
                      setToolInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  addToList(
                    formData.tools_used,
                    toolInput,
                    (list) => setFormData({ ...formData, tools_used: list }),
                    setToolInput
                  )
                }
              >
                Add
              </Button>
            </div>
            {formData.tools_used.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.tools_used.map((tool) => (
                  <Badge key={tool} variant="secondary" className="gap-1">
                    {tool}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() =>
                        removeFromList(
                          formData.tools_used,
                          tool,
                          (list) => setFormData({ ...formData, tools_used: list })
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
              <Label htmlFor="is_active">Active threat actor</Label>
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
              ? "Create Actor"
              : "Update Actor"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Users,
  Globe,
  Calendar,
  Link2,
  Target,
  Pencil,
  Shield,
  Crosshair,
  ExternalLink,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { threatsAPI } from "@/lib/api-client";
import { toast } from "sonner";
import {
  ThreatLevelBadge,
  MotivationBadge,
  SophisticationBadge,
  ActiveStatusBadge,
} from "@/components/threats/ThreatBadges";
import { ActorDialog } from "@/components/threats/ActorDialog";

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

interface IOC {
  id: string;
  value: string;
  type: string;
  threat_level: string;
}

interface Campaign {
  id: string;
  name: string;
  campaign_type?: string;
  threat_level: string;
  is_active: boolean;
}

function formatDate(dateString?: string): string {
  if (!dateString) return "-";
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function ActorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const actorId = params.id as string;

  const [showEditDialog, setShowEditDialog] = useState(false);

  const { data: actor, isLoading } = useQuery({
    queryKey: ["actor", actorId],
    queryFn: () => threatsAPI.getActor(token!, actorId) as Promise<ThreatActor>,
    enabled: !!token && !!actorId,
  });

  // Fetch linked IOCs (placeholder - would need backend support)
  const { data: linkedIOCs } = useQuery({
    queryKey: ["actor-iocs", actorId],
    queryFn: async () => {
      // This would need a backend endpoint to fetch IOCs linked to an actor
      return [] as IOC[];
    },
    enabled: !!token && !!actorId,
  });

  // Fetch linked campaigns (placeholder - would need backend support)
  const { data: linkedCampaigns } = useQuery({
    queryKey: ["actor-campaigns", actorId],
    queryFn: async () => {
      // This would need a backend endpoint to fetch campaigns linked to an actor
      return [] as Campaign[];
    },
    enabled: !!token && !!actorId,
  });

  if (isLoading || !actor) {
    return <PageLoading />;
  }

  return (
    <div className="flex flex-col h-full">
      <Header title={actor.name} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Back button and actions */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => router.push("/threats")}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Threats
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowEditDialog(true)}>
              <Pencil className="h-4 w-4 mr-2" />
              Edit Actor
            </Button>
          </div>
        </div>

        {/* Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Users className="h-8 w-8 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle className="text-2xl flex items-center gap-3">
                    {actor.name}
                    <ActiveStatusBadge isActive={actor.is_active} />
                  </CardTitle>
                  {actor.aliases.length > 0 && (
                    <CardDescription className="mt-1">
                      Also known as: {actor.aliases.join(", ")}
                    </CardDescription>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <MotivationBadge motivation={actor.motivation} />
                <SophisticationBadge sophistication={actor.sophistication} />
                <ThreatLevelBadge level={actor.threat_level} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {actor.country_of_origin && (
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Origin:</span>
                  <span className="font-medium">{actor.country_of_origin}</span>
                </div>
              )}
              {actor.first_seen && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">First Seen:</span>
                  <span className="font-medium">{formatDate(actor.first_seen)}</span>
                </div>
              )}
              {actor.last_seen && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Last Seen:</span>
                  <span className="font-medium">{formatDate(actor.last_seen)}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Crosshair className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">IOCs:</span>
                <span className="font-medium">{actor.ioc_count}</span>
              </div>
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Campaigns:</span>
                <span className="font-medium">{actor.campaign_count}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Description */}
        {actor.description && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground whitespace-pre-wrap">{actor.description}</p>
            </CardContent>
          </Card>
        )}

        {/* Targets */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {actor.target_sectors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Target Sectors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {actor.target_sectors.map((sector) => (
                    <Badge key={sector} variant="secondary">
                      {sector}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {actor.target_countries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Target Countries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {actor.target_countries.map((country) => (
                    <Badge key={country} variant="outline">
                      {country}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* TTPs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {actor.mitre_techniques.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  MITRE ATT&CK Techniques
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {actor.mitre_techniques.map((tech) => (
                    <Badge
                      key={tech}
                      variant="outline"
                      className="font-mono cursor-pointer hover:bg-muted"
                      onClick={() => window.open(`https://attack.mitre.org/techniques/${tech.replace('.', '/')}`, '_blank')}
                    >
                      {tech}
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {actor.tools_used.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tools Used</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {actor.tools_used.map((tool) => (
                    <Badge key={tool} variant="secondary">
                      {tool}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Linked IOCs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Crosshair className="h-5 w-5" />
                Linked IOCs
              </CardTitle>
              <Button variant="outline" size="sm">
                <Link2 className="h-4 w-4 mr-2" />
                Link IOC
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {linkedIOCs && linkedIOCs.length > 0 ? (
              <div className="divide-y">
                {linkedIOCs.map((ioc) => (
                  <div key={ioc.id} className="py-2 flex items-center justify-between">
                    <div className="font-mono text-sm">{ioc.value}</div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{ioc.type}</Badge>
                      <Badge>{ioc.threat_level}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-4">
                No IOCs linked to this actor yet.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Linked Campaigns */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="h-5 w-5" />
              Related Campaigns
            </CardTitle>
          </CardHeader>
          <CardContent>
            {linkedCampaigns && linkedCampaigns.length > 0 ? (
              <div className="divide-y">
                {linkedCampaigns.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="py-2 flex items-center justify-between cursor-pointer hover:bg-muted/50 px-2 -mx-2 rounded"
                    onClick={() => router.push(`/threats/campaigns/${campaign.id}`)}
                  >
                    <div className="font-medium">{campaign.name}</div>
                    <div className="flex items-center gap-2">
                      {campaign.campaign_type && (
                        <Badge variant="outline">{campaign.campaign_type}</Badge>
                      )}
                      <Badge>{campaign.threat_level}</Badge>
                      <ActiveStatusBadge isActive={campaign.is_active} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-4">
                No campaigns associated with this actor.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Edit Dialog */}
      <ActorDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        actor={actor}
        mode="edit"
      />
    </div>
  );
}

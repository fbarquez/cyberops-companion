"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Target,
  Users,
  Calendar,
  Link2,
  Crosshair,
  Pencil,
  Shield,
  ExternalLink,
  Swords,
  Bug,
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
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { threatsAPI } from "@/lib/api-client";
import { toast } from "sonner";
import { ThreatLevelBadge, ActiveStatusBadge } from "@/components/threats/ThreatBadges";
import { CampaignDialog } from "@/components/threats/CampaignDialog";

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

interface IOC {
  id: string;
  value: string;
  type: string;
  threat_level: string;
}

interface ThreatActor {
  id: string;
  name: string;
  motivation: string;
  sophistication: string;
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

function getCampaignTypeLabel(type?: string): string {
  if (!type) return "Unknown";
  return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const campaignId = params.id as string;

  const [showEditDialog, setShowEditDialog] = useState(false);

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => threatsAPI.getCampaign(token!, campaignId) as Promise<Campaign>,
    enabled: !!token && !!campaignId,
  });

  // Fetch linked IOCs (placeholder - would need backend support)
  const { data: linkedIOCs } = useQuery({
    queryKey: ["campaign-iocs", campaignId],
    queryFn: async () => {
      // This would need a backend endpoint to fetch IOCs linked to a campaign
      return [] as IOC[];
    },
    enabled: !!token && !!campaignId,
  });

  // Fetch linked actors (placeholder - would need backend support)
  const { data: linkedActors } = useQuery({
    queryKey: ["campaign-actors", campaignId],
    queryFn: async () => {
      // This would need a backend endpoint to fetch actors linked to a campaign
      return [] as ThreatActor[];
    },
    enabled: !!token && !!campaignId,
  });

  if (isLoading || !campaign) {
    return <PageLoading />;
  }

  return (
    <div className="flex flex-col h-full">
      <Header title={campaign.name} />

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
              Edit Campaign
            </Button>
          </div>
        </div>

        {/* Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Target className="h-8 w-8 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle className="text-2xl flex items-center gap-3">
                    {campaign.name}
                    <ActiveStatusBadge isActive={campaign.is_active} />
                  </CardTitle>
                  {campaign.campaign_type && (
                    <CardDescription className="mt-1">
                      Type: {getCampaignTypeLabel(campaign.campaign_type)}
                    </CardDescription>
                  )}
                </div>
              </div>
              <ThreatLevelBadge level={campaign.threat_level} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {campaign.start_date && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Start Date:</span>
                  <span className="font-medium">{formatDate(campaign.start_date)}</span>
                </div>
              )}
              {campaign.end_date && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">End Date:</span>
                  <span className="font-medium">{formatDate(campaign.end_date)}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Actors:</span>
                <span className="font-medium">{campaign.actor_count}</span>
              </div>
              <div className="flex items-center gap-2">
                <Crosshair className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">IOCs:</span>
                <span className="font-medium">{campaign.ioc_count}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Description & Objectives */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {campaign.description && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Description</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-wrap">{campaign.description}</p>
              </CardContent>
            </Card>
          )}
          {campaign.objectives && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Objectives</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-wrap">{campaign.objectives}</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Attack Vectors */}
        {campaign.attack_vectors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Swords className="h-5 w-5" />
                Attack Vectors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {campaign.attack_vectors.map((vector) => (
                  <Badge key={vector} variant="destructive">
                    {vector}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Targets */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {campaign.target_sectors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Target Sectors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {campaign.target_sectors.map((sector) => (
                    <Badge key={sector} variant="secondary">
                      {sector}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {campaign.target_countries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Target Countries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {campaign.target_countries.map((country) => (
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
          {campaign.mitre_techniques.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  MITRE ATT&CK Techniques
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {campaign.mitre_techniques.map((tech) => (
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
          {campaign.malware_used.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Bug className="h-5 w-5" />
                  Malware Used
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {campaign.malware_used.map((malware) => (
                    <Badge key={malware} variant="secondary">
                      {malware}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Linked Actors */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5" />
                Associated Threat Actors
              </CardTitle>
              <Button variant="outline" size="sm">
                <Link2 className="h-4 w-4 mr-2" />
                Link Actor
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {linkedActors && linkedActors.length > 0 ? (
              <div className="divide-y">
                {linkedActors.map((actor) => (
                  <div
                    key={actor.id}
                    className="py-2 flex items-center justify-between cursor-pointer hover:bg-muted/50 px-2 -mx-2 rounded"
                    onClick={() => router.push(`/threats/actors/${actor.id}`)}
                  >
                    <div className="font-medium">{actor.name}</div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{actor.motivation}</Badge>
                      <Badge variant="secondary">{actor.sophistication}</Badge>
                      <ActiveStatusBadge isActive={actor.is_active} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-4">
                No threat actors linked to this campaign yet.
              </p>
            )}
          </CardContent>
        </Card>

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
                No IOCs linked to this campaign yet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Edit Dialog */}
      <CampaignDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        campaign={campaign}
        mode="edit"
      />
    </div>
  );
}

"use client";

import { ArrowRight, Shield, Target, AlertTriangle, Crown, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PathNode {
  id: string;
  name: string;
  type: string;
  isEntryPoint?: boolean;
  isCrownJewel?: boolean;
  vulnerabilities?: number;
  riskScore?: number;
}

interface AttackPathVisualizationProps {
  path: {
    id: string;
    name: string;
    entryPoint: PathNode;
    target: PathNode;
    intermediateNodes: PathNode[];
    riskScore: number;
    exploitabilityScore: number;
    impactScore: number;
    status: string;
  };
  compact?: boolean;
  onNodeClick?: (nodeId: string) => void;
}

export function AttackPathVisualization({
  path,
  compact = false,
  onNodeClick,
}: AttackPathVisualizationProps) {
  const getRiskColor = (score: number) => {
    if (score >= 8) return "border-red-500 bg-red-50";
    if (score >= 6) return "border-orange-500 bg-orange-50";
    if (score >= 4) return "border-yellow-500 bg-yellow-50";
    return "border-green-500 bg-green-50";
  };

  const getRiskBadgeColor = (score: number) => {
    if (score >= 8) return "bg-red-500 text-white";
    if (score >= 6) return "bg-orange-500 text-white";
    if (score >= 4) return "bg-yellow-500 text-black";
    return "bg-green-500 text-white";
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "active": return "bg-blue-100 text-blue-800";
      case "mitigated": return "bg-green-100 text-green-800";
      case "accepted": return "bg-gray-100 text-gray-800";
      case "false_positive": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const NodeBox = ({ node, isFirst, isLast }: { node: PathNode; isFirst?: boolean; isLast?: boolean }) => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "relative flex flex-col items-center p-2 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md min-w-[80px]",
              isFirst && "border-red-400 bg-red-50",
              isLast && "border-yellow-400 bg-yellow-50",
              !isFirst && !isLast && "border-gray-300 bg-gray-50",
              node.vulnerabilities && node.vulnerabilities > 0 && "ring-2 ring-red-300"
            )}
            onClick={() => onNodeClick?.(node.id)}
          >
            <div className="flex items-center gap-1 mb-1">
              {isFirst && <MapPin className="h-4 w-4 text-red-500" />}
              {isLast && <Crown className="h-4 w-4 text-yellow-500" />}
              {!isFirst && !isLast && <Shield className="h-4 w-4 text-gray-500" />}
            </div>
            <span className={cn(
              "text-xs font-medium text-center truncate max-w-[70px]",
              compact && "text-[10px]"
            )}>
              {node.name}
            </span>
            <span className="text-[10px] text-muted-foreground capitalize">
              {node.type}
            </span>
            {node.vulnerabilities !== undefined && node.vulnerabilities > 0 && (
              <Badge variant="destructive" className="absolute -top-2 -right-2 h-4 w-4 p-0 text-[10px] flex items-center justify-center">
                {node.vulnerabilities}
              </Badge>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-sm">
            <p className="font-medium">{node.name}</p>
            <p className="text-muted-foreground capitalize">{node.type}</p>
            {node.vulnerabilities !== undefined && (
              <p className="text-red-500">{node.vulnerabilities} vulnerabilities</p>
            )}
            {node.riskScore !== undefined && (
              <p>Risk Score: {node.riskScore.toFixed(1)}</p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );

  const Arrow = () => (
    <div className="flex items-center justify-center px-1">
      <ArrowRight className={cn("text-gray-400", compact ? "h-3 w-3" : "h-4 w-4")} />
    </div>
  );

  const allNodes = [
    path.entryPoint,
    ...path.intermediateNodes,
    path.target,
  ];

  return (
    <div className={cn(
      "rounded-lg border p-4",
      getRiskColor(path.riskScore)
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-sm">{path.name}</h4>
          <Badge className={getStatusColor(path.status)}>
            {path.status.replace(/_/g, " ")}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={getRiskBadgeColor(path.riskScore)}>
            Risk: {path.riskScore.toFixed(1)}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {allNodes.length} hops
          </span>
        </div>
      </div>

      {/* Path Visualization */}
      <div className="flex items-center overflow-x-auto pb-2">
        {allNodes.map((node, index) => (
          <div key={node.id} className="flex items-center">
            <NodeBox
              node={node}
              isFirst={index === 0}
              isLast={index === allNodes.length - 1}
            />
            {index < allNodes.length - 1 && <Arrow />}
          </div>
        ))}
      </div>

      {/* Scores */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <AlertTriangle className="h-3 w-3" />
          <span>Exploitability: {path.exploitabilityScore.toFixed(1)}</span>
        </div>
        <div className="flex items-center gap-1">
          <Target className="h-3 w-3" />
          <span>Impact: {path.impactScore.toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}

// Simple list view for multiple paths
interface AttackPathListProps {
  paths: Array<{
    id: string;
    name: string;
    entry_point_name: string;
    target_name: string;
    target_criticality: string;
    hop_count: number;
    risk_score: number;
    status: string;
  }>;
  onPathClick?: (pathId: string) => void;
}

export function AttackPathList({ paths, onPathClick }: AttackPathListProps) {
  const getRiskColor = (score: number) => {
    if (score >= 8) return "text-red-600";
    if (score >= 6) return "text-orange-600";
    if (score >= 4) return "text-yellow-600";
    return "text-green-600";
  };

  const getCriticalityColor = (criticality: string) => {
    switch (criticality?.toLowerCase()) {
      case "critical": return "bg-red-500 text-white";
      case "high": return "bg-orange-500 text-white";
      case "medium": return "bg-yellow-500 text-black";
      case "low": return "bg-green-500 text-white";
      default: return "bg-gray-500 text-white";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "active": return "bg-blue-100 text-blue-800";
      case "mitigated": return "bg-green-100 text-green-800";
      case "accepted": return "bg-gray-100 text-gray-800";
      case "false_positive": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (paths.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No attack paths found.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {paths.map((path) => (
        <div
          key={path.id}
          className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
          onClick={() => onPathClick?.(path.id)}
        >
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-red-500 flex-shrink-0" />
              <span className="text-sm font-medium truncate max-w-[120px]">
                {path.entry_point_name}
              </span>
            </div>

            <div className="flex items-center text-muted-foreground">
              <ArrowRight className="h-4 w-4" />
              <span className="text-xs mx-1">{path.hop_count} hops</span>
              <ArrowRight className="h-4 w-4" />
            </div>

            <div className="flex items-center gap-2">
              <Crown className="h-4 w-4 text-yellow-500 flex-shrink-0" />
              <span className="text-sm font-medium truncate max-w-[120px]">
                {path.target_name}
              </span>
              <Badge className={getCriticalityColor(path.target_criticality)} variant="secondary">
                {path.target_criticality}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <Badge variant="outline" className={getStatusColor(path.status)}>
              {path.status.replace(/_/g, " ")}
            </Badge>
            <div className={cn("font-bold text-lg", getRiskColor(path.risk_score))}>
              {path.risk_score.toFixed(1)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Compact summary card for dashboard
interface AttackPathSummaryProps {
  totalPaths: number;
  criticalPaths: number;
  highRiskPaths: number;
  topRiskScore?: number;
}

export function AttackPathSummary({
  totalPaths,
  criticalPaths,
  highRiskPaths,
  topRiskScore,
}: AttackPathSummaryProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="text-center">
        <div className="text-2xl font-bold">{totalPaths}</div>
        <div className="text-xs text-muted-foreground">Total Paths</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-red-600">{criticalPaths}</div>
        <div className="text-xs text-muted-foreground">Critical</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-orange-600">{highRiskPaths}</div>
        <div className="text-xs text-muted-foreground">High Risk</div>
      </div>
      {topRiskScore !== undefined && (
        <div className="text-center">
          <div className="text-2xl font-bold">{topRiskScore.toFixed(1)}</div>
          <div className="text-xs text-muted-foreground">Top Risk</div>
        </div>
      )}
    </div>
  );
}

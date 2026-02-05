"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  Users,
  Server,
  Save,
  AlertCircle,
  CheckCircle2,
  Clock,
  ClipboardList,
  FileText,
  Plus,
  Trash2,
  Shield,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuthStore } from "@/stores/auth-store";
import { bcmAPI } from "@/lib/api-client";
import { Header } from "@/components/shared/header";

// Types
interface Process {
  id: string;
  process_id: string;
  name: string;
  description: string | null;
  owner: string;
  department: string | null;
  criticality: string;
  status: string;
  internal_dependencies: string[];
  external_dependencies: string[];
  it_systems: string[];
  key_personnel: string[];
  has_bia: boolean;
  bia_status: string | null;
  created_at: string;
  updated_at: string | null;
}

interface Strategy {
  id: string;
  process_id: string;
  strategy_type: string;
  name: string;
  description: string;
  activation_trigger: string;
  activation_procedure: string;
  achievable_rto_hours: number;
  achievable_rpo_hours: number;
  status: string;
}

interface StrategyListResponse {
  strategies: Strategy[];
  total: number;
}

const STRATEGY_TYPE_LABELS: Record<string, string> = {
  do_nothing: "Accept Risk",
  manual_workaround: "Manual Workaround",
  alternate_site: "Alternate Site",
  alternate_supplier: "Alternate Supplier",
  redundancy: "Redundancy",
  outsource: "Outsource",
  insurance: "Insurance",
};

export default function ProcessDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const processId = params.id as string;
  const [activeTab, setActiveTab] = useState("details");
  const [isEditing, setIsEditing] = useState(false);
  const [isAddStrategyOpen, setIsAddStrategyOpen] = useState(false);

  // Form state
  const [processForm, setProcessForm] = useState({
    process_id: "",
    name: "",
    description: "",
    owner: "",
    department: "",
    criticality: "medium",
    status: "active",
    internal_dependencies: [] as string[],
    external_dependencies: [] as string[],
    it_systems: [] as string[],
    key_personnel: [] as string[],
  });

  const [newStrategy, setNewStrategy] = useState({
    strategy_type: "manual_workaround",
    name: "",
    description: "",
    activation_trigger: "",
    activation_procedure: "",
    achievable_rto_hours: 24,
    achievable_rpo_hours: 4,
  });

  // Queries
  const { data: process, isLoading: processLoading } = useQuery<Process>({
    queryKey: ["bcm", "process", processId],
    queryFn: () => bcmAPI.getProcess(token!, processId) as Promise<Process>,
    enabled: !!token && !!processId,
  });

  const { data: strategiesData, isLoading: strategiesLoading } = useQuery<StrategyListResponse>({
    queryKey: ["bcm", "strategies", processId],
    queryFn: () => bcmAPI.listStrategies(token!, processId) as Promise<StrategyListResponse>,
    enabled: !!token && !!processId,
  });

  // Initialize form from process
  useEffect(() => {
    if (process) {
      setProcessForm({
        process_id: process.process_id,
        name: process.name,
        description: process.description || "",
        owner: process.owner,
        department: process.department || "",
        criticality: process.criticality,
        status: process.status,
        internal_dependencies: process.internal_dependencies || [],
        external_dependencies: process.external_dependencies || [],
        it_systems: process.it_systems || [],
        key_personnel: process.key_personnel || [],
      });
    }
  }, [process]);

  // Mutations
  const updateProcessMutation = useMutation({
    mutationFn: (data: typeof processForm) => bcmAPI.updateProcess(token!, processId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm"] });
      setIsEditing(false);
    },
  });

  const createStrategyMutation = useMutation({
    mutationFn: (data: typeof newStrategy) => bcmAPI.createStrategy(token!, processId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm", "strategies", processId] });
      setIsAddStrategyOpen(false);
      setNewStrategy({
        strategy_type: "manual_workaround",
        name: "",
        description: "",
        activation_trigger: "",
        activation_procedure: "",
        achievable_rto_hours: 24,
        achievable_rpo_hours: 4,
      });
    },
  });

  const deleteStrategyMutation = useMutation({
    mutationFn: (strategyId: string) => bcmAPI.deleteStrategy(token!, strategyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bcm", "strategies", processId] });
    },
  });

  const handleAddListItem = (
    field: "internal_dependencies" | "external_dependencies" | "it_systems" | "key_personnel",
    value: string
  ) => {
    if (value.trim()) {
      setProcessForm({
        ...processForm,
        [field]: [...processForm[field], value.trim()],
      });
    }
  };

  const handleRemoveListItem = (
    field: "internal_dependencies" | "external_dependencies" | "it_systems" | "key_personnel",
    index: number
  ) => {
    setProcessForm({
      ...processForm,
      [field]: processForm[field].filter((_, i) => i !== index),
    });
  };

  const getCriticalityBadge = (criticality: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "default",
      medium: "secondary",
      low: "outline",
    };
    return (
      <Badge variant={variants[criticality] || "secondary"}>
        {criticality.charAt(0).toUpperCase() + criticality.slice(1)}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "outline"; label: string }> = {
      active: { variant: "default", label: "Active" },
      inactive: { variant: "secondary", label: "Inactive" },
      under_review: { variant: "outline", label: "Under Review" },
      planned: { variant: "outline", label: "Planned" },
      implemented: { variant: "default", label: "Implemented" },
      tested: { variant: "default", label: "Tested" },
      approved: { variant: "default", label: "Approved" },
    };
    const statusConfig = config[status] || { variant: "secondary", label: status };
    return <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>;
  };

  if (processLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading process...</div>
      </div>
    );
  }

  if (!process) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Process not found</p>
        <Button onClick={() => router.push("/bcm")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to BCM
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header
        title={process.name}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/bcm")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            {isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => updateProcessMutation.mutate(processForm)}
                  disabled={updateProcessMutation.isPending}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateProcessMutation.isPending ? "Saving..." : "Save"}
                </Button>
              </>
            ) : (
              <Button onClick={() => setIsEditing(true)}>Edit Process</Button>
            )}
          </div>
        }
      />

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="bia">Business Impact</TabsTrigger>
            <TabsTrigger value="strategies">Strategies</TabsTrigger>
          </TabsList>

          {/* Details Tab */}
          <TabsContent value="details" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Process ID</Label>
                      {isEditing ? (
                        <Input
                          value={processForm.process_id}
                          onChange={(e) =>
                            setProcessForm({ ...processForm, process_id: e.target.value })
                          }
                        />
                      ) : (
                        <p className="font-mono">{process.process_id}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      {isEditing ? (
                        <Select
                          value={processForm.status}
                          onValueChange={(value) =>
                            setProcessForm({ ...processForm, status: value })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="active">Active</SelectItem>
                            <SelectItem value="inactive">Inactive</SelectItem>
                            <SelectItem value="under_review">Under Review</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        getStatusBadge(process.status)
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Process Name</Label>
                    {isEditing ? (
                      <Input
                        value={processForm.name}
                        onChange={(e) =>
                          setProcessForm({ ...processForm, name: e.target.value })
                        }
                      />
                    ) : (
                      <p className="font-semibold">{process.name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Description</Label>
                    {isEditing ? (
                      <Textarea
                        value={processForm.description}
                        onChange={(e) =>
                          setProcessForm({ ...processForm, description: e.target.value })
                        }
                        rows={3}
                      />
                    ) : (
                      <p className="text-muted-foreground">
                        {process.description || "No description"}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Criticality</Label>
                    {isEditing ? (
                      <Select
                        value={processForm.criticality}
                        onValueChange={(value) =>
                          setProcessForm({ ...processForm, criticality: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="critical">Critical</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="low">Low</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      getCriticalityBadge(process.criticality)
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Ownership */}
              <Card>
                <CardHeader>
                  <CardTitle>Ownership</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Process Owner</Label>
                    {isEditing ? (
                      <Input
                        value={processForm.owner}
                        onChange={(e) =>
                          setProcessForm({ ...processForm, owner: e.target.value })
                        }
                      />
                    ) : (
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{process.owner}</span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Department</Label>
                    {isEditing ? (
                      <Input
                        value={processForm.department}
                        onChange={(e) =>
                          setProcessForm({ ...processForm, department: e.target.value })
                        }
                      />
                    ) : (
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span>{process.department || "Not specified"}</span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Key Personnel</Label>
                    {isEditing ? (
                      <>
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add key personnel..."
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleAddListItem("key_personnel", e.currentTarget.value);
                                e.currentTarget.value = "";
                              }
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                              handleAddListItem("key_personnel", input.value);
                              input.value = "";
                            }}
                          >
                            Add
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {processForm.key_personnel.map((person, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="cursor-pointer"
                              onClick={() => handleRemoveListItem("key_personnel", idx)}
                            >
                              {person} &times;
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {process.key_personnel?.length > 0 ? (
                          process.key_personnel.map((person, idx) => (
                            <Badge key={idx} variant="secondary">
                              <Users className="h-3 w-3 mr-1" />
                              {person}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None specified</span>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle>Dependencies</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Internal Dependencies</Label>
                    {isEditing ? (
                      <>
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add internal dependency..."
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleAddListItem("internal_dependencies", e.currentTarget.value);
                                e.currentTarget.value = "";
                              }
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                              handleAddListItem("internal_dependencies", input.value);
                              input.value = "";
                            }}
                          >
                            Add
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {processForm.internal_dependencies.map((dep, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="cursor-pointer"
                              onClick={() => handleRemoveListItem("internal_dependencies", idx)}
                            >
                              {dep} &times;
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {process.internal_dependencies?.length > 0 ? (
                          process.internal_dependencies.map((dep, idx) => (
                            <Badge key={idx} variant="outline">{dep}</Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None</span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>External Dependencies</Label>
                    {isEditing ? (
                      <>
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add external dependency..."
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleAddListItem("external_dependencies", e.currentTarget.value);
                                e.currentTarget.value = "";
                              }
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                              handleAddListItem("external_dependencies", input.value);
                              input.value = "";
                            }}
                          >
                            Add
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {processForm.external_dependencies.map((dep, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="cursor-pointer"
                              onClick={() => handleRemoveListItem("external_dependencies", idx)}
                            >
                              {dep} &times;
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {process.external_dependencies?.length > 0 ? (
                          process.external_dependencies.map((dep, idx) => (
                            <Badge key={idx} variant="outline">{dep}</Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None</span>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* IT Systems */}
              <Card>
                <CardHeader>
                  <CardTitle>IT Systems</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Systems Required</Label>
                    {isEditing ? (
                      <>
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add IT system..."
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleAddListItem("it_systems", e.currentTarget.value);
                                e.currentTarget.value = "";
                              }
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                              handleAddListItem("it_systems", input.value);
                              input.value = "";
                            }}
                          >
                            Add
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {processForm.it_systems.map((sys, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="cursor-pointer"
                              onClick={() => handleRemoveListItem("it_systems", idx)}
                            >
                              {sys} &times;
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {process.it_systems?.length > 0 ? (
                          process.it_systems.map((sys, idx) => (
                            <Badge key={idx} variant="secondary">
                              <Server className="h-3 w-3 mr-1" />
                              {sys}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-sm">None specified</span>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* BIA Tab */}
          <TabsContent value="bia" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Business Impact Analysis</CardTitle>
                <CardDescription>
                  View and manage the Business Impact Analysis for this process.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {process.has_bia ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle2 className="h-5 w-5" />
                      <span>BIA completed - Status: {process.bia_status}</span>
                    </div>
                    <Button onClick={() => router.push(`/bcm/bia/${processId}`)}>
                      <ClipboardList className="h-4 w-4 mr-2" />
                      View/Edit BIA
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center py-8">
                    <AlertCircle className="h-12 w-12 text-yellow-500 mb-4" />
                    <p className="text-muted-foreground mb-4">
                      No Business Impact Analysis has been conducted for this process.
                    </p>
                    <Button onClick={() => router.push(`/bcm/bia/${processId}`)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create BIA
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Strategies Tab */}
          <TabsContent value="strategies" className="mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Continuity Strategies</CardTitle>
                  <CardDescription>
                    Define strategies to maintain or recover this process during disruptions.
                  </CardDescription>
                </div>
                <Button onClick={() => setIsAddStrategyOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Strategy
                </Button>
              </CardHeader>
              <CardContent>
                {strategiesLoading ? (
                  <p className="text-muted-foreground py-8 text-center">Loading strategies...</p>
                ) : strategiesData?.strategies?.length === 0 ? (
                  <div className="flex flex-col items-center py-8">
                    <Shield className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">
                      No continuity strategies defined for this process.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {strategiesData?.strategies?.map((strategy) => (
                      <Card key={strategy.id}>
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                <h4 className="font-semibold">{strategy.name}</h4>
                                <Badge variant="outline">
                                  {STRATEGY_TYPE_LABELS[strategy.strategy_type] || strategy.strategy_type}
                                </Badge>
                                {getStatusBadge(strategy.status)}
                              </div>
                              <p className="text-sm text-muted-foreground">{strategy.description}</p>
                              <div className="flex gap-4 text-sm">
                                <div className="flex items-center gap-1">
                                  <Clock className="h-4 w-4 text-muted-foreground" />
                                  <span>RTO: {strategy.achievable_rto_hours}h</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <RefreshCw className="h-4 w-4 text-muted-foreground" />
                                  <span>RPO: {strategy.achievable_rpo_hours}h</span>
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive"
                              onClick={() => deleteStrategyMutation.mutate(strategy.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Add Strategy Dialog */}
      <Dialog open={isAddStrategyOpen} onOpenChange={setIsAddStrategyOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Continuity Strategy</DialogTitle>
            <DialogDescription>
              Define a new strategy to maintain or recover this process.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Strategy Type</Label>
              <Select
                value={newStrategy.strategy_type}
                onValueChange={(value) =>
                  setNewStrategy({ ...newStrategy, strategy_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(STRATEGY_TYPE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Strategy Name</Label>
              <Input
                value={newStrategy.name}
                onChange={(e) => setNewStrategy({ ...newStrategy, name: e.target.value })}
                placeholder="e.g., Remote Work Capability"
              />
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={newStrategy.description}
                onChange={(e) => setNewStrategy({ ...newStrategy, description: e.target.value })}
                placeholder="Describe the strategy..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Activation Trigger</Label>
              <Input
                value={newStrategy.activation_trigger}
                onChange={(e) =>
                  setNewStrategy({ ...newStrategy, activation_trigger: e.target.value })
                }
                placeholder="When should this strategy be activated?"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Achievable RTO (hours)</Label>
                <Input
                  type="number"
                  min="0"
                  value={newStrategy.achievable_rto_hours}
                  onChange={(e) =>
                    setNewStrategy({
                      ...newStrategy,
                      achievable_rto_hours: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Achievable RPO (hours)</Label>
                <Input
                  type="number"
                  min="0"
                  value={newStrategy.achievable_rpo_hours}
                  onChange={(e) =>
                    setNewStrategy({
                      ...newStrategy,
                      achievable_rpo_hours: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddStrategyOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createStrategyMutation.mutate(newStrategy)}
              disabled={!newStrategy.name || createStrategyMutation.isPending}
            >
              {createStrategyMutation.isPending ? "Creating..." : "Create Strategy"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

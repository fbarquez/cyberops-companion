"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Globe,
  Shield,
  FileText,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Landmark,
  Factory,
  Car,
  Zap,
  Heart,
  Truck,
  Server,
  AlertTriangle,
  Check,
  X,
  Loader2,
  Sparkles,
  ListChecks,
  Calendar,
  Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API functions
const onboardingAPI = {
  getWizardState: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/wizard-state`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch wizard state");
    return res.json();
  },
  getIndustries: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/industries`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch industries");
    return res.json();
  },
  getCountries: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/countries`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch countries");
    return res.json();
  },
  getCompanySizes: async (token: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/company-sizes`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch company sizes");
    return res.json();
  },
  createProfile: async (token: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create profile");
    return res.json();
  },
  updateSpecialStatus: async (token: string, profileId: string, data: any) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/special-status`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update status");
    return res.json();
  },
  detectRegulations: async (token: string, profileId: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/detect-regulations`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to detect regulations");
    return res.json();
  },
  confirmRegulations: async (token: string, profileId: string, regulations: string[]) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/confirm-regulations`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ confirmed_regulations: regulations }),
    });
    if (!res.ok) throw new Error("Failed to confirm regulations");
    return res.json();
  },
  recommendFrameworks: async (token: string, profileId: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/recommend-frameworks`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get recommendations");
    return res.json();
  },
  selectFrameworks: async (token: string, profileId: string, frameworks: string[]) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/select-frameworks`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ selected_frameworks: frameworks }),
    });
    if (!res.ok) throw new Error("Failed to select frameworks");
    return res.json();
  },
  generatePlan: async (token: string, profileId: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/generate-plan`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to generate plan");
    return res.json();
  },
  completeOnboarding: async (token: string, profileId: string) => {
    const res = await fetch(`${API_URL}/api/v1/onboarding/profile/${profileId}/complete`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ create_initial_assessments: true }),
    });
    if (!res.ok) throw new Error("Failed to complete onboarding");
    return res.json();
  },
};

const STEPS = [
  { id: 1, name: "Organization", icon: Building2 },
  { id: 2, name: "Regulations", icon: Globe },
  { id: 3, name: "Frameworks", icon: Shield },
  { id: 4, name: "Plan", icon: FileText },
  { id: 5, name: "Complete", icon: CheckCircle },
];

const INDUSTRY_ICONS: Record<string, any> = {
  Landmark: Landmark,
  Factory: Factory,
  Car: Car,
  Zap: Zap,
  Heart: Heart,
  Truck: Truck,
  Server: Server,
  Building2: Building2,
};

export default function OnboardingWizard() {
  const router = useRouter();
  const { token } = useAuthStore();
  const { completeOnboarding: markOnboardingComplete } = useOnboardingStore();
  const queryClient = useQueryClient();

  const [currentStep, setCurrentStep] = useState(1);
  const [profileId, setProfileId] = useState<string | null>(null);

  // Step 1 state
  const [orgName, setOrgName] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [country, setCountry] = useState("DE");
  const [employeeCount, setEmployeeCount] = useState("");

  // Step 2 state
  const [specialStatus, setSpecialStatus] = useState({
    is_kritis_operator: false,
    is_bafin_regulated: false,
    is_essential_service: false,
    is_important_entity: false,
    supplies_to_oem: false,
  });
  const [selectedRegulations, setSelectedRegulations] = useState<string[]>([]);

  // Step 3 state
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);

  // Queries
  const { data: industries } = useQuery({
    queryKey: ["industries"],
    queryFn: () => onboardingAPI.getIndustries(token!),
    enabled: !!token,
  });

  const { data: countries } = useQuery({
    queryKey: ["countries"],
    queryFn: () => onboardingAPI.getCountries(token!),
    enabled: !!token,
  });

  const { data: companySizes } = useQuery({
    queryKey: ["company-sizes"],
    queryFn: () => onboardingAPI.getCompanySizes(token!),
    enabled: !!token,
  });

  const { data: detectedRegulations, refetch: refetchRegulations } = useQuery({
    queryKey: ["detected-regulations", profileId],
    queryFn: () => onboardingAPI.detectRegulations(token!, profileId!),
    enabled: !!token && !!profileId && currentStep >= 2,
  });

  const { data: frameworkRecommendations, refetch: refetchFrameworks } = useQuery({
    queryKey: ["framework-recommendations", profileId],
    queryFn: () => onboardingAPI.recommendFrameworks(token!, profileId!),
    enabled: !!token && !!profileId && currentStep >= 3,
  });

  const { data: compliancePlan, refetch: refetchPlan } = useQuery({
    queryKey: ["compliance-plan", profileId],
    queryFn: () => onboardingAPI.generatePlan(token!, profileId!),
    enabled: !!token && !!profileId && currentStep >= 4,
  });

  // Mutations
  const createProfileMutation = useMutation({
    mutationFn: (data: any) => onboardingAPI.createProfile(token!, data),
    onSuccess: (data) => {
      setProfileId(data.id);
      toast.success("Profile created");
      setCurrentStep(2);
    },
    onError: () => toast.error("Failed to create profile"),
  });

  const updateStatusMutation = useMutation({
    mutationFn: (data: any) => onboardingAPI.updateSpecialStatus(token!, profileId!, data),
    onSuccess: () => {
      refetchRegulations();
    },
  });

  const confirmRegulationsMutation = useMutation({
    mutationFn: (regulations: string[]) =>
      onboardingAPI.confirmRegulations(token!, profileId!, regulations),
    onSuccess: () => {
      toast.success("Regulations confirmed");
      setCurrentStep(3);
      refetchFrameworks();
    },
    onError: () => toast.error("Failed to confirm regulations"),
  });

  const selectFrameworksMutation = useMutation({
    mutationFn: (frameworks: string[]) =>
      onboardingAPI.selectFrameworks(token!, profileId!, frameworks),
    onSuccess: () => {
      toast.success("Frameworks selected");
      setCurrentStep(4);
      refetchPlan();
    },
    onError: () => toast.error("Failed to select frameworks"),
  });

  const completeMutation = useMutation({
    mutationFn: () => onboardingAPI.completeOnboarding(token!, profileId!),
    onSuccess: () => {
      markOnboardingComplete();
      toast.success("Onboarding complete!");
      setCurrentStep(5);
    },
    onError: () => toast.error("Failed to complete onboarding"),
  });

  // Auto-select applicable regulations
  useEffect(() => {
    if (detectedRegulations?.regulations) {
      const applicable = detectedRegulations.regulations
        .filter((r: any) => r.applies)
        .map((r: any) => r.regulation_id);
      setSelectedRegulations(applicable);
    }
  }, [detectedRegulations]);

  // Auto-select recommended frameworks
  useEffect(() => {
    if (frameworkRecommendations?.recommendations) {
      const recommended = frameworkRecommendations.recommendations
        .filter((f: any) => f.recommended)
        .map((f: any) => f.id);
      setSelectedFrameworks(recommended);
    }
  }, [frameworkRecommendations]);

  const handleStep1Submit = () => {
    if (!orgName || !industry || !companySize || !country) {
      toast.error("Please fill all required fields");
      return;
    }
    createProfileMutation.mutate({
      organization_name: orgName,
      industry_sector: industry,
      company_size: companySize,
      headquarters_country: country,
      employee_count: employeeCount ? parseInt(employeeCount) : null,
      operates_in_eu: true,
    });
  };

  const handleStep2Submit = () => {
    updateStatusMutation.mutate(specialStatus, {
      onSuccess: () => {
        confirmRegulationsMutation.mutate(selectedRegulations);
      },
    });
  };

  const handleStep3Submit = () => {
    if (selectedFrameworks.length === 0) {
      toast.error("Please select at least one framework");
      return;
    }
    selectFrameworksMutation.mutate(selectedFrameworks);
  };

  const handleStep4Submit = () => {
    completeMutation.mutate();
  };

  const handleGoToDashboard = () => {
    router.push("/compliance");
  };

  const progress = (currentStep / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Shield className="h-10 w-10 text-primary" />
            <h1 className="text-3xl font-bold">Welcome to ISORA</h1>
          </div>
          <p className="text-muted-foreground">
            Let's set up your compliance profile in a few easy steps
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <Progress value={progress} className="h-2 mb-4" />
          <div className="flex justify-between">
            {STEPS.map((step) => {
              const StepIcon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              return (
                <div
                  key={step.id}
                  className={`flex flex-col items-center gap-1 ${
                    isActive
                      ? "text-primary"
                      : isCompleted
                      ? "text-green-600"
                      : "text-muted-foreground"
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : isCompleted
                        ? "bg-green-100 dark:bg-green-900"
                        : "bg-muted"
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <StepIcon className="h-5 w-5" />
                    )}
                  </div>
                  <span className="text-xs font-medium hidden sm:block">{step.name}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <Card className="mb-6">
          {/* Step 1: Organization Profile */}
          {currentStep === 1 && (
            <>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Tell us about your organization
                </CardTitle>
                <CardDescription>
                  We'll use this information to determine which regulations apply to you
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="orgName">Organization Name *</Label>
                  <Input
                    id="orgName"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="Your Company GmbH"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Industry Sector *</Label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {industries?.slice(0, 12).map((ind: any) => {
                      const Icon = INDUSTRY_ICONS[ind.icon] || Building2;
                      const isSelected = industry === ind.id;
                      return (
                        <button
                          key={ind.id}
                          onClick={() => setIndustry(ind.id)}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            isSelected
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/50"
                          }`}
                        >
                          <Icon className={`h-5 w-5 mb-1 ${isSelected ? "text-primary" : ""}`} />
                          <div className="text-sm font-medium">{ind.name_en}</div>
                        </button>
                      );
                    })}
                  </div>
                  {industries?.length > 12 && (
                    <Select value={industry} onValueChange={setIndustry}>
                      <SelectTrigger>
                        <SelectValue placeholder="Or select from all industries..." />
                      </SelectTrigger>
                      <SelectContent>
                        {industries?.map((ind: any) => (
                          <SelectItem key={ind.id} value={ind.id}>
                            {ind.name_en}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Company Size *</Label>
                    <Select value={companySize} onValueChange={setCompanySize}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select size..." />
                      </SelectTrigger>
                      <SelectContent>
                        {companySizes?.map((size: any) => (
                          <SelectItem key={size.id} value={size.id}>
                            {size.name_en}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Headquarters Country *</Label>
                    <Select value={country} onValueChange={setCountry}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {countries?.map((c: any) => (
                          <SelectItem key={c.code} value={c.code}>
                            {c.name_en}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employees">Number of Employees (optional)</Label>
                  <Input
                    id="employees"
                    type="number"
                    value={employeeCount}
                    onChange={(e) => setEmployeeCount(e.target.value)}
                    placeholder="e.g., 150"
                  />
                </div>
              </CardContent>
            </>
          )}

          {/* Step 2: Regulations */}
          {currentStep === 2 && (
            <>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Applicable Regulations
                </CardTitle>
                <CardDescription>
                  Based on your profile, these regulations may apply to you
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Special Status */}
                <div className="space-y-4">
                  <Label className="text-base font-semibold">Special Regulatory Status</Label>
                  <div className="grid gap-3">
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="kritis"
                        checked={specialStatus.is_kritis_operator}
                        onCheckedChange={(checked) =>
                          setSpecialStatus({ ...specialStatus, is_kritis_operator: !!checked })
                        }
                      />
                      <Label htmlFor="kritis" className="font-normal">
                        We are a <strong>KRITIS operator</strong> (Critical Infrastructure)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="bafin"
                        checked={specialStatus.is_bafin_regulated}
                        onCheckedChange={(checked) =>
                          setSpecialStatus({ ...specialStatus, is_bafin_regulated: !!checked })
                        }
                      />
                      <Label htmlFor="bafin" className="font-normal">
                        We are <strong>BaFin regulated</strong> (Financial supervision)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="essential"
                        checked={specialStatus.is_essential_service}
                        onCheckedChange={(checked) =>
                          setSpecialStatus({ ...specialStatus, is_essential_service: !!checked })
                        }
                      />
                      <Label htmlFor="essential" className="font-normal">
                        We provide <strong>essential services</strong> (NIS2)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="oem"
                        checked={specialStatus.supplies_to_oem}
                        onCheckedChange={(checked) =>
                          setSpecialStatus({ ...specialStatus, supplies_to_oem: !!checked })
                        }
                      />
                      <Label htmlFor="oem" className="font-normal">
                        We <strong>supply to automotive OEMs</strong>
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Detected Regulations */}
                <div className="space-y-4">
                  <Label className="text-base font-semibold">Detected Regulations</Label>
                  <div className="space-y-3">
                    {detectedRegulations?.regulations?.map((reg: any) => (
                      <div
                        key={reg.regulation_id}
                        className={`p-4 rounded-lg border ${
                          reg.applies
                            ? "border-primary/50 bg-primary/5"
                            : "border-border bg-muted/30 opacity-60"
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <Checkbox
                              checked={selectedRegulations.includes(reg.regulation_id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedRegulations([...selectedRegulations, reg.regulation_id]);
                                } else {
                                  setSelectedRegulations(
                                    selectedRegulations.filter((r) => r !== reg.regulation_id)
                                  );
                                }
                              }}
                            />
                            <div>
                              <div className="font-medium flex items-center gap-2">
                                {reg.name}
                                {reg.mandatory && (
                                  <Badge variant="destructive" className="text-xs">
                                    Mandatory
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">{reg.reason}</p>
                              {reg.deadline && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Deadline: {reg.deadline}
                                </p>
                              )}
                            </div>
                          </div>
                          {reg.applies ? (
                            <Check className="h-5 w-5 text-green-600" />
                          ) : (
                            <X className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {detectedRegulations?.summary && (
                  <div className="flex gap-4 text-sm">
                    <Badge variant="default">
                      {detectedRegulations.summary.mandatory} mandatory
                    </Badge>
                    <Badge variant="secondary">
                      {detectedRegulations.summary.recommended} recommended
                    </Badge>
                  </div>
                )}
              </CardContent>
            </>
          )}

          {/* Step 3: Frameworks */}
          {currentStep === 3 && (
            <>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Implementation Frameworks
                </CardTitle>
                <CardDescription>
                  Select the frameworks you'll use to implement your security controls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  {frameworkRecommendations?.recommendations?.map((fw: any) => (
                    <div
                      key={fw.id}
                      className={`p-4 rounded-lg border ${
                        selectedFrameworks.includes(fw.id)
                          ? "border-primary bg-primary/5"
                          : "border-border"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={selectedFrameworks.includes(fw.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedFrameworks([...selectedFrameworks, fw.id]);
                            } else {
                              setSelectedFrameworks(selectedFrameworks.filter((f) => f !== fw.id));
                            }
                          }}
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <div className="font-medium flex items-center gap-2">
                              {fw.name}
                              {fw.recommended && (
                                <Badge variant="secondary" className="text-xs">
                                  <Sparkles className="h-3 w-3 mr-1" />
                                  Recommended
                                </Badge>
                              )}
                            </div>
                            <Badge variant="outline">{fw.controls_count} controls</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{fw.description}</p>
                          <p className="text-xs text-muted-foreground mt-2">
                            <strong>Why:</strong> {fw.reason}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              ~{fw.estimated_effort_days} days effort
                            </span>
                            {fw.maps_to_regulations?.length > 0 && (
                              <span>Maps to: {fw.maps_to_regulations.join(", ")}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {frameworkRecommendations && (
                  <Card className="bg-muted/50">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Total Controls: </span>
                          <strong>{frameworkRecommendations.total_controls}</strong>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Estimated Effort: </span>
                          <strong>~{frameworkRecommendations.estimated_effort_months} months</strong>
                        </div>
                      </div>
                      <div className="mt-2">
                        <span className="text-sm text-muted-foreground">Focus Areas: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {frameworkRecommendations.controls_focus?.map((focus: string) => (
                            <Badge key={focus} variant="outline" className="text-xs">
                              {focus}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </>
          )}

          {/* Step 4: Compliance Plan */}
          {currentStep === 4 && (
            <>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ListChecks className="h-5 w-5" />
                  Your Compliance Plan
                </CardTitle>
                <CardDescription>
                  Here's your personalized compliance implementation plan
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {compliancePlan && (
                  <>
                    {/* Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <div className="text-2xl font-bold">{compliancePlan.summary?.total_items}</div>
                          <div className="text-sm text-muted-foreground">Total Items</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <div className="text-2xl font-bold text-red-600">
                            {compliancePlan.summary?.by_priority?.critical}
                          </div>
                          <div className="text-sm text-muted-foreground">Critical</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <div className="text-2xl font-bold text-orange-600">
                            {compliancePlan.summary?.by_priority?.high}
                          </div>
                          <div className="text-sm text-muted-foreground">High Priority</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <div className="text-2xl font-bold">
                            {compliancePlan.summary?.estimated_effort_days}
                          </div>
                          <div className="text-sm text-muted-foreground">Effort (days)</div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Timeline */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Implementation Timeline</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {compliancePlan.timeline?.milestones?.map((milestone: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-4">
                              <div className="w-3 h-3 rounded-full bg-primary" />
                              <div className="flex-1">
                                <div className="font-medium">{milestone.name}</div>
                                {milestone.items_count && (
                                  <div className="text-sm text-muted-foreground">
                                    {milestone.items_count} items
                                  </div>
                                )}
                              </div>
                              <Badge variant={milestone.type === "regulatory" ? "destructive" : "outline"}>
                                {new Date(milestone.date).toLocaleDateString()}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Plan Items by Category */}
                    <div className="space-y-4">
                      <h3 className="font-semibold">Plan Items</h3>
                      {Object.entries(compliancePlan.items_by_category || {}).map(
                        ([category, items]: [string, any]) => (
                          <div key={category}>
                            <h4 className="text-sm font-medium text-muted-foreground mb-2">
                              {category} ({items.length})
                            </h4>
                            <div className="space-y-2">
                              {items.slice(0, 3).map((item: any) => (
                                <div
                                  key={item.id}
                                  className="flex items-center justify-between p-3 border rounded-lg"
                                >
                                  <div className="flex items-center gap-3">
                                    <Badge
                                      variant={
                                        item.priority === 1
                                          ? "destructive"
                                          : item.priority === 2
                                          ? "default"
                                          : "secondary"
                                      }
                                      className="text-xs"
                                    >
                                      {item.priority_label}
                                    </Badge>
                                    <div>
                                      <div className="font-medium text-sm">{item.title}</div>
                                      {item.control_ref && (
                                        <div className="text-xs text-muted-foreground">
                                          {item.control_ref}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    {item.owner_role && (
                                      <Badge variant="outline" className="text-xs">
                                        <Users className="h-3 w-3 mr-1" />
                                        {item.owner_role}
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              ))}
                              {items.length > 3 && (
                                <div className="text-sm text-muted-foreground text-center">
                                  + {items.length - 3} more items
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </>
          )}

          {/* Step 5: Complete */}
          {currentStep === 5 && (
            <>
              <CardHeader className="text-center">
                <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-4">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <CardTitle>You're all set!</CardTitle>
                <CardDescription>
                  Your compliance profile has been created successfully
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <Card className="bg-muted/50">
                  <CardContent className="pt-4">
                    <h3 className="font-semibold mb-3">Next Steps</h3>
                    <ul className="space-y-2">
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-600" />
                        Review and customize your compliance plan
                      </li>
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-600" />
                        Assign owners to plan items
                      </li>
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-600" />
                        Begin implementing Phase 1 controls
                      </li>
                      <li className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-600" />
                        Schedule your first risk assessment
                      </li>
                    </ul>
                  </CardContent>
                </Card>

                <div className="text-center">
                  <Button size="lg" onClick={handleGoToDashboard}>
                    Go to Compliance Hub
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </>
          )}
        </Card>

        {/* Navigation */}
        {currentStep < 5 && (
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
              disabled={currentStep === 1}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            <Button
              onClick={() => {
                if (currentStep === 1) handleStep1Submit();
                else if (currentStep === 2) handleStep2Submit();
                else if (currentStep === 3) handleStep3Submit();
                else if (currentStep === 4) handleStep4Submit();
              }}
              disabled={
                createProfileMutation.isPending ||
                confirmRegulationsMutation.isPending ||
                selectFrameworksMutation.isPending ||
                completeMutation.isPending
              }
            >
              {(createProfileMutation.isPending ||
                confirmRegulationsMutation.isPending ||
                selectFrameworksMutation.isPending ||
                completeMutation.isPending) && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              {currentStep === 4 ? "Complete Setup" : "Continue"}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

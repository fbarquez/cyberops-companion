"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  ClipboardCheck,
  AlertTriangle,
  FileText,
  Plus,
  Search,
  Filter,
  Shield,
  Clock,
  TrendingUp,
  Users,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { tprmAPI } from "@/lib/api-client";

interface DashboardStats {
  total_vendors: number;
  vendors_by_status: Record<string, number>;
  vendors_by_tier: Record<string, number>;
  vendors_by_risk_rating: Record<string, number>;
  total_assessments: number;
  assessments_pending: number;
  assessments_overdue: number;
  assessments_completed_this_month: number;
  total_findings: number;
  findings_by_severity: Record<string, number>;
  findings_open: number;
  findings_overdue: number;
  contracts_expiring_30_days: number;
  contracts_expiring_90_days: number;
  high_risk_vendors: number;
  vendors_requiring_assessment: number;
}

interface Vendor {
  id: string;
  vendor_id: string;
  name: string;
  legal_name?: string;
  description?: string;
  status: string;
  tier: string;
  category: string;
  website?: string;
  primary_contact_name?: string;
  primary_contact_email?: string;
  country?: string;
  services_provided?: string;
  current_risk_rating?: string;
  has_pii_access?: boolean;
  has_phi_access?: boolean;
  has_pci_access?: boolean;
  certifications?: string[];
  last_assessment_date?: string;
  next_assessment_due?: string;
  created_at: string;
}

interface Assessment {
  id: string;
  assessment_id: string;
  vendor_id: string;
  title: string;
  description?: string;
  assessment_type: string;
  status: string;
  overall_score?: number;
  residual_risk?: string;
  questionnaire_due_date?: string;
  initiated_date: string;
  completed_date?: string;
  assessor?: string;
}

interface Finding {
  id: string;
  finding_id: string;
  vendor_id: string;
  assessment_id: string;
  title: string;
  description?: string;
  severity: string;
  status: string;
  control_domain?: string;
  risk_score?: number;
  remediation_due_date?: string;
  created_at: string;
}

interface Contract {
  id: string;
  contract_id: string;
  vendor_id: string;
  title: string;
  description?: string;
  contract_type?: string;
  status: string;
  effective_date?: string;
  expiration_date?: string;
  has_dpa?: boolean;
  has_nda?: boolean;
  has_sla?: boolean;
  has_right_to_audit?: boolean;
  contract_value?: number;
  currency?: string;
}

interface VendorListResponse {
  items: Vendor[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface AssessmentListResponse {
  items: Assessment[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface FindingListResponse {
  items: Finding[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface ContractListResponse {
  items: Contract[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function TPRMPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [vendorStatus, setVendorStatus] = useState<string>("all");
  const [vendorTier, setVendorTier] = useState<string>("all");
  const [assessmentStatus, setAssessmentStatus] = useState<string>("all");
  const [findingSeverity, setFindingSeverity] = useState<string>("all");
  const [findingStatus, setFindingStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddVendorOpen, setIsAddVendorOpen] = useState(false);
  const [newVendor, setNewVendor] = useState({
    name: "",
    tier: "tier_3",
    category: "other",
    services_provided: "",
    primary_contact_email: "",
  });

  // Dashboard stats
  const { data: dashboardData } = useQuery({
    queryKey: ["tprm-dashboard"],
    queryFn: () => tprmAPI.getDashboard(token!) as Promise<DashboardStats>,
    enabled: !!token,
    refetchInterval: 60000,
  });

  // Vendors list
  const { data: vendorsData, refetch: refetchVendors } = useQuery({
    queryKey: ["tprm-vendors", vendorStatus, vendorTier, searchQuery],
    queryFn: () =>
      tprmAPI.listVendors(token!, {
        status: vendorStatus !== "all" ? vendorStatus : undefined,
        tier: vendorTier !== "all" ? vendorTier : undefined,
        search: searchQuery || undefined,
        size: 50,
      }) as Promise<VendorListResponse>,
    enabled: !!token && activeTab === "vendors",
  });

  // Assessments list
  const { data: assessmentsData } = useQuery({
    queryKey: ["tprm-assessments", assessmentStatus],
    queryFn: () =>
      tprmAPI.listAssessments(token!, {
        status: assessmentStatus !== "all" ? assessmentStatus : undefined,
        size: 50,
      }) as Promise<AssessmentListResponse>,
    enabled: !!token && activeTab === "assessments",
  });

  // Findings list
  const { data: findingsData } = useQuery({
    queryKey: ["tprm-findings", findingSeverity, findingStatus],
    queryFn: () =>
      tprmAPI.listFindings(token!, {
        severity: findingSeverity !== "all" ? findingSeverity : undefined,
        status: findingStatus !== "all" ? findingStatus : undefined,
        size: 50,
      }) as Promise<FindingListResponse>,
    enabled: !!token && activeTab === "findings",
  });

  // Contracts list
  const { data: contractsData } = useQuery({
    queryKey: ["tprm-contracts"],
    queryFn: () =>
      tprmAPI.listContracts(token!, {
        size: 50,
      }) as Promise<ContractListResponse>,
    enabled: !!token && activeTab === "contracts",
  });

  const handleCreateVendor = async () => {
    if (!token || !newVendor.name) return;

    try {
      await tprmAPI.createVendor(token, newVendor);
      setIsAddVendorOpen(false);
      setNewVendor({
        name: "",
        tier: "tier_3",
        category: "other",
        services_provided: "",
        primary_contact_email: "",
      });
      refetchVendors();
    } catch (error) {
      console.error("Failed to create vendor:", error);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      active: "default",
      approved: "default",
      completed: "default",
      prospect: "secondary",
      under_review: "secondary",
      draft: "secondary",
      on_hold: "outline",
      terminated: "destructive",
      expired: "destructive",
      overdue: "destructive",
    };
    return variants[status] || "secondary";
  };

  const getRiskBadgeVariant = (risk: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "destructive",
      medium: "secondary",
      low: "outline",
      minimal: "outline",
    };
    return variants[risk] || "secondary";
  };

  const getSeverityBadgeVariant = (severity: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      critical: "destructive",
      high: "destructive",
      medium: "secondary",
      low: "outline",
      informational: "outline",
    };
    return variants[severity] || "secondary";
  };

  const getTierLabel = (tier: string) => {
    const labels: Record<string, string> = {
      tier_1: t("tprm.tier1"),
      tier_2: t("tprm.tier2"),
      tier_3: t("tprm.tier3"),
      tier_4: t("tprm.tier4"),
    };
    return labels[tier] || tier;
  };

  const stats = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("tprm.title")}</h1>
          <p className="text-muted-foreground">
            Manage vendor risk assessments, findings, and contracts
          </p>
        </div>
        <Dialog open={isAddVendorOpen} onOpenChange={setIsAddVendorOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t("tprm.addVendor")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("tprm.addVendor")}</DialogTitle>
              <DialogDescription>
                Add a new third-party vendor to the risk management system.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Vendor Name</Label>
                <Input
                  id="name"
                  value={newVendor.name}
                  onChange={(e) =>
                    setNewVendor({ ...newVendor, name: e.target.value })
                  }
                  placeholder="Vendor name"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tier">Tier</Label>
                  <Select
                    value={newVendor.tier}
                    onValueChange={(v) =>
                      setNewVendor({ ...newVendor, tier: v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tier_1">{t("tprm.tier1")}</SelectItem>
                      <SelectItem value="tier_2">{t("tprm.tier2")}</SelectItem>
                      <SelectItem value="tier_3">{t("tprm.tier3")}</SelectItem>
                      <SelectItem value="tier_4">{t("tprm.tier4")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={newVendor.category}
                    onValueChange={(v) =>
                      setNewVendor({ ...newVendor, category: v })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cloud_services">
                        {t("tprm.cloudServices")}
                      </SelectItem>
                      <SelectItem value="software">
                        {t("tprm.softwareVendor")}
                      </SelectItem>
                      <SelectItem value="hardware">
                        {t("tprm.hardware")}
                      </SelectItem>
                      <SelectItem value="professional_services">
                        {t("tprm.professionalServices")}
                      </SelectItem>
                      <SelectItem value="managed_services">
                        {t("tprm.managedServices")}
                      </SelectItem>
                      <SelectItem value="data_processing">
                        {t("tprm.dataProcessing")}
                      </SelectItem>
                      <SelectItem value="other">{t("tprm.other")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Contact Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={newVendor.primary_contact_email}
                  onChange={(e) =>
                    setNewVendor({
                      ...newVendor,
                      primary_contact_email: e.target.value,
                    })
                  }
                  placeholder="contact@vendor.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="services">Services Provided</Label>
                <Textarea
                  id="services"
                  value={newVendor.services_provided}
                  onChange={(e) =>
                    setNewVendor({
                      ...newVendor,
                      services_provided: e.target.value,
                    })
                  }
                  placeholder="Describe the services provided by this vendor..."
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsAddVendorOpen(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleCreateVendor} disabled={!newVendor.name}>
                Create Vendor
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            {t("tprm.dashboard")}
          </TabsTrigger>
          <TabsTrigger value="vendors" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            {t("tprm.vendors")}
          </TabsTrigger>
          <TabsTrigger value="assessments" className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            {t("tprm.assessments")}
          </TabsTrigger>
          <TabsTrigger value="findings" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {t("tprm.findings")}
          </TabsTrigger>
          <TabsTrigger value="contracts" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {t("tprm.contracts")}
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.totalVendors")}
                </CardTitle>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.total_vendors || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.vendors_by_status?.active || 0} {t("tprm.active")}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.highRiskVendors")}
                </CardTitle>
                <Shield className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-destructive">
                  {stats?.high_risk_vendors || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Critical or high risk rating
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.pendingAssessments")}
                </CardTitle>
                <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.assessments_pending || 0}
                </div>
                <p className="text-xs text-destructive">
                  {stats?.assessments_overdue || 0} {t("tprm.overdueAssessments")}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.openFindings")}
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.findings_open || 0}
                </div>
                <p className="text-xs text-destructive">
                  {stats?.findings_overdue || 0} {t("tprm.overdueFindings")}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Second Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.expiringContracts30")}
                </CardTitle>
                <Clock className="h-4 w-4 text-warning" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.contracts_expiring_30_days || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.contracts_expiring_90_days || 0} in 90 days
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("tprm.vendorsRequiringAssessment")}
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.vendors_requiring_assessment || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Assessment overdue or due
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Findings by Severity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="destructive">
                    {stats?.findings_by_severity?.critical || 0} Critical
                  </Badge>
                  <Badge variant="destructive">
                    {stats?.findings_by_severity?.high || 0} High
                  </Badge>
                  <Badge variant="secondary">
                    {stats?.findings_by_severity?.medium || 0} Medium
                  </Badge>
                  <Badge variant="outline">
                    {stats?.findings_by_severity?.low || 0} Low
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Vendors by Tier
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="destructive">
                    {stats?.vendors_by_tier?.tier_1 || 0} T1
                  </Badge>
                  <Badge variant="secondary">
                    {stats?.vendors_by_tier?.tier_2 || 0} T2
                  </Badge>
                  <Badge variant="outline">
                    {stats?.vendors_by_tier?.tier_3 || 0} T3
                  </Badge>
                  <Badge variant="outline">
                    {stats?.vendors_by_tier?.tier_4 || 0} T4
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Vendors Tab */}
        <TabsContent value="vendors" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search vendors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={vendorStatus} onValueChange={setVendorStatus}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="prospect">{t("tprm.prospect")}</SelectItem>
                <SelectItem value="under_review">{t("tprm.underReview")}</SelectItem>
                <SelectItem value="approved">{t("tprm.approved")}</SelectItem>
                <SelectItem value="active">{t("tprm.active")}</SelectItem>
                <SelectItem value="on_hold">{t("tprm.onHold")}</SelectItem>
                <SelectItem value="terminated">{t("tprm.terminated")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={vendorTier} onValueChange={setVendorTier}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="tier_1">{t("tprm.tier1")}</SelectItem>
                <SelectItem value="tier_2">{t("tprm.tier2")}</SelectItem>
                <SelectItem value="tier_3">{t("tprm.tier3")}</SelectItem>
                <SelectItem value="tier_4">{t("tprm.tier4")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Vendors List */}
          <div className="grid gap-4">
            {vendorsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("tprm.noVendors")}</p>
                </CardContent>
              </Card>
            )}
            {vendorsData?.items?.map((vendor) => (
              <Card key={vendor.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{vendor.name}</h3>
                        <Badge variant="outline">{vendor.vendor_id}</Badge>
                        <Badge variant={getStatusBadgeVariant(vendor.status)}>
                          {vendor.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {vendor.services_provided || "No services description"}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        <Badge variant="secondary">
                          {getTierLabel(vendor.tier)}
                        </Badge>
                        {vendor.current_risk_rating && (
                          <Badge variant={getRiskBadgeVariant(vendor.current_risk_rating)}>
                            {vendor.current_risk_rating} risk
                          </Badge>
                        )}
                        {vendor.has_pii_access && (
                          <Badge variant="outline">{t("tprm.piiAccess")}</Badge>
                        )}
                        {vendor.has_pci_access && (
                          <Badge variant="outline">{t("tprm.pciAccess")}</Badge>
                        )}
                        {vendor.certifications?.map((cert) => (
                          <Badge key={cert} variant="outline">
                            {cert}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {vendor.website && (
                        <a
                          href={vendor.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                          Website <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                      {vendor.next_assessment_due && (
                        <p className="text-xs text-muted-foreground">
                          Next assessment: {new Date(vendor.next_assessment_due).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Assessments Tab */}
        <TabsContent value="assessments" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <Select value={assessmentStatus} onValueChange={setAssessmentStatus}>
              <SelectTrigger className="w-[200px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">{t("tprm.draft")}</SelectItem>
                <SelectItem value="questionnaire_sent">{t("tprm.questionnaireSent")}</SelectItem>
                <SelectItem value="questionnaire_received">{t("tprm.questionnaireReceived")}</SelectItem>
                <SelectItem value="under_review">{t("tprm.underAssessmentReview")}</SelectItem>
                <SelectItem value="completed">{t("tprm.completed")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Assessments List */}
          <div className="grid gap-4">
            {assessmentsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <ClipboardCheck className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("tprm.noAssessments")}</p>
                </CardContent>
              </Card>
            )}
            {assessmentsData?.items?.map((assessment) => (
              <Card key={assessment.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{assessment.title}</h3>
                        <Badge variant="outline">{assessment.assessment_id}</Badge>
                        <Badge variant={getStatusBadgeVariant(assessment.status)}>
                          {assessment.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {assessment.description || "No description"}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        <Badge variant="secondary">{assessment.assessment_type}</Badge>
                        {assessment.overall_score !== undefined && (
                          <Badge variant={assessment.overall_score >= 70 ? "default" : "destructive"}>
                            Score: {assessment.overall_score}%
                          </Badge>
                        )}
                        {assessment.residual_risk && (
                          <Badge variant={getRiskBadgeVariant(assessment.residual_risk)}>
                            {assessment.residual_risk} residual risk
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-sm">
                      {assessment.assessor && (
                        <span className="text-muted-foreground">
                          Assessor: {assessment.assessor}
                        </span>
                      )}
                      <span className="text-muted-foreground">
                        Started: {new Date(assessment.initiated_date).toLocaleDateString()}
                      </span>
                      {assessment.questionnaire_due_date && (
                        <span className="text-muted-foreground">
                          Due: {new Date(assessment.questionnaire_due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Findings Tab */}
        <TabsContent value="findings" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <Select value={findingSeverity} onValueChange={setFindingSeverity}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">{t("tprm.critical")}</SelectItem>
                <SelectItem value="high">{t("tprm.high")}</SelectItem>
                <SelectItem value="medium">{t("tprm.medium")}</SelectItem>
                <SelectItem value="low">{t("tprm.low")}</SelectItem>
                <SelectItem value="informational">{t("tprm.informational")}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={findingStatus} onValueChange={setFindingStatus}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">{t("tprm.open")}</SelectItem>
                <SelectItem value="in_progress">{t("tprm.inProgress")}</SelectItem>
                <SelectItem value="remediated">{t("tprm.remediated")}</SelectItem>
                <SelectItem value="accepted">{t("tprm.accepted")}</SelectItem>
                <SelectItem value="closed">{t("tprm.closed")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Findings List */}
          <div className="grid gap-4">
            {findingsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("tprm.noFindings")}</p>
                </CardContent>
              </Card>
            )}
            {findingsData?.items?.map((finding) => (
              <Card key={finding.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{finding.title}</h3>
                        <Badge variant="outline">{finding.finding_id}</Badge>
                        <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                          {finding.severity}
                        </Badge>
                        <Badge variant={getStatusBadgeVariant(finding.status)}>
                          {finding.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {finding.description || "No description"}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {finding.control_domain && (
                          <Badge variant="secondary">{finding.control_domain}</Badge>
                        )}
                        {finding.risk_score && (
                          <Badge variant="outline">Risk Score: {finding.risk_score}</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-sm">
                      {finding.remediation_due_date && (
                        <span className="text-muted-foreground">
                          Due: {new Date(finding.remediation_due_date).toLocaleDateString()}
                        </span>
                      )}
                      <span className="text-muted-foreground">
                        Created: {new Date(finding.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Contracts Tab */}
        <TabsContent value="contracts" className="space-y-4">
          {/* Contracts List */}
          <div className="grid gap-4">
            {contractsData?.items?.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t("tprm.noContracts")}</p>
                </CardContent>
              </Card>
            )}
            {contractsData?.items?.map((contract) => (
              <Card key={contract.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{contract.title}</h3>
                        <Badge variant="outline">{contract.contract_id}</Badge>
                        <Badge variant={getStatusBadgeVariant(contract.status)}>
                          {contract.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {contract.description || contract.contract_type || "No description"}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {contract.has_dpa && (
                          <Badge variant="outline">{t("tprm.dpa")}</Badge>
                        )}
                        {contract.has_nda && (
                          <Badge variant="outline">{t("tprm.nda")}</Badge>
                        )}
                        {contract.has_sla && (
                          <Badge variant="outline">{t("tprm.sla")}</Badge>
                        )}
                        {contract.has_right_to_audit && (
                          <Badge variant="outline">{t("tprm.rightToAudit")}</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-sm">
                      {contract.contract_value && (
                        <span className="font-medium">
                          {contract.contract_value.toLocaleString()} {contract.currency || "USD"}
                        </span>
                      )}
                      {contract.effective_date && (
                        <span className="text-muted-foreground">
                          Start: {new Date(contract.effective_date).toLocaleDateString()}
                        </span>
                      )}
                      {contract.expiration_date && (
                        <span className="text-muted-foreground">
                          Expires: {new Date(contract.expiration_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

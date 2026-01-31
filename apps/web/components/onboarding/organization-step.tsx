"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Building2, ArrowRight, ArrowLeft } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";

interface OrganizationStepProps {
  onNext: () => void;
  onBack: () => void;
}

const organizationSizes = [
  { value: "1-10", label: "1-10 employees" },
  { value: "11-50", label: "11-50 employees" },
  { value: "51-200", label: "51-200 employees" },
  { value: "201-500", label: "201-500 employees" },
  { value: "501-1000", label: "501-1,000 employees" },
  { value: "1000+", label: "1,000+ employees" },
];

const industries = [
  { value: "technology", label: "Technology" },
  { value: "finance", label: "Finance & Banking" },
  { value: "healthcare", label: "Healthcare" },
  { value: "government", label: "Government" },
  { value: "education", label: "Education" },
  { value: "retail", label: "Retail & E-commerce" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "energy", label: "Energy & Utilities" },
  { value: "consulting", label: "Consulting & Services" },
  { value: "other", label: "Other" },
];

const jobTitles = [
  { value: "ciso", label: "CISO / Security Director" },
  { value: "security_manager", label: "Security Manager" },
  { value: "security_analyst", label: "Security Analyst" },
  { value: "soc_analyst", label: "SOC Analyst" },
  { value: "incident_responder", label: "Incident Responder" },
  { value: "compliance_officer", label: "Compliance Officer" },
  { value: "it_manager", label: "IT Manager" },
  { value: "developer", label: "Developer / DevSecOps" },
  { value: "other", label: "Other" },
];

export function OrganizationStep({ onNext, onBack }: OrganizationStepProps) {
  const { data, updateData } = useOnboardingStore();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = () => {
    const newErrors: Record<string, string> = {};

    if (!data.organizationName.trim()) {
      newErrors.organizationName = "Organization name is required";
    }
    if (!data.organizationSize) {
      newErrors.organizationSize = "Please select organization size";
    }
    if (!data.industry) {
      newErrors.industry = "Please select your industry";
    }
    if (!data.jobTitle) {
      newErrors.jobTitle = "Please select your role";
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      onNext();
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Building2 className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Tell us about your organization</h2>
        <p className="text-muted-foreground">
          This helps us customize your experience
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="orgName">Organization Name</Label>
          <Input
            id="orgName"
            placeholder="Acme Corporation"
            value={data.organizationName}
            onChange={(e) => updateData({ organizationName: e.target.value })}
          />
          {errors.organizationName && (
            <p className="text-sm text-destructive">{errors.organizationName}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Organization Size</Label>
          <Select
            value={data.organizationSize}
            onValueChange={(value) => updateData({ organizationSize: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select size" />
            </SelectTrigger>
            <SelectContent>
              {organizationSizes.map((size) => (
                <SelectItem key={size.value} value={size.value}>
                  {size.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.organizationSize && (
            <p className="text-sm text-destructive">{errors.organizationSize}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Industry</Label>
          <Select
            value={data.industry}
            onValueChange={(value) => updateData({ industry: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select industry" />
            </SelectTrigger>
            <SelectContent>
              {industries.map((industry) => (
                <SelectItem key={industry.value} value={industry.value}>
                  {industry.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.industry && (
            <p className="text-sm text-destructive">{errors.industry}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Your Role</Label>
          <Select
            value={data.jobTitle}
            onValueChange={(value) => updateData({ jobTitle: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select your role" />
            </SelectTrigger>
            <SelectContent>
              {jobTitles.map((job) => (
                <SelectItem key={job.value} value={job.value}>
                  {job.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.jobTitle && (
            <p className="text-sm text-destructive">{errors.jobTitle}</p>
          )}
        </div>
      </div>

      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={handleSubmit}>
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

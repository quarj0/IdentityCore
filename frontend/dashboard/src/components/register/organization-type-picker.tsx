"use client";

import { useState } from "react";
import {
  Briefcase,
  Building2,
  GraduationCap,
  HeartPulse,
  Landmark,
  Rocket,
  Users,
} from "lucide-react";
import { cn, Input, Label } from "@identitycore/ui";

const ORGANIZATION_TYPES = [
  {
    value: "government",
    label: "Government",
    description: "Public agencies and civic platforms",
    icon: Landmark,
  },
  {
    value: "financial_institution",
    label: "Financial institution",
    description: "Banks, fintechs, and lenders",
    icon: Building2,
  },
  {
    value: "educational_institution",
    label: "Education",
    description: "Schools, universities, and exam bodies",
    icon: GraduationCap,
  },
  {
    value: "healthcare_provider",
    label: "Healthcare",
    description: "Clinics, hospitals, and telehealth",
    icon: HeartPulse,
  },
  {
    value: "enterprise",
    label: "Enterprise",
    description: "Internal workforce or customer operations",
    icon: Building2,
  },
  {
    value: "ngo",
    label: "NGO",
    description: "Non-profits and development programs",
    icon: Users,
  },
  {
    value: "startup",
    label: "Startup",
    description: "Early-stage products and new teams",
    icon: Rocket,
  },
  {
    value: "other",
    label: "Other",
    description: "A custom or mixed organization type",
    icon: Briefcase,
  },
] as const;

interface OrganizationTypePickerProps {
  id?: string;
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function OrganizationTypePicker({
  id = "organizationType",
  label = "Organization type",
  value = "",
  onChange,
}: OrganizationTypePickerProps) {
  const [selectedValue, setSelectedValue] = useState(value);

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <Label htmlFor={id}>{label}</Label>
        <Input id={id} value={selectedValue} readOnly className="sr-only" />
      </div>

      <div
        role="radiogroup"
        aria-label={label}
        className="grid gap-3 sm:grid-cols-2"
      >
        {ORGANIZATION_TYPES.map((type) => {
          const Icon = type.icon;
          const isSelected = selectedValue === type.value;

          return (
            <label
              key={type.value}
              className={cn(
                "group flex cursor-pointer items-start gap-3 rounded-2xl border bg-white p-4 text-left shadow-sm transition-all",
                isSelected
                  ? "border-blue-500 bg-blue-50/60 ring-2 ring-blue-100"
                  : "border-slate-200 hover:border-blue-200 hover:bg-slate-50",
              )}
            >
              <input
                type="radio"
                name={id}
                value={type.value}
                checked={isSelected}
                onChange={() => {
                  setSelectedValue(type.value);
                  onChange?.(type.value);
                }}
                className="sr-only"
              />

              <div
                className={cn(
                  "flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl ring-1",
                  isSelected
                    ? "bg-blue-100 text-blue-700 ring-blue-200"
                    : "bg-slate-50 text-slate-600 ring-slate-200 group-hover:bg-blue-50 group-hover:text-blue-700 group-hover:ring-blue-100",
                )}
              >
                <Icon className="h-4 w-4" />
              </div>

              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900">
                  {type.label}
                </p>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  {type.description}
                </p>
              </div>
            </label>
          );
        })}
      </div>

      <p className="text-xs leading-5 text-muted-foreground">
        Choose the option that best matches the primary environment where your
        identity workflows will run.
      </p>
    </div>
  );
}

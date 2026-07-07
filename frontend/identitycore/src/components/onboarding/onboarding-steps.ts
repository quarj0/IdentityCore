import {
  Circle,
  FileText,
  Fingerprint,
  Rocket,
  ShieldCheck,
} from "lucide-react";
import type { OnboardingStep } from "@/components/onboarding/onboarding-checklist";

export const onboardingSteps: OnboardingStep[] = [
  {
    title: "Organization profile",
    description: "Add registration, address, website, and support details.",
    status: "current",
    icon: FileText,
    actionHref: "/onboarding/organization-profile",
    actionLabel: "Complete profile",
  },
  {
    title: "Organization verification",
    description: "Upload supporting organization documents for review.",
    status: "upcoming",
    icon: ShieldCheck,
    actionHref: "/onboarding/organization-verification",
    actionLabel: "Prepare documents",
  },
  {
    title: "Administrator identity",
    description: "Verify the primary administrator using IdentityCore.",
    status: "upcoming",
    icon: Fingerprint,
    actionHref: "/onboarding/admin-identity",
    actionLabel: "Start identity check",
  },
  {
    title: "First workflow",
    description: "Create or clone your first identity workflow.",
    status: "upcoming",
    icon: Rocket,
    actionHref: "/onboarding/first-workflow",
    actionLabel: "Choose a workflow",
  },
  {
    title: "Production approval",
    description: "Submit your workspace for production access.",
    status: "upcoming",
    icon: Circle,
    actionHref: "/onboarding/production-approval",
    actionLabel: "Review approval",
  },
];

export const onboardingStepPaths = [
  "/onboarding/organization-profile",
  "/onboarding/organization-verification",
  "/onboarding/admin-identity",
  "/onboarding/first-workflow",
  "/onboarding/production-approval",
];

export function getOnboardingStepIndex(pathname: string) {
  return onboardingStepPaths.indexOf(pathname);
}

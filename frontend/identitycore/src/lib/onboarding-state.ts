"use client";

import type { OnboardingState } from "@/lib/onboarding-api";

export function getOnboardingRoute(state: OnboardingState | null) {
  if (!state) {
    return "/onboarding";
  }

  switch (state.currentStep) {
    case "email_verification":
      return "/verify-email";
    case "organization_verification":
      return "/onboarding/organization-verification";
    case "administrator_identity_verification":
      return "/onboarding/admin-identity";
    case "platform_review":
      return "/onboarding/production-approval";
    case "active":
      return "/onboarding";
    default:
      return "/onboarding";
  }
}

export function buildOnboardingSteps(state: OnboardingState | null) {
  const currentStep = state?.currentStep ?? "organization_verification";
  const organizationVerificationNeedsAttention = [
    "needs_information",
    "rejected",
  ].includes(state?.organizationVerificationReviewStatus || "");
  const organizationVerificationDone =
    Boolean(state?.organizationVerificationSubmittedAt) &&
    !organizationVerificationNeedsAttention &&
    currentStep !== "organization_verification";
  const adminIdentityDone = ["submitted", "verified"].includes(
    state?.administratorIdentityVerificationStatus || "",
  );
  const productionPending =
    state?.platformReviewStatus === "pending_review" ||
    state?.onboardingStatus === "platform_review_pending";
  const active = state?.onboardingStatus === "active";

  return [
    {
      title: "Organization profile",
      description: "Review the workspace details captured during registration.",
      status:
        currentStep === "organization_verification" ||
        currentStep === "email_verification"
          ? "current"
          : "complete",
      actionHref: "/onboarding/organization-profile",
      actionLabel: "Review profile",
    },
    {
      title: "Organization verification",
      description: "Submit your registration details for workspace review.",
      status:
        currentStep === "organization_verification" ||
        organizationVerificationNeedsAttention
          ? "current"
          : organizationVerificationDone
            ? "complete"
            : "upcoming",
      actionHref: "/onboarding/organization-verification",
      actionLabel: "Submit details",
    },
    {
      title: "Administrator identity",
      description: "Complete the administrator identity verification.",
      status: adminIdentityDone
        ? "complete"
        : currentStep === "administrator_identity_verification"
          ? "current"
          : "upcoming",
      actionHref: "/onboarding/admin-identity",
      actionLabel: "Start verification",
    },
    {
      title: "First workflow",
      description: "Choose the first workflow template for your workspace.",
      status:
        adminIdentityDone || productionPending || active ? "current" : "upcoming",
      actionHref: "/onboarding/first-workflow",
      actionLabel: "Choose workflow",
    },
    {
      title: "Production approval",
      description: "Track your workspace review and production readiness.",
      status: active
        ? "complete"
        : productionPending
          ? "current"
          : "upcoming",
      actionHref: "/onboarding/production-approval",
      actionLabel: "Review status",
    },
  ] as const;
}

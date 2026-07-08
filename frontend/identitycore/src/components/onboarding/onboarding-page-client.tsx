"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, FolderCheck, Loader2 } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
  toast,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { OnboardingChecklist } from "@/components/onboarding/onboarding-checklist";
import { OnboardingTierCard } from "@/components/onboarding/onboarding-tier-card";
import { getErrorMessage } from "@/lib/api-client";
import { fetchCurrentOnboarding, type OnboardingState } from "@/lib/onboarding-api";
import { buildOnboardingSteps } from "@/lib/onboarding-state";

export function OnboardingPageClient() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentOnboarding()
      .then(setState)
      .catch((error) => {
        toast({
          title: "Unable to load onboarding",
          description: getErrorMessage(error),
          variant: "destructive",
        });
      })
      .finally(() => setLoading(false));
  }, []);

  const steps = useMemo(() => buildOnboardingSteps(state), [state]);
  const completedSteps = steps.filter((step) => step.status === "complete").length;
  const currentStep = steps.find((step) => step.status === "current");
  const progressValue = Math.round((completedSteps / steps.length) * 100);

  return (
    <AuthShell
      badge="Workspace onboarding"
      title="Complete your organization setup."
      description="Your workspace starts in sandbox. Complete these steps to prepare for production approval."
      layout="stacked"
    >
      {loading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardDescription>Account status</CardDescription>
                  <CardTitle>
                    {state?.emailVerifiedAt ? "Email verified" : "Email pending"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {state?.emailVerifiedAt
                        ? "Your administrator email is confirmed and onboarding can continue."
                        : "Verify the administrator email to unlock the next onboarding step."}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardDescription>Current focus</CardDescription>
                  <CardTitle>{currentStep?.title ?? "Getting started"}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-6 text-muted-foreground">
                    {currentStep?.description ??
                      "Work through the next required step to keep onboarding moving."}
                  </p>
                </CardContent>
              </Card>

              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader className="pb-3">
                  <CardDescription>Progress</CardDescription>
                  <CardTitle>{progressValue}% complete</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Progress value={progressValue} />
                  <p className="text-sm leading-6 text-muted-foreground">
                    {completedSteps} of {steps.length} onboarding milestones completed.
                  </p>
                </CardContent>
              </Card>
            </div>

            <OnboardingChecklist
              steps={steps.map((step, index) => ({
                ...step,
                icon:
                  index === 0
                    ? FolderCheck
                    : index === 1
                      ? FolderCheck
                      : index === 2
                        ? CheckCircle2
                        : FolderCheck,
              }))}
            />
          </div>

          <div className="space-y-4">
            <OnboardingTierCard
              title="Current tier"
              description="Your workspace is currently in sandbox while onboarding is completed."
              summary={`Tier ${state?.organizationTier ?? "trial"}: complete onboarding and await platform approval before production access is enabled.`}
              ctaHref="/templates"
              ctaLabel="Choose first workflow"
              badge={(state?.organizationTier ?? "trial").toUpperCase()}
              features={[
                "Review onboarding status in one place",
                "Complete organization and administrator verification",
                "Prepare workflow choices before production review",
              ]}
            />

            <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <Badge variant="secondary" className="w-fit rounded-full">
                  Workspace state
                </Badge>
                <CardTitle className="mt-2">
                  {state?.organizationName ?? "Organization workspace"}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>Organization status: {state?.organizationStatus ?? "unknown"}</p>
                <p>Tenant status: {state?.tenantStatus ?? "unknown"}</p>
                <p>Platform review: {state?.platformReviewStatus ?? "not_started"}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AuthShell>
  );
}

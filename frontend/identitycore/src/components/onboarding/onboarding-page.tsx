import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
} from "@identitycore/ui";
import {
  CheckCircle2,
  FolderCheck,
} from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import {
  OnboardingChecklist,
} from "@/components/onboarding/onboarding-checklist";
import { OnboardingTierCard } from "@/components/onboarding/onboarding-tier-card";
import { onboardingSteps } from "@/components/onboarding/onboarding-steps";

export function OnboardingPageContent() {
  const completedSteps = onboardingSteps.filter(
    (step) => step.status === "complete",
  ).length;
  const currentStep = onboardingSteps.find((step) => step.status === "current");
  const progressValue = Math.round(
    (completedSteps / onboardingSteps.length) * 100,
  );

  return (
    <AuthShell
      badge="Workspace onboarding"
      title="Complete your organization setup."
      description="Your workspace starts in sandbox. Complete these steps to prepare for production approval."
      layout="stacked"
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
              <CardHeader className="pb-3">
                <CardDescription>Account status</CardDescription>
                <CardTitle>Email verified</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Your administrator email is already confirmed. You can go
                    straight into organization setup.
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
                  {completedSteps} of {onboardingSteps.length} organization
                  setup steps completed.
                </p>
              </CardContent>
            </Card>
          </div>

          <OnboardingChecklist steps={onboardingSteps} />
        </div>

        <div className="space-y-4">
          <OnboardingTierCard
            title="Current tier"
            description="Your workspace is currently in sandbox while onboarding is completed."
            summary="Tier 0 — Trial: Sandbox workflows, templates, test API keys, and mock verification responses."
            ctaHref="/templates"
            ctaLabel="Choose first workflow"
            badge="Sandbox"
            features={[
              "Test API keys and mock provider responses",
              "Access workflow templates before production review",
              "Prepare internal approvals and integration work",
            ]}
          />

          <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <Badge variant="secondary" className="w-fit rounded-full">
                Next up
              </Badge>
              <CardTitle className="mt-2">What to prepare now</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Legal organization details and support contact",
                "Verification documents for organization review",
                "Administrator identity documents",
              ].map((item) => (
                <div
                  key={item}
                  className="flex gap-3 text-sm text-muted-foreground"
                >
                  <FolderCheck className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                  {item}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-slate-200 bg-slate-950 text-white shadow-sm">
            <CardHeader>
              <CardTitle>Production path</CardTitle>
              <CardDescription className="text-slate-300">
                Move from sandbox to verified production access in clear stages.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Complete organization profile",
                "Pass organization and admin verification",
                "Choose a workflow and submit for review",
              ].map((item, index) => (
                <div
                  key={item}
                  className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3"
                >
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-xs font-semibold text-blue-200">
                    {index + 1}
                  </div>
                  <p className="text-sm text-slate-100">{item}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </AuthShell>
  );
}

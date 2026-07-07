import { Rocket, ShieldCheck } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function ProductionApprovalPage() {
  return (
    <OnboardingPageShell
      eyebrow="Production approval"
      title="Submit your workspace for production access."
      description="Production access is reviewed to protect IdentityCore, organizations, and verification subjects from abuse."
      pathname="/onboarding/production-approval"
    >
      <Card className="max-w-2xl rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <Rocket className="mb-4 h-7 w-7 text-blue-600" />
          <CardTitle>Ready for review</CardTitle>
          <CardDescription className="leading-7">
            Once your organization profile, documents, administrator identity, and first workflow are complete, submit for production review.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 h-5 w-5 text-blue-600" />
              <p className="text-sm leading-7 text-muted-foreground">
                Approval unlocks production workflows, production API keys, webhooks, and live verification sessions.
              </p>
            </div>
          </div>

          <Button type="button" size="lg" className="w-full rounded-xl sm:w-auto">
            Submit for production approval
          </Button>
        </CardContent>
      </Card>
    </OnboardingPageShell>
  );
}

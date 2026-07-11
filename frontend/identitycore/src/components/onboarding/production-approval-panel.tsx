"use client";

import { useEffect, useState } from "react";
import { Loader2, Rocket, ShieldCheck } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import { fetchCurrentOnboarding, type OnboardingState } from "@/lib/onboarding-api";

export function ProductionApprovalPanel() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const dashboardUrl = process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

  useEffect(() => {
    fetchCurrentOnboarding()
      .then(setState)
      .catch((error) => {
        setErrorMessage(getErrorMessage(error));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!state || !["submitted", "verified"].includes(state.administratorIdentityVerificationStatus)) return;
    const timer = window.setTimeout(() => window.location.assign(dashboardUrl), 1500);
    return () => window.clearTimeout(timer);
  }, [dashboardUrl, state]);

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-4">
      {errorMessage ? (
        <InlineStatus
          kind="error"
          title="Unable to load production approval state"
          message={errorMessage}
        />
      ) : null}

      <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <Rocket className="mb-4 h-7 w-7 text-blue-600" />
          <CardTitle>Production approval status</CardTitle>
          <CardDescription className="leading-7">
            The onboarding workflow is currently `{state?.platformReviewStatus ?? "not_started"}`.
            Tenant users do not submit a separate production request in the current API;
            the platform review begins after administrator identity submission.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4"><p className="text-sm text-blue-900">Your review continues in the background. You can use sandbox features while production approval is pending.</p><Button asChild className="mt-3"><a href={dashboardUrl}>Go to dashboard now</a></Button></div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 h-5 w-5 text-blue-600" />
              <p className="text-sm leading-7 text-muted-foreground">
                Organization status: {state?.organizationStatus ?? "unknown"}.
                Tenant status: {state?.tenantStatus ?? "unknown"}.
              </p>
            </div>
          </div>

          {state?.platformReviewNote ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-muted-foreground">
              Review note: {state.platformReviewNote}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

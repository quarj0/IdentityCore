"use client";

import { useEffect, useState } from "react";
import { Loader2, Rocket, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, toast } from "@identitycore/ui";
import { getErrorMessage } from "@/lib/api-client";
import { fetchCurrentOnboarding, type OnboardingState } from "@/lib/onboarding-api";

export function ProductionApprovalPanel() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentOnboarding()
      .then(setState)
      .catch((error) => {
        toast({
          title: "Unable to load production approval state",
          description: getErrorMessage(error),
          variant: "destructive",
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <Card className="max-w-2xl rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
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
  );
}

"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Clock3, Loader2 } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, Organization } from "@/lib/dashboard-api";

export function ApprovalStatusPage() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [error, setError] = useState("");
  const home = process.env.NEXT_PUBLIC_IDENTITYCORE_ORIGIN ?? "http://localhost:3001";
  useEffect(() => { dashboardApi.organization().then(setOrganization).catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load approval status.")); }, []);
  if (error) return <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>;
  if (!organization) return <div className="flex min-h-64 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-blue-600" /></div>;

  const onboarding = (organization.settings.onboarding ?? {}) as Record<string, unknown>;
  const review = (onboarding.platform_review ?? {}) as Record<string, unknown>;
  const onboardingStatus = String(onboarding.status ?? organization.status);
  const needsInformation = onboardingStatus === "needs_information" || String(review.status ?? "") === "needs_information";
  const approved = organization.status === "active" || onboardingStatus === "active";

  return <div className="space-y-8"><PageHeading title="Approval status" description="Track your organization review and production-access status." />
    <Card><CardContent className="space-y-5 p-6">
      <div className="flex items-start gap-3">{approved ? <CheckCircle2 className="mt-0.5 h-6 w-6 text-emerald-600" /> : needsInformation ? <AlertCircle className="mt-0.5 h-6 w-6 text-amber-600" /> : <Clock3 className="mt-0.5 h-6 w-6 text-blue-600" />}<div><h2 className="font-semibold">{approved ? "Production access approved" : needsInformation ? "Additional information required" : "Platform review in progress"}</h2><p className="mt-1 text-sm leading-6 text-slate-600">{approved ? "Your workspace has full production access." : needsInformation ? String(review.note ?? "Please update the requested organization information.") : "Your onboarding submission is complete. You can use the limited sandbox while our team reviews your organization."}</p></div></div>
      {needsInformation ? <Button asChild><a href={`${home}/onboarding`}>Provide requested information</a></Button> : null}
    </CardContent></Card>
  </div>;
}

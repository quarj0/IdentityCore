"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, toast } from "@identitycore/ui";
import { getErrorMessage } from "@/lib/api-client";
import { fetchCurrentOnboarding, type OnboardingState } from "@/lib/onboarding-api";

export function OrganizationProfilePanel() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentOnboarding()
      .then(setState)
      .catch((error) => {
        toast({
          title: "Unable to load organization profile",
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
    <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
      <CardHeader>
        <CardTitle>Registered workspace details</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-5 sm:grid-cols-2">
        <InfoField label="Organization name" value={state?.organizationName} />
        <InfoField label="Organization type" value={state?.organizationType} />
        <InfoField label="Organization country" value={state?.organizationCountry} />
        <InfoField label="Website" value={state?.website} />
        <InfoField label="Support email" value={state?.supportEmail} />
        <InfoField label="Phone number" value={state?.phoneNumber} />
        <InfoField
          label="Administrator"
          value={state?.administratorFullName}
        />
        <InfoField
          label="Administrator email"
          value={state?.administratorEmail}
        />
      </CardContent>
    </Card>
  );
}

function InfoField({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-medium text-slate-900">{label}</p>
      <p className="text-sm text-muted-foreground">{value || "Not provided yet"}</p>
    </div>
  );
}

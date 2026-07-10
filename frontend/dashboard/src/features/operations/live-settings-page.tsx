"use client";

import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Organization, Tenant } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveSettingsPage() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([dashboardApi.organization(), dashboardApi.tenant()])
      .then(([org, workspace]) => {
        setOrganization(org);
        setTenant(workspace);
      })
      .catch((caught) => setError(messageOf(caught)));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading title="Settings" description="Review live organization and workspace configuration." />
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {!organization || !tenant ? (
        <p className="text-sm text-slate-500">Loading settings...</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader><CardTitle className="flex items-center gap-2"><Building2 className="h-5 w-5 text-blue-600" /> Organization</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-700">
              <p>Name: {organization.name}</p>
              <p>Slug: {organization.slug}</p>
              <p>Industry: {organization.industry || "Not set"}</p>
              <div><StatusBadge status={organization.status} /></div>
            </CardContent>
          </Card>
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader><CardTitle>Workspace</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-700">
              <p>Name: {tenant.name}</p>
              <p>Slug: {tenant.slug}</p>
              <div><StatusBadge status={tenant.status} /></div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Activity, Building2, Loader2, ShieldCheck, Users } from "lucide-react";
import { Card, CardContent } from "@identitycore/ui";
import { backend } from "@/lib/backend";
import { PageHeading } from "@/components/shared/page-heading";

interface DashboardData {
  user: { first_name: string; last_name: string; email: string; roles: string[] };
  organization: { name: string; status: string; industry: string };
  tenant: { name: string; status: string };
  verificationCount: number;
}

export function LiveDashboardOverview() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        await backend.restoreSession();
        const [me, organization, tenant, verifications] = await Promise.all([
          backend.rest<{ user: DashboardData["user"] }>("/auth/me"),
          backend.rest<DashboardData["organization"]>("/organization/me/"),
          backend.rest<DashboardData["tenant"]>("/tenant/me/"),
          backend.rest<{ pagination: { total: number } }>("/verifications/?page=1&page_size=1"),
        ]);
        setData({ user: me.user, organization, tenant, verificationCount: verifications.pagination.total });
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to load the workspace.");
      }
    })();
  }, []);

  if (error) return <Card className="rounded-3xl border-red-200 bg-red-50"><CardContent className="p-8"><h1 className="font-semibold text-red-800">Workspace unavailable</h1><p className="mt-2 text-sm text-red-700">{error}</p><a className="mt-4 inline-block text-sm font-medium text-blue-700" href={`${process.env.NEXT_PUBLIC_IDENTITYCORE_ORIGIN ?? "http://localhost:3001"}/login`}>Sign in again</a></CardContent></Card>;
  if (!data) return <div className="flex min-h-64 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-blue-600" /></div>;

  const cards = [
    { label: "Organization", value: data.organization.name, detail: data.organization.status, icon: Building2 },
    { label: "Workspace", value: data.tenant.name, detail: data.tenant.status, icon: Users },
    { label: "Verifications", value: String(data.verificationCount), detail: "Tenant-scoped total", icon: Activity },
    { label: "Access", value: data.user.roles[0] ?? "Member", detail: data.user.email, icon: ShieldCheck },
  ];
  return <div className="space-y-8"><PageHeading title={`Welcome, ${data.user.first_name || data.organization.name}`} description="Your live IdentityCore organization workspace." /><div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ icon: Icon, ...card }) => <Card key={card.label} className="rounded-3xl border-slate-200 shadow-sm"><CardContent className="p-6"><Icon className="h-5 w-5 text-blue-600" /><p className="mt-5 text-sm text-slate-500">{card.label}</p><p className="mt-2 truncate text-xl font-semibold">{card.value}</p><p className="mt-2 truncate text-xs text-slate-500">{card.detail}</p></CardContent></Card>)}</div></div>;
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Building2,
  CheckCircle2,
  Fingerprint,
  Globe2,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
} from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { SettingsNavigation } from "@/components/shared/settings-navigation";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Organization, Tenant } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="text-right text-sm font-medium text-slate-900">{value}</dd>
    </div>
  );
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

  const loading = !organization || !tenant;

  return (
    <div className="mx-auto max-w-6xl space-y-7">
      <PageHeading
        title="Workspace settings"
        description="Review your organization identity, environment, and account controls."
      />
      <SettingsNavigation />

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      ) : null}

      {loading && !error ? (
        <div className="grid gap-5 lg:grid-cols-2">
          {[0, 1].map((item) => (
            <Card key={item} className="rounded-2xl border-slate-200">
              <CardHeader>
                <Skeleton className="h-6 w-36" />
                <Skeleton className="h-4 w-64" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : organization && tenant ? (
        <>
          <section
            className="grid gap-5 lg:grid-cols-2"
            aria-label="Workspace details"
          >
            <Card className="overflow-hidden rounded-2xl border-slate-200 shadow-sm">
              <CardHeader className="border-b border-slate-100 bg-slate-50/60">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Organization</CardTitle>
                      <CardDescription className="mt-1">
                        Your customer-facing business identity.
                      </CardDescription>
                    </div>
                  </div>
                  <StatusBadge status={organization.status} />
                </div>
              </CardHeader>
              <CardContent className="px-6 py-2">
                <dl>
                  <Detail label="Organization name" value={organization.name} />
                  <Detail label="Organization slug" value={organization.slug} />
                  <Detail
                    label="Industry"
                    value={organization.industry || "Not specified"}
                  />
                </dl>
              </CardContent>
            </Card>

            <Card className="overflow-hidden rounded-2xl border-slate-200 shadow-sm">
              <CardHeader className="border-b border-slate-100 bg-slate-50/60">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-700">
                      <Globe2 className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Workspace</CardTitle>
                      <CardDescription className="mt-1">
                        The environment your team is currently using.
                      </CardDescription>
                    </div>
                  </div>
                  <StatusBadge status={tenant.status} />
                </div>
              </CardHeader>
              <CardContent className="px-6 py-2">
                <dl>
                  <Detail label="Workspace name" value={tenant.name} />
                  <Detail label="Workspace slug" value={tenant.slug} />
                  <Detail label="Workspace ID" value={tenant.id} />
                </dl>
              </CardContent>
            </Card>
          </section>

          <section aria-labelledby="workspace-management-heading">
            <div className="mb-4">
              <h2
                id="workspace-management-heading"
                className="text-lg font-semibold text-slate-950"
              >
                Workspace management
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Manage the people, security, and identity configuration for this
                workspace.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                {
                  href: "/team",
                  icon: UsersRound,
                  title: "Team access",
                  text: "Invite members and manage workspace access.",
                },
                {
                  href: "/settings/security",
                  icon: ShieldCheck,
                  title: "Security",
                  text: "Review credentials and security controls.",
                },
                {
                  href: "/settings/profile",
                  icon: Fingerprint,
                  title: "Your profile",
                  text: "Update your personal account information.",
                },
              ].map(({ href, icon: Icon, title, text }) => (
                <Link
                  key={href}
                  href={href}
                  className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                      <Icon className="h-4 w-4" />
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-slate-400 transition group-hover:text-slate-900" />
                  </div>
                  <h3 className="mt-4 text-sm font-semibold text-slate-950">
                    {title}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    {text}
                  </p>
                </Link>
              ))}
            </div>
          </section>

          <Card className="rounded-2xl border-emerald-200 bg-emerald-50/60 shadow-none">
            <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
                <div>
                  <p className="text-sm font-semibold text-emerald-950">
                    Workspace is active
                  </p>
                  <p className="mt-1 text-sm text-emerald-800">
                    Your organization and workspace are configured and available
                    to your team.
                  </p>
                </div>
              </div>
              <Button
                asChild
                variant="outline"
                className="border-emerald-300 bg-white text-emerald-900 hover:bg-emerald-100"
              >
                <Link href="/approval-status">View approval status</Link>
              </Button>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

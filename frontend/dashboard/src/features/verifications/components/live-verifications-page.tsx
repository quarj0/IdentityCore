"use client";

import Link from "next/link";
import { SubmitEvent, useEffect, useMemo, useState } from "react";
import { Copy, FileCheck2, Loader2, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Organization, Policy, VerificationSummary } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveVerificationsPage() {
  const [items, setItems] = useState<VerificationSummary[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [hostedLink, setHostedLink] = useState("");
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [organization, setOrganization] = useState<Organization | null>(null);

  const activePolicies = useMemo(
    () => policies.filter((item) => item.status === "active"),
    [policies],
  );

  async function load() {
    setError("");
    try {
      const [page, templates, org] = await Promise.all([
        dashboardApi.verifications(),
        dashboardApi.policies(),
        dashboardApi.organization(),
      ]);
      setItems(page.results);
      setPolicies(templates);
      setOrganization(org);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    Promise.all([dashboardApi.verifications(), dashboardApi.policies(), dashboardApi.organization()])
      .then(([page, templates, org]) => {
        setItems(page.results);
        setPolicies(templates);
        setOrganization(org);
      })
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  async function create(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setCreating(true);
    setError("");
    setCopied(false);
    try {
      const result = await dashboardApi.createVerification({
        purpose: String(data.get("purpose") || "").trim(),
        policy_id: String(data.get("policy_id") || "").trim(),
        external_reference: String(data.get("external_reference") || "").trim(),
        verification_subject: {
          full_name: String(data.get("full_name") || "").trim(),
          email: String(data.get("email") || "").trim(),
        },
      });
      setHostedLink(result.verification_url);
      form.reset();
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setCreating(false);
    }
  }

  async function copyLink() {
    await navigator.clipboard.writeText(hostedLink);
    setCopied(true);
  }

  return (
    <div className="space-y-8">
      <PageHeading
        title="Verifications"
        description="Create hosted verification links, track progress, and resend fresh links when needed."
        action={
          <Button variant="outline" className="rounded-xl" onClick={() => void load()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />
      {organization?.sandbox_usage.pending_approval ? <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900"><strong>Sandbox usage:</strong> {organization.sandbox_usage.monthly_verifications} of {organization.sandbox_usage.monthly_verification_limit} verifications used this month.</div> : null}

      {error ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {hostedLink ? (
        <Card className="rounded-2xl border-blue-100 bg-blue-50 shadow-none">
          <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr_auto] md:items-center">
            <Input readOnly value={hostedLink} className="bg-white" aria-label="Hosted verification link" />
            <Button onClick={copyLink} className="rounded-xl">
              <Copy className="h-4 w-4" />
              {copied ? "Copied" : "Copy link"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Create request</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="full_name">Full name</Label>
              <Input id="full_name" name="full_name" required />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" required />
            </div>
            <div>
              <Label htmlFor="purpose">Purpose</Label>
              <Input id="purpose" name="purpose" required placeholder="Customer onboarding" />
            </div>
            <div>
              <Label htmlFor="external_reference">External reference</Label>
              <Input id="external_reference" name="external_reference" placeholder="Optional customer ID" />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="policy_id">Template</Label>
              <select
                id="policy_id"
                name="policy_id"
                required
                className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              >
                <option value="">Choose an active template</option>
                {activePolicies.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} v{item.version}
                  </option>
                ))}
              </select>
              {activePolicies.length === 0 ? (
                <p className="mt-2 text-sm text-amber-700">
                  Activate a template before creating dashboard verifications.
                </p>
              ) : null}
            </div>
            <div className="md:col-span-2">
              <Button disabled={creating || activePolicies.length === 0 || Boolean(organization?.sandbox_usage.monthly_verification_limit && organization.sandbox_usage.monthly_verifications >= organization.sandbox_usage.monthly_verification_limit)} className="rounded-xl">
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Create and email link
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-sm text-slate-500">Loading verifications...</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={FileCheck2}
          title="No verifications"
          description="Create a request to send a hosted verification link to a subject."
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-4 font-medium">Subject</th>
                <th className="px-5 py-4 font-medium">Template</th>
                <th className="px-5 py-4 font-medium">Purpose</th>
                <th className="px-5 py-4 font-medium">Status</th>
                <th className="px-5 py-4 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-200">
                  <td className="px-5 py-4">
                    <Link href={`/verifications/${item.id}`} className="font-medium text-slate-950 hover:text-blue-700">
                      {item.subject.full_name || item.subject.email || item.id}
                    </Link>
                    <p className="mt-1 text-xs text-slate-500">{item.subject.email}</p>
                  </td>
                  <td className="px-5 py-4 text-slate-700">
                    {item.policy.name ? `${item.policy.name} v${item.policy.version ?? "-"}` : "No template"}
                  </td>
                  <td className="px-5 py-4 text-slate-700">{item.purpose}</td>
                  <td className="px-5 py-4"><StatusBadge status={item.status} /></td>
                  <td className="px-5 py-4 text-slate-500">{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

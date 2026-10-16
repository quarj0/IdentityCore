"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { PageHeading } from "@/components/shared/page-heading";
import { getErrorMessage } from "@/lib/api-client";
import { billingApi, formatMinor, type BillingPlan, type BillingSubscription } from "@/lib/billing-api";

export default function BillingPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [subscription, setSubscription] = useState<BillingSubscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const reload = useCallback(async () => {
    try {
      const [available, account] = await Promise.all([billingApi.plans(), billingApi.account()]);
      setPlans(available.results);
      setSubscription(account.subscription);
      setError("");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([billingApi.plans(), billingApi.account()]).then(([available, account]) => {
      if (!active) return;
      setPlans(available.results);
      setSubscription(account.subscription);
      setError("");
    }).catch((reason) => {
      if (active) setError(getErrorMessage(reason));
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function enroll(plan: BillingPlan) {
    setBusy(plan.id);
    setError("");
    setNotice("");
    try {
      await billingApi.subscribe(plan.id);
      setNotice("Plan selected. Usage is billed in monthly arrears after invoice issuance.");
      await reload();
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="space-y-6">
      <PageHeading
        title="Billing"
        description="See your organization plan, infrastructure usage prices, and invoices."
      />
      {loading ? <p role="status" className="text-sm text-muted-foreground">Loading billing information…</p> : null}
      {error ? <p role="alert" className="rounded-md border border-red-300 p-3 text-sm">{error}</p> : null}
      {notice ? <p role="status" className="rounded-md border p-3 text-sm">{notice}</p> : null}
      <section className="rounded-xl border p-5" aria-label="Current subscription">
        <h2 className="text-lg font-semibold">Current subscription</h2>
        {subscription ? (
          <p className="mt-2 text-sm">
            <strong>{subscription.plan}</strong> · {subscription.status} · {subscription.currency}
          </p>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            No plan selected. An authorized organization administrator can select a published plan.
          </p>
        )}
        <Link className="mt-4 inline-block text-sm underline underline-offset-4" href="/billing/invoices">
          View invoices and payment status
        </Link>
      </section>
      <section aria-label="Available billing plans" className="space-y-4">
        <h2 className="text-lg font-semibold">Available plans</h2>
        {plans.length === 0 && !loading ? (
          <p className="text-sm text-muted-foreground">No commercial plans have been published yet.</p>
        ) : null}
        <div className="grid gap-4 lg:grid-cols-2">
          {plans.map((plan) => (
            <article key={plan.id} className="rounded-xl border p-5">
              <h3 className="font-semibold">{plan.name}</h3>
              <p className="mt-2 text-xl font-semibold">
                {formatMinor(plan.monthly_price_minor, plan.currency)}
                <span className="ml-1 text-sm font-normal text-muted-foreground">/ month</span>
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Metered usage below is in addition to the monthly infrastructure charge.
              </p>
              <div className="mt-3 space-y-1">
                {plan.meters.map((meter) => (
                  <p key={meter.provider_scope + meter.capability + meter.outcome} className="text-sm">
                    {meter.provider_scope === "tenant_owned" ? "BYOP" : "Platform"} ·{" "}
                    {meter.capability} ({meter.outcome}):{" "}
                    {formatMinor(meter.unit_price_minor, plan.currency)} / check
                  </p>
                ))}
                {plan.meters.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No usage rates published.</p>
                ) : null}
              </div>
              {!subscription ? (
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => void enroll(plan)}
                  className="mt-4 rounded-md border px-4 py-2 text-sm font-medium disabled:opacity-50"
                >
                  {busy === plan.id ? "Selecting…" : "Select plan"}
                </button>
              ) : null}
            </article>
          ))}
        </div>
      </section>
      <p className="text-xs text-muted-foreground">
        IdentityCore does not handle card details. Invoices can be paid through hosted checkout after issue.
        Provider fees payable directly to your BYOP vendors are separate.
      </p>
    </main>
  );
}

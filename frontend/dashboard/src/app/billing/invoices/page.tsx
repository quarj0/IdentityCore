"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeading } from "@/components/shared/page-heading";
import { getErrorMessage } from "@/lib/api-client";
import { checkedCheckoutUrl } from "@/lib/billing-checkout";
import {
  billingApi,
  formatMinor,
  type BillingInvoice,
  type PaymentProvider,
} from "@/lib/billing-api";

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [details, setDetails] = useState<BillingInvoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [providers, setProviders] = useState<Record<string, PaymentProvider>>(
    {},
  );

  const refresh = useCallback(async () => {
    try {
      const result = await billingApi.invoices();
      setInvoices(result.results);
      setDetails((current) => {
        const updated = result.results.find(
          (invoice) => invoice.id === current?.id,
        );
        return current && updated
          ? { ...current, ...updated, lines: current.lines }
          : current;
      });
      setError("");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyPayment = useCallback(
    async (paymentId: string) => {
      setBusy(paymentId);
      setNotice("");
      try {
        const result = await billingApi.verifyPayment(paymentId);
        await refresh();
        setError("");
        setNotice(
          result.verified
            ? "Payment transaction verified. The invoice shows its current status."
            : "Payment has not been confirmed yet. You can check again shortly.",
        );
      } catch (reason) {
        await refresh();
        setError(getErrorMessage(reason));
      } finally {
        setBusy(null);
      }
    },
    [refresh],
  );

  useEffect(() => {
    let active = true;
    const paymentId = new URLSearchParams(window.location.search).get("payment_id");
    const verification = paymentId && /^bpa_[A-Za-z0-9]{1,64}$/.test(paymentId)
      ? billingApi.verifyPayment(paymentId) : Promise.resolve(null);
    verification.then(async (result) => {
      const data = await billingApi.invoices();
      if (!active) return;
      setInvoices(data.results);
      setError("");
      if (result) setNotice(result.verified
        ? "Payment transaction verified. The invoice shows its current status."
        : "Payment has not been confirmed yet. You can check again shortly.");
    }).catch((reason) => {
      if (active) setError(getErrorMessage(reason));
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function openInvoice(id: string) {
    setBusy(id);
    try {
      setDetails(await billingApi.invoice(id));
      setError("");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(null);
    }
  }

  async function checkout(id: string, provider: PaymentProvider) {
    setBusy(id);
    setNotice("");
    try {
      const payment = await billingApi.checkout(id, provider);
      if (payment.status === "paid") {
        await refresh();
        setBusy(null);
        return;
      }
      window.location.assign(
        checkedCheckoutUrl(payment.checkout_url, payment.provider),
      );
    } catch (reason) {
      setError(getErrorMessage(reason));
      setBusy(null);
    }
  }

  return (
    <main className="space-y-6">
      <PageHeading
        title="Invoices"
        description="Review charges, issued invoices and secure checkout."
      />
      <button
        type="button"
        disabled={busy !== null}
        onClick={() => {
          setNotice("");
          void refresh();
        }}
        className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
      >
        Refresh invoice status
      </button>
      {loading ? (
        <p role="status" className="text-sm text-muted-foreground">
          Loading invoices…
        </p>
      ) : null}
      {notice ? (
        <p role="status" className="rounded-md border p-3 text-sm">
          {notice}
        </p>
      ) : null}
      {error ? (
        <p
          role="alert"
          className="rounded-md border border-red-300 p-3 text-sm"
        >
          {error}
        </p>
      ) : null}
      {invoices.length === 0 && !loading ? (
        <p className="rounded-xl border p-6 text-sm text-muted-foreground">
          No invoices have been issued. Your first bill will appear after a
          billing period closes.
        </p>
      ) : null}
      <div className="space-y-3">
        {invoices.map((invoice) => {
          const available = invoice.payment_providers ?? [];
          const selected =
            invoice.payment?.status === "pending"
              ? invoice.payment.provider
              : (providers[invoice.id] ?? available[0]);
          return (
            <article key={invoice.id} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold">
                    {invoice.period_start} – {invoice.period_end}
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {invoice.status.replaceAll("_", " ")} · {invoice.plan_code}{" "}
                    · {formatMinor(invoice.amount_minor, invoice.currency)}
                  </p>
                  {invoice.due_at ? (
                    <p className="text-xs text-muted-foreground">
                      Due {new Date(invoice.due_at).toLocaleDateString()}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void openInvoice(invoice.id)}
                    className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
                  >
                    Details
                  </button>
                  {invoice.can_manage_billing &&
                  invoice.status === "issued" &&
                  invoice.amount_minor > 0 ? (
                    <>
                      {available.length > 1 &&
                      invoice.payment?.status !== "pending" ? (
                        <label className="text-sm">
                          Payment provider
                          <select
                            aria-label="Payment provider"
                            disabled={busy !== null}
                            value={selected}
                            onChange={(event) =>
                              setProviders((current) => ({
                                ...current,
                                [invoice.id]: event.target
                                  .value as PaymentProvider,
                              }))
                            }
                            className="ml-2 rounded-md border px-2 py-2"
                          >
                            {available.map((provider) => (
                              <option key={provider} value={provider}>
                                {provider === "paystack"
                                  ? "Paystack"
                                  : "Stripe"}
                              </option>
                            ))}
                          </select>
                        </label>
                      ) : null}
                      {selected && available.includes(selected) ? (
                        <button
                          type="button"
                          disabled={busy !== null}
                          onClick={() => void checkout(invoice.id, selected)}
                          className="rounded-md border px-3 py-2 text-sm font-semibold disabled:opacity-50"
                        >
                          {busy === invoice.id
                            ? "Opening…"
                            : `Pay with ${selected === "paystack" ? "Paystack" : "Stripe"}`}
                        </button>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          Payment options are currently unavailable. Contact
                          billing support.
                        </p>
                      )}
                      {invoice.payment?.status === "pending" ? (
                        <button
                          type="button"
                          disabled={busy !== null}
                          onClick={() =>
                            void verifyPayment(invoice.payment!.id)
                          }
                          className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
                        >
                          Check payment
                        </button>
                      ) : null}
                    </>
                  ) : null}
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {details ? (
        <section
          aria-label="Invoice breakdown"
          className="rounded-xl border p-5"
        >
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              Invoice breakdown · {details.status.replaceAll("_", " ")}
            </h2>
            <button
              type="button"
              onClick={() => setDetails(null)}
              className="text-sm underline"
            >
              Close
            </button>
          </div>
          <ul className="mt-3 space-y-2">
            {(details.lines ?? []).map((line, index) => (
              <li
                key={index}
                className="flex justify-between gap-4 border-b pb-2 text-sm"
              >
                <span>
                  {line.description} × {line.quantity}
                </span>
                <span>{formatMinor(line.amount_minor, details.currency)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-right font-semibold">
            Total: {formatMinor(details.amount_minor, details.currency)}
          </p>
        </section>
      ) : null}
      <p className="text-xs text-muted-foreground">
        Your invoice is updated after payment verification. Use Check payment if
        its status is still pending.
      </p>
    </main>
  );
}

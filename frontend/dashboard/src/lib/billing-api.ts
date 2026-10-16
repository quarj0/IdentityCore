import { restRequest } from "@/lib/api-client";

export type BillingPlan = {
  id: string;
  code: string;
  name: string;
  version: number;
  currency: string;
  monthly_price_minor: number;
  meters: {
    provider_scope: "platform" | "tenant_owned";
    capability: string;
    outcome: string;
    unit_price_minor: number;
  }[];
};

export type BillingSubscription = {
  id: string;
  plan: string;
  currency: string;
  status: string;
  started_at: string;
};

export type InvoiceLine = {
  description: string;
  quantity: number;
  unit_price_minor: number;
  amount_minor: number;
};

export type BillingInvoice = {
  id: string;
  plan_code: string;
  plan_version: number;
  period_start: string;
  period_end: string;
  amount_minor: number;
  currency: string;
  status: string;
  due_at: string | null;
  issued_at: string | null;
  paid_at: string | null;
  lines?: InvoiceLine[];
  payment_providers: PaymentProvider[];
  payment: { id: string; provider: PaymentProvider; status: string } | null;
  can_manage_billing: boolean;
};

export type PaymentProvider = "paystack";

export const billingApi = {
  plans: () => restRequest<{ results: BillingPlan[] }>("/billing/plans"),
  account: () =>
    restRequest<{ subscription: BillingSubscription | null }>(
      "/billing/account",
    ),
  subscribe: (plan_id: string) =>
    restRequest<{ id: string; plan: string; status: string }>(
      "/billing/subscribe",
      {
        method: "POST",
        body: JSON.stringify({ plan_id }),
      },
    ),
  invoices: () =>
    restRequest<{ results: BillingInvoice[] }>("/billing/invoices"),
  invoice: (id: string) =>
    restRequest<BillingInvoice>("/billing/invoices/" + encodeURIComponent(id)),
  checkout: (id: string, provider: PaymentProvider) =>
    restRequest<{
      payment_id: string;
      reference: string;
      currency: string;
      amount_minor: number;
      checkout_url: string;
      provider: PaymentProvider;
      status: string;
    }>("/billing/invoices/" + encodeURIComponent(id) + "/checkout", {
      method: "POST",
      body: JSON.stringify({ provider }),
    }),
  verifyPayment: (id: string) =>
    restRequest<{ verified: boolean }>(
      "/billing/payments/" + encodeURIComponent(id),
      { method: "POST" },
    ),
};

export function formatMinor(amount_minor: number, currency: string) {
  const supported = /^[A-Z]{3}$/.test(currency) ? currency : "GHS";
  return new Intl.NumberFormat("en-GH", {
    style: "currency",
    currency: supported,
  }).format(amount_minor / 100);
}

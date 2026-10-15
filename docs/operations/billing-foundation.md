# IdentityCore commercial billing and payments

**Scope:** GHS monthly postpaid billing with rate-card snapshots, BYOP/platform
metering, invoices, hosted Paystack checkout, authenticated webhook and
server-side payment verification. The core accounting records are provider
neutral; Paystack is currently the only payment adapter. This is not an
approval to take live payments before staging, commercial and legal checks.

## What the implementation does

- Every completed, failed or timed-out production ProviderCheck is eligible
  for an idempotent, **unrated** tenant/project-scoped usage fact. Sandbox
  and unprojected work never enters the ledger. Terminal failures are never
  presumed chargeable; explicit plan rates decide whether they carry a charge.
- Platform-owned and tenant-owned (BYOP) providers use **separate meters**.
  This categorizes infrastructure usage, not the provider's direct bill.
  Customers remain responsible for separate BYOP vendor contracts.
- Published plans have frozen terms. Pricing revisions create a new plan
  version; each monthly invoice records the applicable plan and unit amounts.
- Calendar-month invoices include subscription base fee plus metered events.
  The first partial month has usage-only billing (no prorated base fee).
  A month will not close if eligible provider checks lack reconciled usage or
  some usage has no explicit rate. Invoice issuance requires line total parity.
- Published plans may be selected by authorized organization admins.
  Billing permissions use the tenant-scoped manage_billing role permission.
- Invoices are read-only to customers. Only **issued**, nonzero invoices can
  start hosted checkout. The server calculates amount and currency and creates
  unique references; checkout URLs must point to checkout.paystack.com.
- Signed Paystack webhooks use the secret-key HMAC-SHA512 of exact raw request
  bytes, size caps and replay-resistant state transitions. Successful charges
  MUST pass a separate Paystack transaction verification for reference,
  amount, currency and transaction ID before settling an invoice.
- An authenticated customer can verify payment status. Operator
  reconciliation covers missed callbacks/webhooks and pending references.
- Authenticated refund notifications are independently verified via the
  Paystack refund API using the settled transaction ID and bounded amount.
  Completed refunds and signed charge disputes put the invoice in disputed
  state for finance review. **Refund creation is manual through Paystack's
  dashboard** to avoid unaudited duplicate payout requests.
- Billing endpoints are dashboard-internal, not part of public SDK/OpenAPI.
  No application stores customer card numbers or card security codes.

## Merchant setup

Use a Paystack merchant account legally entitled to collect **GHS**. Do not
reuse an account for a different legal entity without authorization. Set the
following in a secret manager for the Django/worker deployment:

    BILLING_USAGE_CAPTURE_ENABLED=true
    BILLING_AUTO_INVOICE_ENABLED=false
    BILLING_PAYMENTS_ENABLED=false
    PAYSTACK_SECRET_KEY=<test merchant secret>
    BILLING_RETURN_URL=https://your-approved-dashboard.example/billing/invoices

1. Apply migrations, run protected CI, and review production access controls.
2. Create a draft billing plan in the platform Django admin and add a
   platform/BYOP meter for **every eligible check type and outcome**; zero
   rates are explicit and allowed. Publish only after reviewing currency,
   base fee, rates and contract terms. Plan codes can repeat across versions.
3. Select a plan as a tenant admin from the Billing dashboard. Changing a
   subscribed plan currently needs a controlled operations workflow.
4. Enable usage capture and reconcile previously finished provider checks.
   The background task runs every 10 minutes when enabled; the manual command
   can process individual tenant history:

       python backend/django/manage.py reconcile_provider_usage --tenant TENANT_ID --limit 100

5. For an already-closed UTC month, issue a sample invoice in staging:

       python backend/django/manage.py issue_billing_invoices --tenant TENANT_ID --month YYYY-MM --issue

   This command is operator-only; it refuses incomplete accounting. For
   production, after approved rate/legal setup and month-close checks,
   enable BILLING_AUTO_INVOICE_ENABLED=true.
6. With **Paystack test key**, turn on BILLING_PAYMENTS_ENABLED=true and test
   a checkout on an issued invoice, verified callback/webhook, duplicate
   callbacks, wrong amounts, gateway outages and refund/dispute reconciliation.
7. Configure Paystack dashboard webhook URL:

       https://YOUR-API-HOST/api/v1/billing/paystack/webhook

   Route exact raw bytes through HTTPS without JSON reserialization.
   Keep gateway secret solely server-side. Confirm origin and amount/currency
   according to Paystack's current docs.
8. Switch to live credentials **only after** approved merchant onboarding,
   penetration testing, tax/VAT and invoice requirements, terms, jurisdiction
   and data-processing review, production monitoring and separate finance
   signoff. PAYSTACK_SECRET_KEY must never be committed or exposed to clients.

## API (authenticated organization dashboard)

- GET billing/plans, billing/account, billing/invoices,
  billing/invoices/{id}
- POST billing/subscribe (manage_billing permission; JSON plan_id)
- POST billing/invoices/{id}/checkout (manage_billing permission)
- GET billing/payments/{id}
- POST billing/payments/{id} (manage_billing permission; Paystack verification)
- POST billing/paystack/webhook (no dashboard credentials; **signed HMAC**)

All paths are under /api/v1/. Amounts are **integer minor units**, no
floating-point currency calculations. NEVER infer payment from a redirect.
Receipts, failed gateway responses, merchant disputes and refunds require
reconciliation by finance before changing contractual entitlements.

## Deliberate boundaries / work outside the first GHS release

- No auto-debit subscriptions, saved payment methods or customer card storage.
  Recurring bills are customer-paid hosted invoices.
- No automatic taxes/VAT or multi-jurisdiction invoice compliance, no foreign
  gateway enabled and no automated FX.
- No automatic production suspension on overdue payments.
- No unreviewed self-service plan switch/proration after enrollment.
- Refunds are initiated by authorized operators through Paystack Dashboard;
  application mirrors independently verified refund statuses.
- No production approval based on synthetic gateway mocks: run live Paystack
  **test-mode** end-to-end and obtain authorized merchant launch signoff.

References:
- https://paystack.com/docs/payments/accept-payments/
- https://paystack.com/docs/payments/verify-payments/
- https://paystack.com/docs/payments/webhooks/
- https://paystack.com/docs/payments/refunds/
- docs/operations/release-evidence-gate.md

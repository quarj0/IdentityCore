# IdentityCore Paystack billing and payments

## Accounting and checkout

Monthly postpaid invoices combine a published plan's base fee with immutable,
tenant-scoped production usage and rate snapshots. Platform and BYOP usage have
separate meters; sandbox work is excluded. Explicit rates, including zero rates,
determine chargeability. The first partial month has no base fee, including
subscriptions started after midnight UTC on day one. Recorded active intervals
control usage eligibility. A pause or cancellation after month close preserves
the completed month's charges. Partial active months and pause/resume gaps have
no base fee; only usage within active intervals is rated. Pausing billing does
not suspend verification processing.

The activity-history migration records a conservative deployment cutover for
existing subscriptions. Earlier unknown activity blocks invoicing pending
operator review; current status is insufficient evidence of past activity.
Restore earlier intervals only from independently verified subscription records
through an approved data repair. Do not backdate the cutoff based on assumptions.

Month close rejects missing usage, changed provider facts, unpriced meters and
line-total mismatches. Interrupted drafts resume through the operator command
or scheduled task. Generation and issuance commit together. Completed tenants
are excluded before applying the batch limit. Tenant accounting errors roll
back independently, allow the selected batch to finish, and fail the task with
a bounded review summary. Durable subscription attempt timestamps move failures
behind unattempted or older tenants on later runs, including full failed pages.

Usage checks with invalid ownership or attribution are quarantined without
creating accounting facts. Valid checks in the same batch still complete;
scheduled runs skip quarantined rows so a full page of bad data cannot starve
other tenants. Review BillingUsageReconciliationIssue in the read-only finance
admin, repair the source through an authorized operations workflow, then rerun
reconcile_provider_usage for that tenant. Unquarantined checks run first, then
the oldest failed checks. Use `--check PROVIDER_CHECK_PUBLIC_ID` to retry a
specific repaired check without waiting behind other quarantined checks. Successful independent reconciliation
clears the marker. The affected tenant's month close remains blocked until its
missing usage is resolved. Logs expose only check IDs and controlled codes.

Hosted **Paystack checkout supports GHS invoices**. Amounts remain integer minor
units; there is no currency conversion, saved-card storage or automatic debit.
Only tenant users with `manage_billing` can enroll, initialize checkout or request
verification. Concurrent requests share one pending payment. The backend owns
the amount, currency and unique reference and accepts checkout redirects only
at `https://checkout.paystack.com`.

A return redirect is not payment evidence. Settlement requires an independent
Paystack transaction lookup matching the server reference, amount, currency
and transaction ID. Confirmation and audit are idempotent. Reversed, failed or
abandoned pending attempts become terminal so the customer can retry. A late
failure cannot undo an already settled payment. Initialization interrupted
before saving a checkout URL expires after two minutes; retry creates a fresh
reference rather than resubmitting a reference already accepted by Paystack.
A failed return verification still loads invoices and offers an explicit retry.

Webhooks authenticate exact raw bytes using HMAC-SHA512 before parsing. Refund
webhooks correlate through `transaction_reference`, including a null
`refund_reference`; independently authenticated, paginated refund listings
supply the numeric refund IDs and accounting facts. `needs-attention` remains
pending and requires an operator to provide bank details through Paystack.
IdentityCore does not store card or refund bank account credentials.

Refunds and disputes require independent gateway evidence against the settled
transaction. Partial/full refunds produce `partially_refunded`/`refunded`.
Open or lost disputes produce `disputed`; resolved declined disputes restore
the appropriate paid/refund state. Partial dispute amounts use the verified
`refund_amount`. Refund totals cannot exceed the charge. Operators initiate
refunds in Paystack Dashboard; this application only reconciles their outcomes.

## Deployment

Apply migrations before enabling capture or checkout. Configure server-side
secrets in Django and workers:

```dotenv
BILLING_USAGE_CAPTURE_ENABLED=true
BILLING_AUTO_INVOICE_ENABLED=false
BILLING_PAYMENTS_ENABLED=false
PAYSTACK_SECRET_KEY=<Paystack test secret from your secret manager>
BILLING_RETURN_URL=https://YOUR-DASHBOARD-HOST/billing/return
```

The return URL must be HTTPS without credentials or a fragment. The backend adds
an opaque payment ID, and the dashboard requests authenticated verification.
The hosted integration uses the server secret; it does not require embedding a
merchant public key in the dashboard. Never commit keys or expose the secret to
a browser. Startup validates the secret and return URL when payments are enabled.

1. Create a draft plan in the platform admin. Add rates for every eligible
   capability, provider scope and outcome. Publish reviewed GHS terms; published
   plan versions are frozen.
2. Enroll a tenant through Billing with `manage_billing`.
3. Reconcile historical production usage and issue a closed UTC month:

   ```sh
   python backend/django/manage.py reconcile_provider_usage --tenant TENANT_ID --limit 100
   python backend/django/manage.py issue_billing_invoices --tenant TENANT_ID --month YYYY-MM --issue
   ```

   Running the invoice command first without `--issue` creates a draft; a later
   `--issue` resumes it. Usage reconciliation runs every ten minutes when
   enabled. Enable automatic invoicing only after validating month close.
4. Configure the exact HTTPS webhook destination in Paystack:

   ```text
   https://YOUR-API-HOST/api/v1/billing/paystack/webhook
   ```

   Preserve raw bytes and subscribe to charge, refund and dispute lifecycle
   events, including `refund.needs-attention`.
5. Enable payments with test credentials. Exercise checkout, return verification,
   signed delivery, duplicate confirmation, wrong amounts, outages, missed
   webhooks, refunds and disputes.
6. Reconcile missed payments and known pending adjustments regularly and after
   webhook outages:

   ```sh
   python backend/django/manage.py reconcile_billing_payments --tenant TENANT_ID --limit 50 --include-adjustments
   ```

   Nonzero exits require operator review. Replay entirely missed adjustment
   events through Paystack to discover their independently verified refund
   facts. The command refreshes adjustments already recorded locally and never
   initiates refunds.

## Dashboard API

All paths are under `/api/v1/` and outside the public machine SDK contract:

- `GET billing/plans`, `billing/account`, `billing/invoices`, `billing/invoices/{id}`
- `POST billing/subscribe` with `plan_id`
- `POST billing/invoices/{id}/checkout` with an empty object or `provider: paystack`
- `GET billing/payments/{id}`; `POST billing/payments/{id}` independently verifies it
- `POST billing/paystack/webhook` with the Paystack signature

## Acceptance and launch

Automated coverage uses synthetic gateway responses for HTTP, signature,
settlement, refund and dispute boundaries, real PostgreSQL concurrency tests,
invoice recovery and Chromium/WebKit billing journeys. Record merchant
**test-mode** checkout and reconciliation evidence separately.

Live collection requires authorized GHS merchant onboarding, finance signoff,
applicable invoice/tax requirements and privacy processor/transfer review.
Automatic tax, FX, overdue suspension, self-service plan switching and refund
initiation are outside this implementation. Recurring invoices remain
customer-paid.

References:

- [Paystack payment verification](https://paystack.com/docs/payments/verify-payments/)
- [Paystack webhooks](https://paystack.com/docs/payments/webhooks/)
- [Paystack refunds](https://paystack.com/docs/payments/refunds/)
- [Paystack disputes](https://paystack.com/docs/api/dispute/)
- [Release evidence gate](release-evidence-gate.md)

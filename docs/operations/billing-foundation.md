# IdentityCore commercial billing and payments

## Accounting and checkout

Monthly postpaid invoices combine a published plan's base fee with immutable,
tenant-scoped production usage and rate snapshots. Platform and BYOP usage
have separate meters. Sandbox work is excluded. Explicit rates, including
zero rates, determine chargeability; failures are never automatically billable.
Month close rejects missing usage, changed provider facts, unpriced meters and
line-total mismatches. Interrupted drafts resume; generation and automatic
issuance commit together, including the operator command. Completed tenants do not consume the next batch. A tenant accounting error rolls back that tenant, allows the rest of the selected batch to finish, and then fails the task with a review summary; logs identify the affected subscriptions. A durable last-attempt timestamp moves failed subscriptions behind unattempted or older tenants on subsequent bounded runs, even when a whole page fails.

Both **Paystack and Stripe** support customer-paid hosted invoices. Paystack is
restricted to GHS. Stripe defaults to USD, EUR and GBP; configure another
supported two-decimal currency only after confirming merchant eligibility.
Checkout never converts currency. Available providers are filtered against the
invoice currency and deployment configuration. Plan changes after enrollment
require an operations workflow; there are no saved cards or automatic debits.

Only tenant users with `manage_billing` can subscribe, create checkout or
request gateway verification. Invoices remain readable according to dashboard
permissions. The backend owns amounts, currency and unique references. A single
pending attempt is shared across concurrent checkout requests, including requests
for different providers. Hosted redirects accept only the exact HTTPS checkout
host for the selected provider. Card numbers and security codes never enter
IdentityCore.

A return redirect is not proof of payment. Paystack settlement requires a separate
transaction lookup matching reference, amount, currency and transaction ID.
Stripe settlement requires independent Checkout Session and PaymentIntent
lookups, matching the server reference, amount and currency, a complete paid
session and a succeeded intent with the exact amount received. Pending and
asynchronous payments remain pending. Repeated confirmations settle and audit
once. Late failures cannot undo settled payments.

Webhooks authenticate exact raw request bytes before parsing: Paystack uses
HMAC-SHA512; Stripe uses its endpoint secret, SHA256 signature and a five-minute
timestamp tolerance. Event and transaction attribution includes the gateway.
Refunds and disputes require independent gateway lookups against the settled
transaction. Paystack refund webhooks correlate through transaction_reference,
including a null refund_reference: authenticated, paginated refund listings
supply the numeric IDs and current accounting facts. The needs-attention
state remains pending; operators supply bank details through Paystack, with
no bank account details stored by IdentityCore. Partial and full refunds produce `partially_refunded` and
`refunded` states. Open or lost disputes produce `disputed`; a verified won Stripe dispute or a
resolved declined Paystack dispute restores the appropriate paid/refund state.
Paystack partial dispute amounts use its verified `refund_amount` in minor units. Refund totals cannot
exceed the original payment. Refund creation remains an authorized operator
action in the relevant gateway dashboard.

## Deployment configuration

Apply migrations before enabling capture or checkout. Keep secrets in the
Django and worker secret manager, never in frontend configuration:

```dotenv
BILLING_USAGE_CAPTURE_ENABLED=true
BILLING_AUTO_INVOICE_ENABLED=false
BILLING_PAYMENTS_ENABLED=false
BILLING_PAYMENT_PROVIDERS=paystack,stripe
BILLING_DEFAULT_PROVIDER=paystack
PAYSTACK_SECRET_KEY=<Paystack test secret>
STRIPE_SECRET_KEY=<Stripe test secret>
STRIPE_WEBHOOK_SECRET=<Stripe endpoint signing secret>
STRIPE_PAYMENT_CURRENCIES=USD,EUR,GBP
BILLING_RETURN_URL=https://YOUR-DASHBOARD-HOST/billing/return
```

The return URL must be HTTPS without credentials or a fragment. The backend
adds an opaque payment ID; the dashboard requests authenticated verification.
Enable only providers provisioned for the collecting legal entity. Enabling
payments validates their required secrets at startup. Stripe requests pin API
version `2025-06-30.basil`.

1. Create a draft plan in the platform admin. Add explicit rates for every
   eligible capability, provider scope and outcome, then publish a reviewed
   currency, base fee and rate version. Published terms are frozen.
2. Enroll a tenant through the Billing dashboard using `manage_billing`.
3. Reconcile historical production usage before closing a month:

   ```sh
   python backend/django/manage.py reconcile_provider_usage --tenant TENANT_ID --limit 100
   python backend/django/manage.py issue_billing_invoices --tenant TENANT_ID --month YYYY-MM --issue
   ```

   Usage capture runs every ten minutes when enabled. Enable
   `BILLING_AUTO_INVOICE_ENABLED=true` only after validating month close.
4. Configure exact HTTPS POST webhook destinations, preserving raw bytes:

   ```text
   https://YOUR-API-HOST/api/v1/billing/paystack/webhook
   https://YOUR-API-HOST/api/v1/billing/stripe/webhook
   ```

   Stripe event subscriptions: `checkout.session.completed`,
   `checkout.session.async_payment_succeeded`,
   `checkout.session.async_payment_failed`, `checkout.session.expired`,
   `refund.created`, `refund.updated`, `charge.dispute.created`,
   `charge.dispute.updated`, and `charge.dispute.closed`.
5. Enable payments with test credentials. Exercise both providers' hosted
   checkout, return verification, signed delivery, duplicates, wrong amounts,
   timeouts, missed webhooks, refunds and disputes with eligible invoice currency.
6. Reconcile missed payments and known pending adjustments regularly, and after
   webhook outages:

   ```sh
   python backend/django/manage.py reconcile_billing_payments --tenant TENANT_ID --limit 50 --include-adjustments
   ```

   Optional `--provider paystack` or `--provider stripe` restricts a run.
   Nonzero exits require operator review. Recover entirely missed adjustment
   notifications through the gateway's event replay tools; this command only
   refreshes adjustments already recorded locally. Reconciliation does not
   initiate refunds.

## Dashboard API

All paths are under `/api/v1/`; these are dashboard endpoints, outside the public
SDK contract. Amounts are integer minor units.

- `GET billing/plans`, `billing/account`, `billing/invoices`, `billing/invoices/{id}`
- `POST billing/subscribe` with `plan_id`
- `POST billing/invoices/{id}/checkout` with optional `provider` (`paystack` or `stripe`)
- `GET billing/payments/{id}`; `POST billing/payments/{id}` independently verifies it
- `POST billing/paystack/webhook`, `billing/stripe/webhook` with gateway signatures

## Launch evidence and boundaries

Automated coverage includes gateway HTTP/signature validation, independent
settlement checks, refunds/disputes, PostgreSQL payment races, invoice recovery,
and Chromium/WebKit billing UI flows. Gateway network calls in these tests are
mocked; they do not prove merchant onboarding or actual test-mode settlement.
Record real merchant test-mode results for **both providers** before live keys.

Live collection requires authorized merchant onboarding, finance signoff,
applicable invoice/tax requirements and privacy processor/transfer review.
Automatic tax, FX, automatic overdue suspension, self-service plan switching
and refund initiation are outside this implementation. Recurring invoices are
customer-paid; this does not create gateway-managed subscription debits.

References:

- [Stripe Checkout fulfillment](https://docs.stripe.com/checkout/fulfillment)
- [Stripe webhook verification and recovery](https://docs.stripe.com/events/manage-webhook-endpoints)
- [Paystack payment verification](https://paystack.com/docs/payments/verify-payments/)
- [Paystack webhooks](https://paystack.com/docs/payments/webhooks/)
- [Release evidence gate](release-evidence-gate.md)

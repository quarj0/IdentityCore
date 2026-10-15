# Unrated usage ledger (commercial infrastructure foundation)

This is an incremental implementation, NOT a finished billing/payment system.
The provider usage ledger exists to measure production work safely while the
commercial model is still being approved. It does not invoice, rate, collect,
suspend, or charge a customer.

ProviderCheck is the unique source of each BillingUsageEvent. Events are
created by explicit operator reconciliation after a provider check reaches
completed, failed or timeout with a completion timestamp. Cancelled, pending,
processing, unprojected and sandbox work never enter this ledger.

For a controlled tenant reconciliation:

    python backend/django/manage.py reconcile_provider_usage \
      --tenant ten_<trusted-public-id> --limit 100

The operation locks the source record, checks tenant/organization/project and
provider ownership consistency, and uses a unique provider_check constraint to
avoid duplicate usage. It records one event with quantity=1 and
rating_state=unrated. A changed terminal outcome after reconciliation causes a
hard conflict requiring manual accounting correction; it is NOT overwritten.

provider_scope=tenant_owned means customer-supplied provider configuration.
provider_scope=platform means a platform-owned provider. This is ownership
attribution, NOT proof that it is a paid managed-AI provider. Never apply
prices solely from this field. BYOP and managed processing may have different
billing models, processor costs and legal terms.

## Outstanding work before accepting payments

- Agree currency, jurisdiction, tax treatment, merchant of record and
  billing/payment processor for the legal operating entity.
- Approve a versioned catalog of plans, meters and effective-dated unit rates.
- Decide which successful/failed provider outcomes are billable, including
  retries, fallback and manually reviewed results.
- Record immutable corrections/credits, rate evaluations and customer-facing
  invoices with reconciliation against processor settlements and chargebacks.
- Implement signed processor webhooks with idempotency and audited refunds.
- Add dashboard invoices, payment methods, usage transparency, limits and
  tenant-facing dispute support.
- Require authorized admin approval and isolated payment-gateway test
  credentials before any live charging or automatic suspension.
- Complete commercial privacy, terms and tax/legal review for launch.

The customer onboarding journey must be tested separately for unmanaged BYOP,
managed verification and a sandbox-only organization. Avoid promising live
customer access while independent model/security/privacy gates are incomplete.

See docs/operations/release-evidence-gate.md.

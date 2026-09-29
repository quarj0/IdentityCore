# Privacy-safe product metrics

`GET /api/v1/analytics/product-metrics?days=30` returns aggregate counts for the authenticated tenant only. Supported windows are 7, 30, and 90 days, measured from the verification creation timestamp. The endpoint never returns a verification ID, subject identifier, external reference, free-text reason, evidence, locale, device fingerprint, IP address, or provider payload.

## Definitions

- **Cohort size:** tenant verifications created inside the selected window.
- **Completed:** a verification with a completion timestamp or a verified, rejected, or manual-review-required outcome.
- **Abandoned:** a verification whose final state is expired or cancelled.
- **Manual review:** a verification in manual-review-required state.
- **Failure:** a rejected or failed verification. Failure reasons are coarsened to document quality, liveness, provider, policy, or other; arbitrary source codes and details are never returned.
- **Completion rate:** completed verifications divided by cohort size.
- **Completion latency:** mean elapsed seconds between verification creation and completion timestamp.

These definitions describe operational workflow outcomes. They do not measure identity accuracy or imply an applicant’s risk.

## Disclosure controls

The minimum cohort is 10. For a cohort below 10, all metric values and cohort size are suppressed. For a larger cohort, individual count buckets from 1 through 9 are suppressed, latency is shown only when at least 10 completed records contribute, and failure-reason buckets are shown only at 10 or more. Failure categories are fixed and coarse.

The query uses `request.user.tenant` for every aggregate; callers cannot request another tenant. Access requires an authenticated tenant user. The endpoint is not available to the platform-wide admin query surface.

## Opt-out and retention

`PATCH /api/v1/analytics/product-metrics` accepts `{"product_metrics_opt_out": true|false}`. When opted out, reads return `{"status":"disabled","reason":"tenant_opt_out"}` and do not compute or return aggregates. The preference is stored in the tenant’s encrypted settings.

Metrics are computed on demand from verification records. No separate event table or copy is retained; the existing verification retention/deletion policy therefore bounds metric availability. A deletion or expiry that removes a source verification also removes its contribution from later queries. Do not export suppressed values or attempt to reconstruct hidden buckets from successive overlapping windows.

## Operator checks

During pilot readiness, confirm that tenant access is isolated, a cohort under 10 returns suppressed values, 1–9 buckets do not appear, and the opt-out takes effect. Keep dashboard screenshots and exports within the same access controls as the tenant account; never attach applicant-level records to a product-metrics report.

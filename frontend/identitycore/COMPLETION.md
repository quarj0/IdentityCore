# Public website maturity and ownership

Last reviewed: 2026-10-18

`frontend/identitycore` owns the public marketing website. Organization registration,
authentication, password/email recovery and onboarding are owned by `frontend/dashboard`.
Applicant consent/capture/liveness are owned by `frontend/verification-portal`.

## Implemented boundaries

- Public landing, platform, solutions, templates, developers, security, pricing,
  company, contact and legal surfaces.
- Account and `/onboarding/:path*` redirects to `NEXT_PUBLIC_DASHBOARD_URL`.
- A legacy `/verification` redirect to the hosted portal, moving its credential into
  a fragment rather than creating a duplicate capture journey.
- Public catalog/contact integrations, responsive navigation, metadata, sitemap and
  configurable indexing.

Legacy helper modules remaining in this directory do not establish a second active
account/onboarding application. Evaluate historical findings at their current execution
path, including dashboard components to which a feature moved. The
[historical audit](../../docs/reviews/README.md) remains open.

## Validation and remaining work

Run the website lint/build checks and the browser acceptance applicable to changed
public navigation and cross-application redirects. Content/legal approval, configured
production URLs/indexing, visual/accessibility assessment and deployment monitoring
remain release responsibilities. Production identity-provider, physical-device and
verification assurance belong to the hosted workload release evidence.

Public claims must follow the [current capability assessment](../../docs/architecture/product-alignment.md).
Do not advertise future claims, universal provider/country coverage or certified models
as implemented merely because a page describes the architectural direction.

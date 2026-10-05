# ADR 044: Explicit sandbox outcome simulation

Status: Accepted

An authenticated sandbox-only command on a pristine verification selects one of five fixed scenarios: approved, declined, review, timeout or provider_error. The service rechecks tenant and project environment under locks; debug mode, metadata flags, request headers and applicant values cannot enable simulation on a production project. Tenant and API-client environment authorization applies before the command reaches the service.

The simulator performs no outbound provider calls, media access or real identity processing. It writes synthetic provider provenance, a normal version-one decision snapshot and the normal result/event schemas. Simulation markers remain explicit. Its state transitions, audit and environment-filtered webhook outbox writes use the existing domain transaction. Sessions are revoked so later capture cannot attach actual evidence to an artificial result. Existing consent, evidence, processing jobs or decisions make a case ineligible.

Each case accepts one scenario. Repeating it returns the existing result without a second event; requesting a different scenario conflicts. Public production result semantics do not gain scenario selection or special applicant identifiers. Operations documentation provides normal create, simulate and result examples with sandbox credentials only.

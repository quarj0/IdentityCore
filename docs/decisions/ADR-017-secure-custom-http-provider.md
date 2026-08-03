# ADR-017: Secure custom HTTP provider adapter

## Status

Accepted

## Decision

Custom provider HTTP calls use an explicit hostname allowlist and HTTPS only.
Every resolved address is checked against public-network policy, including
private, loopback, link-local, reserved, and metadata destinations. Redirects
are disabled, timeouts are bounded, responses have a fixed maximum size, and
only JSON responses are accepted.

Provider credentials remain caller-supplied headers and are never included in
error messages or telemetry. The adapter returns bounded structured errors so
the provider orchestration layer can apply its normal retry and manual-review
policy.

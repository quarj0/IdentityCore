# ADR-024: Authorized, redacted, expiring data-subject exports

## Status

Accepted

## Decision

Exports are created and downloaded only within the authenticated tenant
scope. The payload is stored encrypted, delivered through a short-lived
single-purpose token, and audited at creation and download.

The export contains documented subject profile and verification outcome data,
while excluding document numbers, biometric templates, raw media, provider
credentials, network/device fingerprints, and internal notes. Expired or
invalid tokens return no payload.

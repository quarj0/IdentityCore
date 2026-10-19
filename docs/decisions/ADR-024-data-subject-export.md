# ADR-024: Authorized, redacted, expiring data-subject exports

## Status

Accepted

## Decision

Exports are created and downloaded only within the authenticated tenant
scope, with explicit `manage_subject_privacy` authorization for creation. Creation
serializes with deletion and reloads the current subject; deleted subjects cannot
create new exports. Deletion clears prior stored payloads and invalidates tokens.
The payload is stored encrypted, delivered through a short-lived
single-purpose token, and audited at creation and download.

The export contains documented subject profile and verification outcome data,
while excluding document numbers, biometric templates, raw media, provider
credentials, network/device fingerprints, and internal notes. Expired or
invalid tokens return no payload.

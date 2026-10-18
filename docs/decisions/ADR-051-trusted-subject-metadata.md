# ADR 051: Trusted hosted-journey subject metadata

Status: Accepted

The verification BFF signs a bounded metadata envelope with a purpose-specific shared
server secret. The envelope binds the upstream method, path, authorization digest,
request ID and timestamp to the reported User-Agent and optional ingress-asserted IP.
Django verifies the signature and request binding before using these attributes for
session, consent or audit records. Invalid or expired envelopes fail closed.

Client IP is accepted only from an explicitly configured single-address ingress header.
The ingress must overwrite that header and be the only network path to the portal.
Without that deployment guarantee, leave the setting empty: subject IP is unknown.
Generic forwarding chains are never interpreted. User-Agent remains browser-reported
context, not a verified device identity. Audit metadata labels both provenance and trust.
The immediate peer remains unchanged for throttling and transport security.

Unsigned direct API requests retain their immediate-peer semantics. Enabling the
shared secret requires signed metadata on hosted session/upload requests authenticated
with the reserved `IdentityCore-Verification-BFF/1` User-Agent, so an outdated portal
cannot silently record itself as the subject. Other direct SDK clients are unaffected.
The envelope is not an authorization credential; it is short-lived and bound to the
existing session credential. Existing session, consent and handoff replay controls
remain authoritative. Historical records are not rewritten or retroactively attributed.

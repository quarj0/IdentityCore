# Hosted subject metadata attribution

The verification BFF forwards a signed envelope for session exchange, authenticated
verification/upload actions and mobile handoff redemption. Django uses verified
subject context for session IP/User-Agent, immutable consent acceptance and audit.
Audit metadata and consent proof `request_provenance` distinguish `verification_portal`,
`direct`, and `unattributed_portal` sources. User-Agent is always reported context,
not proof of a device or physical person. No historical acceptance is rewritten.

## Configuration and rollout

1. Generate a dedicated random secret of at least 32 characters. Set
   `VERIFICATION_METADATA_SECRET` to the same server-only value on Django and the
   portal. Keep it independent of session/provider/JWT keys and out of browser
   variables, telemetry, source control and support records.
2. Deploy the Django verifier before the new portal. Existing direct SDK calls
   retain immediate-peer semantics. The production portal fails readiness and
   requests when its key is missing/short. A configured verifier rejects missing,
   invalid or expired envelopes from the identified BFF before state changes.
3. Leave `VERIFICATION_CLIENT_IP_HEADER` empty unless a trusted ingress overwrites
   one single-address header on every request and direct portal access is blocked.
   With that guarantee, set the portal variable to that header name, e.g.
   `x-real-ip`. Never copy an arbitrary forwarding chain or a client-supplied value.
   Invalid addresses, lists and scoped IPv6 addresses are recorded as unavailable.
4. Verify a synthetic session exchange and consent acceptance. Session, consent
   and audit should agree on subject context and provenance; the transport peer
   used by throttling must remain unchanged. Unknown IP is null, never the BFF IP.
5. Rotate by draining hosted requests, replacing the key on both servers and
   resuming after the probe. No key-overlap fallback is implemented; mismatched
   keys fail closed. Retained consent/audit evidence does not require this key.

The envelope contains a schema version, timestamp (60-second maximum skew), upstream
method/path, credential digest, request ID, reported User-Agent (1024 characters
maximum) and optional IP. Django verifies the HMAC over the exact base64url bytes
before decoding. Binding it to the session credential, route and request prevents
reuse in another request context. It is not an authorization credential or a
separate replay cache; session/consent/handoff controls still enforce operation
replay. TLS remains mandatory. Redaction covers the complete metadata header and
signature so encoded IP/User-Agent never enter ordinary logs.

With no key in development, the identified BFF has explicit `unattributed_portal`
context with no IP/User-Agent. Direct callers' forwarding headers are ignored.
Do not backfill historical records by guessing an applicant from proxy metadata.

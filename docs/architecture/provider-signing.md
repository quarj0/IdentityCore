# Provider message signing protocol (v1)

Set `signing_mode` to `hmac_v1` in an environment's provider configuration to
sign connection tests and capability requests and require authenticated responses.
The provider setup form selects this mode for new configurations. Existing
configurations without the field retain bearer authentication; `bearer` is an
explicit compatibility option and provides no message signature or nonce guarantee.
A signed connection test must pass before activation, including production approval.

In signed mode, every request and response carries `X-IC-Key-Id`, `X-IC-Timestamp`, `X-IC-Nonce`,
`X-IC-Signature-Version`, and `X-IC-Signature`. Responses must echo the request
nonce, which binds them to the initiating call. A verifier rejects messages more
than five minutes from its clock and atomically claims each accepted nonce, so a
valid message cannot be replayed.

## Canonical form

Sign the exact HTTP body bytes and verify the received bytes before decoding
JSON. Never parse and reserialize a body to verify it. The Python `canonical_json`
helper sorts keys, uses compact UTF-8 JSON and forbids non-finite numbers, but is
not a cross-runtime JSON canonicalization standard: number formatting and key
ordering can differ in other languages. The fixture includes the exact body
string for implementations in any language. The signed byte sequence is these
newline-separated fields:

```text
ic-provider-v1
UPPERCASE_HTTP_METHOD
/path?query=unchanged
unix_timestamp_seconds
nonce
lowercase_hex_sha256_of_body
```

The signature is the lowercase hexadecimal HMAC-SHA256 of those bytes. Providers
must compare it in constant time. The complete deterministic fixture at
[`docs/fixtures/provider-signing-v1.json`](../fixtures/provider-signing-v1.json)
is suitable for implementations in any language.

## Rotation

Verifiers receive a key ring indexed by key ID and signers select one active key.
To rotate safely, publish the new verification key, switch the signing key ID,
wait longer than the timestamp tolerance and maximum in-flight request duration,
then remove the old key. Unknown key IDs always fail closed.

## Verification boundaries

Header key IDs use 1–128 ASCII letters, digits, dots, underscores or hyphens.
Nonces use 1–256 ASCII letters, digits, underscores or hyphens; timestamps are
1–12 decimal ASCII digits and signatures are 64 lowercase hexadecimal digits.
Malformed values are rejected before comparison or nonce claims.

Use one stable replay namespace per provider and traffic direction across signing
key rotations. Nonce claims exclude key IDs, so an accepted nonce cannot be
reused under another active key. Independent providers may use separate namespaces.
The helper uses the dedicated `provider_signatures` Django cache alias backed by
Redis at `REDIS_URL`. Claims use Redis's atomic insert-if-absent operation across
API and worker processes. Configure Redis without eviction of live nonce keys;
unit tests explicitly use an isolated local-memory alias. A Redis outage fails
closed with retryable `provider_replay_store_unavailable`, never unsigned acceptance.

## Credential derivation and interoperability

The existing encrypted environment API credential is also the input to a
purpose-specific signing-key derivation. The signing secret is the lowercase
hexadecimal HMAC-SHA256 of the ASCII bytes `identitycore-provider-hmac-v1`, keyed
by the API credential's ASCII bytes. Use those 64 hexadecimal characters as the
UTF-8 key for the message signature algorithm above. Do not use the raw API key
directly as the message-signing key. The request key ID is the configuration's
public ID; the provider must echo that ID in its signed response.

The request retains its bearer Authorization header for provider authentication.
Verify the signature over the exact request body bytes and the POST URL path
(including an unchanged query, if present). Sign the exact response body bytes
using that same method/path and echo the request nonce. Responses may choose a
fresh timestamp within the five-minute tolerance. Missing, malformed, stale,
unbound or invalid response signatures fail before JSON results are returned.
No response-signature failure falls back to bearer mode. Signed HTTP error bodies
are also bounded and authenticated before their status can control retries, fallback
or circuit state. Authenticated HTTP errors retain their status-based retry semantics;
unsigned, altered or replayed errors return `provider_signature_invalid`.

Replay namespaces bind provider ID, environment and response direction, excluding
configuration/key IDs so rotation cannot reopen an accepted nonce. Nonces expire
after twice the timestamp tolerance. Cache connections and operations have a
one-second timeout independent of the bounded provider HTTP exchange.

The exact-wire interoperability cases in [`provider-signing-wire-v1.json`](../fixtures/provider-signing-wire-v1.json) cover Python and ECMAScript number formatting, signed zero and supplementary Unicode key ordering. Python and Node regression tests verify the published signatures over each raw body; reserializing a received body changes its signature.

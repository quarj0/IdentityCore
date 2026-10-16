# Provider message signing protocol (v1)

The repository supplies an HMAC-SHA256 signing helper and fixture. The current
configured provider transport uses bearer authentication; it does not invoke this
helper or verify signed responses. Integrating signing into that transport and
configuring a shared atomic nonce store remain required before claiming signed
BYOP traffic or replay protection across workers.

When integrated, every request and response carries `X-IC-Key-Id`, `X-IC-Timestamp`, `X-IC-Nonce`,
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
The default helper uses Django's cache, whose default local-memory backend is
process-local; production integration must supply a shared atomic `claim_nonce`
implementation rather than relying on that development default.

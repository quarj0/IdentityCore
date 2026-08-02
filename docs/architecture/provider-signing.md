# Provider message signing protocol (v1)

IdentityCore authenticates custom-provider traffic with an HMAC-SHA256 signature.
Every request and response carries `X-IC-Key-Id`, `X-IC-Timestamp`, `X-IC-Nonce`,
`X-IC-Signature-Version`, and `X-IC-Signature`. Responses must echo the request
nonce, which binds them to the initiating call. A verifier rejects messages more
than five minutes from its clock and atomically claims each accepted nonce, so a
valid message cannot be replayed.

## Canonical form

JSON bodies are UTF-8 encoded with object keys sorted, no insignificant
whitespace, Unicode characters unescaped, and non-finite numbers forbidden. The
signed byte sequence is these newline-separated fields:

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

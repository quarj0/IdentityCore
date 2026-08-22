# IdentityCore Java SDK

Production server-side Java 17+ client for IdentityCore. API-client secrets must never be shipped in Android or browser applications.

```java
var client = IdentityCoreClient.builder()
    .apiOrigin("https://api.identitycore.com")
    .clientId(System.getenv("IDENTITYCORE_CLIENT_ID"))
    .clientSecret(System.getenv("IDENTITYCORE_CLIENT_SECRET"))
    .build();

var input = new ObjectMapper().createObjectNode()
    .put("purpose", "Customer onboarding")
    .put("policy_id", "pol_...")
    .set("verification_subject", new ObjectMapper().createObjectNode().put("full_name", "Kwame Mensah"));
var verification = client.verifications.create(input, "customer-123-onboarding-v1");
var result = client.verifications.result(verification.path("id").asText());
```

The SDK provides policies, verification creation/list/detail/result/cancel/resend/evidence helpers, lazy pagination, safe retries, structured API errors, request IDs, timeouts, and constant-time webhook verification.

Use `WebhookVerifier.verifyV1` with the raw body, signature, timestamp, event ID, and the current/temporarily previous signing secrets; the five-argument overload applies the default five-minute tolerance and current time. For replay protection, use the full overload with a `Predicate<String>` that atomically inserts the event ID only if absent and returns whether it succeeded. IdentityCore emits signatures for both secrets during the rotation overlap. Canonical behavior is tested from `sdk/fixtures/webhook-signature-v1.json`.

Run `mvn test package` from this directory.

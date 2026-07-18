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
```

The SDK provides policies, verification creation/list/detail/cancel/resend/evidence helpers, lazy pagination, safe retries, structured API errors, request IDs, timeouts, and constant-time webhook verification.

Run `mvn test package` from this directory.


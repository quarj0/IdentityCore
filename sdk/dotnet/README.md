# IdentityCore .NET SDK

Production server-side .NET 8 client for IdentityCore. Never include API-client secrets in Blazor WebAssembly, MAUI, desktop, or other distributed client applications.

```csharp
using var client = new IdentityCoreClient(new()
{
    ApiOrigin = new Uri("https://api.identitycore.com"),
    ClientId = Environment.GetEnvironmentVariable("IDENTITYCORE_CLIENT_ID")!,
    ClientSecret = Environment.GetEnvironmentVariable("IDENTITYCORE_CLIENT_SECRET")!,
});

var verification = await client.Verifications.CreateAsync(new
{
    purpose = "Customer onboarding",
    policy_id = "pol_...",
    verification_subject = new { full_name = "Kwame Mensah" },
}, "customer-123-onboarding-v1");
var result = await client.Verifications.ResultAsync(verification.GetProperty("id").GetString()!);
```

The SDK provides policies, verification creation/list/detail/result/cancel/resend/evidence helpers, async pagination, safe retries, structured API errors, cancellation, timeouts, and constant-time webhook verification.

Use `WebhookVerifier.VerifyV1` with the raw body, signature, timestamp, event ID, and the current/temporarily previous signing secrets. Pass a durable event-ID set to reject replays; the default timestamp tolerance is five minutes. Canonical behavior is tested from `sdk/fixtures/webhook-signature-v1.json`.

Run `dotnet test IdentityCore.sln` and `dotnet pack src/IdentityCore/IdentityCore.csproj -c Release`.

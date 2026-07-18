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
```

The SDK provides policies, verification creation/list/detail/cancel/resend/evidence helpers, async pagination, safe retries, structured API errors, cancellation, timeouts, and constant-time webhook verification.

Run `dotnet test IdentityCore.sln` and `dotnet pack src/IdentityCore/IdentityCore.csproj -c Release`.

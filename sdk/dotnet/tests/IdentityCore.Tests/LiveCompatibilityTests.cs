using System.Security.Cryptography;
using System.Text;
using Xunit;

namespace IdentityCore.Tests;

public sealed class LiveCompatibilityTests
{
    [Fact]
    public async Task CreateGetListErrorAndWebhook()
    {
        var origin = Environment.GetEnvironmentVariable("IDENTITYCORE_COMPAT_URL");
        if (string.IsNullOrWhiteSpace(origin)) return;
        using var client = new IdentityCoreClient(new() { ApiOrigin = new Uri(origin), ClientId = Environment.GetEnvironmentVariable("IDENTITYCORE_COMPAT_CLIENT_ID")!, ClientSecret = Environment.GetEnvironmentVariable("IDENTITYCORE_COMPAT_CLIENT_SECRET")! });
        var reference = "dotnet-" + Guid.NewGuid().ToString("N");
        var created = await client.Verifications.CreateAsync(new { purpose = "SDK compatibility", policy_id = Environment.GetEnvironmentVariable("IDENTITYCORE_COMPAT_POLICY_ID"), external_reference = reference, verification_subject = new { full_name = ".NET Compatibility" } });
        var id = created.GetProperty("id").GetString()!;
        Assert.Equal(id, (await client.Verifications.RetrieveAsync(id)).GetProperty("id").GetString());
        Assert.Contains((await client.Verifications.ListAsync(externalReference: reference)).GetProperty("results").EnumerateArray(), item => item.GetProperty("id").GetString() == id);
        var error = await Assert.ThrowsAsync<IdentityCoreApiException>(() => client.Verifications.RetrieveAsync("ver_does_not_exist"));
        Assert.Equal(404, error.Status);

        const string eventId = "evt_live_compatibility", secret = "webhook-secret";
        var payload = Encoding.UTF8.GetBytes($"{{\"id\":\"{eventId}\",\"schema_version\":\"1\",\"type\":\"verification.completed\"}}");
        var timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString();
        var derivedKey = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(secret))).ToLowerInvariant();
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(derivedKey));
        var signature = "v1=" + Convert.ToHexString(hmac.ComputeHash(Encoding.UTF8.GetBytes($"{timestamp}.{eventId}.").Concat(payload).ToArray())).ToLowerInvariant();
        Assert.True(WebhookVerifier.VerifyV1(payload, signature, timestamp, eventId, [secret]));
    }
}

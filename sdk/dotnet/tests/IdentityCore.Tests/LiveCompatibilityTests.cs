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

        var payload = Encoding.UTF8.GetBytes("{\"type\":\"verification.completed\"}"); var timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString(); const string key = "webhook-secret";
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(key)); var signature = "sha256=" + Convert.ToHexString(hmac.ComputeHash(Encoding.UTF8.GetBytes(timestamp + ".").Concat(payload).ToArray())).ToLowerInvariant();
        Assert.True(WebhookVerifier.Verify(payload, signature, timestamp, key));
    }
}

using System.Text;
using System.Text.Json;
using Xunit;

namespace IdentityCore.Tests;

public sealed class WebhookVerifierTests
{
    [Fact]
    public void Verifies_canonical_v1_fixture_rotation_tolerance_and_replay()
    {
        using var fixture = JsonDocument.Parse(File.ReadAllText("webhook-signature-v1.json"));
        var root = fixture.RootElement;
        var body = Encoding.UTF8.GetBytes(root.GetProperty("raw_body").GetString()!);
        var eventId = root.GetProperty("event_id").GetString()!;
        var timestamp = root.GetProperty("timestamp").GetString()!;
        var secrets = new[] { root.GetProperty("current_secret").GetString()!, root.GetProperty("previous_secret").GetString()! };
        var seen = new HashSet<string>();
        Assert.True(WebhookVerifier.VerifyV1(body, root.GetProperty("rotation_signature_header").GetString()!, timestamp, eventId, [root.GetProperty("previous_secret").GetString()!], TimeSpan.FromMinutes(5), DateTimeOffset.FromUnixTimeSeconds(root.GetProperty("now_within_tolerance").GetInt64()), seen.Add));
        Assert.False(WebhookVerifier.VerifyV1(body, root.GetProperty("previous_signature").GetString()!, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), DateTimeOffset.FromUnixTimeSeconds(root.GetProperty("now_within_tolerance").GetInt64()), seen.Add));
        Assert.False(WebhookVerifier.VerifyV1(body, root.GetProperty("current_signature").GetString()!, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), DateTimeOffset.FromUnixTimeSeconds(root.GetProperty("now_outside_tolerance").GetInt64())));
        var signature = root.GetProperty("current_signature").GetString()!;
        var now = DateTimeOffset.FromUnixTimeSeconds(root.GetProperty("now_within_tolerance").GetInt64());
        Assert.True(WebhookVerifier.VerifyV1(body, root.GetProperty("rotation_signature_header").GetString()!, timestamp, eventId, [root.GetProperty("current_secret").GetString()!], TimeSpan.FromMinutes(5), now));
        Assert.True(WebhookVerifier.VerifyV1(body, signature, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(body, signature.Replace("v1=", "v2="), timestamp, eventId, secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(body, signature, timestamp, "evt_other", secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(Encoding.UTF8.GetBytes(root.GetProperty("raw_body").GetString()! + " "), signature, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(Encoding.UTF8.GetBytes(root.GetProperty("non_object_raw_body").GetString()!), root.GetProperty("non_object_signature").GetString()!, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(Encoding.UTF8.GetBytes(root.GetProperty("invalid_schema_raw_body").GetString()!), root.GetProperty("invalid_schema_signature").GetString()!, timestamp, eventId, secrets, TimeSpan.FromMinutes(5), now));
        Assert.False(WebhookVerifier.VerifyV1(body, signature, long.MinValue.ToString(), eventId, secrets, TimeSpan.FromMinutes(5), DateTimeOffset.UnixEpoch));
    }
}

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace IdentityCore;

public static class WebhookVerifier
{
    public static bool Verify(ReadOnlySpan<byte> rawBody, string signature, string timestamp, string signingKey, TimeSpan? tolerance = null, DateTimeOffset? now = null)
    {
        if (string.IsNullOrWhiteSpace(signingKey)) throw new IdentityCoreException("signingKey is required.");
        var window = tolerance ?? TimeSpan.FromMinutes(5);
        if (window < TimeSpan.Zero) throw new IdentityCoreException("tolerance cannot be negative.");
        if (!long.TryParse(timestamp, out var sentAt)) throw new IdentityCoreException("Webhook timestamp is invalid.");
        var current = (now ?? DateTimeOffset.UtcNow).ToUnixTimeSeconds();
        long age;
        try { age = checked(current - sentAt); }
        catch (OverflowException) { return false; }
        if (age > window.TotalSeconds || age < -window.TotalSeconds) return false;
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(signingKey));
        var prefix = Encoding.UTF8.GetBytes(timestamp + ".");
        var message = new byte[prefix.Length + rawBody.Length];
        prefix.CopyTo(message, 0); rawBody.CopyTo(message.AsSpan(prefix.Length));
        var expected = Encoding.UTF8.GetBytes("sha256=" + Convert.ToHexString(hmac.ComputeHash(message)).ToLowerInvariant());
        var received = Encoding.UTF8.GetBytes(signature ?? string.Empty);
        return expected.Length == received.Length && CryptographicOperations.FixedTimeEquals(expected, received);
    }

    public static bool VerifyV1(ReadOnlySpan<byte> rawBody, string signature, string timestamp, string eventId, IEnumerable<string> signingSecrets, TimeSpan? tolerance = null, DateTimeOffset? now = null, Func<string, bool>? claimEventId = null)
    {
        if (string.IsNullOrWhiteSpace(eventId)) throw new IdentityCoreException("eventId is required for v1 signatures.");
        var secrets = signingSecrets?.Where(secret => !string.IsNullOrWhiteSpace(secret)).ToArray() ?? [];
        if (secrets.Length == 0) throw new IdentityCoreException("At least one signing secret is required.");
        var window = tolerance ?? TimeSpan.FromMinutes(5);
        if (window < TimeSpan.Zero) throw new IdentityCoreException("tolerance cannot be negative.");
        if (!long.TryParse(timestamp, out var sentAt)) throw new IdentityCoreException("Webhook timestamp is invalid.");
        var current = (now ?? DateTimeOffset.UtcNow).ToUnixTimeSeconds();
        long age;
        try { age = checked(current - sentAt); }
        catch (OverflowException) { return false; }
        if (age > window.TotalSeconds || age < -window.TotalSeconds) return false;
        var prefix = Encoding.UTF8.GetBytes($"{timestamp}.{eventId}.");
        var message = new byte[prefix.Length + rawBody.Length];
        prefix.CopyTo(message, 0); rawBody.CopyTo(message.AsSpan(prefix.Length));
        var receivedSignatures = (signature ?? string.Empty).Split(',').Select(value => Encoding.UTF8.GetBytes(value.Trim())).ToArray();
        var valid = secrets.Any(secret =>
        {
            var derivedKey = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(secret))).ToLowerInvariant();
            using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(derivedKey));
            var expected = Encoding.UTF8.GetBytes("v1=" + Convert.ToHexString(hmac.ComputeHash(message)).ToLowerInvariant());
            return receivedSignatures.Any(received =>
                expected.Length == received.Length && CryptographicOperations.FixedTimeEquals(expected, received));
        });
        if (!valid) return false;
        try
        {
            using var document = JsonDocument.Parse(rawBody.ToArray());
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object
                || !root.TryGetProperty("id", out var payloadEventId)
                || !root.TryGetProperty("schema_version", out var schemaVersion)
                || payloadEventId.ValueKind != JsonValueKind.String
                || schemaVersion.ValueKind != JsonValueKind.String
                || payloadEventId.GetString() != eventId
                || schemaVersion.GetString() != "1") return false;
        }
        catch (JsonException) { return false; }
        if (claimEventId is not null && !claimEventId(eventId)) return false;
        return true;
    }
}

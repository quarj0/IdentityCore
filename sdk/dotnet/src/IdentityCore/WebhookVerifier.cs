using System.Security.Cryptography;
using System.Text;

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
        if (Math.Abs(current - sentAt) > window.TotalSeconds) return false;
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(signingKey));
        var prefix = Encoding.UTF8.GetBytes(timestamp + ".");
        var message = new byte[prefix.Length + rawBody.Length];
        prefix.CopyTo(message, 0); rawBody.CopyTo(message.AsSpan(prefix.Length));
        var expected = Encoding.UTF8.GetBytes("sha256=" + Convert.ToHexString(hmac.ComputeHash(message)).ToLowerInvariant());
        var received = Encoding.UTF8.GetBytes(signature ?? string.Empty);
        return expected.Length == received.Length && CryptographicOperations.FixedTimeEquals(expected, received);
    }
}


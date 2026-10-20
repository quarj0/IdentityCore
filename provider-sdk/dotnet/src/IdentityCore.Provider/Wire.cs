using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace IdentityCore.Provider;

public sealed class ProtocolError(string message) : Exception(message);
public sealed class StorageUnavailable() : Exception("Provider durable storage is unavailable.");

public sealed record SigningKey(string KeyId, [property: JsonIgnore] string Secret, string TenantId, string Environment, IReadOnlySet<string> Capabilities)
{
    public override string ToString() => $"ProviderSigningKey({KeyId})";
}

public static class Wire
{
    public const string Version = "ic-provider-v1";
    public const int MaxBodyBytes = 256 * 1024;
    private static readonly JsonSerializerOptions JsonOptions = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping, MaxDepth = 64 };
    public sealed record Auth(SigningKey Key, string Nonce);
    public static string RandomToken() => Convert.ToBase64String(RandomNumberGenerator.GetBytes(24)).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    public static string Digest(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    private static string Hmac(string secret, byte[] bytes) => Convert.ToHexString(HMACSHA256.HashData(Encoding.UTF8.GetBytes(secret), bytes)).ToLowerInvariant();
    public static string DeriveSigningSecret(string apiKey)
    {
        if (apiKey.Any(c => c > 127)) throw new ProtocolError("Provider credential is invalid.");
        return Hmac(apiKey, Encoding.ASCII.GetBytes("identitycore-provider-hmac-v1"));
    }
    public static byte[] Bytes(JsonNode value)
    {
        try { return JsonSerializer.SerializeToUtf8Bytes(value, JsonOptions); }
        catch { throw new ProtocolError("Provider JSON is invalid."); }
    }
    public static JsonNode Canonical(JsonNode value) => value switch
    {
        JsonObject obj => new JsonObject(obj.OrderBy(pair => pair.Key, StringComparer.Ordinal).Select(pair => new KeyValuePair<string, JsonNode?>(pair.Key, pair.Value is null ? null : Canonical(pair.Value)))),
        JsonArray array => new JsonArray(array.Select(item => item is null ? null : Canonical(item)).ToArray()),
        _ => value.DeepClone()
    };
    public static JsonObject Parse(byte[] bytes)
    {
        if (bytes.Length > MaxBodyBytes) throw new ProtocolError("Provider message exceeds its size limit.");
        try
        {
            // JsonNode alone permits ambiguous duplicate names. Validate the complete tree first.
            using var document = JsonDocument.Parse(bytes, new JsonDocumentOptions { MaxDepth = 64 });
            void Validate(JsonElement value)
            {
                if (value.ValueKind == JsonValueKind.Object)
                {
                    var names = new HashSet<string>(StringComparer.Ordinal);
                    foreach (var field in value.EnumerateObject())
                    {
                        if (!names.Add(field.Name)) throw new ProtocolError("Duplicate JSON fields are forbidden.");
                        Validate(field.Value);
                    }
                }
                else if (value.ValueKind == JsonValueKind.Array) foreach (var item in value.EnumerateArray()) Validate(item);
                else if (value.ValueKind == JsonValueKind.Number && (!value.TryGetDouble(out var number) || !double.IsFinite(number))) throw new ProtocolError("Nonfinite JSON is forbidden.");
            }
            Validate(document.RootElement);
            return JsonNode.Parse(bytes, documentOptions: new JsonDocumentOptions { MaxDepth = 64 }) as JsonObject ?? throw new ProtocolError("Provider messages must be objects.");
        }
        catch { throw new ProtocolError("Provider JSON is invalid."); }
    }
    public static byte[] Message(string method, string path, long timestamp, string nonce, byte[] body) => Encoding.UTF8.GetBytes(string.Join("\n", Version, method.ToUpperInvariant(), path, timestamp.ToString(CultureInfo.InvariantCulture), nonce, Digest(body)));
    public static Dictionary<string, string> Sign(string method, string path, byte[] body, SigningKey key, long? timestamp = null, string? nonce = null)
    {
        var time = timestamp ?? DateTimeOffset.UtcNow.ToUnixTimeSeconds(); var token = nonce ?? RandomToken();
        return new() { ["X-IC-Key-Id"] = key.KeyId, ["X-IC-Timestamp"] = time.ToString(CultureInfo.InvariantCulture), ["X-IC-Nonce"] = token, ["X-IC-Signature-Version"] = Version, ["X-IC-Signature"] = Hmac(key.Secret, Message(method, path, time, token, body)) };
    }
    public static async Task<Auth> VerifyAsync(string method, string path, byte[] body, IReadOnlyDictionary<string, string> headers, IReadOnlyDictionary<string, SigningKey> keys, Func<string, long, Task<bool>> claimNonce, long? now = null, string? expectedNonce = null, string replayNamespace = "provider-request")
    {
        if (body.Length > MaxBodyBytes || claimNonce is null) throw new ProtocolError("Provider authentication is unavailable.");
        var lower = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var header in headers) if (!lower.TryAdd(header.Key, header.Value)) throw new ProtocolError("Provider authentication failed.");
        foreach (var pair in new Dictionary<string, string> { ["X-IC-Key-Id"] = "[A-Za-z0-9_.-]{1,128}", ["X-IC-Timestamp"] = "[0-9]{1,12}", ["X-IC-Nonce"] = "[A-Za-z0-9_-]{1,256}", ["X-IC-Signature"] = "[0-9a-f]{64}" })
            if (!lower.TryGetValue(pair.Key, out var value) || !Regex.IsMatch(value, "\\A" + pair.Value + "\\z", RegexOptions.CultureInvariant)) throw new ProtocolError("Provider authentication failed.");
        if (!lower.TryGetValue("X-IC-Signature-Version", out var version) || version != Version || !keys.TryGetValue(lower["X-IC-Key-Id"], out var key)) throw new ProtocolError("Provider authentication failed.");
        var timestamp = long.Parse(lower["X-IC-Timestamp"], CultureInfo.InvariantCulture); var nonce = lower["X-IC-Nonce"];
        if (Math.Abs((now ?? DateTimeOffset.UtcNow.ToUnixTimeSeconds()) - timestamp) > 300 || (expectedNonce is not null && nonce != expectedNonce)) throw new ProtocolError("Provider authentication failed.");
        var expected = Sign(method, path, body, key, timestamp, nonce)["X-IC-Signature"];
        if (!CryptographicOperations.FixedTimeEquals(Encoding.ASCII.GetBytes(expected), Encoding.ASCII.GetBytes(lower["X-IC-Signature"]))) throw new ProtocolError("Provider authentication failed.");
        var scope = new JsonArray(Version, replayNamespace, key.TenantId, key.Environment, nonce);
        if (!await claimNonce(Digest(Bytes(scope)), timestamp + 301)) throw new ProtocolError("Provider nonce was already used.");
        return new Auth(key, nonce);
    }
}

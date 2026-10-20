using System.Globalization;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace IdentityCore.Provider;

public static class Contracts
{
    public const string OperationContract = "ic-provider-operations-v1";
    private static readonly HashSet<string> Fields = ["operation_contract", "operation_id", "configuration_id", "tenant_id", "project_id", "environment", "capability", "contract_version", "request_sha256", "lease_generation", "deadline", "callback_path", "lease_token"];
    internal static string Text(JsonNode? node) => node is JsonValue value && value.TryGetValue<string>(out var text) ? text : throw new ProtocolError("Provider field must be a string.");
    internal static bool Match(string value, string pattern) => Regex.IsMatch(value, "\\A" + pattern + "\\z", RegexOptions.CultureInvariant);
    private static bool Integer(JsonNode? node, out long number)
    {
        number = 0;
        return node is JsonValue && Match(node.ToJsonString(), "-?[0-9]+") && long.TryParse(node.ToJsonString(), NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out number);
    }
    private static bool Number(JsonNode? node, out double number)
    {
        number = 0;
        return node is JsonValue && double.TryParse(node.ToJsonString(), NumberStyles.Float, CultureInfo.InvariantCulture, out number) && double.IsFinite(number);
    }
    public static DateTimeOffset ValidateBinding(JsonObject binding, SigningKey key, DateTimeOffset? now = null, bool completion = true)
    {
        if (!Fields.SetEquals(binding.Select(pair => pair.Key))) throw new ProtocolError("Operation binding is incomplete.");
        foreach (var field in Fields.Where(field => field != "lease_generation")) Text(binding[field]);
        if (Text(binding["operation_contract"]) != OperationContract || Text(binding["contract_version"]) != "1" || Text(binding["configuration_id"]) != key.KeyId || Text(binding["tenant_id"]) != key.TenantId || Text(binding["environment"]) != key.Environment || !key.Capabilities.Contains(Text(binding["capability"])) || !Integer(binding["lease_generation"], out var number) || number < 1 || number > 9007199254740991L) throw new ProtocolError("Operation scope does not match this provider key.");
        foreach (var field in new[] { "operation_id", "configuration_id", "tenant_id", "project_id" }) if (!Match(Text(binding[field]), "[A-Za-z0-9_-]{1,64}")) throw new ProtocolError("Operation identifiers are invalid.");
        if (!Match(Text(binding["request_sha256"]), "[0-9a-f]{64}") || !Match(Text(binding["lease_token"]), "[A-Za-z0-9_-]{16,256}")) throw new ProtocolError("Operation fingerprint or lease is invalid.");
        if (Text(binding["callback_path"]) != $"/api/v1/providers/operations/{Text(binding["operation_id"])}/callback") throw new ProtocolError("Operation callback path is invalid.");
        var rawDeadline = Text(binding["deadline"]);
        if (!Match(rawDeadline, @"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})") || !DateTimeOffset.TryParse(rawDeadline, CultureInfo.InvariantCulture, DateTimeStyles.None, out var deadline) || (completion && deadline <= (now ?? DateTimeOffset.UtcNow))) throw new ProtocolError("Operation deadline is invalid or expired.");
        return deadline;
    }
    public static JsonObject ValidateResult(string capability, JsonObject result)
    {
        if (Text(result["contract_version"]) != "1" || Text(result["capability"]) != capability || !new[] { "completed", "failed", "inconclusive" }.Contains(Text(result["status"]))) throw new ProtocolError("Provider result envelope is invalid.");
        var bytes = Wire.Bytes(result); if (bytes.Length > 200 * 1024) throw new ProtocolError("Provider result exceeds its size limit."); Wire.Parse(bytes);
        if (capability == "liveness" && Text(result["status"]) == "completed")
        {
            if (result["metrics"] is not JsonObject metrics || !Integer(metrics["face_count"], out var faces) || faces < 0 || !Number(metrics["avg_detection_confidence"], out var score) || !double.IsFinite(score) || score < 0 || score > 1) throw new ProtocolError("Liveness result metrics are invalid.");
            foreach (var field in new[] { "model_name", "model_version" }) { var value = Text(result[field]); if (string.IsNullOrWhiteSpace(value) || value.Length > (field == "model_name" ? 120 : 64)) throw new ProtocolError("Liveness model provenance is required."); }
        }
        return result;
    }
    public static string BindingDigest(JsonObject binding) => Wire.Digest(Wire.Bytes(Wire.Canonical(binding)));
}

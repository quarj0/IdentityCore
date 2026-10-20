using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace IdentityCore.Provider;

public sealed record ProviderResponse(int Status, [property: JsonIgnore] byte[] Body, [property: JsonIgnore] IReadOnlyDictionary<string, string> Headers)
{
    public override string ToString() => $"ProviderResponse({Status})";
}
public sealed record ProviderCallback([property: JsonIgnore] byte[] Body, [property: JsonIgnore] IReadOnlyDictionary<string, string> Headers)
{
    public override string ToString() => "ProviderCallback(redacted)";
}

/// <summary>Framework-neutral endpoint. Preserve exact request and response bytes in HTTP adapters.</summary>
public sealed class ProviderRuntime
{
    public delegate Task<JsonObject> CapabilityHandler(string? operationId, JsonObject inputs, CancellationToken cancellationToken);
    public delegate Task<bool> LifecycleHandler(JsonObject binding, CancellationToken cancellationToken);
    private readonly IReadOnlyDictionary<string, SigningKey> keys;
    private readonly IOperationStore store;
    private readonly IReadOnlyDictionary<string, CapabilityHandler> handlers;
    private readonly LifecycleHandler cancelHandler;
    private readonly LifecycleHandler deleteHandler;
    public ProviderRuntime(IReadOnlyDictionary<string, SigningKey> keys, IOperationStore store, IReadOnlyDictionary<string, CapabilityHandler> handlers, LifecycleHandler cancelHandler, LifecycleHandler deleteHandler)
    {
        if (keys.Count == 0 || store is null || cancelHandler is null || deleteHandler is null) throw new ArgumentException("Provider keys, durable storage and explicit lifecycle handlers are required.");
        this.keys = new Dictionary<string, SigningKey>(keys); this.store = store; this.handlers = new Dictionary<string, CapabilityHandler>(handlers); this.cancelHandler = cancelHandler; this.deleteHandler = deleteHandler;
    }
    private static JsonObject Error(string code, bool retryable) => new() { ["contract_version"] = "1", ["status"] = "failed", ["error"] = new JsonObject { ["code"] = code, ["retryable"] = retryable } };
    private static bool Fields(JsonObject value, params string[] fields) => new HashSet<string>(fields).SetEquals(value.Select(pair => pair.Key));
    private static ProviderResponse Unsigned(int status, string code, bool retryable) => new(status, Wire.Bytes(Error(code, retryable)), new Dictionary<string, string> { ["Content-Type"] = "application/json", ["Cache-Control"] = "no-store" });
    public async Task<ProviderResponse> HandleAsync(string method, string path, byte[] body, IReadOnlyDictionary<string, string> headers, long? now = null, CancellationToken cancellationToken = default)
    {
        Wire.Auth auth; var time = now ?? DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        try { auth = await Wire.VerifyAsync(method, path, body, headers, keys, store.ClaimNonceAsync, time); }
        catch (ProtocolError) { return Unsigned(403, "provider_authentication_failed", false); }
        catch { return Unsigned(503, "provider_replay_store_unavailable", true); }
        var status = 200; JsonObject payload;
        try
        {
            var request = Wire.Parse(body); var key = auth.Key;
            if (!method.Equals("POST", StringComparison.OrdinalIgnoreCase) || Contracts.Text(request["contract_version"]) != "1") throw new ProtocolError("Provider request method or version is unsupported.");
            var operation = request.ContainsKey("operation") ? Contracts.Text(request["operation"]) : null;
            if (operation == "connection_test")
            {
                var allowed = new HashSet<string> { "contract_version", "operation", "environment", "challenge", "capabilities", "operation_contract" };
                if (request.Any(pair => !allowed.Contains(pair.Key)) || Contracts.Text(request["environment"]) != key.Environment || request["capabilities"] is not JsonArray capabilities || capabilities.Count == 0) throw new ProtocolError("Provider negotiation scope does not match.");
                var challenge = Contracts.Text(request["challenge"]); var names = capabilities.Select(Contracts.Text).ToArray();
                if (challenge.Length is < 1 or > 256 || names.Distinct(StringComparer.Ordinal).Count() != names.Length || names.Any(name => !key.Capabilities.Contains(name))) throw new ProtocolError("Provider negotiation scope does not match.");
                var contract = request.ContainsKey("operation_contract") ? Contracts.Text(request["operation_contract"]) : "sync";
                if (contract is not ("sync" or Contracts.OperationContract)) throw new ProtocolError("Provider operation contract is unsupported.");
                payload = new JsonObject { ["contract_version"] = "1", ["status"] = "completed", ["challenge"] = challenge, ["capabilities"] = capabilities.DeepClone() };
                if (request.ContainsKey("operation_contract")) payload["operation_contract"] = contract;
            }
            else if (operation is "start" or "poll" or "cancel" or "delete")
            {
                var fields = operation == "start" ? new[] { "contract_version", "operation", "binding", "inputs" } : new[] { "contract_version", "operation", "binding" };
                if (!Fields(request, fields) || request["binding"] is not JsonObject binding) throw new ProtocolError("Provider operation fields are unsupported.");
                var deadline = Contracts.ValidateBinding(binding, key, DateTimeOffset.FromUnixTimeSeconds(time), operation is "start" or "poll");
                if (operation == "start")
                {
                    if (request["inputs"] is not JsonObject inputs) throw new ProtocolError("Provider inputs must be an object.");
                    payload = await store.AdmitAsync(binding, inputs, deadline);
                }
                else if (operation == "poll") payload = await store.PollAsync(binding);
                else
                {
                    // Fence local workers before attempting external cancellation or erasure.
                    await store.ControlAsync(binding, "cancel");
                    if (!await (operation == "delete" ? deleteHandler : cancelHandler)(binding, cancellationToken)) throw new InvalidOperationException();
                    payload = await store.ControlAsync(binding, operation);
                }
            }
            else if (operation is null)
            {
                if (!Fields(request, "contract_version", "capability", "environment", "inputs") || Contracts.Text(request["environment"]) != key.Environment || request["inputs"] is not JsonObject inputs) throw new ProtocolError("Provider invocation scope does not match.");
                var capability = Contracts.Text(request["capability"]);
                if (!key.Capabilities.Contains(capability) || !handlers.TryGetValue(capability, out var handler)) throw new ProtocolError("Provider capability handler is unavailable.");
                payload = Contracts.ValidateResult(capability, await handler(null, inputs, cancellationToken));
            }
            else throw new ProtocolError("Provider operation is unsupported.");
        }
        catch (ProtocolError) { status = 400; payload = Error("provider_invalid_request", false); }
        catch { status = 503; payload = Error("provider_temporarily_unavailable", true); }
        var encoded = Wire.Bytes(payload); var responseHeaders = Wire.Sign(method, path, encoded, auth.Key, time, auth.Nonce);
        responseHeaders["Content-Type"] = "application/json"; responseHeaders["Cache-Control"] = "no-store";
        return new ProviderResponse(status, encoded, responseHeaders);
    }
    public async Task<JsonObject?> WorkOnceAsync(int leaseSeconds = 30, CancellationToken cancellationToken = default)
    {
        var lease = await store.ClaimJobAsync(leaseSeconds); if (lease is null) return null;
        using var stop = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        async Task Heartbeat()
        {
            using var timer = new PeriodicTimer(TimeSpan.FromMilliseconds(Math.Max(250, leaseSeconds * 1000 / 3)));
            try { while (await timer.WaitForNextTickAsync(stop.Token)) if (!await store.RenewAsync(lease, leaseSeconds)) { stop.Cancel(); return; } }
            catch { stop.Cancel(); }
        }
        var heartbeat = Heartbeat();
        try
        {
            var capability = Contracts.Text(lease.Binding["capability"]);
            if (!handlers.TryGetValue(capability, out var handler)) throw new ProtocolError("Provider capability handler is unavailable.");
            var result = Contracts.ValidateResult(capability, await handler(lease.OperationId, lease.Inputs, stop.Token));
            return await store.CompleteAsync(lease, result);
        }
        catch { throw new ProtocolError("Provider processing did not complete; its durable lease will permit retry."); }
        finally { stop.Cancel(); await heartbeat; }
    }
    public async Task<ProviderCallback> CallbackAsync(JsonObject binding, long? timestamp = null)
    {
        if (!keys.TryGetValue(Contracts.Text(binding["configuration_id"]), out var key)) throw new ProtocolError("Provider callback key is unavailable.");
        Contracts.ValidateBinding(binding, key); var payload = await store.PollAsync(binding);
        if (Contracts.Text(payload["status"]) is not ("completed" or "failed")) throw new ProtocolError("The operation has no terminal result to deliver.");
        var body = Wire.Bytes(payload); return new ProviderCallback(body, Wire.Sign("POST", Contracts.Text(binding["callback_path"]), body, key, timestamp));
    }
}

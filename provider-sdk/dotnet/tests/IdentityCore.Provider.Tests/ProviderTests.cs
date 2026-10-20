using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Xunit;

namespace IdentityCore.Provider.Tests;

public sealed class ProviderTests : IDisposable
{
    private const long Now = 1800000000;
    private readonly string directory = Path.Combine(Path.GetTempPath(), "identitycore-provider-tests-" + Guid.NewGuid().ToString("N"));
    private readonly SQLiteStore store;
    private readonly SigningKey key = new("pec_synthetic", "synthetic-wire-secret", "ten_synthetic", "sandbox", new HashSet<string> { "document_ocr" });
    private readonly JsonObject binding;
    private readonly ProviderRuntime runtime;
    private readonly List<string?> processed = [];
    private static byte[] StorageKey() => Enumerable.Range(0, 32).Select(i => (byte)i).ToArray();
    public ProviderTests()
    {
        Directory.CreateDirectory(directory); store = new SQLiteStore(Path.Combine(directory, "provider.sqlite"), StorageKey(), () => Now);
        binding = new JsonObject { ["operation_contract"] = Contracts.OperationContract, ["operation_id"] = "pop_synthetic", ["configuration_id"] = key.KeyId, ["tenant_id"] = key.TenantId, ["project_id"] = "prj_synthetic", ["environment"] = "sandbox", ["capability"] = "document_ocr", ["contract_version"] = "1", ["request_sha256"] = new string('0', 64), ["lease_generation"] = 1L, ["deadline"] = DateTimeOffset.FromUnixTimeSeconds(Now + 900).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"), ["callback_path"] = "/api/v1/providers/operations/pop_synthetic/callback", ["lease_token"] = "synthetic-operation-lease-only" };
        runtime = Runtime(store, (_, _) => Task.FromResult(true));
    }
    private ProviderRuntime Runtime(IOperationStore storage, ProviderRuntime.LifecycleHandler delete) => new(new Dictionary<string, SigningKey> { [key.KeyId] = key }, storage,
        new Dictionary<string, ProviderRuntime.CapabilityHandler> { ["document_ocr"] = (id, inputs, _) => { processed.Add(id); var result = Result(); result["extracted_fields"] = new JsonObject { ["custom_attribute"] = inputs["custom_attribute"]?.DeepClone() }; return Task.FromResult(result); } }, (_, _) => Task.FromResult(true), delete);
    private static JsonObject Result() => new() { ["contract_version"] = "1", ["capability"] = "document_ocr", ["status"] = "completed" };
    private JsonObject Request(string action)
    {
        var request = new JsonObject { ["contract_version"] = "1", ["operation"] = action, ["binding"] = binding.DeepClone() };
        if (action == "start") request["inputs"] = new JsonObject { ["custom_attribute"] = "Private synthetic value" }; return request;
    }
    private Task<ProviderResponse> Send(JsonObject request, ProviderRuntime? target = null)
    {
        var body = Wire.Bytes(request); return (target ?? runtime).HandleAsync("POST", "/invoke", body, Wire.Sign("POST", "/invoke", body, key, Now), Now);
    }
    private async Task Start() { var response = await Send(Request("start")); Assert.Equal(200, response.Status); Assert.Equal("pending", Wire.Parse(response.Body)["status"]!.GetValue<string>()); }
    [Fact] public async Task ExactWireFixturesAndTampering()
    {
        var fixture = Wire.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory, "provider-signing-wire-v1.json")));
        Assert.Equal(fixture["derived_signing_secret"]!.GetValue<string>(), Wire.DeriveSigningSecret(fixture["api_credential"]!.GetValue<string>()));
        foreach (var item in fixture["cases"]!.AsArray())
        {
            var test = item!.AsObject(); var fixtureKey = key with { KeyId = test["key_id"]!.GetValue<string>(), Secret = fixture["derived_signing_secret"]!.GetValue<string>() };
            var body = Encoding.UTF8.GetBytes(test["raw_body"]!.GetValue<string>()); var time = test["timestamp"]!.GetValue<long>();
            var headers = Wire.Sign("POST", "/invoke", body, fixtureKey, time, test["nonce"]!.GetValue<string>());
            Assert.Equal(test["signature"]!.GetValue<string>(), headers["X-IC-Signature"]);
            var keys = new Dictionary<string, SigningKey> { [fixtureKey.KeyId] = fixtureKey };
            await Wire.VerifyAsync("POST", "/invoke", body, headers, keys, store.ClaimNonceAsync, time);
            await Assert.ThrowsAsync<ProtocolError>(() => Wire.VerifyAsync("POST", "/invoke", [.. body, 32], headers, keys, store.ClaimNonceAsync, time));
        }
    }
    [Fact] public async Task AdmissionReopenEncryptionAndCallback()
    {
        await Start(); await Start(); var result = await runtime.WorkOnceAsync(); Assert.Equal("Private synthetic value", result!["result"]!["extracted_fields"]!["custom_attribute"]!.GetValue<string>());
        Assert.Equal(new[] { "pop_synthetic" }, processed); Assert.Null(await runtime.WorkOnceAsync());
        using var reopened = new SQLiteStore(Path.Combine(directory, "provider.sqlite"), StorageKey(), () => Now);
        Assert.Equal("completed", (await reopened.PollAsync(binding))["status"]!.GetValue<string>());
        var callback = await runtime.CallbackAsync(binding, Now);
        await Wire.VerifyAsync("POST", binding["callback_path"]!.GetValue<string>(), callback.Body, callback.Headers, new Dictionary<string, SigningKey> { [key.KeyId] = key }, (_, _) => Task.FromResult(true), Now, replayNamespace: "core-callback");
        foreach (var file in Directory.GetFiles(directory)) { var bytes = Encoding.Latin1.GetString(File.ReadAllBytes(file)); Assert.DoesNotContain("Private synthetic value", bytes); Assert.DoesNotContain("synthetic-operation-lease-only", bytes); }
        Assert.DoesNotContain(key.Secret, key.ToString()); Assert.DoesNotContain(key.Secret, JsonSerializer.Serialize(key));
    }
    [Fact] public async Task ConcurrentClaimAndStaleGenerationAreFenced()
    {
        await Start(); var claims = await Task.WhenAll(Enumerable.Range(0, 4).Select(_ => Task.Run(() => store.ClaimJobAsync(30))));
        var first = Assert.Single(claims, lease => lease is not null)!;
        Assert.DoesNotContain("Private synthetic value", first.ToString()); Assert.DoesNotContain("Private synthetic value", JsonSerializer.Serialize(first));
        using var advanced = new SQLiteStore(Path.Combine(directory, "provider.sqlite"), StorageKey(), () => Now + 31); var replacement = (await advanced.ClaimJobAsync(30))!;
        Assert.Equal(first.Generation + 1, replacement.Generation); Assert.False(await advanced.RenewAsync(first, 30));
        await Assert.ThrowsAsync<ProtocolError>(async () => await advanced.CompleteAsync(first, Result()));
        await advanced.CompleteAsync(replacement, Result());
    }
    [Fact] public async Task CancellationDeletionAndLifecycleFailure()
    {
        await Start(); var lease = (await store.ClaimJobAsync(30))!;
        var failedDelete = Runtime(store, (_, _) => Task.FromResult(false));
        Assert.Equal(503, (await Send(Request("delete"), failedDelete)).Status);
        await Assert.ThrowsAsync<ProtocolError>(async () => await store.CompleteAsync(lease, Result()));
        Assert.Equal("cancelled", (await store.PollAsync(binding))["status"]!.GetValue<string>());
        Assert.Equal("deleted", Wire.Parse((await Send(Request("delete"))).Body)["status"]!.GetValue<string>());
        Assert.Equal("deleted", Wire.Parse((await Send(Request("delete"))).Body)["status"]!.GetValue<string>());
        Assert.Null((await store.PollAsync(binding))["result"]);
    }
    [Fact] public async Task ScopeDuplicateJsonAndRotatedReplayAreRejected()
    {
        var wrong = Request("start"); wrong["binding"]!["tenant_id"] = "ten_foreign"; Assert.Equal(400, (await Send(wrong)).Status);
        var duplicate = Encoding.UTF8.GetBytes("{\"contract_version\":\"1\",\"contract_version\":\"999\"}");
        Assert.Equal(400, (await runtime.HandleAsync("POST", "/invoke", duplicate, Wire.Sign("POST", "/invoke", duplicate, key, Now), Now)).Status);
        var bytes = Wire.Bytes(new JsonObject()); const string nonce = "same-nonce-across-key-rotation";
        await Wire.VerifyAsync("POST", "/invoke", bytes, Wire.Sign("POST", "/invoke", bytes, key, Now, nonce), new Dictionary<string, SigningKey> { [key.KeyId] = key }, store.ClaimNonceAsync, Now);
        var rotated = key with { KeyId = "pec_rotated", Secret = "synthetic-rotated-secret" };
        await Assert.ThrowsAsync<ProtocolError>(() => Wire.VerifyAsync("POST", "/invoke", bytes, Wire.Sign("POST", "/invoke", bytes, rotated, Now, nonce), new Dictionary<string, SigningKey> { [rotated.KeyId] = rotated }, store.ClaimNonceAsync, Now));
    }
    [Fact] public async Task ReplayClaimIsAtomicAcrossFourProcesses()
    {
        var assembly = typeof(ProviderTests).Assembly.Location;
        var processes = Enumerable.Range(0, 4).Select(_ =>
        {
            var info = new ProcessStartInfo("dotnet") { RedirectStandardOutput = true, RedirectStandardError = true };
            info.ArgumentList.Add(assembly); info.ArgumentList.Add("nonce"); info.ArgumentList.Add(Path.Combine(directory, "provider.sqlite"));
            return Process.Start(info)!;
        }).ToArray();
        var results = new List<string>();
        foreach (var process in processes)
        {
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(20)); await process.WaitForExitAsync(timeout.Token);
            Assert.Equal(0, process.ExitCode); results.Add(await process.StandardOutput.ReadToEndAsync()); process.Dispose();
        }
        Assert.Equal(new[] { "false", "false", "false", "true" }, results.Order(StringComparer.Ordinal));
    }
    private static async Task Main(string[] args)
    {
        if (args.Length == 1 && args[0] == "harness") { await ConformanceHarness.Run(); return; }
        if (args.Length != 2 || args[0] != "nonce") throw new ArgumentException();
        using var store = new SQLiteStore(args[1], StorageKey(), () => Now);
        Console.Write(await store.ClaimNonceAsync("shared-nonce", Now + 300) ? "true" : "false");
    }
    public void Dispose() { store.Dispose(); Directory.Delete(directory, recursive: true); }
}

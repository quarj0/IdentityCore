using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace IdentityCore.Provider.Tests;

// Synthetic stdin test controls. Never expose these controls on a deployed provider.
internal static class ConformanceHarness
{
    public static async Task Run()
    {
        long now = 1800000000; var directory = Path.Combine(Path.GetTempPath(), "identitycore-provider-harness-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
        try
        {
            var key = new SigningKey("pec_synthetic", "synthetic-wire-secret", "ten_synthetic", "sandbox", new HashSet<string> { "document_ocr" });
            using var store = new SQLiteStore(Path.Combine(directory, "provider.sqlite"), Enumerable.Range(0, 32).Select(i => (byte)i).ToArray(), () => now);
            var leases = new Dictionary<string, WorkerLease>();
            var runtime = new ProviderRuntime(new Dictionary<string, SigningKey> { [key.KeyId] = key }, store, new Dictionary<string, ProviderRuntime.CapabilityHandler> { ["document_ocr"] = async (_, inputs, cancellation) => { await Task.Delay(Math.Min(inputs["delay_milliseconds"]?.GetValue<int>() ?? 0, 250), cancellation); return new JsonObject { ["contract_version"] = "1", ["capability"] = "document_ocr", ["status"] = "completed", ["extracted_fields"] = new JsonObject { ["custom_attribute"] = "Private synthetic value" } }; } }, (_, _) => Task.FromResult(true), (_, _) => Task.FromResult(true));
            string? line;
            while ((line = await Console.In.ReadLineAsync()) is not null)
            {
                JsonObject output;
                try
                {
                    var command = Wire.Parse(Encoding.UTF8.GetBytes(line));
                    switch (command["action"]!.GetValue<string>())
                    {
                        case "ping": output = new JsonObject { ["ready"] = true }; break;
                        case "handle":
                            var headers = command["headers"]!.AsObject().ToDictionary(pair => pair.Key, pair => pair.Value!.GetValue<string>());
                            var response = await runtime.HandleAsync("POST", "/invoke", Convert.FromBase64String(command["body"]!.GetValue<string>()), headers, now);
                            output = new JsonObject { ["status"] = response.Status, ["body"] = Convert.ToBase64String(response.Body), ["headers"] = JsonSerializer.SerializeToNode(response.Headers) }; break;
                        case "claim":
                            var lease = await store.ClaimJobAsync(30); if (lease is not null) leases[lease.OperationId] = lease;
                            output = new JsonObject { ["claimed"] = lease is not null }; break;
                        case "complete": output = await store.CompleteAsync(leases[command["operation_id"]!.GetValue<string>()], command["result"]!.AsObject()); break;
                        case "callback":
                            var callback = await runtime.CallbackAsync(command["binding"]!.AsObject(), now);
                            output = new JsonObject { ["body"] = Convert.ToBase64String(callback.Body), ["headers"] = JsonSerializer.SerializeToNode(callback.Headers) }; break;
                        case "advance": now += command["seconds"]!.GetValue<long>(); output = new JsonObject { ["now"] = now }; break;
                        case "redaction":
                            var safe = !key.ToString().Contains(key.Secret) && Directory.GetFiles(directory).All(path => !Encoding.Latin1.GetString(File.ReadAllBytes(path)).Contains("Private synthetic value")) && leases.Values.All(value => !value.ToString().Contains("Private synthetic value") && !value.ToString().Contains("synthetic-operation-lease-only"));
                            output = new JsonObject { ["safe"] = safe }; break;
                        default: throw new ArgumentException();
                    }
                }
                catch { output = new JsonObject { ["rejected"] = true }; }
                await Console.Out.WriteLineAsync(output.ToJsonString()); await Console.Out.FlushAsync();
            }
        }
        finally { Directory.Delete(directory, recursive: true); }
    }
}

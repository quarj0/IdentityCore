using System.Net;
using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;

namespace IdentityCore;

public sealed class IdentityCoreClientOptions
{
    public required Uri ApiOrigin { get; init; }
    public required string ClientId { get; init; }
    public required string ClientSecret { get; init; }
    public TimeSpan Timeout { get; init; } = TimeSpan.FromSeconds(30);
    public int MaxRetries { get; init; } = 2;
    public TimeSpan RetryBackoff { get; init; } = TimeSpan.FromMilliseconds(250);
}

public sealed class IdentityCoreClient : IDisposable
{
    public const string Version = "0.2.0";
    private static readonly HashSet<int> RetryableStatuses = [408, 429, 500, 502, 503, 504];
    private readonly IdentityCoreClientOptions options;
    private readonly HttpClient http;
    private readonly bool ownsHttp;
    public PoliciesResource Policies { get; }
    public VerificationsResource Verifications { get; }

    public IdentityCoreClient(IdentityCoreClientOptions options, HttpClient? httpClient = null)
    {
        if (options.ApiOrigin is null || !options.ApiOrigin.IsAbsoluteUri || options.ApiOrigin.Scheme is not ("http" or "https")) throw new IdentityCoreException("ApiOrigin must be an absolute HTTP(S) URL.");
        if (string.IsNullOrWhiteSpace(options.ClientId) || string.IsNullOrWhiteSpace(options.ClientSecret)) throw new IdentityCoreException("ClientId and ClientSecret are required.");
        if (options.Timeout <= TimeSpan.Zero || options.MaxRetries < 0 || options.RetryBackoff < TimeSpan.Zero) throw new IdentityCoreException("Retry and timeout settings are invalid.");
        this.options = options; http = httpClient ?? new HttpClient(); ownsHttp = httpClient is null; if (ownsHttp) http.Timeout = Timeout.InfiniteTimeSpan;
        Policies = new PoliciesResource(this); Verifications = new VerificationsResource(this);
    }

    public Task<JsonElement> HealthAsync(CancellationToken cancellationToken = default) => SendAsync(HttpMethod.Get, "/health", null, null, cancellationToken);

    public async Task<JsonElement> SendAsync(HttpMethod method, string path, object? body = null, string? idempotencyKey = null, CancellationToken cancellationToken = default)
    {
        var retryable = method is { Method: "GET" or "HEAD" or "OPTIONS" } || !string.IsNullOrWhiteSpace(idempotencyKey);
        var requestId = "req_" + Guid.NewGuid().ToString("N");
        for (var attempt = 0; attempt <= options.MaxRetries; attempt++)
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(options.Timeout);
            using var request = new HttpRequestMessage(method, new Uri(options.ApiOrigin, "/api/v1" + path));
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", options.ClientSecret);
            request.Headers.Add("X-Client-Id", options.ClientId); request.Headers.Add("X-Request-Id", requestId); request.Headers.UserAgent.ParseAdd($"identitycore-dotnet/{Version}");
            if (!string.IsNullOrWhiteSpace(idempotencyKey)) request.Headers.Add("Idempotency-Key", idempotencyKey);
            if (body is not null) request.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
            try
            {
                using var response = await http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, timeout.Token).ConfigureAwait(false);
                var text = await response.Content.ReadAsStringAsync(timeout.Token).ConfigureAwait(false);
                if (retryable && RetryableStatuses.Contains((int)response.StatusCode) && attempt < options.MaxRetries) { await Pause(attempt, cancellationToken); continue; }
                return Parse((int)response.StatusCode, response.IsSuccessStatusCode, text);
            }
            catch (OperationCanceledException error) when (!cancellationToken.IsCancellationRequested)
            {
                if (retryable && attempt < options.MaxRetries) { await Pause(attempt, cancellationToken); continue; }
                throw new IdentityCoreTimeoutException("The request timed out. Please try again.", error);
            }
            catch (HttpRequestException error)
            {
                if (retryable && attempt < options.MaxRetries) { await Pause(attempt, cancellationToken); continue; }
                throw new IdentityCoreConnectionException("Could not connect to IdentityCore.", error);
            }
        }
        throw new IdentityCoreConnectionException("Could not connect to IdentityCore.");
    }

    private static JsonElement Parse(int status, bool successStatus, string text)
    {
        JsonDocument document;
        try { document = JsonDocument.Parse(text); }
        catch (JsonException error) { throw new IdentityCoreApiException("The service returned an invalid response.", "invalid_response", status, "", EmptyObject()); }
        using (document)
        {
            var root = document.RootElement;
            var success = root.TryGetProperty("success", out var ok) && ok.ValueKind == JsonValueKind.True;
            if (!successStatus || !success)
            {
                var error = root.TryGetProperty("error", out var e) ? e : default;
                throw new IdentityCoreApiException(Property(error, "message", "Request failed."), Property(error, "code", "request_failed"), status, Property(root, "request_id", ""), error.ValueKind == JsonValueKind.Object && error.TryGetProperty("details", out var d) ? d.Clone() : EmptyObject());
            }
            return root.GetProperty("data").Clone();
        }
    }
    private static string Property(JsonElement element, string name, string fallback) => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var value) ? value.GetString() ?? fallback : fallback;
    private static JsonElement EmptyObject() { using var d = JsonDocument.Parse("{}"); return d.RootElement.Clone(); }
    private Task Pause(int attempt, CancellationToken token) => Task.Delay(TimeSpan.FromMilliseconds(options.RetryBackoff.TotalMilliseconds * Math.Pow(2, attempt)), token);
    public void Dispose() { if (ownsHttp) http.Dispose(); }

    public sealed class PoliciesResource(IdentityCoreClient client)
    {
        public Task<JsonElement> ListAsync(CancellationToken token = default) => client.SendAsync(HttpMethod.Get, "/policies/", cancellationToken: token);
        public Task<JsonElement> RetrieveAsync(string id, CancellationToken token = default) => client.SendAsync(HttpMethod.Get, "/policies/" + Segment(id), cancellationToken: token);
    }

    public sealed class VerificationsResource(IdentityCoreClient client)
    {
        public Task<JsonElement> CreateAsync(object input, string? idempotencyKey = null, CancellationToken token = default) => client.SendAsync(HttpMethod.Post, "/verifications/", input, idempotencyKey ?? "ik_" + Guid.NewGuid().ToString("N"), token);
        public Task<JsonElement> ListAsync(string? status = null, string? externalReference = null, int? page = null, int? pageSize = null, CancellationToken token = default) => client.SendAsync(HttpMethod.Get, "/verifications/" + Query(new() { ["status"] = status, ["external_reference"] = externalReference, ["page"] = page, ["page_size"] = pageSize }), cancellationToken: token);
        public async IAsyncEnumerable<JsonElement> IterateAsync(string? status = null, string? externalReference = null, int pageSize = 100, [EnumeratorCancellation] CancellationToken token = default)
        {
            for (var page=1;;page++) { var result=await ListAsync(status,externalReference,page,pageSize,token); foreach(var item in result.GetProperty("results").EnumerateArray()) yield return item.Clone(); if(page>=result.GetProperty("pagination").GetProperty("total_pages").GetInt32()) yield break; }
        }
        public Task<JsonElement> RetrieveAsync(string id, CancellationToken token = default) => client.SendAsync(HttpMethod.Get, "/verifications/" + Segment(id), cancellationToken: token);
        public Task<JsonElement> CancelAsync(string id, string reason = "", CancellationToken token = default) => client.SendAsync(HttpMethod.Post, "/verifications/" + Segment(id) + "/cancel", new { reason }, cancellationToken: token);
        public Task<JsonElement> ResendLinkAsync(string id, CancellationToken token = default) => client.SendAsync(HttpMethod.Post, "/verifications/" + Segment(id) + "/resend-link", new { channel = "email" }, cancellationToken: token);
        public Task<JsonElement> EvidenceReportAsync(string id, CancellationToken token = default) => client.SendAsync(HttpMethod.Get, "/verifications/" + Segment(id) + "/evidence-report", cancellationToken: token);
    }
    private static string Segment(string value) => Uri.EscapeDataString(value);
    private static string Query(Dictionary<string,object?> values) { var parts=values.Where(x=>x.Value is not null && !string.IsNullOrWhiteSpace(x.Value.ToString())).Select(x=>$"{Uri.EscapeDataString(x.Key)}={Uri.EscapeDataString(x.Value!.ToString()!)}"); var q=string.Join("&",parts); return q.Length==0?"":"?"+q; }
}

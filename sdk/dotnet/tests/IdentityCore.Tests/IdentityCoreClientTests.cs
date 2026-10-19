using System.Net;
using System.Text;
using System.Text.Json;
using Xunit;

namespace IdentityCore.Tests;

public sealed class IdentityCoreClientTests
{
    [Fact]
    public async Task Date_filters_survive_list_and_every_cursor_page()
    {
        var urls = new List<string>();
        var http = new HttpClient(new Handler(request => {
            urls.Add(request.RequestUri!.Query);
            var cursor = urls.Count == 3 ? "\"next\"" : "null";
            return Response(HttpStatusCode.OK, "{\"success\":true,\"data\":{\"results\":[{\"id\":\"1\"}],\"pagination\":{\"next_cursor\":" + cursor + "}}}");
        }));
        using var client = new IdentityCoreClient(new(){ApiOrigin=new Uri("https://api.example.test"),ClientId="c",ClientSecret="s"},http);
        await client.Verifications.ListAsync(createdFrom: "2026-01-01", createdTo: "2026-01-31", page: 1);
        await client.Verifications.ListCursorAsync(createdFrom: "2026-01-01", createdTo: "2026-01-31");
        var count = 0;
        await foreach (var item in client.Verifications.IterateAsync(createdFrom: "2026-01-01", createdTo: "2026-01-31")) count++;
        Assert.Equal(2, count);
        Assert.Equal(4, urls.Count);
        Assert.All(urls, url => { Assert.Contains("created_from=2026-01-01", url); Assert.Contains("created_to=2026-01-31", url); });
        Assert.Contains("cursor=next", urls[3]);
    }

    [Fact]
    public async Task Create_sends_auth_and_idempotency_headers()
    {
        HttpRequestMessage? seen = null;
        var http = new HttpClient(new Handler(async request => { seen = request; return await Response(HttpStatusCode.Created, "{\"success\":true,\"data\":{\"id\":\"ver_1\"}}"); }));
        using var client = new IdentityCoreClient(new() { ApiOrigin = new Uri("https://api.example.test"), ClientId = "cli_test", ClientSecret = "secret" }, http);
        var result = await client.Verifications.CreateAsync(new { purpose = "Onboarding" }, "customer-1");
        Assert.Equal("ver_1", result.GetProperty("id").GetString());
        Assert.Equal("customer-1", seen!.Headers.GetValues("Idempotency-Key").Single());
        Assert.Equal("cli_test", seen.Headers.GetValues("X-Client-Id").Single());
    }

    [Fact]
    public async Task Reads_retry_transient_statuses()
    {
        var calls=0; var http=new HttpClient(new Handler(_=>Response(++calls==1?HttpStatusCode.ServiceUnavailable:HttpStatusCode.OK,calls==1?"{\"success\":false,\"error\":{\"message\":\"down\"}}":"{\"success\":true,\"data\":[]}")));
        using var client=new IdentityCoreClient(new(){ApiOrigin=new Uri("https://api.example.test"),ClientId="c",ClientSecret="s",RetryBackoff=TimeSpan.Zero},http);
        Assert.Equal(JsonValueKind.Array,(await client.Policies.ListAsync()).ValueKind); Assert.Equal(2,calls);
    }
    [Fact]
    public async Task Retrieves_versioned_verification_result()
    {
        Uri? seen = null;
        var http = new HttpClient(new Handler(request => { seen = request.RequestUri; return Response(HttpStatusCode.OK, "{\"success\":true,\"data\":{\"schema_version\":\"1\"}}"); }));
        using var client = new IdentityCoreClient(new(){ApiOrigin=new Uri("https://api.example.test"),ClientId="c",ClientSecret="s"},http);
        Assert.Equal("1", (await client.Verifications.ResultAsync("ver_1")).GetProperty("schema_version").GetString());
        Assert.Equal("https://api.example.test/api/v1/verifications/ver_1/result", seen!.ToString());
    }
    private static Task<HttpResponseMessage> Response(HttpStatusCode status,string body)=>Task.FromResult(new HttpResponseMessage(status){Content=new StringContent(body,Encoding.UTF8,"application/json")});
    private sealed class Handler(Func<HttpRequestMessage,Task<HttpResponseMessage>> send):HttpMessageHandler { protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,CancellationToken cancellationToken)=>send(request); }
}

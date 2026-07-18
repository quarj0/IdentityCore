using System.Net;
using System.Text;
using System.Text.Json;

namespace IdentityCore.Tests;

public sealed class IdentityCoreClientTests
{
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
    private static Task<HttpResponseMessage> Response(HttpStatusCode status,string body)=>Task.FromResult(new HttpResponseMessage(status){Content=new StringContent(body,Encoding.UTF8,"application/json")});
    private sealed class Handler(Func<HttpRequestMessage,Task<HttpResponseMessage>> send):HttpMessageHandler { protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,CancellationToken cancellationToken)=>send(request); }
}


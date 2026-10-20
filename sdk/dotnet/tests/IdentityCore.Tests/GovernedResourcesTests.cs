using System.Net;
using System.Text;
using System.Text.Json;
using IdentityCore.Models;
using Xunit;

namespace IdentityCore.Tests;

public sealed class GovernedResourcesTests
{
    private sealed class Handler(Func<HttpRequestMessage, Task<HttpResponseMessage>> send) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) => send(request);
    }
    private static HttpResponseMessage Ok() => new(HttpStatusCode.OK) { Content = new StringContent("{\"success\":true,\"data\":{}}", Encoding.UTF8, "application/json") };
    [Fact] public async Task ExactScopeAndDisclosureHeaderArePreserved()
    {
        var urls = new List<string>(); var headers = new List<Dictionary<string,string>>(); var bodies = new List<string>();
        var http = new HttpClient(new Handler(async request => { urls.Add(request.RequestUri!.AbsoluteUri); headers.Add(request.Headers.ToDictionary(pair => pair.Key, pair => pair.Value.Single())); bodies.Add(request.Content is null ? "" : await request.Content.ReadAsStringAsync()); return Ok(); }));
        using var client = new IdentityCoreClient(new() { ApiOrigin = new Uri("https://api.example.test"), ClientId = "recipient", ClientSecret = "synthetic-secret" }, http);
        await client.Governed.GetEvidenceAsync("evd_one/../../claims?x=y", new Dictionary<string,object?> { ["project_id"] = "prj_one", ["purpose"] = "address & employment" });
        Assert.Contains("evd_one%2F..%2F..%2Fclaims%3Fx%3Dy", urls[0]); Assert.Contains("address%20%26%20employment", urls[0]);
        await client.Governed.RedeemClaimDisclosureAsync("dcl_one", new { project_id = "prj_one" }, "synthetic-capability", idempotencyKey: "once");
        Assert.Equal("synthetic-capability", headers[1]["X-Disclosure-Token"]); Assert.Equal("once", headers[1]["Idempotency-Key"]);
        Assert.DoesNotContain("synthetic-capability", urls[1]); Assert.DoesNotContain("synthetic-capability", bodies[1]);
    }
    [Fact] public async Task HumanApprovalUsesUserJwtWithoutClientIdentity()
    {
        var http = new HttpClient(new Handler(request => { Assert.Equal("Bearer synthetic-user-jwt", request.Headers.Authorization!.ToString()); Assert.False(request.Headers.Contains("X-Client-Id")); return Task.FromResult(Ok()); }));
        using var client = new IdentityCoreClient(new() { ApiOrigin = new Uri("https://api.example.test"), AccessToken = "synthetic-user-jwt" }, http);
        await client.Governed.ApprovePurposeAuthorizationAsync("paz_one", new { });
    }
    [Fact] public void NumericAndHyphenatedEnumsUseExactWireStrings()
    {
        Assert.Equal("\"ic-provider-operations-v1\"", JsonSerializer.Serialize(ProviderCertificationOperationContract.IcProviderOperationsV1));
        Assert.Equal(ProviderCertificationOperationContract.IcProviderOperationsV1, JsonSerializer.Deserialize<ProviderCertificationOperationContract>("\"ic-provider-operations-v1\""));
        Assert.Equal("\"1\"", JsonSerializer.Serialize(ProviderCertificationContractVersion.Value1));
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ProviderCertificationContractVersion>("0"));
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ProviderCertificationContractVersion>("\"unsupported\""));
    }
}

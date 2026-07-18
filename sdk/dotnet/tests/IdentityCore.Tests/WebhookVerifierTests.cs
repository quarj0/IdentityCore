using System.Security.Cryptography;
using System.Text;
using Xunit;

namespace IdentityCore.Tests;

public sealed class WebhookVerifierTests
{
    [Fact] public void Verifies_raw_body_and_rejects_stale_timestamp()
    {
        var body=Encoding.UTF8.GetBytes("{\"id\":\"evt_1\"}"); const string timestamp="1000",key="whsec_test";
        using var hmac=new HMACSHA256(Encoding.UTF8.GetBytes(key)); var signature="sha256="+Convert.ToHexString(hmac.ComputeHash([..Encoding.UTF8.GetBytes(timestamp+"."),..body])).ToLowerInvariant();
        Assert.True(WebhookVerifier.Verify(body,signature,timestamp,key,TimeSpan.FromMinutes(5),DateTimeOffset.FromUnixTimeSeconds(1001)));
        Assert.False(WebhookVerifier.Verify(body,signature,timestamp,key,TimeSpan.FromMinutes(5),DateTimeOffset.FromUnixTimeSeconds(2000)));
    }
}


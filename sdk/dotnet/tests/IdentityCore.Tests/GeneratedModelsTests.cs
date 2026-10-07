using System.Text.Json;
using IdentityCore.Models;
using Xunit;

namespace IdentityCore.Tests;

public sealed class GeneratedModelsTests
{
    [Fact]
    public void Minimal_request_omits_unset_optional_fields()
    {
        var request = new VerificationCreateRequest
        {
            Purpose = "Fixture",
            PolicyId = "pol_fixture",
            VerificationSubject = new VerificationSubjectInput { FullName = "Fixture" }
        };
        using var json = JsonDocument.Parse(JsonSerializer.Serialize(request));
        Assert.Equal(3, json.RootElement.EnumerateObject().Count());
        Assert.False(json.RootElement.TryGetProperty("external_reference", out _));
        Assert.False(json.RootElement.TryGetProperty("project_id", out _));
        Assert.False(json.RootElement.TryGetProperty("redirect_url", out _));
        Assert.Equal(1, json.RootElement.GetProperty("verification_subject").EnumerateObject().Count());
    }

    [Fact]
    public void Enum_request_serializes_the_contract_value_and_round_trips()
    {
        var request = new ManualReviewDecisionRequest
        {
            Decision = ManualReviewDecisionRequestDecision.verified
        };
        var json = JsonSerializer.Serialize(request);
        Assert.Equal("verified", JsonDocument.Parse(json).RootElement.GetProperty("decision").GetString());
        Assert.Equal(request.Decision, JsonSerializer.Deserialize<ManualReviewDecisionRequest>(json)!.Decision);
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ManualReviewDecisionRequest>("{\"decision\":\"invalid\"}"));
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ManualReviewDecisionRequest>("{\"decision\":99}"));
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ManualReviewDecisionRequest>("{\"decision\":0}"));
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ManualReviewApprovalRequest>("{}"));
        Assert.Throws<JsonException>(() => JsonSerializer.Serialize(new ManualReviewDecisionRequest { Decision = (ManualReviewDecisionRequestDecision)99 }));
    }
}

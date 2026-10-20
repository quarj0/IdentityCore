// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.
using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Runtime.Serialization;
using System.Collections.Generic;

namespace IdentityCore.Models;

public sealed class ContractStringEnumConverter<TEnum> : JsonConverter<TEnum> where TEnum : struct, Enum
{
    private static string Wire(TEnum value) => ((EnumMemberAttribute?)Attribute.GetCustomAttribute(typeof(TEnum).GetField(value.ToString())!, typeof(EnumMemberAttribute)))?.Value ?? value.ToString();
    public override TEnum Read(ref Utf8JsonReader reader, Type type, JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.String) throw new JsonException("Expected a string enum.");
        var wire = reader.GetString();
        foreach (var value in Enum.GetValues<TEnum>()) if (StringComparer.Ordinal.Equals(Wire(value), wire)) return value;
        throw new JsonException("Unsupported string enum value.");
    }
    public override void Write(Utf8JsonWriter writer, TEnum value, JsonSerializerOptions options)
    {
        if (!Enum.IsDefined(value)) throw new JsonException("Unsupported enum value.");
        writer.WriteStringValue(Wire(value));
    }
}

public sealed record Error
{
    [JsonPropertyName("code")]
    public string Code { get; init; }
    [JsonPropertyName("message")]
    public string Message { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("details")]
    public JsonElement? Details { get; init; }
}

public sealed record ErrorEnvelope
{
    [JsonPropertyName("success")]
    public bool Success { get; init; }
    [JsonPropertyName("error")]
    public Error Error { get; init; }
    [JsonPropertyName("request_id")]
    public string RequestId { get; init; }
}

public sealed record WorkflowSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("steps")]
    public IReadOnlyList<string> Steps { get; init; }
    [JsonPropertyName("settings")]
    public JsonElement Settings { get; init; }
    [JsonPropertyName("current_version")]
    public int CurrentVersion { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("source_template_id")]
    public string? SourceTemplateId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("source_template_version")]
    public string? SourceTemplateVersion { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("created_at")]
    public string? CreatedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<PolicyStatus>))]
public enum PolicyStatus
{
    [EnumMember(Value = "draft")]
    draft,
    [EnumMember(Value = "active")]
    active,
    [EnumMember(Value = "archived")]
    archived,
}

[JsonConverter(typeof(ContractStringEnumConverter<PolicyRequiredLivenessLevel>))]
public enum PolicyRequiredLivenessLevel
{
    [EnumMember(Value = "passive")]
    passive,
    [EnumMember(Value = "active")]
    active,
}

[JsonConverter(typeof(ContractStringEnumConverter<PolicyExternalRiskFailureAction>))]
public enum PolicyExternalRiskFailureAction
{
    [EnumMember(Value = "manual_review")]
    manual_review,
    [EnumMember(Value = "ignore")]
    ignore,
}

public sealed record Policy
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("status")]
    public required PolicyStatus Status { get; init; }
    [JsonPropertyName("required_document_types")]
    public IReadOnlyList<string> RequiredDocumentTypes { get; init; }
    [JsonPropertyName("required_liveness_level")]
    public required PolicyRequiredLivenessLevel RequiredLivenessLevel { get; init; }
    [JsonPropertyName("face_match_threshold")]
    public double FaceMatchThreshold { get; init; }
    [JsonPropertyName("manual_review_threshold")]
    public double ManualReviewThreshold { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("review_reason_rules")]
    public JsonElement? ReviewReasonRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reuse_rules")]
    public JsonElement? ReuseRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_consistency_rules")]
    public JsonElement? DocumentConsistencyRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_authenticity_required")]
    public bool? DocumentAuthenticityRequired { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_authenticity_min_confidence")]
    public double? DocumentAuthenticityMinConfidence { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_enabled")]
    public bool? ExternalRiskEnabled { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_failure_action")]
    public PolicyExternalRiskFailureAction? ExternalRiskFailureAction { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_review_threshold")]
    public double? ExternalRiskReviewThreshold { get; init; }
    [JsonPropertyName("maker_checker_required")]
    public bool MakerCheckerRequired { get; init; }
    [JsonPropertyName("verification_expiry_minutes")]
    public int VerificationExpiryMinutes { get; init; }
    [JsonPropertyName("media_retention_days")]
    public int MediaRetentionDays { get; init; }
    [JsonPropertyName("metadata_retention_days")]
    public int MetadataRetentionDays { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record VerificationSubjectInput
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("full_name")]
    public string? FullName { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("email")]
    public string? Email { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("phone_number")]
    public string? PhoneNumber { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("date_of_birth")]
    public string? DateOfBirth { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("metadata")]
    public JsonElement? Metadata { get; init; }
}

public sealed record VerificationCreateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_reference")]
    public string? ExternalReference { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("policy_id")]
    public string PolicyId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("verification_subject")]
    public VerificationSubjectInput VerificationSubject { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("redirect_url")]
    public string? RedirectUrl { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("metadata")]
    public JsonElement? Metadata { get; init; }
}

public sealed record PlatformUserLoginRequest
{
    [JsonPropertyName("email")]
    public string Email { get; init; }
    [JsonPropertyName("password")]
    public string Password { get; init; }
}

public sealed record PlatformUser
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("email")]
    public string Email { get; init; }
    [JsonPropertyName("first_name")]
    public string FirstName { get; init; }
    [JsonPropertyName("last_name")]
    public string LastName { get; init; }
    [JsonPropertyName("phone_number")]
    public string PhoneNumber { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string? TenantPublicId { get; init; }
    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }
    [JsonPropertyName("tenant_status")]
    public string? TenantStatus { get; init; }
    [JsonPropertyName("is_platform_admin")]
    public bool IsPlatformAdmin { get; init; }
    [JsonPropertyName("mfa_enabled")]
    public bool MfaEnabled { get; init; }
    [JsonPropertyName("roles")]
    public IReadOnlyList<string> Roles { get; init; }
    [JsonPropertyName("notification_preferences")]
    public JsonElement NotificationPreferences { get; init; }
    [JsonPropertyName("last_login_at")]
    public string? LastLoginAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record PlatformUserMfaChallenge
{
    [JsonPropertyName("mfa_required")]
    public bool MfaRequired { get; init; }
    [JsonPropertyName("mfa_enrollment_required")]
    public bool MfaEnrollmentRequired { get; init; }
    [JsonPropertyName("mfa_token")]
    public string MfaToken { get; init; }
}

public sealed record PlatformUserAuthentication
{
    [JsonPropertyName("tokens")]
    public JsonElement Tokens { get; init; }
    [JsonPropertyName("user")]
    public PlatformUser User { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("recovery_codes")]
    public IReadOnlyList<string>? RecoveryCodes { get; init; }
}

public sealed record PlatformUserMfaEnrollmentRequest
{
    [JsonPropertyName("mfa_token")]
    public string MfaToken { get; init; }
}

public sealed record PlatformUserMfaCodeRequest
{
    [JsonPropertyName("mfa_token")]
    public string MfaToken { get; init; }
    [JsonPropertyName("code")]
    public string Code { get; init; }
}

public sealed record PlatformUserMfaEnrollment
{
    [JsonPropertyName("secret")]
    public string Secret { get; init; }
    [JsonPropertyName("provisioning_uri")]
    public string ProvisioningUri { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<VerificationPolicyCreateRequestRequiredLivenessLevel>))]
public enum VerificationPolicyCreateRequestRequiredLivenessLevel
{
    [EnumMember(Value = "passive")]
    passive,
    [EnumMember(Value = "active")]
    active,
}

[JsonConverter(typeof(ContractStringEnumConverter<VerificationPolicyCreateRequestExternalRiskFailureAction>))]
public enum VerificationPolicyCreateRequestExternalRiskFailureAction
{
    [EnumMember(Value = "manual_review")]
    manual_review,
    [EnumMember(Value = "ignore")]
    ignore,
}

public sealed record VerificationPolicyCreateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("consent_template_id")]
    public string? ConsentTemplateId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("default_locale")]
    public string? DefaultLocale { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("supported_locales")]
    public IReadOnlyList<string>? SupportedLocales { get; init; }
    [JsonPropertyName("required_document_types")]
    public IReadOnlyList<string> RequiredDocumentTypes { get; init; }
    [JsonPropertyName("required_liveness_level")]
    public required VerificationPolicyCreateRequestRequiredLivenessLevel RequiredLivenessLevel { get; init; }
    [JsonPropertyName("face_match_threshold")]
    public double FaceMatchThreshold { get; init; }
    [JsonPropertyName("manual_review_threshold")]
    public double ManualReviewThreshold { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("review_reason_rules")]
    public JsonElement? ReviewReasonRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reuse_rules")]
    public JsonElement? ReuseRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_consistency_rules")]
    public JsonElement? DocumentConsistencyRules { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_authenticity_required")]
    public bool? DocumentAuthenticityRequired { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_authenticity_min_confidence")]
    public double? DocumentAuthenticityMinConfidence { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_enabled")]
    public bool? ExternalRiskEnabled { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_failure_action")]
    public VerificationPolicyCreateRequestExternalRiskFailureAction? ExternalRiskFailureAction { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("external_risk_review_threshold")]
    public double? ExternalRiskReviewThreshold { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("maker_checker_required")]
    public bool? MakerCheckerRequired { get; init; }
    [JsonPropertyName("verification_expiry_minutes")]
    public int VerificationExpiryMinutes { get; init; }
    [JsonPropertyName("media_retention_days")]
    public int MediaRetentionDays { get; init; }
    [JsonPropertyName("metadata_retention_days")]
    public int MetadataRetentionDays { get; init; }
}

public sealed record VerificationPolicyCreateResponse
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
}

public sealed record VerificationCreateResponse
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("verification_url")]
    public string VerificationUrl { get; init; }
    [JsonPropertyName("session_id")]
    public string SessionId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("session_token")]
    public string? SessionToken { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record VerificationSessionConsentRequest
{
    [JsonPropertyName("accepted")]
    public bool Accepted { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("template_id")]
    public string? TemplateId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("version")]
    public int? Version { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("locale")]
    public string? Locale { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("content_hash")]
    public string? ContentHash { get; init; }
}

public sealed record VerificationSessionDocumentRequest
{
    [JsonPropertyName("document_type")]
    public string DocumentType { get; init; }
    [JsonPropertyName("country_code")]
    public string CountryCode { get; init; }
    [JsonPropertyName("captures")]
    public IReadOnlyList<JsonElement> Captures { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<VerificationSessionSelfieRequestCaptureType>))]
public enum VerificationSessionSelfieRequestCaptureType
{
    [EnumMember(Value = "image")]
    image,
    [EnumMember(Value = "video")]
    video,
}

public sealed record VerificationSessionSelfieRequest
{
    [JsonPropertyName("capture_type")]
    public required VerificationSessionSelfieRequestCaptureType CaptureType { get; init; }
    [JsonPropertyName("upload_id")]
    public string UploadId { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<VerificationSessionLivenessRequestLivenessType>))]
public enum VerificationSessionLivenessRequestLivenessType
{
    [EnumMember(Value = "passive")]
    passive,
    [EnumMember(Value = "active")]
    active,
}

public sealed record VerificationSessionLivenessRequest
{
    [JsonPropertyName("liveness_type")]
    public required VerificationSessionLivenessRequestLivenessType LivenessType { get; init; }
    [JsonPropertyName("selfie_capture_id")]
    public string SelfieCaptureId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("challenge_id")]
    public string? ChallengeId { get; init; }
}

public sealed record VerificationMobileHandoffRedeemResponse
{
    [JsonPropertyName("session_id")]
    public string SessionId { get; init; }
    [JsonPropertyName("session_token")]
    public string SessionToken { get; init; }
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<VerificationSessionResponseDirection>))]
public enum VerificationSessionResponseDirection
{
    [EnumMember(Value = "ltr")]
    ltr,
    [EnumMember(Value = "rtl")]
    rtl,
}

public sealed record VerificationSessionResponse
{
    [JsonPropertyName("session_id")]
    public string SessionId { get; init; }
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("organization")]
    public JsonElement Organization { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("redirect_url")]
    public string RedirectUrl { get; init; }
    [JsonPropertyName("required_steps")]
    public IReadOnlyList<string> RequiredSteps { get; init; }
    [JsonPropertyName("workflow")]
    public JsonElement Workflow { get; init; }
    [JsonPropertyName("locale")]
    public string Locale { get; init; }
    [JsonPropertyName("supported_locales")]
    public IReadOnlyList<string> SupportedLocales { get; init; }
    [JsonPropertyName("direction")]
    public required VerificationSessionResponseDirection Direction { get; init; }
    [JsonPropertyName("consent")]
    public JsonElement Consent { get; init; }
    [JsonPropertyName("document")]
    public JsonElement Document { get; init; }
    [JsonPropertyName("available_documents")]
    public IReadOnlyList<JsonElement> AvailableDocuments { get; init; }
    [JsonPropertyName("available_countries")]
    public IReadOnlyList<JsonElement> AvailableCountries { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record VerificationSessionConsentResponse
{
    [JsonPropertyName("consent_record_id")]
    public string ConsentRecordId { get; init; }
    [JsonPropertyName("next_step")]
    public string NextStep { get; init; }
}

public sealed record VerificationSessionDocumentResponse
{
    [JsonPropertyName("identity_document_id")]
    public string IdentityDocumentId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("next_step")]
    public string NextStep { get; init; }
}

public sealed record VerificationSessionSelfieResponse
{
    [JsonPropertyName("selfie_capture_id")]
    public string SelfieCaptureId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("next_step")]
    public string NextStep { get; init; }
}

public sealed record VerificationSessionLivenessResponse
{
    [JsonPropertyName("liveness_check_id")]
    public string LivenessCheckId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
}

public sealed record VerificationSessionLivenessChallengeResponse
{
    [JsonPropertyName("challenge_id")]
    public string ChallengeId { get; init; }
    [JsonPropertyName("actions")]
    public IReadOnlyList<string> Actions { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
    [JsonPropertyName("expires_in")]
    public int ExpiresIn { get; init; }
}

public sealed record VerificationSessionStatusResponse
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("current_step")]
    public string CurrentStep { get; init; }
    [JsonPropertyName("message")]
    public string Message { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("withdrawal_available")]
    public bool? WithdrawalAvailable { get; init; }
    [JsonPropertyName("evidence")]
    public JsonElement Evidence { get; init; }
}

public sealed record VerificationMobileHandoffResponse
{
    [JsonPropertyName("handoff_url")]
    public string HandoffUrl { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record VerificationSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("external_reference")]
    public string ExternalReference { get; init; }
    [JsonPropertyName("subject")]
    public JsonElement Subject { get; init; }
    [JsonPropertyName("policy")]
    public JsonElement Policy { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("completed_at")]
    public string? CompletedAt { get; init; }
}

public sealed record VerificationDetail
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("policy")]
    public JsonElement Policy { get; init; }
    [JsonPropertyName("workflow")]
    public JsonElement Workflow { get; init; }
    [JsonPropertyName("external_reference")]
    public string ExternalReference { get; init; }
    [JsonPropertyName("verification_subject")]
    public JsonElement VerificationSubject { get; init; }
    [JsonPropertyName("checks")]
    public JsonElement Checks { get; init; }
    [JsonPropertyName("risk_assessment")]
    public JsonElement? RiskAssessment { get; init; }
    [JsonPropertyName("document_classification")]
    public JsonElement? DocumentClassification { get; init; }
    [JsonPropertyName("evidence_report")]
    public JsonElement? EvidenceReport { get; init; }
    [JsonPropertyName("decision")]
    public JsonElement? Decision { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("completed_at")]
    public string? CompletedAt { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<SandboxSimulationRequestScenario>))]
public enum SandboxSimulationRequestScenario
{
    [EnumMember(Value = "approved")]
    approved,
    [EnumMember(Value = "declined")]
    declined,
    [EnumMember(Value = "review")]
    review,
    [EnumMember(Value = "timeout")]
    timeout,
    [EnumMember(Value = "provider_error")]
    provider_error,
}

public sealed record SandboxSimulationRequest
{
    [JsonPropertyName("scenario")]
    public required SandboxSimulationRequestScenario Scenario { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<SandboxSimulationMarkerScenario>))]
public enum SandboxSimulationMarkerScenario
{
    [EnumMember(Value = "approved")]
    approved,
    [EnumMember(Value = "declined")]
    declined,
    [EnumMember(Value = "review")]
    review,
    [EnumMember(Value = "timeout")]
    timeout,
    [EnumMember(Value = "provider_error")]
    provider_error,
}

public sealed record SandboxSimulationMarker
{
    [JsonPropertyName("scenario")]
    public required SandboxSimulationMarkerScenario Scenario { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
}

public sealed record VerificationResult
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("simulation")]
    public SandboxSimulationMarker? Simulation { get; init; }
    [JsonPropertyName("schema_version")]
    public string SchemaVersion { get; init; }
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("decision")]
    public JsonElement? Decision { get; init; }
    [JsonPropertyName("policy")]
    public JsonElement Policy { get; init; }
    [JsonPropertyName("workflow")]
    public JsonElement Workflow { get; init; }
    [JsonPropertyName("check_provenance")]
    public IReadOnlyList<JsonElement> CheckProvenance { get; init; }
    [JsonPropertyName("timestamps")]
    public JsonElement Timestamps { get; init; }
}

public sealed record CursorPagination
{
    [JsonPropertyName("limit")]
    public int Limit { get; init; }
    [JsonPropertyName("next_cursor")]
    public string? NextCursor { get; init; }
    [JsonPropertyName("has_more")]
    public bool HasMore { get; init; }
}

public sealed record PagePagination
{
    [JsonPropertyName("page")]
    public int Page { get; init; }
    [JsonPropertyName("page_size")]
    public int PageSize { get; init; }
    [JsonPropertyName("total")]
    public int Total { get; init; }
    [JsonPropertyName("total_pages")]
    public int TotalPages { get; init; }
}

public sealed record AuditEvent
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("actor_type")]
    public string ActorType { get; init; }
    [JsonPropertyName("actor_id")]
    public string ActorId { get; init; }
    [JsonPropertyName("action")]
    public string Action { get; init; }
    [JsonPropertyName("action_label")]
    public string ActionLabel { get; init; }
    [JsonPropertyName("actor_display_name")]
    public string ActorDisplayName { get; init; }
    [JsonPropertyName("target_type")]
    public string TargetType { get; init; }
    [JsonPropertyName("target_id")]
    public string TargetId { get; init; }
    [JsonPropertyName("target_label")]
    public string TargetLabel { get; init; }
    [JsonPropertyName("ip_address")]
    public string? IpAddress { get; init; }
    [JsonPropertyName("user_agent")]
    public string UserAgent { get; init; }
    [JsonPropertyName("metadata")]
    public JsonElement Metadata { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
}

public sealed record EvidenceReport
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("storage_key")]
    public string StorageKey { get; init; }
    [JsonPropertyName("download_url")]
    public string DownloadUrl { get; init; }
    [JsonPropertyName("pdf_storage_key")]
    public string PdfStorageKey { get; init; }
    [JsonPropertyName("pdf_download_url")]
    public string PdfDownloadUrl { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<PortalUploadCreateRequestCaptureMethod>))]
public enum PortalUploadCreateRequestCaptureMethod
{
    [EnumMember(Value = "camera")]
    camera,
    [EnumMember(Value = "live_recording")]
    live_recording,
    [EnumMember(Value = "file")]
    file,
    [EnumMember(Value = "unreported")]
    unreported,
}

[JsonConverter(typeof(ContractStringEnumConverter<PortalUploadCreateRequestPurpose>))]
public enum PortalUploadCreateRequestPurpose
{
    [EnumMember(Value = "document_capture")]
    document_capture,
    [EnumMember(Value = "selfie_capture")]
    selfie_capture,
    [EnumMember(Value = "liveness_capture")]
    liveness_capture,
}

public sealed record PortalUploadCreateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("capture_method")]
    public PortalUploadCreateRequestCaptureMethod? CaptureMethod { get; init; }
    [JsonPropertyName("purpose")]
    public required PortalUploadCreateRequestPurpose Purpose { get; init; }
    [JsonPropertyName("mime_type")]
    public string MimeType { get; init; }
    [JsonPropertyName("file_size_bytes")]
    public int FileSizeBytes { get; init; }
}

public sealed record PortalUploadCreateResponse
{
    [JsonPropertyName("upload_id")]
    public string UploadId { get; init; }
    [JsonPropertyName("upload_url")]
    public string UploadUrl { get; init; }
    [JsonPropertyName("upload_headers")]
    public JsonElement UploadHeaders { get; init; }
    [JsonPropertyName("upload_transfer_path")]
    public string UploadTransferPath { get; init; }
    [JsonPropertyName("upload_complete_path")]
    public string UploadCompletePath { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record PortalUploadTransferResponse
{
    [JsonPropertyName("upload_id")]
    public string UploadId { get; init; }
}

public sealed record OrganizationProfile
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("slug")]
    public string Slug { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("industry")]
    public string? Industry { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("tenant_id")]
    public string? TenantId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("tenant_status")]
    public string? TenantStatus { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("default_country_profile_id")]
    public string? DefaultCountryProfileId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("default_jurisdiction_id")]
    public string? DefaultJurisdictionId { get; init; }
    [JsonPropertyName("settings")]
    public JsonElement Settings { get; init; }
    [JsonPropertyName("sandbox_usage")]
    public JsonElement SandboxUsage { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("created_at")]
    public string? CreatedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<OrganizationBrandingAssetUploadRequestAssetType>))]
public enum OrganizationBrandingAssetUploadRequestAssetType
{
    [EnumMember(Value = "logo")]
    logo,
    [EnumMember(Value = "branding_image")]
    branding_image,
}

public sealed record OrganizationBrandingAssetUploadRequest
{
    [JsonPropertyName("asset_type")]
    public required OrganizationBrandingAssetUploadRequestAssetType AssetType { get; init; }
    [JsonPropertyName("filename")]
    public string Filename { get; init; }
    [JsonPropertyName("mime_type")]
    public string MimeType { get; init; }
}

public sealed record OrganizationBrandingAssetUploadResponse
{
    [JsonPropertyName("asset_type")]
    public string AssetType { get; init; }
    [JsonPropertyName("storage_key")]
    public string StorageKey { get; init; }
    [JsonPropertyName("bucket_name")]
    public string BucketName { get; init; }
    [JsonPropertyName("upload_url")]
    public string UploadUrl { get; init; }
    [JsonPropertyName("asset_url")]
    public string AssetUrl { get; init; }
}

public sealed record OrganizationSupportingDocumentUploadRequest
{
    [JsonPropertyName("filename")]
    public string Filename { get; init; }
    [JsonPropertyName("mime_type")]
    public string MimeType { get; init; }
    [JsonPropertyName("file_size_bytes")]
    public int FileSizeBytes { get; init; }
}

public sealed record OrganizationSupportingDocumentUploadResponse
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; }
    [JsonPropertyName("filename")]
    public string Filename { get; init; }
    [JsonPropertyName("file_size_bytes")]
    public int FileSizeBytes { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("storage_key")]
    public string StorageKey { get; init; }
    [JsonPropertyName("download_url")]
    public string DownloadUrl { get; init; }
    [JsonPropertyName("upload_url")]
    public string UploadUrl { get; init; }
}

public sealed record OrganizationSupportingDocumentCompleteResponse
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
}

public sealed record OrganizationSupportingDocumentDeleteResponse
{
    [JsonPropertyName("document_id")]
    public string DocumentId { get; init; }
    [JsonPropertyName("deleted")]
    public bool Deleted { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProjectSummaryEnvironment>))]
public enum ProjectSummaryEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

public sealed record ProjectSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("slug")]
    public string Slug { get; init; }
    [JsonPropertyName("environment")]
    public required ProjectSummaryEnvironment Environment { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("allowed_origins")]
    public IReadOnlyList<string> AllowedOrigins { get; init; }
    [JsonPropertyName("is_default")]
    public bool IsDefault { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProjectCreateRequestEnvironment>))]
public enum ProjectCreateRequestEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

public sealed record ProjectCreateRequest
{
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("slug")]
    public string? Slug { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("environment")]
    public ProjectCreateRequestEnvironment? Environment { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("allowed_origins")]
    public IReadOnlyList<string>? AllowedOrigins { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProjectUpdateRequestEnvironment>))]
public enum ProjectUpdateRequestEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

public sealed record ProjectUpdateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("name")]
    public string? Name { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("slug")]
    public string? Slug { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("environment")]
    public ProjectUpdateRequestEnvironment? Environment { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("allowed_origins")]
    public IReadOnlyList<string>? AllowedOrigins { get; init; }
}

public sealed record APIClientSummary
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string TenantPublicId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("client_id")]
    public string ClientId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("scopes")]
    public IReadOnlyList<string> Scopes { get; init; }
    [JsonPropertyName("allowed_networks")]
    public IReadOnlyList<string> AllowedNetworks { get; init; }
    [JsonPropertyName("rate_limit_per_minute")]
    public int RateLimitPerMinute { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("last_used_at")]
    public string? LastUsedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("client_secret_overlap_expires_at")]
    public string? ClientSecretOverlapExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record APIClientCreateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("scopes")]
    public IReadOnlyList<string> Scopes { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("allowed_networks")]
    public IReadOnlyList<string>? AllowedNetworks { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("rate_limit_per_minute")]
    public int? RateLimitPerMinute { get; init; }
}

public sealed record APIClientCreateResponse
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string TenantPublicId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("client_id")]
    public string ClientId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("scopes")]
    public IReadOnlyList<string> Scopes { get; init; }
    [JsonPropertyName("allowed_networks")]
    public IReadOnlyList<string> AllowedNetworks { get; init; }
    [JsonPropertyName("rate_limit_per_minute")]
    public int RateLimitPerMinute { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("last_used_at")]
    public string? LastUsedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("client_secret_overlap_expires_at")]
    public string? ClientSecretOverlapExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
    [JsonPropertyName("client_secret")]
    public string ClientSecret { get; init; }
}

public sealed record APIClientActionResponse
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string TenantPublicId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("client_id")]
    public string ClientId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("scopes")]
    public IReadOnlyList<string> Scopes { get; init; }
    [JsonPropertyName("allowed_networks")]
    public IReadOnlyList<string> AllowedNetworks { get; init; }
    [JsonPropertyName("rate_limit_per_minute")]
    public int RateLimitPerMinute { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("last_used_at")]
    public string? LastUsedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("client_secret_overlap_expires_at")]
    public string? ClientSecretOverlapExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("client_secret")]
    public string? ClientSecret { get; init; }
}

public sealed record WebhookEndpointSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("url")]
    public string Url { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("events")]
    public IReadOnlyList<string> Events { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("signing_secret_version")]
    public int SigningSecretVersion { get; init; }
    [JsonPropertyName("previous_secret_expires_at")]
    public string? PreviousSecretExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record WebhookEndpointCreateRequest
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("url")]
    public string Url { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("events")]
    public IReadOnlyList<string> Events { get; init; }
}

public sealed record WebhookEndpointCreateResponse
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("secret")]
    public string Secret { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
}

public sealed record WebhookEndpointTestResponse
{
    [JsonPropertyName("queued")]
    public bool Queued { get; init; }
}

public sealed record ManualReviewSummary
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("subject")]
    public JsonElement Subject { get; init; }
    [JsonPropertyName("risk_level")]
    public string RiskLevel { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("document_classification")]
    public JsonElement? DocumentClassification { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ManualReviewDecisionRequestDecision>))]
public enum ManualReviewDecisionRequestDecision
{
    [EnumMember(Value = "verified")]
    verified,
    [EnumMember(Value = "rejected")]
    rejected,
    [EnumMember(Value = "failed")]
    failed,
}

public sealed record ManualReviewDecisionRequest
{
    [JsonPropertyName("decision")]
    public required ManualReviewDecisionRequestDecision Decision { get; init; }
    [JsonPropertyName("reason_code")]
    public string ReasonCode { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reason_detail")]
    public string? ReasonDetail { get; init; }
}

public sealed record ManualReviewDecisionResponse
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("decision")]
    public string Decision { get; init; }
    [JsonPropertyName("decision_type")]
    public string DecisionType { get; init; }
    [JsonPropertyName("decided_at")]
    public string DecidedAt { get; init; }
}

public sealed record ManualReviewPendingDecisionResponse
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("decision")]
    public string Decision { get; init; }
    [JsonPropertyName("approval_status")]
    public string ApprovalStatus { get; init; }
    [JsonPropertyName("approval_required")]
    public bool ApprovalRequired { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ManualReviewApprovalRequestDecision>))]
public enum ManualReviewApprovalRequestDecision
{
    [EnumMember(Value = "verified")]
    verified,
    [EnumMember(Value = "rejected")]
    rejected,
    [EnumMember(Value = "failed")]
    failed,
}

public sealed record ManualReviewApprovalRequest
{
    [JsonPropertyName("decision")]
    public required ManualReviewApprovalRequestDecision Decision { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reason_code")]
    public string? ReasonCode { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reason_detail")]
    public string? ReasonDetail { get; init; }
}

public sealed record ManualReviewApprovalResponse
{
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("decision")]
    public string Decision { get; init; }
    [JsonPropertyName("approval_status")]
    public string ApprovalStatus { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<GovernedSchemaCreateKind>))]
public enum GovernedSchemaCreateKind
{
    [EnumMember(Value = "evidence")]
    evidence,
    [EnumMember(Value = "claim")]
    claim,
}

public sealed record GovernedSchemaCreate
{
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("kind")]
    public required GovernedSchemaCreateKind Kind { get; init; }
    [JsonPropertyName("definition")]
    public JsonElement Definition { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("disclosure_fields")]
    public IReadOnlyList<string>? DisclosureFields { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<PurposeAuthorizationCreateLegalBasis>))]
public enum PurposeAuthorizationCreateLegalBasis
{
    [EnumMember(Value = "consent")]
    consent,
    [EnumMember(Value = "contract")]
    contract,
    [EnumMember(Value = "legal_obligation")]
    legal_obligation,
    [EnumMember(Value = "legitimate_interest")]
    legitimate_interest,
}

public sealed record PurposeAuthorizationCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("legal_basis")]
    public required PurposeAuthorizationCreateLegalBasis LegalBasis { get; init; }
    [JsonPropertyName("justification")]
    public JsonElement Justification { get; init; }
    [JsonPropertyName("operations")]
    public IReadOnlyList<string> Operations { get; init; }
    [JsonPropertyName("valid_from")]
    public string ValidFrom { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("delete_after")]
    public string? DeleteAfter { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("consent_record_id")]
    public string? ConsentRecordId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("reuse_from_ids")]
    public IReadOnlyList<string>? ReuseFromIds { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<EvidenceCreateEvidenceType>))]
public enum EvidenceCreateEvidenceType
{
    [EnumMember(Value = "submitted")]
    submitted,
    [EnumMember(Value = "provider")]
    provider,
    [EnumMember(Value = "system")]
    system,
    [EnumMember(Value = "human")]
    human,
    [EnumMember(Value = "authoritative")]
    authoritative,
}

public sealed record EvidenceCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("authorization_id")]
    public string AuthorizationId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("evidence_type")]
    public required EvidenceCreateEvidenceType EvidenceType { get; init; }
    [JsonPropertyName("operation_reference")]
    public string OperationReference { get; init; }
    [JsonPropertyName("payload")]
    public JsonElement Payload { get; init; }
    [JsonPropertyName("provenance")]
    public JsonElement Provenance { get; init; }
    [JsonPropertyName("observed_at")]
    public string ObservedAt { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("source_ids")]
    public IReadOnlyList<string>? SourceIds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("supersedes_id")]
    public string? SupersedesId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("verification_id")]
    public string? VerificationId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("source_check_id")]
    public string? SourceCheckId { get; init; }
}

public sealed record GovernedReason
{
    [JsonPropertyName("reason")]
    public string Reason { get; init; }
}

public sealed record GovernedEmptyAction
{
}

public sealed record ResourceLegalHoldCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("reason")]
    public JsonElement Reason { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("expires_at")]
    public string? ExpiresAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ClaimCreateRuleName>))]
public enum ClaimCreateRuleName
{
    [EnumMember(Value = "")]
    Empty,
    [EnumMember(Value = "copy")]
    copy,
    [EnumMember(Value = "field")]
    field,
    [EnumMember(Value = "normalize_name")]
    normalize_name,
    [EnumMember(Value = "iso_date")]
    iso_date,
    [EnumMember(Value = "age_over")]
    age_over,
    [EnumMember(Value = "document_current")]
    document_current,
    [EnumMember(Value = "exact_corroboration")]
    exact_corroboration,
}

public sealed record ClaimCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("authorization_id")]
    public string AuthorizationId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("observed_at")]
    public string ObservedAt { get; init; }
    [JsonPropertyName("valid_from")]
    public string ValidFrom { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("evidence_ids")]
    public IReadOnlyList<string>? EvidenceIds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("claim_ids")]
    public IReadOnlyList<string>? ClaimIds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("value")]
    public JsonElement? Value { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("confidence")]
    public double? Confidence { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("rule_name")]
    public ClaimCreateRuleName? RuleName { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("rule_version")]
    public int? RuleVersion { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("rule_parameters")]
    public JsonElement? RuleParameters { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("supersedes_id")]
    public string? SupersedesId { get; init; }
}

public sealed record ClaimReusePolicyCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("purposes")]
    public IReadOnlyList<string> Purposes { get; init; }
    [JsonPropertyName("accepted_classes")]
    public IReadOnlyList<string> AcceptedClasses { get; init; }
    [JsonPropertyName("fields")]
    public IReadOnlyList<string> Fields { get; init; }
    [JsonPropertyName("max_age_seconds")]
    public int MaxAgeSeconds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("minimum_confidence")]
    public double? MinimumConfidence { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ClaimConflictReviewOutcome>))]
public enum ClaimConflictReviewOutcome
{
    [EnumMember(Value = "selected")]
    selected,
    [EnumMember(Value = "disputed")]
    disputed,
    [EnumMember(Value = "more_evidence")]
    more_evidence,
}

public sealed record ClaimConflictReview
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("selected_claim_id")]
    public string? SelectedClaimId { get; init; }
    [JsonPropertyName("outcome")]
    public required ClaimConflictReviewOutcome Outcome { get; init; }
    [JsonPropertyName("reason")]
    public JsonElement Reason { get; init; }
}

public sealed record ClaimRevoke
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("reason")]
    public string Reason { get; init; }
}

public sealed record ClaimEvaluation
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("policy_id")]
    public string PolicyId { get; init; }
}

public sealed record ClaimDisclosureCreate
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("authorization_id")]
    public string AuthorizationId { get; init; }
    [JsonPropertyName("audience_id")]
    public string AudienceId { get; init; }
    [JsonPropertyName("selections")]
    public IReadOnlyList<JsonElement> Selections { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("lifetime_seconds")]
    public int? LifetimeSeconds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("max_redemptions")]
    public int? MaxRedemptions { get; init; }
}

public sealed record GovernedProjectAction
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationCreateAssuranceLevel>))]
public enum ProviderCertificationCreateAssuranceLevel
{
    [EnumMember(Value = "conformance")]
    conformance,
    [EnumMember(Value = "assured")]
    assured,
}

public sealed record ProviderCertificationCreate
{
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("report")]
    public JsonElement Report { get; init; }
    [JsonPropertyName("assurance_level")]
    public required ProviderCertificationCreateAssuranceLevel AssuranceLevel { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
}

public sealed record ProviderCertificationRevoke
{
    [JsonPropertyName("reason")]
    public string Reason { get; init; }
}

public sealed record ProviderOperationCancel
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("reason")]
    public string Reason { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<GovernedSchemaKind>))]
public enum GovernedSchemaKind
{
    [EnumMember(Value = "evidence")]
    evidence,
    [EnumMember(Value = "claim")]
    claim,
}

public sealed record GovernedSchema
{
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("kind")]
    public required GovernedSchemaKind Kind { get; init; }
    [JsonPropertyName("definition")]
    public JsonElement Definition { get; init; }
    [JsonPropertyName("disclosure_fields")]
    public IReadOnlyList<string> DisclosureFields { get; init; }
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("retired_at")]
    public string? RetiredAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<PurposeAuthorizationLegalBasis>))]
public enum PurposeAuthorizationLegalBasis
{
    [EnumMember(Value = "consent")]
    consent,
    [EnumMember(Value = "contract")]
    contract,
    [EnumMember(Value = "legal_obligation")]
    legal_obligation,
    [EnumMember(Value = "legitimate_interest")]
    legitimate_interest,
}

public sealed record PurposeAuthorization
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("legal_basis")]
    public required PurposeAuthorizationLegalBasis LegalBasis { get; init; }
    [JsonPropertyName("operations")]
    public IReadOnlyList<string> Operations { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("approved_at")]
    public string? ApprovedAt { get; init; }
    [JsonPropertyName("valid_from")]
    public string ValidFrom { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("revoked_at")]
    public string? RevokedAt { get; init; }
    [JsonPropertyName("reuse_from_ids")]
    public IReadOnlyList<string> ReuseFromIds { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<PurposeAuthorizationDetailLegalBasis>))]
public enum PurposeAuthorizationDetailLegalBasis
{
    [EnumMember(Value = "consent")]
    consent,
    [EnumMember(Value = "contract")]
    contract,
    [EnumMember(Value = "legal_obligation")]
    legal_obligation,
    [EnumMember(Value = "legitimate_interest")]
    legitimate_interest,
}

public sealed record PurposeAuthorizationDetail
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("legal_basis")]
    public required PurposeAuthorizationDetailLegalBasis LegalBasis { get; init; }
    [JsonPropertyName("operations")]
    public IReadOnlyList<string> Operations { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("approved_at")]
    public string? ApprovedAt { get; init; }
    [JsonPropertyName("valid_from")]
    public string ValidFrom { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("revoked_at")]
    public string? RevokedAt { get; init; }
    [JsonPropertyName("reuse_from_ids")]
    public IReadOnlyList<string> ReuseFromIds { get; init; }
    [JsonPropertyName("justification")]
    public JsonElement Justification { get; init; }
    [JsonPropertyName("proposed_by_id")]
    public string ProposedById { get; init; }
    [JsonPropertyName("approved_by_id")]
    public string? ApprovedById { get; init; }
    [JsonPropertyName("consent_record_id")]
    public string? ConsentRecordId { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ResourceLegalHoldScope>))]
public enum ResourceLegalHoldScope
{
    [EnumMember(Value = "subject_project_lineage")]
    subject_project_lineage,
}

public sealed record ResourceLegalHold
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("expires_at")]
    public string? ExpiresAt { get; init; }
    [JsonPropertyName("released_at")]
    public string? ReleasedAt { get; init; }
    [JsonPropertyName("scope")]
    public required ResourceLegalHoldScope Scope { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ResourceLegalHoldDetailScope>))]
public enum ResourceLegalHoldDetailScope
{
    [EnumMember(Value = "subject_project_lineage")]
    subject_project_lineage,
}

public sealed record ResourceLegalHoldDetail
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("expires_at")]
    public string? ExpiresAt { get; init; }
    [JsonPropertyName("released_at")]
    public string? ReleasedAt { get; init; }
    [JsonPropertyName("scope")]
    public required ResourceLegalHoldDetailScope Scope { get; init; }
    [JsonPropertyName("reason")]
    public JsonElement Reason { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<GovernedEvidenceEvidenceType>))]
public enum GovernedEvidenceEvidenceType
{
    [EnumMember(Value = "submitted")]
    submitted,
    [EnumMember(Value = "provider")]
    provider,
    [EnumMember(Value = "system")]
    system,
    [EnumMember(Value = "human")]
    human,
    [EnumMember(Value = "authoritative")]
    authoritative,
}

[JsonConverter(typeof(ContractStringEnumConverter<GovernedEvidenceOrigin>))]
public enum GovernedEvidenceOrigin
{
    [EnumMember(Value = "persisted_provider_check")]
    persisted_provider_check,
    [EnumMember(Value = "caller_asserted")]
    caller_asserted,
}

public sealed record GovernedEvidence
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("schema_version")]
    public int SchemaVersion { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("observed_at")]
    public string ObservedAt { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonPropertyName("source_evidence_ids")]
    public IReadOnlyList<string> SourceEvidenceIds { get; init; }
    [JsonPropertyName("evidence_type")]
    public required GovernedEvidenceEvidenceType EvidenceType { get; init; }
    [JsonPropertyName("origin")]
    public required GovernedEvidenceOrigin Origin { get; init; }
    [JsonPropertyName("supersedes_id")]
    public string? SupersedesId { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("payload")]
    public JsonElement? Payload { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("provenance")]
    public JsonElement? Provenance { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<GovernedClaimClaimClass>))]
public enum GovernedClaimClaimClass
{
    [EnumMember(Value = "candidate")]
    candidate,
    [EnumMember(Value = "normalized")]
    normalized,
    [EnumMember(Value = "corroborated")]
    corroborated,
    [EnumMember(Value = "derived")]
    derived,
    [EnumMember(Value = "reviewed")]
    reviewed,
}

public sealed record GovernedClaim
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("subject_id")]
    public string SubjectId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("schema_version")]
    public int SchemaVersion { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("observed_at")]
    public string ObservedAt { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonPropertyName("source_evidence_ids")]
    public IReadOnlyList<string> SourceEvidenceIds { get; init; }
    [JsonPropertyName("claim_class")]
    public required GovernedClaimClaimClass ClaimClass { get; init; }
    [JsonPropertyName("confidence")]
    public string? Confidence { get; init; }
    [JsonPropertyName("valid_from")]
    public string ValidFrom { get; init; }
    [JsonPropertyName("rule")]
    public JsonElement? Rule { get; init; }
    [JsonPropertyName("source_claim_ids")]
    public IReadOnlyList<string> SourceClaimIds { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("value")]
    public JsonElement? Value { get; init; }
}

public sealed record GovernedReceipt
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("status")]
    public string? Status { get; init; }
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
}

public sealed record GovernedStateReceipt
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
}

public sealed record GovernedLineage
{
    [JsonPropertyName("root_id")]
    public string RootId { get; init; }
    [JsonPropertyName("nodes")]
    public IReadOnlyList<JsonElement> Nodes { get; init; }
    [JsonPropertyName("edges")]
    public IReadOnlyList<JsonElement> Edges { get; init; }
    [JsonPropertyName("truncated")]
    public bool Truncated { get; init; }
}

public sealed record ClaimReusePolicy
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("schema_id")]
    public string SchemaId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("purposes")]
    public IReadOnlyList<string> Purposes { get; init; }
    [JsonPropertyName("accepted_classes")]
    public IReadOnlyList<string> AcceptedClasses { get; init; }
    [JsonPropertyName("fields")]
    public IReadOnlyList<string> Fields { get; init; }
    [JsonPropertyName("max_age_seconds")]
    public int MaxAgeSeconds { get; init; }
    [JsonPropertyName("minimum_confidence")]
    public string? MinimumConfidence { get; init; }
    [JsonPropertyName("approved_at")]
    public string? ApprovedAt { get; init; }
    [JsonPropertyName("retired_at")]
    public string? RetiredAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ClaimReviewReceiptOutcome>))]
public enum ClaimReviewReceiptOutcome
{
    [EnumMember(Value = "selected")]
    selected,
    [EnumMember(Value = "disputed")]
    disputed,
    [EnumMember(Value = "more_evidence")]
    more_evidence,
}

public sealed record ClaimReviewReceipt
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("outcome")]
    public required ClaimReviewReceiptOutcome Outcome { get; init; }
    [JsonPropertyName("selected_claim_id")]
    public string? SelectedClaimId { get; init; }
}

public sealed record ClaimPolicyEvaluation
{
    [JsonPropertyName("satisfied")]
    public bool Satisfied { get; init; }
    [JsonPropertyName("reason_codes")]
    public IReadOnlyList<string> ReasonCodes { get; init; }
    [JsonPropertyName("claim_id")]
    public string ClaimId { get; init; }
    [JsonPropertyName("policy_id")]
    public string PolicyId { get; init; }
    [JsonPropertyName("usable_until")]
    public string? UsableUntil { get; init; }
    [JsonPropertyName("claim_class")]
    public string ClaimClass { get; init; }
    [JsonPropertyName("fresh_until")]
    public string FreshUntil { get; init; }
}

public sealed record ClaimDisclosureReceipt
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("audience_id")]
    public string AudienceId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
    [JsonPropertyName("max_redemptions")]
    public int MaxRedemptions { get; init; }
    [JsonPropertyName("token")]
    public string? Token { get; init; }
    [JsonPropertyName("token_available")]
    public bool TokenAvailable { get; init; }
}

public sealed record ClaimDisclosureRedemption
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("audience_id")]
    public string AudienceId { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("claims")]
    public IReadOnlyList<JsonElement> Claims { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record ClaimDisclosureRevocation
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("revoked")]
    public bool Revoked { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationEnvironment>))]
public enum ProviderCertificationEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationContractVersion>))]
public enum ProviderCertificationContractVersion
{
    [EnumMember(Value = "1")]
    Value1,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationOperationContract>))]
public enum ProviderCertificationOperationContract
{
    [EnumMember(Value = "sync")]
    sync,
    [EnumMember(Value = "ic-provider-operations-v1")]
    IcProviderOperationsV1,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationAssuranceLevel>))]
public enum ProviderCertificationAssuranceLevel
{
    [EnumMember(Value = "conformance")]
    conformance,
    [EnumMember(Value = "assured")]
    assured,
}

public sealed record ProviderCertification
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("environment")]
    public required ProviderCertificationEnvironment Environment { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("contract_version")]
    public required ProviderCertificationContractVersion ContractVersion { get; init; }
    [JsonPropertyName("operation_contract")]
    public required ProviderCertificationOperationContract OperationContract { get; init; }
    [JsonPropertyName("suite_version")]
    public string SuiteVersion { get; init; }
    [JsonPropertyName("report_sha256")]
    public string ReportSha256 { get; init; }
    [JsonPropertyName("assurance_level")]
    public required ProviderCertificationAssuranceLevel AssuranceLevel { get; init; }
    [JsonPropertyName("approved_at")]
    public string? ApprovedAt { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("revoked")]
    public bool Revoked { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonPropertyName("proposed_by_id")]
    public string ProposedById { get; init; }
    [JsonPropertyName("approved_by_id")]
    public string? ApprovedById { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationDetailEnvironment>))]
public enum ProviderCertificationDetailEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationDetailContractVersion>))]
public enum ProviderCertificationDetailContractVersion
{
    [EnumMember(Value = "1")]
    Value1,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationDetailOperationContract>))]
public enum ProviderCertificationDetailOperationContract
{
    [EnumMember(Value = "sync")]
    sync,
    [EnumMember(Value = "ic-provider-operations-v1")]
    IcProviderOperationsV1,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderCertificationDetailAssuranceLevel>))]
public enum ProviderCertificationDetailAssuranceLevel
{
    [EnumMember(Value = "conformance")]
    conformance,
    [EnumMember(Value = "assured")]
    assured,
}

public sealed record ProviderCertificationDetail
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("environment")]
    public required ProviderCertificationDetailEnvironment Environment { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("contract_version")]
    public required ProviderCertificationDetailContractVersion ContractVersion { get; init; }
    [JsonPropertyName("operation_contract")]
    public required ProviderCertificationDetailOperationContract OperationContract { get; init; }
    [JsonPropertyName("suite_version")]
    public string SuiteVersion { get; init; }
    [JsonPropertyName("report_sha256")]
    public string ReportSha256 { get; init; }
    [JsonPropertyName("assurance_level")]
    public required ProviderCertificationDetailAssuranceLevel AssuranceLevel { get; init; }
    [JsonPropertyName("approved_at")]
    public string? ApprovedAt { get; init; }
    [JsonPropertyName("valid_until")]
    public string ValidUntil { get; init; }
    [JsonPropertyName("revoked")]
    public bool Revoked { get; init; }
    [JsonPropertyName("report")]
    public JsonElement Report { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonPropertyName("proposed_by_id")]
    public string ProposedById { get; init; }
    [JsonPropertyName("approved_by_id")]
    public string? ApprovedById { get; init; }
}

public sealed record ProviderCertificationScope
{
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("environment")]
    public string Environment { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("contract_version")]
    public string ContractVersion { get; init; }
    [JsonPropertyName("operation_contract")]
    public string OperationContract { get; init; }
    [JsonPropertyName("configuration_digest")]
    public string ConfigurationDigest { get; init; }
    [JsonPropertyName("manifest_sha256")]
    public string ManifestSha256 { get; init; }
    [JsonPropertyName("suite_version")]
    public string SuiteVersion { get; init; }
    [JsonPropertyName("required_cases")]
    public IReadOnlyList<string> RequiredCases { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationStatus>))]
public enum ProviderOperationStatus
{
    [EnumMember(Value = "created")]
    created,
    [EnumMember(Value = "pending")]
    pending,
    [EnumMember(Value = "completed")]
    completed,
    [EnumMember(Value = "failed")]
    failed,
    [EnumMember(Value = "cancelled")]
    cancelled,
    [EnumMember(Value = "expired")]
    expired,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationRemoteAction>))]
public enum ProviderOperationRemoteAction
{
    [EnumMember(Value = "cancel")]
    cancel,
    [EnumMember(Value = "delete")]
    delete,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationRemoteActionStatus>))]
public enum ProviderOperationRemoteActionStatus
{
    [EnumMember(Value = "pending")]
    pending,
    [EnumMember(Value = "acknowledged")]
    acknowledged,
    [EnumMember(Value = "expired")]
    expired,
}

public sealed record ProviderOperation
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("status")]
    public required ProviderOperationStatus Status { get; init; }
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("check_id")]
    public string CheckId { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("deadline")]
    public string Deadline { get; init; }
    [JsonPropertyName("completed_at")]
    public string? CompletedAt { get; init; }
    [JsonPropertyName("verification_id")]
    public string VerificationId { get; init; }
    [JsonPropertyName("delete_after")]
    public string DeleteAfter { get; init; }
    [JsonPropertyName("invalidation_reason")]
    public string InvalidationReason { get; init; }
    [JsonPropertyName("remote_action")]
    public required ProviderOperationRemoteAction? RemoteAction { get; init; }
    [JsonPropertyName("remote_action_status")]
    public required ProviderOperationRemoteActionStatus? RemoteActionStatus { get; init; }
    [JsonPropertyName("remote_requested_at")]
    public string? RemoteRequestedAt { get; init; }
    [JsonPropertyName("remote_attempted_at")]
    public string? RemoteAttemptedAt { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationBindingOperationContract>))]
public enum ProviderOperationBindingOperationContract
{
    [EnumMember(Value = "ic-provider-operations-v1")]
    IcProviderOperationsV1,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationBindingEnvironment>))]
public enum ProviderOperationBindingEnvironment
{
    [EnumMember(Value = "sandbox")]
    sandbox,
    [EnumMember(Value = "production")]
    production,
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationBindingContractVersion>))]
public enum ProviderOperationBindingContractVersion
{
    [EnumMember(Value = "1")]
    Value1,
}

public sealed record ProviderOperationBinding
{
    [JsonPropertyName("operation_contract")]
    public required ProviderOperationBindingOperationContract OperationContract { get; init; }
    [JsonPropertyName("operation_id")]
    public string OperationId { get; init; }
    [JsonPropertyName("configuration_id")]
    public string ConfigurationId { get; init; }
    [JsonPropertyName("tenant_id")]
    public string TenantId { get; init; }
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; }
    [JsonPropertyName("environment")]
    public required ProviderOperationBindingEnvironment Environment { get; init; }
    [JsonPropertyName("capability")]
    public string Capability { get; init; }
    [JsonPropertyName("contract_version")]
    public required ProviderOperationBindingContractVersion ContractVersion { get; init; }
    [JsonPropertyName("request_sha256")]
    public string RequestSha256 { get; init; }
    [JsonPropertyName("lease_generation")]
    public int LeaseGeneration { get; init; }
    [JsonPropertyName("deadline")]
    public string Deadline { get; init; }
    [JsonPropertyName("callback_path")]
    public string CallbackPath { get; init; }
    [JsonPropertyName("lease_token")]
    public string LeaseToken { get; init; }
}

[JsonConverter(typeof(ContractStringEnumConverter<ProviderOperationCallbackStatus>))]
public enum ProviderOperationCallbackStatus
{
    [EnumMember(Value = "pending")]
    pending,
    [EnumMember(Value = "completed")]
    completed,
    [EnumMember(Value = "failed")]
    failed,
}

public sealed record ProviderOperationCallback
{
    [JsonPropertyName("binding")]
    public ProviderOperationBinding Binding { get; init; }
    [JsonPropertyName("status")]
    public required ProviderOperationCallbackStatus Status { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("result")]
    public JsonElement? Result { get; init; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("retry_after_seconds")]
    public int? RetryAfterSeconds { get; init; }
}

public sealed record GovernedSchemaPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<GovernedSchema> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record PurposeAuthorizationPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<PurposeAuthorization> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record ResourceLegalHoldPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<ResourceLegalHold> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record GovernedEvidencePage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<GovernedEvidence> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record GovernedClaimPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<GovernedClaim> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record ClaimReusePolicyPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<ClaimReusePolicy> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record ProviderCertificationPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<ProviderCertification> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

public sealed record ProviderOperationPage
{
    [JsonPropertyName("results")]
    public IReadOnlyList<ProviderOperation> Results { get; init; }
    [JsonPropertyName("pagination")]
    public CursorPagination Pagination { get; init; }
}

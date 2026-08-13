// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.
using System.Text.Json;
using System.Text.Json.Serialization;

namespace IdentityCore.Models;

public sealed record Error
{
    [JsonPropertyName("code")]
    public string Code { get; init; }
    [JsonPropertyName("message")]
    public string Message { get; init; }
    [JsonPropertyName("details")]
    public JsonElement? Details { get; init; }
}

public sealed record ErrorEnvelope
{
    [JsonPropertyName("success")]
    public JsonElement Success { get; init; }
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
    [JsonPropertyName("source_template_id")]
    public string? SourceTemplateId { get; init; }
    [JsonPropertyName("source_template_version")]
    public string? SourceTemplateVersion { get; init; }
    [JsonPropertyName("created_at")]
    public string? CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; init; }
}

public sealed record Policy
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("version")]
    public int Version { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("required_document_types")]
    public IReadOnlyList<string> RequiredDocumentTypes { get; init; }
    [JsonPropertyName("required_liveness_level")]
    public string RequiredLivenessLevel { get; init; }
    [JsonPropertyName("face_match_threshold")]
    public double FaceMatchThreshold { get; init; }
    [JsonPropertyName("manual_review_threshold")]
    public double ManualReviewThreshold { get; init; }
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
    [JsonPropertyName("full_name")]
    public string? FullName { get; init; }
    [JsonPropertyName("email")]
    public string? Email { get; init; }
    [JsonPropertyName("phone_number")]
    public string? PhoneNumber { get; init; }
    [JsonPropertyName("date_of_birth")]
    public string? DateOfBirth { get; init; }
    [JsonPropertyName("metadata")]
    public JsonElement? Metadata { get; init; }
}

public sealed record VerificationCreateRequest
{
    [JsonPropertyName("external_reference")]
    public string? ExternalReference { get; init; }
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
    [JsonPropertyName("policy_id")]
    public string PolicyId { get; init; }
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("verification_subject")]
    public VerificationSubjectInput VerificationSubject { get; init; }
    [JsonPropertyName("redirect_url")]
    public string? RedirectUrl { get; init; }
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

public sealed record VerificationPolicyCreateRequest
{
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("consent_template_id")]
    public string? ConsentTemplateId { get; init; }
    [JsonPropertyName("default_locale")]
    public string? DefaultLocale { get; init; }
    [JsonPropertyName("supported_locales")]
    public IReadOnlyList<string>? SupportedLocales { get; init; }
    [JsonPropertyName("required_document_types")]
    public IReadOnlyList<string> RequiredDocumentTypes { get; init; }
    [JsonPropertyName("required_liveness_level")]
    public string RequiredLivenessLevel { get; init; }
    [JsonPropertyName("face_match_threshold")]
    public double FaceMatchThreshold { get; init; }
    [JsonPropertyName("manual_review_threshold")]
    public double ManualReviewThreshold { get; init; }
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
    [JsonPropertyName("session_token")]
    public string? SessionToken { get; init; }
    [JsonPropertyName("expires_at")]
    public string ExpiresAt { get; init; }
}

public sealed record VerificationSessionConsentRequest
{
    [JsonPropertyName("accepted")]
    public bool Accepted { get; init; }
    [JsonPropertyName("template_id")]
    public string? TemplateId { get; init; }
    [JsonPropertyName("version")]
    public int? Version { get; init; }
    [JsonPropertyName("locale")]
    public string? Locale { get; init; }
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

public sealed record VerificationSessionSelfieRequest
{
    [JsonPropertyName("capture_type")]
    public string CaptureType { get; init; }
    [JsonPropertyName("upload_id")]
    public string UploadId { get; init; }
}

public sealed record VerificationSessionLivenessRequest
{
    [JsonPropertyName("liveness_type")]
    public string LivenessType { get; init; }
    [JsonPropertyName("selfie_capture_id")]
    public string SelfieCaptureId { get; init; }
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
    public string Direction { get; init; }
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
    [JsonPropertyName("external_reference")]
    public string ExternalReference { get; init; }
    [JsonPropertyName("subject")]
    public JsonElement Subject { get; init; }
    [JsonPropertyName("policy")]
    public JsonElement Policy { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("completed_at")]
    public string? CompletedAt { get; init; }
    [JsonPropertyName("verification_subject")]
    public JsonElement? VerificationSubject { get; init; }
    [JsonPropertyName("checks")]
    public JsonElement? Checks { get; init; }
    [JsonPropertyName("risk_assessment")]
    public JsonElement? RiskAssessment { get; init; }
    [JsonPropertyName("evidence_report")]
    public JsonElement? EvidenceReport { get; init; }
    [JsonPropertyName("decision")]
    public JsonElement? Decision { get; init; }
    [JsonPropertyName("expires_at")]
    public string? ExpiresAt { get; init; }
}

public sealed record VerificationResult
{
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

public sealed record PortalUploadCreateRequest
{
    [JsonPropertyName("purpose")]
    public string Purpose { get; init; }
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
    [JsonPropertyName("industry")]
    public string? Industry { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("tenant_id")]
    public string? TenantId { get; init; }
    [JsonPropertyName("tenant_name")]
    public string? TenantName { get; init; }
    [JsonPropertyName("tenant_status")]
    public string? TenantStatus { get; init; }
    [JsonPropertyName("default_country_profile_id")]
    public string? DefaultCountryProfileId { get; init; }
    [JsonPropertyName("default_jurisdiction_id")]
    public string? DefaultJurisdictionId { get; init; }
    [JsonPropertyName("settings")]
    public JsonElement Settings { get; init; }
    [JsonPropertyName("sandbox_usage")]
    public JsonElement SandboxUsage { get; init; }
    [JsonPropertyName("created_at")]
    public string? CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; init; }
}

public sealed record OrganizationBrandingAssetUploadRequest
{
    [JsonPropertyName("asset_type")]
    public string AssetType { get; init; }
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

public sealed record ProjectSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("slug")]
    public string Slug { get; init; }
    [JsonPropertyName("environment")]
    public string Environment { get; init; }
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

public sealed record ProjectCreateRequest
{
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("slug")]
    public string? Slug { get; init; }
    [JsonPropertyName("environment")]
    public string? Environment { get; init; }
    [JsonPropertyName("allowed_origins")]
    public IReadOnlyList<string>? AllowedOrigins { get; init; }
}

public sealed record APIClientSummary
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string TenantPublicId { get; init; }
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
    [JsonPropertyName("last_used_at")]
    public string? LastUsedAt { get; init; }
    [JsonPropertyName("client_secret_overlap_expires_at")]
    public string? ClientSecretOverlapExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record APIClientCreateRequest
{
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("name")]
    public string Name { get; init; }
    [JsonPropertyName("scopes")]
    public IReadOnlyList<string> Scopes { get; init; }
    [JsonPropertyName("allowed_networks")]
    public IReadOnlyList<string>? AllowedNetworks { get; init; }
    [JsonPropertyName("rate_limit_per_minute")]
    public int? RateLimitPerMinute { get; init; }
}

public sealed record APIClientCreateResponse
{
    [JsonPropertyName("public_id")]
    public string PublicId { get; init; }
    [JsonPropertyName("tenant_public_id")]
    public string TenantPublicId { get; init; }
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
    [JsonPropertyName("last_used_at")]
    public string? LastUsedAt { get; init; }
    [JsonPropertyName("client_secret_overlap_expires_at")]
    public string? ClientSecretOverlapExpiresAt { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
    [JsonPropertyName("client_secret")]
    public string ClientSecret { get; init; }
}

public sealed record WebhookEndpointSummary
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("url")]
    public string Url { get; init; }
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("events")]
    public IReadOnlyList<string> Events { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
}

public sealed record WebhookEndpointCreateRequest
{
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("url")]
    public string Url { get; init; }
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("events")]
    public IReadOnlyList<string> Events { get; init; }
}

public sealed record WebhookEndpointCreateResponse
{
    [JsonPropertyName("id")]
    public string Id { get; init; }
    [JsonPropertyName("project_id")]
    public string? ProjectId { get; init; }
    [JsonPropertyName("url")]
    public string Url { get; init; }
    [JsonPropertyName("description")]
    public string? Description { get; init; }
    [JsonPropertyName("events")]
    public IReadOnlyList<string> Events { get; init; }
    [JsonPropertyName("status")]
    public string Status { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; }
    [JsonPropertyName("secret")]
    public string Secret { get; init; }
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
    [JsonPropertyName("document_classification")]
    public JsonElement? DocumentClassification { get; init; }
    [JsonPropertyName("created_at")]
    public string CreatedAt { get; init; }
}

public sealed record ManualReviewDecisionRequest
{
    [JsonPropertyName("decision")]
    public string Decision { get; init; }
    [JsonPropertyName("reason_code")]
    public string ReasonCode { get; init; }
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

public sealed record ManualReviewApprovalRequest
{
    [JsonPropertyName("decision")]
    public string Decision { get; init; }
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

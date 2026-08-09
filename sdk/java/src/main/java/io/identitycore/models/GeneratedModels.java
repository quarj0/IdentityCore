// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.
package io.identitycore.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;

public final class GeneratedModels {
    private GeneratedModels() {}

    public record Error(@JsonProperty("code") String code, @JsonProperty("message") String message, @JsonProperty("details") JsonNode details) {}

    public record ErrorEnvelope(@JsonProperty("success") JsonNode success, @JsonProperty("error") Error error, @JsonProperty("request_id") String request_id) {}

    public record WorkflowSummary(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("description") String description, @JsonProperty("status") String status, @JsonProperty("steps") List<String> steps, @JsonProperty("settings") JsonNode settings, @JsonProperty("current_version") Integer current_version, @JsonProperty("source_template_id") String source_template_id, @JsonProperty("source_template_version") String source_template_version, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record Policy(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("description") String description, @JsonProperty("version") Integer version, @JsonProperty("status") String status, @JsonProperty("required_document_types") List<String> required_document_types, @JsonProperty("required_liveness_level") String required_liveness_level, @JsonProperty("face_match_threshold") Double face_match_threshold, @JsonProperty("manual_review_threshold") Double manual_review_threshold, @JsonProperty("verification_expiry_minutes") Integer verification_expiry_minutes, @JsonProperty("media_retention_days") Integer media_retention_days, @JsonProperty("metadata_retention_days") Integer metadata_retention_days, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record VerificationSubjectInput(@JsonProperty("full_name") String full_name, @JsonProperty("email") String email, @JsonProperty("phone_number") String phone_number, @JsonProperty("date_of_birth") String date_of_birth, @JsonProperty("metadata") JsonNode metadata) {}

    public record VerificationCreateRequest(@JsonProperty("external_reference") String external_reference, @JsonProperty("purpose") String purpose, @JsonProperty("policy_id") String policy_id, @JsonProperty("project_id") String project_id, @JsonProperty("verification_subject") VerificationSubjectInput verification_subject, @JsonProperty("redirect_url") String redirect_url, @JsonProperty("metadata") JsonNode metadata) {}

    public record VerificationCreateResponse(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("verification_url") String verification_url, @JsonProperty("session_id") String session_id, @JsonProperty("session_token") String session_token, @JsonProperty("expires_at") String expires_at) {}

    public record VerificationSummary(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("external_reference") String external_reference, @JsonProperty("subject") JsonNode subject, @JsonProperty("policy") JsonNode policy, @JsonProperty("created_at") String created_at, @JsonProperty("completed_at") String completed_at) {}

    public record VerificationDetail(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("external_reference") String external_reference, @JsonProperty("subject") JsonNode subject, @JsonProperty("policy") JsonNode policy, @JsonProperty("created_at") String created_at, @JsonProperty("completed_at") String completed_at, @JsonProperty("verification_subject") JsonNode verification_subject, @JsonProperty("checks") JsonNode checks, @JsonProperty("risk_assessment") JsonNode risk_assessment, @JsonProperty("evidence_report") JsonNode evidence_report, @JsonProperty("decision") JsonNode decision, @JsonProperty("expires_at") String expires_at) {}

    public record VerificationResult(@JsonProperty("schema_version") String schema_version, @JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("decision") JsonNode decision, @JsonProperty("policy") JsonNode policy, @JsonProperty("workflow") JsonNode workflow, @JsonProperty("check_provenance") List<JsonNode> check_provenance, @JsonProperty("timestamps") JsonNode timestamps) {}

    public record CursorPagination(@JsonProperty("limit") Integer limit, @JsonProperty("next_cursor") String next_cursor, @JsonProperty("has_more") Boolean has_more) {}

    public record PagePagination(@JsonProperty("page") Integer page, @JsonProperty("page_size") Integer page_size, @JsonProperty("total") Integer total, @JsonProperty("total_pages") Integer total_pages) {}

    public record EvidenceReport(@JsonProperty("verification_id") String verification_id, @JsonProperty("storage_key") String storage_key, @JsonProperty("download_url") String download_url, @JsonProperty("pdf_storage_key") String pdf_storage_key, @JsonProperty("pdf_download_url") String pdf_download_url) {}

    public record PortalUploadCreateRequest(@JsonProperty("purpose") String purpose, @JsonProperty("mime_type") String mime_type, @JsonProperty("file_size_bytes") Integer file_size_bytes) {}

    public record PortalUploadCreateResponse(@JsonProperty("upload_id") String upload_id, @JsonProperty("upload_url") String upload_url, @JsonProperty("upload_headers") JsonNode upload_headers, @JsonProperty("upload_transfer_path") String upload_transfer_path, @JsonProperty("expires_at") String expires_at) {}

    public record PortalUploadTransferResponse(@JsonProperty("upload_id") String upload_id) {}

    public record OrganizationProfile(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("industry") String industry, @JsonProperty("status") String status, @JsonProperty("tenant_id") String tenant_id, @JsonProperty("tenant_name") String tenant_name, @JsonProperty("tenant_status") String tenant_status, @JsonProperty("default_country_profile_id") String default_country_profile_id, @JsonProperty("default_jurisdiction_id") String default_jurisdiction_id, @JsonProperty("settings") JsonNode settings, @JsonProperty("sandbox_usage") JsonNode sandbox_usage, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record OrganizationBrandingAssetUploadRequest(@JsonProperty("asset_type") String asset_type, @JsonProperty("filename") String filename, @JsonProperty("mime_type") String mime_type) {}

    public record OrganizationBrandingAssetUploadResponse(@JsonProperty("asset_type") String asset_type, @JsonProperty("storage_key") String storage_key, @JsonProperty("bucket_name") String bucket_name, @JsonProperty("upload_url") String upload_url, @JsonProperty("asset_url") String asset_url) {}

    public record OrganizationSupportingDocumentUploadRequest(@JsonProperty("filename") String filename, @JsonProperty("mime_type") String mime_type, @JsonProperty("file_size_bytes") Integer file_size_bytes) {}

    public record OrganizationSupportingDocumentUploadResponse(@JsonProperty("document_id") String document_id, @JsonProperty("filename") String filename, @JsonProperty("file_size_bytes") Integer file_size_bytes, @JsonProperty("status") String status, @JsonProperty("storage_key") String storage_key, @JsonProperty("download_url") String download_url, @JsonProperty("upload_url") String upload_url) {}

    public record OrganizationSupportingDocumentCompleteResponse(@JsonProperty("document_id") String document_id, @JsonProperty("status") String status) {}

    public record OrganizationSupportingDocumentDeleteResponse(@JsonProperty("document_id") String document_id, @JsonProperty("deleted") Boolean deleted) {}

    public record ProjectSummary(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("environment") String environment, @JsonProperty("status") String status, @JsonProperty("allowed_origins") List<String> allowed_origins, @JsonProperty("is_default") Boolean is_default, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record ProjectCreateRequest(@JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("environment") String environment, @JsonProperty("allowed_origins") List<String> allowed_origins) {}

    public record APIClientSummary(@JsonProperty("public_id") String public_id, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("client_id") String client_id, @JsonProperty("status") String status, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute, @JsonProperty("last_used_at") String last_used_at, @JsonProperty("client_secret_overlap_expires_at") String client_secret_overlap_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record APIClientCreateRequest(@JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute) {}

    public record APIClientCreateResponse(@JsonProperty("public_id") String public_id, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("client_id") String client_id, @JsonProperty("status") String status, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute, @JsonProperty("last_used_at") String last_used_at, @JsonProperty("client_secret_overlap_expires_at") String client_secret_overlap_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at, @JsonProperty("client_secret") String client_secret) {}

    public record WebhookEndpointSummary(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("url") String url, @JsonProperty("description") String description, @JsonProperty("events") List<String> events, @JsonProperty("status") String status, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {}

    public record WebhookEndpointCreateRequest(@JsonProperty("project_id") String project_id, @JsonProperty("url") String url, @JsonProperty("description") String description, @JsonProperty("events") List<String> events) {}

    public record WebhookEndpointCreateResponse(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("url") String url, @JsonProperty("description") String description, @JsonProperty("events") List<String> events, @JsonProperty("status") String status, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at, @JsonProperty("secret") String secret) {}

    public record WebhookEndpointTestResponse(@JsonProperty("queued") Boolean queued) {}

    public record ManualReviewSummary(@JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("subject") JsonNode subject, @JsonProperty("risk_level") String risk_level, @JsonProperty("document_classification") JsonNode document_classification, @JsonProperty("created_at") String created_at) {}

    public record ManualReviewDecisionRequest(@JsonProperty("decision") String decision, @JsonProperty("reason_code") String reason_code, @JsonProperty("reason_detail") String reason_detail) {}

    public record ManualReviewDecisionResponse(@JsonProperty("verification_id") String verification_id, @JsonProperty("decision") String decision, @JsonProperty("decision_type") String decision_type, @JsonProperty("decided_at") String decided_at) {}

}

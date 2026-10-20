// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.
package io.identitycore.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;

public final class GeneratedModels {

    private GeneratedModels() {
    }

    public record Error(@JsonProperty("code") String code, @JsonProperty("message") String message, @JsonProperty("details") JsonNode details) {

    }

    public record ErrorEnvelope(@JsonProperty("success") Boolean success, @JsonProperty("error") Error error, @JsonProperty("request_id") String request_id) {

    }

    public record WorkflowSummary(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("description") String description, @JsonProperty("status") String status, @JsonProperty("steps") List<String> steps, @JsonProperty("settings") JsonNode settings, @JsonProperty("current_version") Integer current_version, @JsonProperty("source_template_id") String source_template_id, @JsonProperty("source_template_version") String source_template_version, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public enum PolicyStatus {
        Draft("draft"), Active("active"), Archived("archived");

        private final String value;
        PolicyStatus(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PolicyStatus fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PolicyStatus member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum PolicyRequiredLivenessLevel {
        Passive("passive"), Active("active");

        private final String value;
        PolicyRequiredLivenessLevel(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PolicyRequiredLivenessLevel fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PolicyRequiredLivenessLevel member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum PolicyExternalRiskFailureAction {
        ManualReview("manual_review"), Ignore("ignore");

        private final String value;
        PolicyExternalRiskFailureAction(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PolicyExternalRiskFailureAction fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PolicyExternalRiskFailureAction member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record Policy(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("description") String description, @JsonProperty("version") Integer version, @JsonProperty("status") PolicyStatus status, @JsonProperty("required_document_types") List<String> required_document_types, @JsonProperty("required_liveness_level") PolicyRequiredLivenessLevel required_liveness_level, @JsonProperty("face_match_threshold") Double face_match_threshold, @JsonProperty("manual_review_threshold") Double manual_review_threshold, @JsonProperty("review_reason_rules") JsonNode review_reason_rules, @JsonProperty("reuse_rules") JsonNode reuse_rules, @JsonProperty("document_consistency_rules") JsonNode document_consistency_rules, @JsonProperty("document_authenticity_required") Boolean document_authenticity_required, @JsonProperty("document_authenticity_min_confidence") Double document_authenticity_min_confidence, @JsonProperty("external_risk_enabled") Boolean external_risk_enabled, @JsonProperty("external_risk_failure_action") PolicyExternalRiskFailureAction external_risk_failure_action, @JsonProperty("external_risk_review_threshold") Double external_risk_review_threshold, @JsonProperty("maker_checker_required") Boolean maker_checker_required, @JsonProperty("verification_expiry_minutes") Integer verification_expiry_minutes, @JsonProperty("media_retention_days") Integer media_retention_days, @JsonProperty("metadata_retention_days") Integer metadata_retention_days, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public record VerificationSubjectInput(@JsonProperty("full_name") String full_name, @JsonProperty("email") String email, @JsonProperty("phone_number") String phone_number, @JsonProperty("date_of_birth") String date_of_birth, @JsonProperty("metadata") JsonNode metadata) {

    }

    public record VerificationCreateRequest(@JsonProperty("external_reference") String external_reference, @JsonProperty("purpose") String purpose, @JsonProperty("policy_id") String policy_id, @JsonProperty("project_id") String project_id, @JsonProperty("verification_subject") VerificationSubjectInput verification_subject, @JsonProperty("redirect_url") String redirect_url, @JsonProperty("metadata") JsonNode metadata) {

    }

    public record PlatformUserLoginRequest(@JsonProperty("email") String email, @JsonProperty("password") String password) {

    }

    public record PlatformUser(@JsonProperty("public_id") String public_id, @JsonProperty("email") String email, @JsonProperty("first_name") String first_name, @JsonProperty("last_name") String last_name, @JsonProperty("phone_number") String phone_number, @JsonProperty("status") String status, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("tenant_name") String tenant_name, @JsonProperty("tenant_status") String tenant_status, @JsonProperty("is_platform_admin") Boolean is_platform_admin, @JsonProperty("mfa_enabled") Boolean mfa_enabled, @JsonProperty("roles") List<String> roles, @JsonProperty("notification_preferences") JsonNode notification_preferences, @JsonProperty("last_login_at") String last_login_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public record PlatformUserMfaChallenge(@JsonProperty("mfa_required") Boolean mfa_required, @JsonProperty("mfa_enrollment_required") Boolean mfa_enrollment_required, @JsonProperty("mfa_token") String mfa_token) {

    }

    public record PlatformUserAuthentication(@JsonProperty("tokens") JsonNode tokens, @JsonProperty("user") PlatformUser user, @JsonProperty("recovery_codes") List<String> recovery_codes) {

    }

    public record PlatformUserMfaEnrollmentRequest(@JsonProperty("mfa_token") String mfa_token) {

    }

    public record PlatformUserMfaCodeRequest(@JsonProperty("mfa_token") String mfa_token, @JsonProperty("code") String code) {

    }

    public record PlatformUserMfaEnrollment(@JsonProperty("secret") String secret, @JsonProperty("provisioning_uri") String provisioning_uri) {

    }

    public enum VerificationPolicyCreateRequestRequiredLivenessLevel {
        Passive("passive"), Active("active");

        private final String value;
        VerificationPolicyCreateRequestRequiredLivenessLevel(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static VerificationPolicyCreateRequestRequiredLivenessLevel fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (VerificationPolicyCreateRequestRequiredLivenessLevel member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum VerificationPolicyCreateRequestExternalRiskFailureAction {
        ManualReview("manual_review"), Ignore("ignore");

        private final String value;
        VerificationPolicyCreateRequestExternalRiskFailureAction(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static VerificationPolicyCreateRequestExternalRiskFailureAction fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (VerificationPolicyCreateRequestExternalRiskFailureAction member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record VerificationPolicyCreateRequest(@JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("description") String description, @JsonProperty("consent_template_id") String consent_template_id, @JsonProperty("default_locale") String default_locale, @JsonProperty("supported_locales") List<String> supported_locales, @JsonProperty("required_document_types") List<String> required_document_types, @JsonProperty("required_liveness_level") VerificationPolicyCreateRequestRequiredLivenessLevel required_liveness_level, @JsonProperty("face_match_threshold") Double face_match_threshold, @JsonProperty("manual_review_threshold") Double manual_review_threshold, @JsonProperty("review_reason_rules") JsonNode review_reason_rules, @JsonProperty("reuse_rules") JsonNode reuse_rules, @JsonProperty("document_consistency_rules") JsonNode document_consistency_rules, @JsonProperty("document_authenticity_required") Boolean document_authenticity_required, @JsonProperty("document_authenticity_min_confidence") Double document_authenticity_min_confidence, @JsonProperty("external_risk_enabled") Boolean external_risk_enabled, @JsonProperty("external_risk_failure_action") VerificationPolicyCreateRequestExternalRiskFailureAction external_risk_failure_action, @JsonProperty("external_risk_review_threshold") Double external_risk_review_threshold, @JsonProperty("maker_checker_required") Boolean maker_checker_required, @JsonProperty("verification_expiry_minutes") Integer verification_expiry_minutes, @JsonProperty("media_retention_days") Integer media_retention_days, @JsonProperty("metadata_retention_days") Integer metadata_retention_days) {

    }

    public record VerificationPolicyCreateResponse(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("version") Integer version, @JsonProperty("status") String status) {

    }

    public record VerificationCreateResponse(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("verification_url") String verification_url, @JsonProperty("session_id") String session_id, @JsonProperty("session_token") String session_token, @JsonProperty("expires_at") String expires_at) {

    }

    public record VerificationSessionConsentRequest(@JsonProperty("accepted") Boolean accepted, @JsonProperty("template_id") String template_id, @JsonProperty("version") Integer version, @JsonProperty("locale") String locale, @JsonProperty("content_hash") String content_hash) {

    }

    public record VerificationSessionDocumentRequest(@JsonProperty("document_type") String document_type, @JsonProperty("country_code") String country_code, @JsonProperty("captures") List<JsonNode> captures) {

    }

    public enum VerificationSessionSelfieRequestCaptureType {
        Image("image"), Video("video");

        private final String value;
        VerificationSessionSelfieRequestCaptureType(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static VerificationSessionSelfieRequestCaptureType fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (VerificationSessionSelfieRequestCaptureType member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record VerificationSessionSelfieRequest(@JsonProperty("capture_type") VerificationSessionSelfieRequestCaptureType capture_type, @JsonProperty("upload_id") String upload_id) {

    }

    public enum VerificationSessionLivenessRequestLivenessType {
        Passive("passive"), Active("active");

        private final String value;
        VerificationSessionLivenessRequestLivenessType(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static VerificationSessionLivenessRequestLivenessType fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (VerificationSessionLivenessRequestLivenessType member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record VerificationSessionLivenessRequest(@JsonProperty("liveness_type") VerificationSessionLivenessRequestLivenessType liveness_type, @JsonProperty("selfie_capture_id") String selfie_capture_id, @JsonProperty("challenge_id") String challenge_id) {

    }

    public record VerificationMobileHandoffRedeemResponse(@JsonProperty("session_id") String session_id, @JsonProperty("session_token") String session_token, @JsonProperty("verification_id") String verification_id) {

    }

    public enum VerificationSessionResponseDirection {
        Ltr("ltr"), Rtl("rtl");

        private final String value;
        VerificationSessionResponseDirection(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static VerificationSessionResponseDirection fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (VerificationSessionResponseDirection member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record VerificationSessionResponse(@JsonProperty("session_id") String session_id, @JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("organization") JsonNode organization, @JsonProperty("purpose") String purpose, @JsonProperty("redirect_url") String redirect_url, @JsonProperty("required_steps") List<String> required_steps, @JsonProperty("workflow") JsonNode workflow, @JsonProperty("locale") String locale, @JsonProperty("supported_locales") List<String> supported_locales, @JsonProperty("direction") VerificationSessionResponseDirection direction, @JsonProperty("consent") JsonNode consent, @JsonProperty("document") JsonNode document, @JsonProperty("available_documents") List<JsonNode> available_documents, @JsonProperty("available_countries") List<JsonNode> available_countries, @JsonProperty("expires_at") String expires_at) {

    }

    public record VerificationSessionConsentResponse(@JsonProperty("consent_record_id") String consent_record_id, @JsonProperty("next_step") String next_step) {

    }

    public record VerificationSessionDocumentResponse(@JsonProperty("identity_document_id") String identity_document_id, @JsonProperty("status") String status, @JsonProperty("next_step") String next_step) {

    }

    public record VerificationSessionSelfieResponse(@JsonProperty("selfie_capture_id") String selfie_capture_id, @JsonProperty("status") String status, @JsonProperty("next_step") String next_step) {

    }

    public record VerificationSessionLivenessResponse(@JsonProperty("liveness_check_id") String liveness_check_id, @JsonProperty("status") String status) {

    }

    public record VerificationSessionLivenessChallengeResponse(@JsonProperty("challenge_id") String challenge_id, @JsonProperty("actions") List<String> actions, @JsonProperty("expires_at") String expires_at, @JsonProperty("expires_in") Integer expires_in) {

    }

    public record VerificationSessionStatusResponse(@JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("current_step") String current_step, @JsonProperty("message") String message, @JsonProperty("withdrawal_available") Boolean withdrawal_available, @JsonProperty("evidence") JsonNode evidence) {

    }

    public record VerificationMobileHandoffResponse(@JsonProperty("handoff_url") String handoff_url, @JsonProperty("expires_at") String expires_at) {

    }

    public record VerificationSummary(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("external_reference") String external_reference, @JsonProperty("subject") JsonNode subject, @JsonProperty("policy") JsonNode policy, @JsonProperty("created_at") String created_at, @JsonProperty("completed_at") String completed_at) {

    }

    public record VerificationDetail(@JsonProperty("id") String id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("policy") JsonNode policy, @JsonProperty("workflow") JsonNode workflow, @JsonProperty("external_reference") String external_reference, @JsonProperty("verification_subject") JsonNode verification_subject, @JsonProperty("checks") JsonNode checks, @JsonProperty("risk_assessment") JsonNode risk_assessment, @JsonProperty("document_classification") JsonNode document_classification, @JsonProperty("evidence_report") JsonNode evidence_report, @JsonProperty("decision") JsonNode decision, @JsonProperty("created_at") String created_at, @JsonProperty("completed_at") String completed_at, @JsonProperty("expires_at") String expires_at) {

    }

    public enum SandboxSimulationRequestScenario {
        Approved("approved"), Declined("declined"), Review("review"), Timeout("timeout"), ProviderError("provider_error");

        private final String value;
        SandboxSimulationRequestScenario(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static SandboxSimulationRequestScenario fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (SandboxSimulationRequestScenario member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record SandboxSimulationRequest(@JsonProperty("scenario") SandboxSimulationRequestScenario scenario) {

    }

    public enum SandboxSimulationMarkerScenario {
        Approved("approved"), Declined("declined"), Review("review"), Timeout("timeout"), ProviderError("provider_error");

        private final String value;
        SandboxSimulationMarkerScenario(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static SandboxSimulationMarkerScenario fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (SandboxSimulationMarkerScenario member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record SandboxSimulationMarker(@JsonProperty("scenario") SandboxSimulationMarkerScenario scenario, @JsonProperty("version") Integer version) {

    }

    public record VerificationResult(@JsonProperty("simulation") SandboxSimulationMarker simulation, @JsonProperty("schema_version") String schema_version, @JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("decision") JsonNode decision, @JsonProperty("policy") JsonNode policy, @JsonProperty("workflow") JsonNode workflow, @JsonProperty("check_provenance") List<JsonNode> check_provenance, @JsonProperty("timestamps") JsonNode timestamps) {

    }

    public record CursorPagination(@JsonProperty("limit") Integer limit, @JsonProperty("next_cursor") String next_cursor, @JsonProperty("has_more") Boolean has_more) {

    }

    public record PagePagination(@JsonProperty("page") Integer page, @JsonProperty("page_size") Integer page_size, @JsonProperty("total") Integer total, @JsonProperty("total_pages") Integer total_pages) {

    }

    public record AuditEvent(@JsonProperty("id") String id, @JsonProperty("actor_type") String actor_type, @JsonProperty("actor_id") String actor_id, @JsonProperty("action") String action, @JsonProperty("action_label") String action_label, @JsonProperty("actor_display_name") String actor_display_name, @JsonProperty("target_type") String target_type, @JsonProperty("target_id") String target_id, @JsonProperty("target_label") String target_label, @JsonProperty("ip_address") String ip_address, @JsonProperty("user_agent") String user_agent, @JsonProperty("metadata") JsonNode metadata, @JsonProperty("created_at") String created_at) {

    }

    public record EvidenceReport(@JsonProperty("verification_id") String verification_id, @JsonProperty("storage_key") String storage_key, @JsonProperty("download_url") String download_url, @JsonProperty("pdf_storage_key") String pdf_storage_key, @JsonProperty("pdf_download_url") String pdf_download_url) {

    }

    public enum PortalUploadCreateRequestCaptureMethod {
        Camera("camera"), LiveRecording("live_recording"), File("file"), Unreported("unreported");

        private final String value;
        PortalUploadCreateRequestCaptureMethod(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PortalUploadCreateRequestCaptureMethod fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PortalUploadCreateRequestCaptureMethod member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum PortalUploadCreateRequestPurpose {
        DocumentCapture("document_capture"), SelfieCapture("selfie_capture"), LivenessCapture("liveness_capture");

        private final String value;
        PortalUploadCreateRequestPurpose(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PortalUploadCreateRequestPurpose fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PortalUploadCreateRequestPurpose member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record PortalUploadCreateRequest(@JsonProperty("capture_method") PortalUploadCreateRequestCaptureMethod capture_method, @JsonProperty("purpose") PortalUploadCreateRequestPurpose purpose, @JsonProperty("mime_type") String mime_type, @JsonProperty("file_size_bytes") Integer file_size_bytes) {

    }

    public record PortalUploadCreateResponse(@JsonProperty("upload_id") String upload_id, @JsonProperty("upload_url") String upload_url, @JsonProperty("upload_headers") JsonNode upload_headers, @JsonProperty("upload_transfer_path") String upload_transfer_path, @JsonProperty("upload_complete_path") String upload_complete_path, @JsonProperty("expires_at") String expires_at) {

    }

    public record PortalUploadTransferResponse(@JsonProperty("upload_id") String upload_id) {

    }

    public record OrganizationProfile(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("industry") String industry, @JsonProperty("status") String status, @JsonProperty("tenant_id") String tenant_id, @JsonProperty("tenant_name") String tenant_name, @JsonProperty("tenant_status") String tenant_status, @JsonProperty("default_country_profile_id") String default_country_profile_id, @JsonProperty("default_jurisdiction_id") String default_jurisdiction_id, @JsonProperty("settings") JsonNode settings, @JsonProperty("sandbox_usage") JsonNode sandbox_usage, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public enum OrganizationBrandingAssetUploadRequestAssetType {
        Logo("logo"), BrandingImage("branding_image");

        private final String value;
        OrganizationBrandingAssetUploadRequestAssetType(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static OrganizationBrandingAssetUploadRequestAssetType fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (OrganizationBrandingAssetUploadRequestAssetType member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record OrganizationBrandingAssetUploadRequest(@JsonProperty("asset_type") OrganizationBrandingAssetUploadRequestAssetType asset_type, @JsonProperty("filename") String filename, @JsonProperty("mime_type") String mime_type) {

    }

    public record OrganizationBrandingAssetUploadResponse(@JsonProperty("asset_type") String asset_type, @JsonProperty("storage_key") String storage_key, @JsonProperty("bucket_name") String bucket_name, @JsonProperty("upload_url") String upload_url, @JsonProperty("asset_url") String asset_url) {

    }

    public record OrganizationSupportingDocumentUploadRequest(@JsonProperty("filename") String filename, @JsonProperty("mime_type") String mime_type, @JsonProperty("file_size_bytes") Integer file_size_bytes) {

    }

    public record OrganizationSupportingDocumentUploadResponse(@JsonProperty("document_id") String document_id, @JsonProperty("filename") String filename, @JsonProperty("file_size_bytes") Integer file_size_bytes, @JsonProperty("status") String status, @JsonProperty("storage_key") String storage_key, @JsonProperty("download_url") String download_url, @JsonProperty("upload_url") String upload_url) {

    }

    public record OrganizationSupportingDocumentCompleteResponse(@JsonProperty("document_id") String document_id, @JsonProperty("status") String status) {

    }

    public record OrganizationSupportingDocumentDeleteResponse(@JsonProperty("document_id") String document_id, @JsonProperty("deleted") Boolean deleted) {

    }

    public enum ProjectSummaryEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProjectSummaryEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProjectSummaryEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProjectSummaryEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProjectSummary(@JsonProperty("id") String id, @JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("environment") ProjectSummaryEnvironment environment, @JsonProperty("status") String status, @JsonProperty("allowed_origins") List<String> allowed_origins, @JsonProperty("is_default") Boolean is_default, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public enum ProjectCreateRequestEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProjectCreateRequestEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProjectCreateRequestEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProjectCreateRequestEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProjectCreateRequest(@JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("environment") ProjectCreateRequestEnvironment environment, @JsonProperty("allowed_origins") List<String> allowed_origins) {

    }

    public enum ProjectUpdateRequestEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProjectUpdateRequestEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProjectUpdateRequestEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProjectUpdateRequestEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProjectUpdateRequest(@JsonProperty("name") String name, @JsonProperty("slug") String slug, @JsonProperty("environment") ProjectUpdateRequestEnvironment environment, @JsonProperty("allowed_origins") List<String> allowed_origins) {

    }

    public record APIClientSummary(@JsonProperty("public_id") String public_id, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("client_id") String client_id, @JsonProperty("status") String status, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute, @JsonProperty("last_used_at") String last_used_at, @JsonProperty("client_secret_overlap_expires_at") String client_secret_overlap_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public record APIClientCreateRequest(@JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute) {

    }

    public record APIClientCreateResponse(@JsonProperty("public_id") String public_id, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("client_id") String client_id, @JsonProperty("status") String status, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute, @JsonProperty("last_used_at") String last_used_at, @JsonProperty("client_secret_overlap_expires_at") String client_secret_overlap_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at, @JsonProperty("client_secret") String client_secret) {

    }

    public record APIClientActionResponse(@JsonProperty("public_id") String public_id, @JsonProperty("tenant_public_id") String tenant_public_id, @JsonProperty("project_id") String project_id, @JsonProperty("name") String name, @JsonProperty("client_id") String client_id, @JsonProperty("status") String status, @JsonProperty("scopes") List<String> scopes, @JsonProperty("allowed_networks") List<String> allowed_networks, @JsonProperty("rate_limit_per_minute") Integer rate_limit_per_minute, @JsonProperty("last_used_at") String last_used_at, @JsonProperty("client_secret_overlap_expires_at") String client_secret_overlap_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at, @JsonProperty("client_secret") String client_secret) {

    }

    public record WebhookEndpointSummary(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("url") String url, @JsonProperty("description") String description, @JsonProperty("events") List<String> events, @JsonProperty("status") String status, @JsonProperty("signing_secret_version") Integer signing_secret_version, @JsonProperty("previous_secret_expires_at") String previous_secret_expires_at, @JsonProperty("created_at") String created_at, @JsonProperty("updated_at") String updated_at) {

    }

    public record WebhookEndpointCreateRequest(@JsonProperty("project_id") String project_id, @JsonProperty("url") String url, @JsonProperty("description") String description, @JsonProperty("events") List<String> events) {

    }

    public record WebhookEndpointCreateResponse(@JsonProperty("id") String id, @JsonProperty("secret") String secret, @JsonProperty("status") String status) {

    }

    public record WebhookEndpointTestResponse(@JsonProperty("queued") Boolean queued) {

    }

    public record ManualReviewSummary(@JsonProperty("verification_id") String verification_id, @JsonProperty("status") String status, @JsonProperty("purpose") String purpose, @JsonProperty("subject") JsonNode subject, @JsonProperty("risk_level") String risk_level, @JsonProperty("document_classification") JsonNode document_classification, @JsonProperty("created_at") String created_at) {

    }

    public enum ManualReviewDecisionRequestDecision {
        Verified("verified"), Rejected("rejected"), Failed("failed");

        private final String value;
        ManualReviewDecisionRequestDecision(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ManualReviewDecisionRequestDecision fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ManualReviewDecisionRequestDecision member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ManualReviewDecisionRequest(@JsonProperty("decision") ManualReviewDecisionRequestDecision decision, @JsonProperty("reason_code") String reason_code, @JsonProperty("reason_detail") String reason_detail) {

    }

    public record ManualReviewDecisionResponse(@JsonProperty("verification_id") String verification_id, @JsonProperty("decision") String decision, @JsonProperty("decision_type") String decision_type, @JsonProperty("decided_at") String decided_at) {

    }

    public record ManualReviewPendingDecisionResponse(@JsonProperty("verification_id") String verification_id, @JsonProperty("decision") String decision, @JsonProperty("approval_status") String approval_status, @JsonProperty("approval_required") Boolean approval_required) {

    }

    public enum ManualReviewApprovalRequestDecision {
        Verified("verified"), Rejected("rejected"), Failed("failed");

        private final String value;
        ManualReviewApprovalRequestDecision(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ManualReviewApprovalRequestDecision fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ManualReviewApprovalRequestDecision member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ManualReviewApprovalRequest(@JsonProperty("decision") ManualReviewApprovalRequestDecision decision, @JsonProperty("reason_code") String reason_code, @JsonProperty("reason_detail") String reason_detail) {

    }

    public record ManualReviewApprovalResponse(@JsonProperty("verification_id") String verification_id, @JsonProperty("decision") String decision, @JsonProperty("approval_status") String approval_status) {

    }

    public enum GovernedSchemaCreateKind {
        Evidence("evidence"), Claim("claim");

        private final String value;
        GovernedSchemaCreateKind(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static GovernedSchemaCreateKind fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (GovernedSchemaCreateKind member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record GovernedSchemaCreate(@JsonProperty("name") String name, @JsonProperty("version") Integer version, @JsonProperty("kind") GovernedSchemaCreateKind kind, @JsonProperty("definition") JsonNode definition, @JsonProperty("disclosure_fields") List<String> disclosure_fields) {

    }

    public enum PurposeAuthorizationCreateLegalBasis {
        Consent("consent"), Contract("contract"), LegalObligation("legal_obligation"), LegitimateInterest("legitimate_interest");

        private final String value;
        PurposeAuthorizationCreateLegalBasis(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PurposeAuthorizationCreateLegalBasis fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PurposeAuthorizationCreateLegalBasis member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record PurposeAuthorizationCreate(@JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("purpose") String purpose, @JsonProperty("legal_basis") PurposeAuthorizationCreateLegalBasis legal_basis, @JsonProperty("justification") JsonNode justification, @JsonProperty("operations") List<String> operations, @JsonProperty("valid_from") String valid_from, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("consent_record_id") String consent_record_id, @JsonProperty("reuse_from_ids") List<String> reuse_from_ids) {

    }

    public enum EvidenceCreateEvidenceType {
        Submitted("submitted"), Provider("provider"), System("system"), Human("human"), Authoritative("authoritative");

        private final String value;
        EvidenceCreateEvidenceType(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static EvidenceCreateEvidenceType fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (EvidenceCreateEvidenceType member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record EvidenceCreate(@JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("authorization_id") String authorization_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("evidence_type") EvidenceCreateEvidenceType evidence_type, @JsonProperty("operation_reference") String operation_reference, @JsonProperty("payload") JsonNode payload, @JsonProperty("provenance") JsonNode provenance, @JsonProperty("observed_at") String observed_at, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("source_ids") List<String> source_ids, @JsonProperty("supersedes_id") String supersedes_id, @JsonProperty("verification_id") String verification_id, @JsonProperty("source_check_id") String source_check_id) {

    }

    public record GovernedReason(@JsonProperty("reason") String reason) {

    }

    public record GovernedEmptyAction() {

    }

    public record ResourceLegalHoldCreate(@JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("reason") JsonNode reason, @JsonProperty("expires_at") String expires_at) {

    }

    public enum ClaimCreateRuleName {
        Empty(""), Copy("copy"), Field("field"), NormalizeName("normalize_name"), IsoDate("iso_date"), AgeOver("age_over"), DocumentCurrent("document_current"), ExactCorroboration("exact_corroboration");

        private final String value;
        ClaimCreateRuleName(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ClaimCreateRuleName fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ClaimCreateRuleName member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ClaimCreate(@JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("authorization_id") String authorization_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("observed_at") String observed_at, @JsonProperty("valid_from") String valid_from, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("evidence_ids") List<String> evidence_ids, @JsonProperty("claim_ids") List<String> claim_ids, @JsonProperty("value") JsonNode value, @JsonProperty("confidence") Double confidence, @JsonProperty("rule_name") ClaimCreateRuleName rule_name, @JsonProperty("rule_version") Integer rule_version, @JsonProperty("rule_parameters") JsonNode rule_parameters, @JsonProperty("supersedes_id") String supersedes_id) {

    }

    public record ClaimReusePolicyCreate(@JsonProperty("project_id") String project_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("name") String name, @JsonProperty("version") Integer version, @JsonProperty("purposes") List<String> purposes, @JsonProperty("accepted_classes") List<String> accepted_classes, @JsonProperty("fields") List<String> fields, @JsonProperty("max_age_seconds") Integer max_age_seconds, @JsonProperty("minimum_confidence") Double minimum_confidence) {

    }

    public enum ClaimConflictReviewOutcome {
        Selected("selected"), Disputed("disputed"), MoreEvidence("more_evidence");

        private final String value;
        ClaimConflictReviewOutcome(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ClaimConflictReviewOutcome fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ClaimConflictReviewOutcome member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ClaimConflictReview(@JsonProperty("project_id") String project_id, @JsonProperty("purpose") String purpose, @JsonProperty("selected_claim_id") String selected_claim_id, @JsonProperty("outcome") ClaimConflictReviewOutcome outcome, @JsonProperty("reason") JsonNode reason) {

    }

    public record ClaimRevoke(@JsonProperty("project_id") String project_id, @JsonProperty("purpose") String purpose, @JsonProperty("reason") String reason) {

    }

    public record ClaimEvaluation(@JsonProperty("project_id") String project_id, @JsonProperty("purpose") String purpose, @JsonProperty("policy_id") String policy_id) {

    }

    public record ClaimDisclosureCreate(@JsonProperty("project_id") String project_id, @JsonProperty("authorization_id") String authorization_id, @JsonProperty("audience_id") String audience_id, @JsonProperty("selections") List<JsonNode> selections, @JsonProperty("lifetime_seconds") Integer lifetime_seconds, @JsonProperty("max_redemptions") Integer max_redemptions) {

    }

    public record GovernedProjectAction(@JsonProperty("project_id") String project_id) {

    }

    public enum ProviderCertificationCreateAssuranceLevel {
        Conformance("conformance"), Assured("assured");

        private final String value;
        ProviderCertificationCreateAssuranceLevel(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationCreateAssuranceLevel fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationCreateAssuranceLevel member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderCertificationCreate(@JsonProperty("configuration_id") String configuration_id, @JsonProperty("capability") String capability, @JsonProperty("report") JsonNode report, @JsonProperty("assurance_level") ProviderCertificationCreateAssuranceLevel assurance_level, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after) {

    }

    public record ProviderCertificationRevoke(@JsonProperty("reason") String reason) {

    }

    public record ProviderOperationCancel(@JsonProperty("project_id") String project_id, @JsonProperty("reason") String reason) {

    }

    public enum GovernedSchemaKind {
        Evidence("evidence"), Claim("claim");

        private final String value;
        GovernedSchemaKind(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static GovernedSchemaKind fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (GovernedSchemaKind member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record GovernedSchema(@JsonProperty("name") String name, @JsonProperty("version") Integer version, @JsonProperty("kind") GovernedSchemaKind kind, @JsonProperty("definition") JsonNode definition, @JsonProperty("disclosure_fields") List<String> disclosure_fields, @JsonProperty("id") String id, @JsonProperty("retired_at") String retired_at) {

    }

    public enum PurposeAuthorizationLegalBasis {
        Consent("consent"), Contract("contract"), LegalObligation("legal_obligation"), LegitimateInterest("legitimate_interest");

        private final String value;
        PurposeAuthorizationLegalBasis(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PurposeAuthorizationLegalBasis fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PurposeAuthorizationLegalBasis member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record PurposeAuthorization(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("purpose") String purpose, @JsonProperty("legal_basis") PurposeAuthorizationLegalBasis legal_basis, @JsonProperty("operations") List<String> operations, @JsonProperty("approved_at") String approved_at, @JsonProperty("valid_from") String valid_from, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("revoked_at") String revoked_at, @JsonProperty("reuse_from_ids") List<String> reuse_from_ids) {

    }

    public enum PurposeAuthorizationDetailLegalBasis {
        Consent("consent"), Contract("contract"), LegalObligation("legal_obligation"), LegitimateInterest("legitimate_interest");

        private final String value;
        PurposeAuthorizationDetailLegalBasis(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static PurposeAuthorizationDetailLegalBasis fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (PurposeAuthorizationDetailLegalBasis member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record PurposeAuthorizationDetail(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("purpose") String purpose, @JsonProperty("legal_basis") PurposeAuthorizationDetailLegalBasis legal_basis, @JsonProperty("operations") List<String> operations, @JsonProperty("approved_at") String approved_at, @JsonProperty("valid_from") String valid_from, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("revoked_at") String revoked_at, @JsonProperty("reuse_from_ids") List<String> reuse_from_ids, @JsonProperty("justification") JsonNode justification, @JsonProperty("proposed_by_id") String proposed_by_id, @JsonProperty("approved_by_id") String approved_by_id, @JsonProperty("consent_record_id") String consent_record_id) {

    }

    public enum ResourceLegalHoldScope {
        SubjectProjectLineage("subject_project_lineage");

        private final String value;
        ResourceLegalHoldScope(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ResourceLegalHoldScope fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ResourceLegalHoldScope member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ResourceLegalHold(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("created_at") String created_at, @JsonProperty("expires_at") String expires_at, @JsonProperty("released_at") String released_at, @JsonProperty("scope") ResourceLegalHoldScope scope) {

    }

    public enum ResourceLegalHoldDetailScope {
        SubjectProjectLineage("subject_project_lineage");

        private final String value;
        ResourceLegalHoldDetailScope(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ResourceLegalHoldDetailScope fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ResourceLegalHoldDetailScope member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ResourceLegalHoldDetail(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("created_at") String created_at, @JsonProperty("expires_at") String expires_at, @JsonProperty("released_at") String released_at, @JsonProperty("scope") ResourceLegalHoldDetailScope scope, @JsonProperty("reason") JsonNode reason) {

    }

    public enum GovernedEvidenceEvidenceType {
        Submitted("submitted"), Provider("provider"), System("system"), Human("human"), Authoritative("authoritative");

        private final String value;
        GovernedEvidenceEvidenceType(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static GovernedEvidenceEvidenceType fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (GovernedEvidenceEvidenceType member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum GovernedEvidenceOrigin {
        PersistedProviderCheck("persisted_provider_check"), CallerAsserted("caller_asserted");

        private final String value;
        GovernedEvidenceOrigin(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static GovernedEvidenceOrigin fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (GovernedEvidenceOrigin member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record GovernedEvidence(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("schema_version") Integer schema_version, @JsonProperty("purpose") String purpose, @JsonProperty("status") String status, @JsonProperty("observed_at") String observed_at, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("source_evidence_ids") List<String> source_evidence_ids, @JsonProperty("evidence_type") GovernedEvidenceEvidenceType evidence_type, @JsonProperty("origin") GovernedEvidenceOrigin origin, @JsonProperty("supersedes_id") String supersedes_id, @JsonProperty("payload") JsonNode payload, @JsonProperty("provenance") JsonNode provenance) {

    }

    public enum GovernedClaimClaimClass {
        Candidate("candidate"), Normalized("normalized"), Corroborated("corroborated"), Derived("derived"), Reviewed("reviewed");

        private final String value;
        GovernedClaimClaimClass(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static GovernedClaimClaimClass fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (GovernedClaimClaimClass member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record GovernedClaim(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("subject_id") String subject_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("schema_version") Integer schema_version, @JsonProperty("purpose") String purpose, @JsonProperty("status") String status, @JsonProperty("observed_at") String observed_at, @JsonProperty("valid_until") String valid_until, @JsonProperty("delete_after") String delete_after, @JsonProperty("source_evidence_ids") List<String> source_evidence_ids, @JsonProperty("claim_class") GovernedClaimClaimClass claim_class, @JsonProperty("confidence") String confidence, @JsonProperty("valid_from") String valid_from, @JsonProperty("rule") JsonNode rule, @JsonProperty("source_claim_ids") List<String> source_claim_ids, @JsonProperty("value") JsonNode value) {

    }

    public record GovernedReceipt(@JsonProperty("status") String status, @JsonProperty("id") String id, @JsonProperty("schema_id") String schema_id, @JsonProperty("created_at") String created_at) {

    }

    public record GovernedStateReceipt(@JsonProperty("id") String id, @JsonProperty("status") String status) {

    }

    public record GovernedLineage(@JsonProperty("root_id") String root_id, @JsonProperty("nodes") List<JsonNode> nodes, @JsonProperty("edges") List<JsonNode> edges, @JsonProperty("truncated") Boolean truncated) {

    }

    public record ClaimReusePolicy(@JsonProperty("id") String id, @JsonProperty("project_id") String project_id, @JsonProperty("schema_id") String schema_id, @JsonProperty("name") String name, @JsonProperty("version") Integer version, @JsonProperty("purposes") List<String> purposes, @JsonProperty("accepted_classes") List<String> accepted_classes, @JsonProperty("fields") List<String> fields, @JsonProperty("max_age_seconds") Integer max_age_seconds, @JsonProperty("minimum_confidence") String minimum_confidence, @JsonProperty("approved_at") String approved_at, @JsonProperty("retired_at") String retired_at) {

    }

    public enum ClaimReviewReceiptOutcome {
        Selected("selected"), Disputed("disputed"), MoreEvidence("more_evidence");

        private final String value;
        ClaimReviewReceiptOutcome(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ClaimReviewReceiptOutcome fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ClaimReviewReceiptOutcome member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ClaimReviewReceipt(@JsonProperty("id") String id, @JsonProperty("outcome") ClaimReviewReceiptOutcome outcome, @JsonProperty("selected_claim_id") String selected_claim_id) {

    }

    public record ClaimPolicyEvaluation(@JsonProperty("satisfied") Boolean satisfied, @JsonProperty("reason_codes") List<String> reason_codes, @JsonProperty("claim_id") String claim_id, @JsonProperty("policy_id") String policy_id, @JsonProperty("usable_until") String usable_until, @JsonProperty("claim_class") String claim_class, @JsonProperty("fresh_until") String fresh_until) {

    }

    public record ClaimDisclosureReceipt(@JsonProperty("id") String id, @JsonProperty("audience_id") String audience_id, @JsonProperty("purpose") String purpose, @JsonProperty("expires_at") String expires_at, @JsonProperty("max_redemptions") Integer max_redemptions, @JsonProperty("token") String token, @JsonProperty("token_available") Boolean token_available) {

    }

    public record ClaimDisclosureRedemption(@JsonProperty("id") String id, @JsonProperty("audience_id") String audience_id, @JsonProperty("purpose") String purpose, @JsonProperty("claims") List<JsonNode> claims, @JsonProperty("expires_at") String expires_at) {

    }

    public record ClaimDisclosureRevocation(@JsonProperty("id") String id, @JsonProperty("revoked") Boolean revoked) {

    }

    public enum ProviderCertificationEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProviderCertificationEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationContractVersion {
        Value1("1");

        private final String value;
        ProviderCertificationContractVersion(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationContractVersion fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationContractVersion member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationOperationContract {
        Sync("sync"), IcProviderOperationsV1("ic-provider-operations-v1");

        private final String value;
        ProviderCertificationOperationContract(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationOperationContract fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationOperationContract member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationAssuranceLevel {
        Conformance("conformance"), Assured("assured");

        private final String value;
        ProviderCertificationAssuranceLevel(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationAssuranceLevel fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationAssuranceLevel member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderCertification(@JsonProperty("id") String id, @JsonProperty("configuration_id") String configuration_id, @JsonProperty("environment") ProviderCertificationEnvironment environment, @JsonProperty("capability") String capability, @JsonProperty("contract_version") ProviderCertificationContractVersion contract_version, @JsonProperty("operation_contract") ProviderCertificationOperationContract operation_contract, @JsonProperty("suite_version") String suite_version, @JsonProperty("report_sha256") String report_sha256, @JsonProperty("assurance_level") ProviderCertificationAssuranceLevel assurance_level, @JsonProperty("approved_at") String approved_at, @JsonProperty("valid_until") String valid_until, @JsonProperty("revoked") Boolean revoked, @JsonProperty("delete_after") String delete_after, @JsonProperty("proposed_by_id") String proposed_by_id, @JsonProperty("approved_by_id") String approved_by_id) {

    }

    public enum ProviderCertificationDetailEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProviderCertificationDetailEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationDetailEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationDetailEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationDetailContractVersion {
        Value1("1");

        private final String value;
        ProviderCertificationDetailContractVersion(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationDetailContractVersion fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationDetailContractVersion member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationDetailOperationContract {
        Sync("sync"), IcProviderOperationsV1("ic-provider-operations-v1");

        private final String value;
        ProviderCertificationDetailOperationContract(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationDetailOperationContract fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationDetailOperationContract member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderCertificationDetailAssuranceLevel {
        Conformance("conformance"), Assured("assured");

        private final String value;
        ProviderCertificationDetailAssuranceLevel(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderCertificationDetailAssuranceLevel fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderCertificationDetailAssuranceLevel member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderCertificationDetail(@JsonProperty("id") String id, @JsonProperty("configuration_id") String configuration_id, @JsonProperty("environment") ProviderCertificationDetailEnvironment environment, @JsonProperty("capability") String capability, @JsonProperty("contract_version") ProviderCertificationDetailContractVersion contract_version, @JsonProperty("operation_contract") ProviderCertificationDetailOperationContract operation_contract, @JsonProperty("suite_version") String suite_version, @JsonProperty("report_sha256") String report_sha256, @JsonProperty("assurance_level") ProviderCertificationDetailAssuranceLevel assurance_level, @JsonProperty("approved_at") String approved_at, @JsonProperty("valid_until") String valid_until, @JsonProperty("revoked") Boolean revoked, @JsonProperty("report") JsonNode report, @JsonProperty("delete_after") String delete_after, @JsonProperty("proposed_by_id") String proposed_by_id, @JsonProperty("approved_by_id") String approved_by_id) {

    }

    public record ProviderCertificationScope(@JsonProperty("configuration_id") String configuration_id, @JsonProperty("environment") String environment, @JsonProperty("capability") String capability, @JsonProperty("contract_version") String contract_version, @JsonProperty("operation_contract") String operation_contract, @JsonProperty("configuration_digest") String configuration_digest, @JsonProperty("manifest_sha256") String manifest_sha256, @JsonProperty("suite_version") String suite_version, @JsonProperty("required_cases") List<String> required_cases) {

    }

    public enum ProviderOperationStatus {
        Created("created"), Pending("pending"), Completed("completed"), Failed("failed"), Cancelled("cancelled"), Expired("expired");

        private final String value;
        ProviderOperationStatus(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationStatus fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationStatus member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderOperationRemoteAction {
        Cancel("cancel"), Delete("delete");

        private final String value;
        ProviderOperationRemoteAction(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationRemoteAction fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationRemoteAction member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderOperationRemoteActionStatus {
        Pending("pending"), Acknowledged("acknowledged"), Expired("expired");

        private final String value;
        ProviderOperationRemoteActionStatus(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationRemoteActionStatus fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationRemoteActionStatus member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderOperation(@JsonProperty("id") String id, @JsonProperty("status") ProviderOperationStatus status, @JsonProperty("configuration_id") String configuration_id, @JsonProperty("check_id") String check_id, @JsonProperty("capability") String capability, @JsonProperty("deadline") String deadline, @JsonProperty("completed_at") String completed_at, @JsonProperty("verification_id") String verification_id, @JsonProperty("delete_after") String delete_after, @JsonProperty("invalidation_reason") String invalidation_reason, @JsonProperty("remote_action") ProviderOperationRemoteAction remote_action, @JsonProperty("remote_action_status") ProviderOperationRemoteActionStatus remote_action_status, @JsonProperty("remote_requested_at") String remote_requested_at, @JsonProperty("remote_attempted_at") String remote_attempted_at) {

    }

    public enum ProviderOperationBindingOperationContract {
        IcProviderOperationsV1("ic-provider-operations-v1");

        private final String value;
        ProviderOperationBindingOperationContract(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationBindingOperationContract fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationBindingOperationContract member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderOperationBindingEnvironment {
        Sandbox("sandbox"), Production("production");

        private final String value;
        ProviderOperationBindingEnvironment(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationBindingEnvironment fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationBindingEnvironment member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public enum ProviderOperationBindingContractVersion {
        Value1("1");

        private final String value;
        ProviderOperationBindingContractVersion(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationBindingContractVersion fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationBindingContractVersion member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderOperationBinding(@JsonProperty("operation_contract") ProviderOperationBindingOperationContract operation_contract, @JsonProperty("operation_id") String operation_id, @JsonProperty("configuration_id") String configuration_id, @JsonProperty("tenant_id") String tenant_id, @JsonProperty("project_id") String project_id, @JsonProperty("environment") ProviderOperationBindingEnvironment environment, @JsonProperty("capability") String capability, @JsonProperty("contract_version") ProviderOperationBindingContractVersion contract_version, @JsonProperty("request_sha256") String request_sha256, @JsonProperty("lease_generation") Integer lease_generation, @JsonProperty("deadline") String deadline, @JsonProperty("callback_path") String callback_path, @JsonProperty("lease_token") String lease_token) {

    }

    public enum ProviderOperationCallbackStatus {
        Pending("pending"), Completed("completed"), Failed("failed");

        private final String value;
        ProviderOperationCallbackStatus(String value) { this.value = value; }
        @JsonValue
        public String value() { return value; }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static ProviderOperationCallbackStatus fromValue(JsonNode input) {
            if (input != null && input.isTextual()) for (ProviderOperationCallbackStatus member : values()) if (member.value.equals(input.textValue())) return member;
            throw new IllegalArgumentException("Unsupported contract enum value.");
        }
    }

    public record ProviderOperationCallback(@JsonProperty("binding") ProviderOperationBinding binding, @JsonProperty("status") ProviderOperationCallbackStatus status, @JsonProperty("result") JsonNode result, @JsonProperty("retry_after_seconds") Integer retry_after_seconds) {

    }

    public record GovernedSchemaPage(@JsonProperty("results") List<GovernedSchema> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record PurposeAuthorizationPage(@JsonProperty("results") List<PurposeAuthorization> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record ResourceLegalHoldPage(@JsonProperty("results") List<ResourceLegalHold> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record GovernedEvidencePage(@JsonProperty("results") List<GovernedEvidence> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record GovernedClaimPage(@JsonProperty("results") List<GovernedClaim> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record ClaimReusePolicyPage(@JsonProperty("results") List<ClaimReusePolicy> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record ProviderCertificationPage(@JsonProperty("results") List<ProviderCertification> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

    public record ProviderOperationPage(@JsonProperty("results") List<ProviderOperation> results, @JsonProperty("pagination") CursorPagination pagination) {

    }

}

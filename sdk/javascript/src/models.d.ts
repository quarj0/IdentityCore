// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.

export interface Error {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorEnvelope {
  success: false;
  error: Error;
  request_id: string;
}

export interface WorkflowSummary {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  status: string;
  steps: Array<string>;
  settings: Record<string, unknown>;
  current_version: number;
  source_template_id?: string | null;
  source_template_version?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Policy {
  id: string;
  name: string;
  description?: string;
  version: number;
  status: "draft" | "active" | "archived";
  required_document_types: Array<"national_id" | "passport" | "driver_license" | "health_id" | "voter_id">;
  required_liveness_level: "passive" | "active";
  face_match_threshold: number;
  manual_review_threshold: number;
  review_reason_rules?: Record<string, unknown>;
  reuse_rules?: Record<string, unknown>;
  document_consistency_rules?: Record<string, unknown>;
  document_authenticity_required?: boolean;
  document_authenticity_min_confidence?: number;
  external_risk_enabled?: boolean;
  external_risk_failure_action?: "manual_review" | "ignore";
  external_risk_review_threshold?: number;
  maker_checker_required: boolean;
  verification_expiry_minutes: number;
  media_retention_days: number;
  metadata_retention_days: number;
  created_at: string;
  updated_at: string;
}

export interface VerificationSubjectInput {
  full_name?: string;
  email?: string;
  phone_number?: string;
  date_of_birth?: string;
  metadata?: Record<string, unknown>;
}

export interface VerificationCreateRequest {
  external_reference?: string;
  purpose: string;
  policy_id: string;
  project_id?: string;
  verification_subject: VerificationSubjectInput;
  redirect_url?: string;
  metadata?: Record<string, unknown>;
}

export interface PlatformUserLoginRequest {
  email: string;
  password: string;
}

export interface PlatformUser {
  public_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  status: string;
  tenant_public_id: string | null;
  tenant_name: string | null;
  tenant_status: string | null;
  is_platform_admin: boolean;
  mfa_enabled: boolean;
  roles: Array<string>;
  notification_preferences: Record<string, unknown>;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlatformUserMfaChallenge {
  mfa_required: true;
  mfa_enrollment_required: boolean;
  mfa_token: string;
}

export interface PlatformUserAuthentication {
  tokens: Record<string, unknown>;
  user: PlatformUser;
  recovery_codes?: Array<string>;
}

export interface PlatformUserMfaEnrollmentRequest {
  mfa_token: string;
}

export interface PlatformUserMfaCodeRequest {
  mfa_token: string;
  code: string;
}

export interface PlatformUserMfaEnrollment {
  secret: string;
  provisioning_uri: string;
}

export interface VerificationPolicyCreateRequest {
  project_id?: string;
  name: string;
  description?: string;
  consent_template_id?: string;
  default_locale?: string;
  supported_locales?: Array<string>;
  required_document_types: Array<"national_id" | "passport" | "driver_license" | "health_id" | "voter_id">;
  required_liveness_level: "passive" | "active";
  face_match_threshold: number;
  manual_review_threshold: number;
  review_reason_rules?: Record<string, unknown>;
  reuse_rules?: Record<string, unknown>;
  document_consistency_rules?: Record<string, unknown>;
  document_authenticity_required?: boolean;
  document_authenticity_min_confidence?: number;
  external_risk_enabled?: boolean;
  external_risk_failure_action?: "manual_review" | "ignore";
  external_risk_review_threshold?: number;
  maker_checker_required?: boolean;
  verification_expiry_minutes: number;
  media_retention_days: number;
  metadata_retention_days: number;
}

export interface VerificationPolicyCreateResponse {
  id: string;
  name: string;
  version: number;
  status: "draft";
}

export interface VerificationCreateResponse {
  id: string;
  status: string;
  verification_url: string;
  session_id: string;
  session_token?: string;
  expires_at: string;
}

export interface VerificationSessionConsentRequest {
  accepted: true;
  template_id?: string;
  version?: number;
  locale?: string;
  content_hash?: string;
}

export interface VerificationSessionDocumentRequest {
  document_type: string;
  country_code: string;
  captures: Array<Record<string, unknown>>;
}

export interface VerificationSessionSelfieRequest {
  capture_type: "image" | "video";
  upload_id: string;
}

export interface VerificationSessionLivenessRequest {
  liveness_type: "passive" | "active";
  selfie_capture_id: string;
  challenge_id?: string;
}

export interface VerificationMobileHandoffRedeemResponse {
  session_id: string;
  session_token: string;
  verification_id: string;
}

export interface VerificationSessionResponse {
  session_id: string;
  verification_id: string;
  status: string;
  organization: Record<string, unknown>;
  purpose: string;
  redirect_url: string;
  required_steps: Array<string>;
  workflow: Record<string, unknown>;
  locale: string;
  supported_locales: Array<string>;
  direction: "ltr" | "rtl";
  consent: Record<string, unknown>;
  document: Record<string, unknown>;
  available_documents: Array<Record<string, unknown>>;
  available_countries: Array<Record<string, unknown>>;
  expires_at: string;
}

export interface VerificationSessionConsentResponse {
  consent_record_id: string;
  next_step: "document_capture";
}

export interface VerificationSessionDocumentResponse {
  identity_document_id: string;
  status: string;
  next_step: "document_processing";
}

export interface VerificationSessionSelfieResponse {
  selfie_capture_id: string;
  status: "processing";
  next_step: "liveness_check";
}

export interface VerificationSessionLivenessResponse {
  liveness_check_id: string;
  status: "processing";
}

export interface VerificationSessionLivenessChallengeResponse {
  challenge_id: string;
  actions: Array<"turn_left" | "turn_right" | "look_up" | "look_down">;
  expires_at: string;
  expires_in: number;
}

export interface VerificationSessionStatusResponse {
  verification_id: string;
  status: string;
  current_step: string;
  message: string;
  withdrawal_available?: boolean;
  evidence: Record<string, unknown>;
}

export interface VerificationMobileHandoffResponse {
  handoff_url: string;
  expires_at: string;
}

export interface VerificationSummary {
  id: string;
  status: string;
  purpose: string;
  external_reference: string;
  subject: Record<string, unknown>;
  policy: Record<string, unknown>;
  created_at: string;
  completed_at?: string | null;
}

export interface VerificationDetail {
  id: string;
  status: string;
  purpose: string;
  policy: Record<string, unknown>;
  workflow: Record<string, unknown>;
  external_reference: string;
  verification_subject: Record<string, unknown>;
  checks: Record<string, unknown>;
  risk_assessment: Record<string, unknown> | null;
  document_classification: Record<string, unknown> | null;
  evidence_report: Record<string, unknown> | null;
  decision: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
  expires_at: string;
}

export interface SandboxSimulationRequest {
  scenario: "approved" | "declined" | "review" | "timeout" | "provider_error";
}

export interface SandboxSimulationMarker {
  scenario: "approved" | "declined" | "review" | "timeout" | "provider_error";
  version: 1;
}

export interface VerificationResult {
  simulation?: SandboxSimulationMarker;
  schema_version: "1";
  verification_id: string;
  status: string;
  decision: Record<string, unknown> | null;
  policy: Record<string, unknown>;
  workflow: Record<string, unknown>;
  check_provenance: Array<Record<string, unknown>>;
  timestamps: Record<string, unknown>;
}

export interface CursorPagination {
  limit: number;
  next_cursor: string | null;
  has_more: boolean;
}

export interface PagePagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AuditEvent {
  id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  action_label: string;
  actor_display_name: string;
  target_type: string;
  target_id: string;
  target_label: string;
  ip_address: string | null;
  user_agent: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface EvidenceReport {
  verification_id: string;
  storage_key: string;
  download_url: string;
  pdf_storage_key: string;
  pdf_download_url: string;
}

export interface PortalUploadCreateRequest {
  capture_method?: "camera" | "live_recording" | "file" | "unreported";
  purpose: "document_capture" | "selfie_capture" | "liveness_capture";
  mime_type: string;
  file_size_bytes: number;
}

export interface PortalUploadCreateResponse {
  upload_id: string;
  upload_url: string;
  upload_headers: Record<string, unknown>;
  upload_transfer_path: string;
  upload_complete_path: string;
  expires_at: string;
}

export interface PortalUploadTransferResponse {
  upload_id: string;
}

export interface OrganizationProfile {
  id: string;
  name: string;
  slug: string;
  industry?: string;
  status: string;
  tenant_id?: string;
  tenant_name?: string;
  tenant_status?: string;
  default_country_profile_id?: string;
  default_jurisdiction_id?: string;
  settings: Record<string, unknown>;
  sandbox_usage: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface OrganizationBrandingAssetUploadRequest {
  asset_type: "logo" | "branding_image";
  filename: string;
  mime_type: string;
}

export interface OrganizationBrandingAssetUploadResponse {
  asset_type: string;
  storage_key: string;
  bucket_name: string;
  upload_url: string;
  asset_url: string;
}

export interface OrganizationSupportingDocumentUploadRequest {
  filename: string;
  mime_type: "application/pdf";
  file_size_bytes: number;
}

export interface OrganizationSupportingDocumentUploadResponse {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  status: string;
  storage_key: string;
  download_url: string;
  upload_url: string;
}

export interface OrganizationSupportingDocumentCompleteResponse {
  document_id: string;
  status: string;
}

export interface OrganizationSupportingDocumentDeleteResponse {
  document_id: string;
  deleted: boolean;
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  environment: "sandbox" | "production";
  status: string;
  allowed_origins: Array<string>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  name: string;
  slug?: string;
  environment?: "sandbox" | "production";
  allowed_origins?: Array<string>;
}

export interface ProjectUpdateRequest {
  name?: string;
  slug?: string;
  environment?: "sandbox" | "production";
  allowed_origins?: Array<string>;
}

export interface APIClientSummary {
  public_id: string;
  tenant_public_id: string;
  project_id?: string | null;
  name: string;
  client_id: string;
  status: string;
  scopes: Array<string>;
  allowed_networks: Array<string>;
  rate_limit_per_minute: number;
  last_used_at?: string | null;
  client_secret_overlap_expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface APIClientCreateRequest {
  project_id?: string;
  name: string;
  scopes: Array<"policies:read" | "verifications:create" | "verifications:read" | "verifications:write">;
  allowed_networks?: Array<string>;
  rate_limit_per_minute?: number;
}

export interface APIClientCreateResponse {
  public_id: string;
  tenant_public_id: string;
  project_id?: string | null;
  name: string;
  client_id: string;
  status: string;
  scopes: Array<string>;
  allowed_networks: Array<string>;
  rate_limit_per_minute: number;
  last_used_at?: string | null;
  client_secret_overlap_expires_at?: string | null;
  created_at: string;
  updated_at: string;
  client_secret: string;
}

export interface APIClientActionResponse {
  public_id: string;
  tenant_public_id: string;
  project_id?: string | null;
  name: string;
  client_id: string;
  status: string;
  scopes: Array<string>;
  allowed_networks: Array<string>;
  rate_limit_per_minute: number;
  last_used_at?: string | null;
  client_secret_overlap_expires_at?: string | null;
  created_at: string;
  updated_at: string;
  client_secret?: string;
}

export interface WebhookEndpointSummary {
  id: string;
  project_id?: string | null;
  url: string;
  description?: string;
  events: Array<"verification.created" | "verification.consent_accepted" | "verification.document_uploaded" | "verification.selfie_uploaded" | "verification.processing" | "verification.manual_review_required" | "verification.verified" | "verification.rejected" | "verification.failed" | "verification.expired" | "verification.cancelled">;
  status: string;
  signing_secret_version: number;
  previous_secret_expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WebhookEndpointCreateRequest {
  project_id?: string;
  url: string;
  description?: string;
  events: Array<"verification.created" | "verification.consent_accepted" | "verification.document_uploaded" | "verification.selfie_uploaded" | "verification.processing" | "verification.manual_review_required" | "verification.verified" | "verification.rejected" | "verification.failed" | "verification.expired" | "verification.cancelled">;
}

export interface WebhookEndpointCreateResponse {
  id: string;
  secret: string;
  status: string;
}

export interface WebhookEndpointTestResponse {
  queued: boolean;
}

export interface ManualReviewSummary {
  verification_id: string;
  status: string;
  purpose: string;
  subject: Record<string, unknown>;
  risk_level: string;
  document_classification?: Record<string, unknown> | null;
  created_at: string;
}

export interface ManualReviewDecisionRequest {
  decision: "verified" | "rejected" | "failed";
  reason_code: string;
  reason_detail?: string;
}

export interface ManualReviewDecisionResponse {
  verification_id: string;
  decision: string;
  decision_type: string;
  decided_at: string;
}

export interface ManualReviewPendingDecisionResponse {
  verification_id: string;
  decision: string;
  approval_status: "pending";
  approval_required: true;
}

export interface ManualReviewApprovalRequest {
  decision: "verified" | "rejected" | "failed";
  reason_code?: string;
  reason_detail?: string;
}

export interface ManualReviewApprovalResponse {
  verification_id: string;
  decision: string;
  approval_status: "approved";
}

export interface GovernedSchemaCreate {
  name: string;
  version: number;
  kind: "evidence" | "claim";
  definition: Record<string, unknown>;
  disclosure_fields?: Array<string>;
}

export interface PurposeAuthorizationCreate {
  project_id: string;
  subject_id: string;
  purpose: string;
  legal_basis: "consent" | "contract" | "legal_obligation" | "legitimate_interest";
  justification: Record<string, unknown>;
  operations: Array<"claims:disclose" | "claims:read" | "claims:write" | "evidence:read" | "evidence:write">;
  valid_from: string;
  valid_until: string;
  delete_after?: string;
  consent_record_id?: string;
  reuse_from_ids?: Array<string>;
}

export interface EvidenceCreate {
  project_id: string;
  subject_id: string;
  authorization_id: string;
  schema_id: string;
  evidence_type: "submitted" | "provider" | "system" | "human" | "authoritative";
  operation_reference: string;
  payload: Record<string, unknown>;
  provenance: Record<string, unknown>;
  observed_at: string;
  valid_until: string;
  delete_after: string;
  source_ids?: Array<string>;
  supersedes_id?: string;
  verification_id?: string;
  source_check_id?: string;
}

export interface GovernedReason {
  reason: string;
}

export interface GovernedEmptyAction {
}

export interface ResourceLegalHoldCreate {
  project_id: string;
  subject_id: string;
  reason: Record<string, unknown>;
  expires_at?: string | null;
}

export interface ClaimCreate {
  project_id: string;
  subject_id: string;
  authorization_id: string;
  schema_id: string;
  observed_at: string;
  valid_from: string;
  valid_until: string;
  delete_after: string;
  evidence_ids?: Array<string>;
  claim_ids?: Array<string>;
  value?: Record<string, unknown>;
  confidence?: number;
  rule_name?: "" | "copy" | "field" | "normalize_name" | "iso_date" | "age_over" | "document_current" | "exact_corroboration";
  rule_version?: number;
  rule_parameters?: Record<string, unknown>;
  supersedes_id?: string;
}

export interface ClaimReusePolicyCreate {
  project_id: string;
  schema_id: string;
  name: string;
  version: number;
  purposes: Array<string>;
  accepted_classes: Array<"candidate" | "corroborated" | "derived" | "normalized" | "provider_asserted" | "reviewed">;
  fields: Array<string>;
  max_age_seconds: number;
  minimum_confidence?: number;
}

export interface ClaimConflictReview {
  project_id: string;
  purpose: string;
  selected_claim_id?: string | null;
  outcome: "selected" | "disputed" | "more_evidence";
  reason: Record<string, unknown>;
}

export interface ClaimRevoke {
  project_id: string;
  purpose: string;
  reason: string;
}

export interface ClaimEvaluation {
  project_id: string;
  purpose: string;
  policy_id: string;
}

export interface ClaimDisclosureCreate {
  project_id: string;
  authorization_id: string;
  audience_id: string;
  selections: Array<Record<string, unknown>>;
  lifetime_seconds?: number;
  max_redemptions?: number;
}

export interface GovernedProjectAction {
  project_id: string;
}

export interface ProviderCertificationCreate {
  configuration_id: string;
  capability: string;
  report: Record<string, unknown>;
  assurance_level: "conformance" | "assured";
  valid_until: string;
  delete_after: string;
}

export interface ProviderCertificationRevoke {
  reason: string;
}

export interface ProviderOperationCancel {
  project_id: string;
  reason: string;
}

export interface GovernedSchema {
  name: string;
  version: number;
  kind: "evidence" | "claim";
  definition: Record<string, unknown>;
  disclosure_fields: Array<string>;
  id: string;
  retired_at: string | null;
}

export interface PurposeAuthorization {
  id: string;
  project_id: string;
  subject_id: string;
  purpose: string;
  legal_basis: "consent" | "contract" | "legal_obligation" | "legitimate_interest";
  operations: Array<string>;
  approved_at?: string | null;
  valid_from: string;
  valid_until: string;
  delete_after: string;
  revoked_at?: string | null;
  reuse_from_ids: Array<string>;
}

export interface PurposeAuthorizationDetail {
  id: string;
  project_id: string;
  subject_id: string;
  purpose: string;
  legal_basis: "consent" | "contract" | "legal_obligation" | "legitimate_interest";
  operations: Array<string>;
  approved_at?: string | null;
  valid_from: string;
  valid_until: string;
  delete_after: string;
  revoked_at?: string | null;
  reuse_from_ids: Array<string>;
  justification: Record<string, unknown>;
  proposed_by_id: string;
  approved_by_id: string | null;
  consent_record_id: string | null;
}

export interface ResourceLegalHold {
  id: string;
  project_id: string;
  subject_id: string;
  created_at: string;
  expires_at: string | null;
  released_at: string | null;
  scope: "subject_project_lineage";
}

export interface ResourceLegalHoldDetail {
  id: string;
  project_id: string;
  subject_id: string;
  created_at: string;
  expires_at: string | null;
  released_at: string | null;
  scope: "subject_project_lineage";
  reason: Record<string, unknown>;
}

export interface GovernedEvidence {
  id: string;
  project_id: string;
  subject_id: string;
  schema_id: string;
  schema_version: number;
  purpose: string;
  status: string;
  observed_at: string;
  valid_until: string;
  delete_after: string;
  source_evidence_ids: Array<string>;
  evidence_type: "submitted" | "provider" | "system" | "human" | "authoritative";
  origin: "persisted_provider_check" | "caller_asserted";
  supersedes_id: string | null;
  payload?: Record<string, unknown>;
  provenance?: Record<string, unknown>;
}

export interface GovernedClaim {
  id: string;
  project_id: string;
  subject_id: string;
  schema_id: string;
  schema_version: number;
  purpose: string;
  status: string;
  observed_at: string;
  valid_until: string;
  delete_after: string;
  source_evidence_ids: Array<string>;
  claim_class: "candidate" | "normalized" | "corroborated" | "derived" | "reviewed";
  confidence: string | null;
  valid_from: string;
  rule: Record<string, unknown> | null;
  source_claim_ids: Array<string>;
  value?: Record<string, unknown>;
}

export interface GovernedReceipt {
  status?: string;
  id: string;
  schema_id: string;
  created_at: string;
}

export interface GovernedStateReceipt {
  id: string;
  status: string;
}

export interface GovernedLineage {
  root_id: string;
  nodes: Array<Record<string, unknown>>;
  edges: Array<Record<string, unknown>>;
  truncated: false;
}

export interface ClaimReusePolicy {
  id: string;
  project_id: string;
  schema_id: string;
  name: string;
  version: number;
  purposes: Array<string>;
  accepted_classes: Array<"candidate" | "corroborated" | "derived" | "normalized" | "provider_asserted" | "reviewed">;
  fields: Array<string>;
  max_age_seconds: number;
  minimum_confidence: string | null;
  approved_at: string | null;
  retired_at: string | null;
}

export interface ClaimReviewReceipt {
  id: string;
  outcome: "selected" | "disputed" | "more_evidence";
  selected_claim_id: string | null;
}

export interface ClaimPolicyEvaluation {
  satisfied: boolean;
  reason_codes: Array<string>;
  claim_id: string;
  policy_id: string;
  usable_until: string | null;
  claim_class: string;
  fresh_until: string;
}

export interface ClaimDisclosureReceipt {
  id: string;
  audience_id: string;
  purpose: string;
  expires_at: string;
  max_redemptions: number;
  token: string | null;
  token_available: boolean;
}

export interface ClaimDisclosureRedemption {
  id: string;
  audience_id: string;
  purpose: string;
  claims: Array<Record<string, unknown>>;
  expires_at: string;
}

export interface ClaimDisclosureRevocation {
  id: string;
  revoked: boolean;
}

export interface ProviderCertification {
  id: string;
  configuration_id: string;
  environment: "sandbox" | "production";
  capability: string;
  contract_version: "1";
  operation_contract: "sync" | "ic-provider-operations-v1";
  suite_version: string;
  report_sha256: string;
  assurance_level: "conformance" | "assured";
  approved_at: string | null;
  valid_until: string;
  revoked: boolean;
  delete_after: string;
  proposed_by_id: string;
  approved_by_id: string | null;
}

export interface ProviderCertificationDetail {
  id: string;
  configuration_id: string;
  environment: "sandbox" | "production";
  capability: string;
  contract_version: "1";
  operation_contract: "sync" | "ic-provider-operations-v1";
  suite_version: string;
  report_sha256: string;
  assurance_level: "conformance" | "assured";
  approved_at: string | null;
  valid_until: string;
  revoked: boolean;
  report: Record<string, unknown>;
  delete_after: string;
  proposed_by_id: string;
  approved_by_id: string | null;
}

export interface ProviderCertificationScope {
  configuration_id: string;
  environment: string;
  capability: string;
  contract_version: string;
  operation_contract: string;
  configuration_digest: string;
  manifest_sha256: string;
  suite_version: string;
  required_cases: Array<string>;
}

export interface ProviderOperation {
  id: string;
  status: "created" | "pending" | "completed" | "failed" | "cancelled" | "expired";
  configuration_id: string;
  check_id: string;
  capability: string;
  deadline: string;
  completed_at: string | null;
  verification_id: string;
  delete_after: string;
  invalidation_reason: string;
  remote_action: "cancel" | "delete" | null | null;
  remote_action_status: "pending" | "acknowledged" | "expired" | null | null;
  remote_requested_at: string | null;
  remote_attempted_at: string | null;
}

export interface ProviderOperationBinding {
  operation_contract: "ic-provider-operations-v1";
  operation_id: string;
  configuration_id: string;
  tenant_id: string;
  project_id: string;
  environment: "sandbox" | "production";
  capability: string;
  contract_version: "1";
  request_sha256: string;
  lease_generation: number;
  deadline: string;
  callback_path: string;
  lease_token: string;
}

export interface ProviderOperationCallback {
  binding: ProviderOperationBinding;
  status: "pending" | "completed" | "failed";
  result?: Record<string, unknown>;
  retry_after_seconds?: number;
}

export interface GovernedSchemaPage {
  results: Array<GovernedSchema>;
  pagination: CursorPagination;
}

export interface PurposeAuthorizationPage {
  results: Array<PurposeAuthorization>;
  pagination: CursorPagination;
}

export interface ResourceLegalHoldPage {
  results: Array<ResourceLegalHold>;
  pagination: CursorPagination;
}

export interface GovernedEvidencePage {
  results: Array<GovernedEvidence>;
  pagination: CursorPagination;
}

export interface GovernedClaimPage {
  results: Array<GovernedClaim>;
  pagination: CursorPagination;
}

export interface ClaimReusePolicyPage {
  results: Array<ClaimReusePolicy>;
  pagination: CursorPagination;
}

export interface ProviderCertificationPage {
  results: Array<ProviderCertification>;
  pagination: CursorPagination;
}

export interface ProviderOperationPage {
  results: Array<ProviderOperation>;
  pagination: CursorPagination;
}

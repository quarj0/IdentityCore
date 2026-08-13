// Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT.

export interface Error {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorEnvelope {
  success: Record<string, unknown>;
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
  status: string;
  required_document_types: Array<string>;
  required_liveness_level: string;
  face_match_threshold: number;
  manual_review_threshold: number;
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
  mfa_required: boolean;
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
  required_document_types: Array<string>;
  required_liveness_level: string;
  face_match_threshold: number;
  manual_review_threshold: number;
  maker_checker_required?: boolean;
  verification_expiry_minutes: number;
  media_retention_days: number;
  metadata_retention_days: number;
}

export interface VerificationPolicyCreateResponse {
  id: string;
  name: string;
  version: number;
  status: string;
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
  accepted: boolean;
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
  capture_type: string;
  upload_id: string;
}

export interface VerificationSessionLivenessRequest {
  liveness_type: string;
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
  direction: string;
  consent: Record<string, unknown>;
  document: Record<string, unknown>;
  available_documents: Array<Record<string, unknown>>;
  available_countries: Array<Record<string, unknown>>;
  expires_at: string;
}

export interface VerificationSessionConsentResponse {
  consent_record_id: string;
  next_step: string;
}

export interface VerificationSessionDocumentResponse {
  identity_document_id: string;
  status: string;
  next_step: string;
}

export interface VerificationSessionSelfieResponse {
  selfie_capture_id: string;
  status: string;
  next_step: string;
}

export interface VerificationSessionLivenessResponse {
  liveness_check_id: string;
  status: string;
}

export interface VerificationSessionLivenessChallengeResponse {
  challenge_id: string;
  actions: Array<string>;
  expires_at: string;
}

export interface VerificationSessionStatusResponse {
  verification_id: string;
  status: string;
  current_step: string;
  message: string;
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
  external_reference: string;
  subject: Record<string, unknown>;
  policy: Record<string, unknown>;
  created_at: string;
  completed_at?: string | null;
  verification_subject?: Record<string, unknown>;
  checks?: Record<string, unknown>;
  risk_assessment?: Record<string, unknown> | null;
  evidence_report?: Record<string, unknown> | null;
  decision?: Record<string, unknown> | null;
  expires_at?: string;
}

export interface VerificationResult {
  schema_version: string;
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
  purpose: string;
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
  asset_type: string;
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
  mime_type: string;
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
  environment: string;
  status: string;
  allowed_origins: Array<string>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  name: string;
  slug?: string;
  environment?: string;
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
  scopes: Array<string>;
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

export interface WebhookEndpointSummary {
  id: string;
  project_id?: string | null;
  url: string;
  description?: string;
  events: Array<string>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WebhookEndpointCreateRequest {
  project_id?: string;
  url: string;
  description?: string;
  events: Array<string>;
}

export interface WebhookEndpointCreateResponse {
  id: string;
  project_id?: string | null;
  url: string;
  description?: string;
  events: Array<string>;
  status: string;
  created_at: string;
  updated_at: string;
  secret: string;
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
  decision: string;
  reason_code: string;
  reason_detail?: string;
}

export interface ManualReviewDecisionResponse {
  verification_id: string;
  decision: string;
  decision_type: string;
  decided_at: string;
}

export interface ManualReviewApprovalRequest {
  decision: string;
}

export interface ManualReviewApprovalResponse {
  verification_id: string;
  decision: string;
  approval_status: string;
}

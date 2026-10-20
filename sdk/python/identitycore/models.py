"""Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT."""

from typing import Any, Literal, Optional, TypedDict


class _ErrorRequired(TypedDict):
    code: str
    message: str


class Error(_ErrorRequired, total=False):
    details: dict[str, Any]


class _ErrorEnvelopeRequired(TypedDict):
    success: Literal[False]
    error: Error
    request_id: str


class ErrorEnvelope(_ErrorEnvelopeRequired, total=False):
    pass


class _WorkflowSummaryRequired(TypedDict):
    id: str
    project_id: str
    name: str
    status: str
    steps: list[str]
    settings: dict[str, Any]
    current_version: int


class WorkflowSummary(_WorkflowSummaryRequired, total=False):
    description: str
    source_template_id: Optional[str]
    source_template_version: Optional[str]
    created_at: str
    updated_at: str


class _PolicyRequired(TypedDict):
    id: str
    name: str
    version: int
    status: Literal['draft', 'active', 'archived']
    required_document_types: list[Literal['national_id', 'passport', 'driver_license', 'health_id', 'voter_id']]
    required_liveness_level: Literal['passive', 'active']
    face_match_threshold: float
    manual_review_threshold: float
    maker_checker_required: bool
    verification_expiry_minutes: int
    media_retention_days: int
    metadata_retention_days: int
    created_at: str
    updated_at: str


class Policy(_PolicyRequired, total=False):
    description: str
    review_reason_rules: dict[str, Any]
    reuse_rules: dict[str, Any]
    document_consistency_rules: dict[str, Any]
    document_authenticity_required: bool
    document_authenticity_min_confidence: float
    external_risk_enabled: bool
    external_risk_failure_action: Literal['manual_review', 'ignore']
    external_risk_review_threshold: float


class _VerificationSubjectInputRequired(TypedDict):
    pass


class VerificationSubjectInput(_VerificationSubjectInputRequired, total=False):
    full_name: str
    email: str
    phone_number: str
    date_of_birth: str
    metadata: dict[str, Any]


class _VerificationCreateRequestRequired(TypedDict):
    purpose: str
    policy_id: str
    verification_subject: VerificationSubjectInput


class VerificationCreateRequest(_VerificationCreateRequestRequired, total=False):
    external_reference: str
    project_id: str
    redirect_url: str
    metadata: dict[str, Any]


class _PlatformUserLoginRequestRequired(TypedDict):
    email: str
    password: str


class PlatformUserLoginRequest(_PlatformUserLoginRequestRequired, total=False):
    pass


class _PlatformUserRequired(TypedDict):
    public_id: str
    email: str
    first_name: str
    last_name: str
    phone_number: str
    status: str
    tenant_public_id: Optional[str]
    tenant_name: Optional[str]
    tenant_status: Optional[str]
    is_platform_admin: bool
    mfa_enabled: bool
    roles: list[str]
    notification_preferences: dict[str, Any]
    last_login_at: Optional[str]
    created_at: str
    updated_at: str


class PlatformUser(_PlatformUserRequired, total=False):
    pass


class _PlatformUserMfaChallengeRequired(TypedDict):
    mfa_required: Literal[True]
    mfa_enrollment_required: bool
    mfa_token: str


class PlatformUserMfaChallenge(_PlatformUserMfaChallengeRequired, total=False):
    pass


class _PlatformUserAuthenticationRequired(TypedDict):
    tokens: dict[str, Any]
    user: PlatformUser


class PlatformUserAuthentication(_PlatformUserAuthenticationRequired, total=False):
    recovery_codes: list[str]


class _PlatformUserMfaEnrollmentRequestRequired(TypedDict):
    mfa_token: str


class PlatformUserMfaEnrollmentRequest(
    _PlatformUserMfaEnrollmentRequestRequired, total=False
):
    pass


class _PlatformUserMfaCodeRequestRequired(TypedDict):
    mfa_token: str
    code: str


class PlatformUserMfaCodeRequest(_PlatformUserMfaCodeRequestRequired, total=False):
    pass


class _PlatformUserMfaEnrollmentRequired(TypedDict):
    secret: str
    provisioning_uri: str


class PlatformUserMfaEnrollment(_PlatformUserMfaEnrollmentRequired, total=False):
    pass


class _VerificationPolicyCreateRequestRequired(TypedDict):
    name: str
    required_document_types: list[Literal['national_id', 'passport', 'driver_license', 'health_id', 'voter_id']]
    required_liveness_level: Literal['passive', 'active']
    face_match_threshold: float
    manual_review_threshold: float
    verification_expiry_minutes: int
    media_retention_days: int
    metadata_retention_days: int


class VerificationPolicyCreateRequest(
    _VerificationPolicyCreateRequestRequired, total=False
):
    project_id: str
    description: str
    consent_template_id: str
    default_locale: str
    supported_locales: list[str]
    review_reason_rules: dict[str, Any]
    reuse_rules: dict[str, Any]
    document_consistency_rules: dict[str, Any]
    document_authenticity_required: bool
    document_authenticity_min_confidence: float
    external_risk_enabled: bool
    external_risk_failure_action: Literal['manual_review', 'ignore']
    external_risk_review_threshold: float
    maker_checker_required: bool


class _VerificationPolicyCreateResponseRequired(TypedDict):
    id: str
    name: str
    version: int
    status: Literal['draft']


class VerificationPolicyCreateResponse(
    _VerificationPolicyCreateResponseRequired, total=False
):
    pass


class _VerificationCreateResponseRequired(TypedDict):
    id: str
    status: str
    verification_url: str
    session_id: str
    expires_at: str


class VerificationCreateResponse(_VerificationCreateResponseRequired, total=False):
    session_token: str


class _VerificationSessionConsentRequestRequired(TypedDict):
    accepted: Literal[True]


class VerificationSessionConsentRequest(
    _VerificationSessionConsentRequestRequired, total=False
):
    template_id: str
    version: int
    locale: str
    content_hash: str


class _VerificationSessionDocumentRequestRequired(TypedDict):
    document_type: str
    country_code: str
    captures: list[dict[str, Any]]


class VerificationSessionDocumentRequest(
    _VerificationSessionDocumentRequestRequired, total=False
):
    pass


class _VerificationSessionSelfieRequestRequired(TypedDict):
    capture_type: Literal['image', 'video']
    upload_id: str


class VerificationSessionSelfieRequest(
    _VerificationSessionSelfieRequestRequired, total=False
):
    pass


class _VerificationSessionLivenessRequestRequired(TypedDict):
    liveness_type: Literal['passive', 'active']
    selfie_capture_id: str


class VerificationSessionLivenessRequest(
    _VerificationSessionLivenessRequestRequired, total=False
):
    challenge_id: str


class _VerificationMobileHandoffRedeemResponseRequired(TypedDict):
    session_id: str
    session_token: str
    verification_id: str


class VerificationMobileHandoffRedeemResponse(
    _VerificationMobileHandoffRedeemResponseRequired, total=False
):
    pass


class _VerificationSessionResponseRequired(TypedDict):
    session_id: str
    verification_id: str
    status: str
    organization: dict[str, Any]
    purpose: str
    redirect_url: str
    required_steps: list[str]
    workflow: dict[str, Any]
    locale: str
    supported_locales: list[str]
    direction: Literal['ltr', 'rtl']
    consent: dict[str, Any]
    document: dict[str, Any]
    available_documents: list[dict[str, Any]]
    available_countries: list[dict[str, Any]]
    expires_at: str


class VerificationSessionResponse(_VerificationSessionResponseRequired, total=False):
    pass


class _VerificationSessionConsentResponseRequired(TypedDict):
    consent_record_id: str
    next_step: Literal['document_capture']


class VerificationSessionConsentResponse(
    _VerificationSessionConsentResponseRequired, total=False
):
    pass


class _VerificationSessionDocumentResponseRequired(TypedDict):
    identity_document_id: str
    status: str
    next_step: Literal['document_processing']


class VerificationSessionDocumentResponse(
    _VerificationSessionDocumentResponseRequired, total=False
):
    pass


class _VerificationSessionSelfieResponseRequired(TypedDict):
    selfie_capture_id: str
    status: Literal['processing']
    next_step: Literal['liveness_check']


class VerificationSessionSelfieResponse(
    _VerificationSessionSelfieResponseRequired, total=False
):
    pass


class _VerificationSessionLivenessResponseRequired(TypedDict):
    liveness_check_id: str
    status: Literal['processing']


class VerificationSessionLivenessResponse(
    _VerificationSessionLivenessResponseRequired, total=False
):
    pass


class _VerificationSessionLivenessChallengeResponseRequired(TypedDict):
    challenge_id: str
    actions: list[Literal['turn_left', 'turn_right', 'look_up', 'look_down']]
    expires_at: str
    expires_in: int


class VerificationSessionLivenessChallengeResponse(
    _VerificationSessionLivenessChallengeResponseRequired, total=False
):
    pass


class _VerificationSessionStatusResponseRequired(TypedDict):
    verification_id: str
    status: str
    current_step: str
    message: str
    evidence: dict[str, Any]


class VerificationSessionStatusResponse(
    _VerificationSessionStatusResponseRequired, total=False
):
    withdrawal_available: bool


class _VerificationMobileHandoffResponseRequired(TypedDict):
    handoff_url: str
    expires_at: str


class VerificationMobileHandoffResponse(
    _VerificationMobileHandoffResponseRequired, total=False
):
    pass


class _VerificationSummaryRequired(TypedDict):
    id: str
    status: str
    purpose: str
    external_reference: str
    subject: dict[str, Any]
    policy: dict[str, Any]
    created_at: str


class VerificationSummary(_VerificationSummaryRequired, total=False):
    completed_at: Optional[str]


class _VerificationDetailRequired(TypedDict):
    id: str
    status: str
    purpose: str
    policy: dict[str, Any]
    workflow: dict[str, Any]
    external_reference: str
    verification_subject: dict[str, Any]
    checks: dict[str, Any]
    risk_assessment: Optional[dict[str, Any]]
    document_classification: Optional[dict[str, Any]]
    evidence_report: Optional[dict[str, Any]]
    decision: Optional[dict[str, Any]]
    created_at: str
    completed_at: Optional[str]
    expires_at: str


class VerificationDetail(_VerificationDetailRequired, total=False):
    pass


class _SandboxSimulationRequestRequired(TypedDict):
    scenario: Literal['approved', 'declined', 'review', 'timeout', 'provider_error']


class SandboxSimulationRequest(_SandboxSimulationRequestRequired, total=False):
    pass


class _SandboxSimulationMarkerRequired(TypedDict):
    scenario: Literal['approved', 'declined', 'review', 'timeout', 'provider_error']
    version: Literal[1]


class SandboxSimulationMarker(_SandboxSimulationMarkerRequired, total=False):
    pass


class _VerificationResultRequired(TypedDict):
    schema_version: Literal['1']
    verification_id: str
    status: str
    decision: Optional[dict[str, Any]]
    policy: dict[str, Any]
    workflow: dict[str, Any]
    check_provenance: list[dict[str, Any]]
    timestamps: dict[str, Any]


class VerificationResult(_VerificationResultRequired, total=False):
    simulation: SandboxSimulationMarker


class _CursorPaginationRequired(TypedDict):
    limit: int
    next_cursor: Optional[str]
    has_more: bool


class CursorPagination(_CursorPaginationRequired, total=False):
    pass


class _PagePaginationRequired(TypedDict):
    page: int
    page_size: int
    total: int
    total_pages: int


class PagePagination(_PagePaginationRequired, total=False):
    pass


class _AuditEventRequired(TypedDict):
    id: str
    actor_type: str
    actor_id: str
    action: str
    action_label: str
    actor_display_name: str
    target_type: str
    target_id: str
    target_label: str
    ip_address: Optional[str]
    user_agent: str
    metadata: dict[str, Any]
    created_at: str


class AuditEvent(_AuditEventRequired, total=False):
    pass


class _EvidenceReportRequired(TypedDict):
    verification_id: str
    storage_key: str
    download_url: str
    pdf_storage_key: str
    pdf_download_url: str


class EvidenceReport(_EvidenceReportRequired, total=False):
    pass


class _PortalUploadCreateRequestRequired(TypedDict):
    purpose: Literal['document_capture', 'selfie_capture', 'liveness_capture']
    mime_type: str
    file_size_bytes: int


class PortalUploadCreateRequest(_PortalUploadCreateRequestRequired, total=False):
    capture_method: Literal['camera', 'live_recording', 'file', 'unreported']


class _PortalUploadCreateResponseRequired(TypedDict):
    upload_id: str
    upload_url: str
    upload_headers: dict[str, Any]
    upload_transfer_path: str
    upload_complete_path: str
    expires_at: str


class PortalUploadCreateResponse(_PortalUploadCreateResponseRequired, total=False):
    pass


class _PortalUploadTransferResponseRequired(TypedDict):
    upload_id: str


class PortalUploadTransferResponse(_PortalUploadTransferResponseRequired, total=False):
    pass


class _OrganizationProfileRequired(TypedDict):
    id: str
    name: str
    slug: str
    status: str
    settings: dict[str, Any]
    sandbox_usage: dict[str, Any]


class OrganizationProfile(_OrganizationProfileRequired, total=False):
    industry: str
    tenant_id: str
    tenant_name: str
    tenant_status: str
    default_country_profile_id: str
    default_jurisdiction_id: str
    created_at: str
    updated_at: str


class _OrganizationBrandingAssetUploadRequestRequired(TypedDict):
    asset_type: Literal['logo', 'branding_image']
    filename: str
    mime_type: str


class OrganizationBrandingAssetUploadRequest(
    _OrganizationBrandingAssetUploadRequestRequired, total=False
):
    pass


class _OrganizationBrandingAssetUploadResponseRequired(TypedDict):
    asset_type: str
    storage_key: str
    bucket_name: str
    upload_url: str
    asset_url: str


class OrganizationBrandingAssetUploadResponse(
    _OrganizationBrandingAssetUploadResponseRequired, total=False
):
    pass


class _OrganizationSupportingDocumentUploadRequestRequired(TypedDict):
    filename: str
    mime_type: Literal['application/pdf']
    file_size_bytes: int


class OrganizationSupportingDocumentUploadRequest(
    _OrganizationSupportingDocumentUploadRequestRequired, total=False
):
    pass


class _OrganizationSupportingDocumentUploadResponseRequired(TypedDict):
    document_id: str
    filename: str
    file_size_bytes: int
    status: str
    storage_key: str
    download_url: str
    upload_url: str


class OrganizationSupportingDocumentUploadResponse(
    _OrganizationSupportingDocumentUploadResponseRequired, total=False
):
    pass


class _OrganizationSupportingDocumentCompleteResponseRequired(TypedDict):
    document_id: str
    status: str


class OrganizationSupportingDocumentCompleteResponse(
    _OrganizationSupportingDocumentCompleteResponseRequired, total=False
):
    pass


class _OrganizationSupportingDocumentDeleteResponseRequired(TypedDict):
    document_id: str
    deleted: bool


class OrganizationSupportingDocumentDeleteResponse(
    _OrganizationSupportingDocumentDeleteResponseRequired, total=False
):
    pass


class _ProjectSummaryRequired(TypedDict):
    id: str
    name: str
    slug: str
    environment: Literal['sandbox', 'production']
    status: str
    allowed_origins: list[str]
    is_default: bool
    created_at: str
    updated_at: str


class ProjectSummary(_ProjectSummaryRequired, total=False):
    pass


class _ProjectCreateRequestRequired(TypedDict):
    name: str


class ProjectCreateRequest(_ProjectCreateRequestRequired, total=False):
    slug: str
    environment: Literal['sandbox', 'production']
    allowed_origins: list[str]


class _ProjectUpdateRequestRequired(TypedDict):
    pass


class ProjectUpdateRequest(_ProjectUpdateRequestRequired, total=False):
    name: str
    slug: str
    environment: Literal['sandbox', 'production']
    allowed_origins: list[str]


class _APIClientSummaryRequired(TypedDict):
    public_id: str
    tenant_public_id: str
    name: str
    client_id: str
    status: str
    scopes: list[str]
    allowed_networks: list[str]
    rate_limit_per_minute: int
    created_at: str
    updated_at: str


class APIClientSummary(_APIClientSummaryRequired, total=False):
    project_id: Optional[str]
    last_used_at: Optional[str]
    client_secret_overlap_expires_at: Optional[str]


class _APIClientCreateRequestRequired(TypedDict):
    name: str
    scopes: list[Literal['policies:read', 'verifications:create', 'verifications:read', 'verifications:write']]


class APIClientCreateRequest(_APIClientCreateRequestRequired, total=False):
    project_id: str
    allowed_networks: list[str]
    rate_limit_per_minute: int


class _APIClientCreateResponseRequired(TypedDict):
    public_id: str
    tenant_public_id: str
    name: str
    client_id: str
    status: str
    scopes: list[str]
    allowed_networks: list[str]
    rate_limit_per_minute: int
    created_at: str
    updated_at: str
    client_secret: str


class APIClientCreateResponse(_APIClientCreateResponseRequired, total=False):
    project_id: Optional[str]
    last_used_at: Optional[str]
    client_secret_overlap_expires_at: Optional[str]


class _APIClientActionResponseRequired(TypedDict):
    public_id: str
    tenant_public_id: str
    name: str
    client_id: str
    status: str
    scopes: list[str]
    allowed_networks: list[str]
    rate_limit_per_minute: int
    created_at: str
    updated_at: str


class APIClientActionResponse(_APIClientActionResponseRequired, total=False):
    project_id: Optional[str]
    last_used_at: Optional[str]
    client_secret_overlap_expires_at: Optional[str]
    client_secret: str


class _WebhookEndpointSummaryRequired(TypedDict):
    id: str
    url: str
    events: list[Literal['verification.created', 'verification.consent_accepted', 'verification.document_uploaded', 'verification.selfie_uploaded', 'verification.processing', 'verification.manual_review_required', 'verification.verified', 'verification.rejected', 'verification.failed', 'verification.expired', 'verification.cancelled']]
    status: str
    signing_secret_version: int
    previous_secret_expires_at: Optional[str]
    created_at: str
    updated_at: str


class WebhookEndpointSummary(_WebhookEndpointSummaryRequired, total=False):
    project_id: Optional[str]
    description: str


class _WebhookEndpointCreateRequestRequired(TypedDict):
    url: str
    events: list[Literal['verification.created', 'verification.consent_accepted', 'verification.document_uploaded', 'verification.selfie_uploaded', 'verification.processing', 'verification.manual_review_required', 'verification.verified', 'verification.rejected', 'verification.failed', 'verification.expired', 'verification.cancelled']]


class WebhookEndpointCreateRequest(_WebhookEndpointCreateRequestRequired, total=False):
    project_id: str
    description: str


class _WebhookEndpointCreateResponseRequired(TypedDict):
    id: str
    secret: str
    status: str


class WebhookEndpointCreateResponse(
    _WebhookEndpointCreateResponseRequired, total=False
):
    pass


class _WebhookEndpointTestResponseRequired(TypedDict):
    queued: bool


class WebhookEndpointTestResponse(_WebhookEndpointTestResponseRequired, total=False):
    pass


class _ManualReviewSummaryRequired(TypedDict):
    verification_id: str
    status: str
    purpose: str
    subject: dict[str, Any]
    risk_level: str
    created_at: str


class ManualReviewSummary(_ManualReviewSummaryRequired, total=False):
    document_classification: Optional[dict[str, Any]]


class _ManualReviewDecisionRequestRequired(TypedDict):
    decision: Literal['verified', 'rejected', 'failed']
    reason_code: str


class ManualReviewDecisionRequest(_ManualReviewDecisionRequestRequired, total=False):
    reason_detail: str


class _ManualReviewDecisionResponseRequired(TypedDict):
    verification_id: str
    decision: str
    decision_type: str
    decided_at: str


class ManualReviewDecisionResponse(_ManualReviewDecisionResponseRequired, total=False):
    pass


class _ManualReviewPendingDecisionResponseRequired(TypedDict):
    verification_id: str
    decision: str
    approval_status: Literal['pending']
    approval_required: Literal[True]


class ManualReviewPendingDecisionResponse(
    _ManualReviewPendingDecisionResponseRequired, total=False
):
    pass


class _ManualReviewApprovalRequestRequired(TypedDict):
    decision: Literal['verified', 'rejected', 'failed']


class ManualReviewApprovalRequest(_ManualReviewApprovalRequestRequired, total=False):
    reason_code: str
    reason_detail: str


class _ManualReviewApprovalResponseRequired(TypedDict):
    verification_id: str
    decision: str
    approval_status: Literal['approved']


class ManualReviewApprovalResponse(_ManualReviewApprovalResponseRequired, total=False):
    pass


class _GovernedSchemaCreateRequired(TypedDict):
    name: str
    version: int
    kind: Literal['evidence', 'claim']
    definition: dict[str, Any]


class GovernedSchemaCreate(_GovernedSchemaCreateRequired, total=False):
    disclosure_fields: list[str]


class _PurposeAuthorizationCreateRequired(TypedDict):
    project_id: str
    subject_id: str
    purpose: str
    legal_basis: Literal['consent', 'contract', 'legal_obligation', 'legitimate_interest']
    justification: dict[str, Any]
    operations: list[Literal['claims:disclose', 'claims:read', 'claims:write', 'evidence:read', 'evidence:write']]
    valid_from: str
    valid_until: str


class PurposeAuthorizationCreate(_PurposeAuthorizationCreateRequired, total=False):
    delete_after: str
    consent_record_id: str
    reuse_from_ids: list[str]


class _EvidenceCreateRequired(TypedDict):
    project_id: str
    subject_id: str
    authorization_id: str
    schema_id: str
    evidence_type: Literal['submitted', 'provider', 'system', 'human', 'authoritative']
    operation_reference: str
    payload: dict[str, Any]
    provenance: dict[str, Any]
    observed_at: str
    valid_until: str
    delete_after: str


class EvidenceCreate(_EvidenceCreateRequired, total=False):
    source_ids: list[str]
    supersedes_id: str
    verification_id: str
    source_check_id: str


class _GovernedReasonRequired(TypedDict):
    reason: str


class GovernedReason(_GovernedReasonRequired, total=False):
    pass


class _GovernedEmptyActionRequired(TypedDict):
    pass


class GovernedEmptyAction(_GovernedEmptyActionRequired, total=False):
    pass


class _ResourceLegalHoldCreateRequired(TypedDict):
    project_id: str
    subject_id: str
    reason: dict[str, Any]


class ResourceLegalHoldCreate(_ResourceLegalHoldCreateRequired, total=False):
    expires_at: Optional[str]


class _ClaimCreateRequired(TypedDict):
    project_id: str
    subject_id: str
    authorization_id: str
    schema_id: str
    observed_at: str
    valid_from: str
    valid_until: str
    delete_after: str


class ClaimCreate(_ClaimCreateRequired, total=False):
    evidence_ids: list[str]
    claim_ids: list[str]
    value: dict[str, Any]
    confidence: float
    rule_name: Literal['', 'copy', 'field', 'normalize_name', 'iso_date', 'age_over', 'document_current', 'exact_corroboration']
    rule_version: int
    rule_parameters: dict[str, Any]
    supersedes_id: str


class _ClaimReusePolicyCreateRequired(TypedDict):
    project_id: str
    schema_id: str
    name: str
    version: int
    purposes: list[str]
    accepted_classes: list[Literal['candidate', 'corroborated', 'derived', 'normalized', 'provider_asserted', 'reviewed']]
    fields: list[str]
    max_age_seconds: int


class ClaimReusePolicyCreate(_ClaimReusePolicyCreateRequired, total=False):
    minimum_confidence: float


class _ClaimConflictReviewRequired(TypedDict):
    project_id: str
    purpose: str
    outcome: Literal['selected', 'disputed', 'more_evidence']
    reason: dict[str, Any]


class ClaimConflictReview(_ClaimConflictReviewRequired, total=False):
    selected_claim_id: Optional[str]


class _ClaimRevokeRequired(TypedDict):
    project_id: str
    purpose: str
    reason: str


class ClaimRevoke(_ClaimRevokeRequired, total=False):
    pass


class _ClaimEvaluationRequired(TypedDict):
    project_id: str
    purpose: str
    policy_id: str


class ClaimEvaluation(_ClaimEvaluationRequired, total=False):
    pass


class _ClaimDisclosureCreateRequired(TypedDict):
    project_id: str
    authorization_id: str
    audience_id: str
    selections: list[dict[str, Any]]


class ClaimDisclosureCreate(_ClaimDisclosureCreateRequired, total=False):
    lifetime_seconds: int
    max_redemptions: int


class _GovernedProjectActionRequired(TypedDict):
    project_id: str


class GovernedProjectAction(_GovernedProjectActionRequired, total=False):
    pass


class _ProviderCertificationCreateRequired(TypedDict):
    configuration_id: str
    capability: str
    report: dict[str, Any]
    assurance_level: Literal['conformance', 'assured']
    valid_until: str
    delete_after: str


class ProviderCertificationCreate(_ProviderCertificationCreateRequired, total=False):
    pass


class _ProviderCertificationRevokeRequired(TypedDict):
    reason: str


class ProviderCertificationRevoke(_ProviderCertificationRevokeRequired, total=False):
    pass


class _ProviderOperationCancelRequired(TypedDict):
    project_id: str
    reason: str


class ProviderOperationCancel(_ProviderOperationCancelRequired, total=False):
    pass


class _GovernedSchemaRequired(TypedDict):
    name: str
    version: int
    kind: Literal['evidence', 'claim']
    definition: dict[str, Any]
    disclosure_fields: list[str]
    id: str
    retired_at: Optional[str]


class GovernedSchema(_GovernedSchemaRequired, total=False):
    pass


class _PurposeAuthorizationRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    purpose: str
    legal_basis: Literal['consent', 'contract', 'legal_obligation', 'legitimate_interest']
    operations: list[str]
    valid_from: str
    valid_until: str
    delete_after: str
    reuse_from_ids: list[str]


class PurposeAuthorization(_PurposeAuthorizationRequired, total=False):
    approved_at: Optional[str]
    revoked_at: Optional[str]


class _PurposeAuthorizationDetailRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    purpose: str
    legal_basis: Literal['consent', 'contract', 'legal_obligation', 'legitimate_interest']
    operations: list[str]
    valid_from: str
    valid_until: str
    delete_after: str
    reuse_from_ids: list[str]
    justification: dict[str, Any]
    proposed_by_id: str
    approved_by_id: Optional[str]
    consent_record_id: Optional[str]


class PurposeAuthorizationDetail(_PurposeAuthorizationDetailRequired, total=False):
    approved_at: Optional[str]
    revoked_at: Optional[str]


class _ResourceLegalHoldRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    created_at: str
    expires_at: Optional[str]
    released_at: Optional[str]
    scope: Literal['subject_project_lineage']


class ResourceLegalHold(_ResourceLegalHoldRequired, total=False):
    pass


class _ResourceLegalHoldDetailRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    created_at: str
    expires_at: Optional[str]
    released_at: Optional[str]
    scope: Literal['subject_project_lineage']
    reason: dict[str, Any]


class ResourceLegalHoldDetail(_ResourceLegalHoldDetailRequired, total=False):
    pass


class _GovernedEvidenceRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    schema_id: str
    schema_version: int
    purpose: str
    status: str
    observed_at: str
    valid_until: str
    delete_after: str
    source_evidence_ids: list[str]
    evidence_type: Literal['submitted', 'provider', 'system', 'human', 'authoritative']
    origin: Literal['persisted_provider_check', 'caller_asserted']
    supersedes_id: Optional[str]


class GovernedEvidence(_GovernedEvidenceRequired, total=False):
    payload: dict[str, Any]
    provenance: dict[str, Any]


class _GovernedClaimRequired(TypedDict):
    id: str
    project_id: str
    subject_id: str
    schema_id: str
    schema_version: int
    purpose: str
    status: str
    observed_at: str
    valid_until: str
    delete_after: str
    source_evidence_ids: list[str]
    claim_class: Literal['candidate', 'normalized', 'corroborated', 'derived', 'reviewed']
    confidence: Optional[str]
    valid_from: str
    rule: Optional[dict[str, Any]]
    source_claim_ids: list[str]


class GovernedClaim(_GovernedClaimRequired, total=False):
    value: dict[str, Any]


class _GovernedReceiptRequired(TypedDict):
    id: str
    schema_id: str
    created_at: str


class GovernedReceipt(_GovernedReceiptRequired, total=False):
    status: str


class _GovernedStateReceiptRequired(TypedDict):
    id: str
    status: str


class GovernedStateReceipt(_GovernedStateReceiptRequired, total=False):
    pass


class _GovernedLineageRequired(TypedDict):
    root_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    truncated: Literal[False]


class GovernedLineage(_GovernedLineageRequired, total=False):
    pass


class _ClaimReusePolicyRequired(TypedDict):
    id: str
    project_id: str
    schema_id: str
    name: str
    version: int
    purposes: list[str]
    accepted_classes: list[Literal['candidate', 'corroborated', 'derived', 'normalized', 'provider_asserted', 'reviewed']]
    fields: list[str]
    max_age_seconds: int
    minimum_confidence: Optional[str]
    approved_at: Optional[str]
    retired_at: Optional[str]


class ClaimReusePolicy(_ClaimReusePolicyRequired, total=False):
    pass


class _ClaimReviewReceiptRequired(TypedDict):
    id: str
    outcome: Literal['selected', 'disputed', 'more_evidence']
    selected_claim_id: Optional[str]


class ClaimReviewReceipt(_ClaimReviewReceiptRequired, total=False):
    pass


class _ClaimPolicyEvaluationRequired(TypedDict):
    satisfied: bool
    reason_codes: list[str]
    claim_id: str
    policy_id: str
    usable_until: Optional[str]
    claim_class: str
    fresh_until: str


class ClaimPolicyEvaluation(_ClaimPolicyEvaluationRequired, total=False):
    pass


class _ClaimDisclosureReceiptRequired(TypedDict):
    id: str
    audience_id: str
    purpose: str
    expires_at: str
    max_redemptions: int
    token: Optional[str]
    token_available: bool


class ClaimDisclosureReceipt(_ClaimDisclosureReceiptRequired, total=False):
    pass


class _ClaimDisclosureRedemptionRequired(TypedDict):
    id: str
    audience_id: str
    purpose: str
    claims: list[dict[str, Any]]
    expires_at: str


class ClaimDisclosureRedemption(_ClaimDisclosureRedemptionRequired, total=False):
    pass


class _ClaimDisclosureRevocationRequired(TypedDict):
    id: str
    revoked: bool


class ClaimDisclosureRevocation(_ClaimDisclosureRevocationRequired, total=False):
    pass


class _ProviderCertificationRequired(TypedDict):
    id: str
    configuration_id: str
    environment: Literal['sandbox', 'production']
    capability: str
    contract_version: Literal['1']
    operation_contract: Literal['sync', 'ic-provider-operations-v1']
    suite_version: str
    report_sha256: str
    assurance_level: Literal['conformance', 'assured']
    approved_at: Optional[str]
    valid_until: str
    revoked: bool
    delete_after: str
    proposed_by_id: str
    approved_by_id: Optional[str]


class ProviderCertification(_ProviderCertificationRequired, total=False):
    pass


class _ProviderCertificationDetailRequired(TypedDict):
    id: str
    configuration_id: str
    environment: Literal['sandbox', 'production']
    capability: str
    contract_version: Literal['1']
    operation_contract: Literal['sync', 'ic-provider-operations-v1']
    suite_version: str
    report_sha256: str
    assurance_level: Literal['conformance', 'assured']
    approved_at: Optional[str]
    valid_until: str
    revoked: bool
    report: dict[str, Any]
    delete_after: str
    proposed_by_id: str
    approved_by_id: Optional[str]


class ProviderCertificationDetail(_ProviderCertificationDetailRequired, total=False):
    pass


class _ProviderCertificationScopeRequired(TypedDict):
    configuration_id: str
    environment: str
    capability: str
    contract_version: str
    operation_contract: str
    configuration_digest: str
    manifest_sha256: str
    suite_version: str
    required_cases: list[str]


class ProviderCertificationScope(_ProviderCertificationScopeRequired, total=False):
    pass


class _ProviderOperationRequired(TypedDict):
    id: str
    status: Literal['created', 'pending', 'completed', 'failed', 'cancelled', 'expired']
    configuration_id: str
    check_id: str
    capability: str
    deadline: str
    completed_at: Optional[str]
    verification_id: str
    delete_after: str
    invalidation_reason: str
    remote_action: Optional[Literal['cancel', 'delete', None]]
    remote_action_status: Optional[Literal['pending', 'acknowledged', 'expired', None]]
    remote_requested_at: Optional[str]
    remote_attempted_at: Optional[str]


class ProviderOperation(_ProviderOperationRequired, total=False):
    pass


class _ProviderOperationBindingRequired(TypedDict):
    operation_contract: Literal['ic-provider-operations-v1']
    operation_id: str
    configuration_id: str
    tenant_id: str
    project_id: str
    environment: Literal['sandbox', 'production']
    capability: str
    contract_version: Literal['1']
    request_sha256: str
    lease_generation: int
    deadline: str
    callback_path: str
    lease_token: str


class ProviderOperationBinding(_ProviderOperationBindingRequired, total=False):
    pass


class _ProviderOperationCallbackRequired(TypedDict):
    binding: ProviderOperationBinding
    status: Literal['pending', 'completed', 'failed']


class ProviderOperationCallback(_ProviderOperationCallbackRequired, total=False):
    result: dict[str, Any]
    retry_after_seconds: int


class _GovernedSchemaPageRequired(TypedDict):
    results: list[GovernedSchema]
    pagination: CursorPagination


class GovernedSchemaPage(_GovernedSchemaPageRequired, total=False):
    pass


class _PurposeAuthorizationPageRequired(TypedDict):
    results: list[PurposeAuthorization]
    pagination: CursorPagination


class PurposeAuthorizationPage(_PurposeAuthorizationPageRequired, total=False):
    pass


class _ResourceLegalHoldPageRequired(TypedDict):
    results: list[ResourceLegalHold]
    pagination: CursorPagination


class ResourceLegalHoldPage(_ResourceLegalHoldPageRequired, total=False):
    pass


class _GovernedEvidencePageRequired(TypedDict):
    results: list[GovernedEvidence]
    pagination: CursorPagination


class GovernedEvidencePage(_GovernedEvidencePageRequired, total=False):
    pass


class _GovernedClaimPageRequired(TypedDict):
    results: list[GovernedClaim]
    pagination: CursorPagination


class GovernedClaimPage(_GovernedClaimPageRequired, total=False):
    pass


class _ClaimReusePolicyPageRequired(TypedDict):
    results: list[ClaimReusePolicy]
    pagination: CursorPagination


class ClaimReusePolicyPage(_ClaimReusePolicyPageRequired, total=False):
    pass


class _ProviderCertificationPageRequired(TypedDict):
    results: list[ProviderCertification]
    pagination: CursorPagination


class ProviderCertificationPage(_ProviderCertificationPageRequired, total=False):
    pass


class _ProviderOperationPageRequired(TypedDict):
    results: list[ProviderOperation]
    pagination: CursorPagination


class ProviderOperationPage(_ProviderOperationPageRequired, total=False):
    pass

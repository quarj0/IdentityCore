"""Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT."""

from typing import Any, Optional, TypedDict

class _ErrorRequired(TypedDict):
    code: str
    message: str

class Error(_ErrorRequired, total=False):
    details: dict[str, Any]

class _ErrorEnvelopeRequired(TypedDict):
    success: dict[str, Any]
    error: Error
    request_id: str

class ErrorEnvelope(_ErrorEnvelopeRequired, total=False):
    pass

class _PolicyRequired(TypedDict):
    id: str
    name: str
    version: int
    status: str
    required_document_types: list[str]
    required_liveness_level: str
    face_match_threshold: float
    manual_review_threshold: float
    verification_expiry_minutes: int
    media_retention_days: int
    metadata_retention_days: int
    created_at: str
    updated_at: str

class Policy(_PolicyRequired, total=False):
    description: str

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

class _VerificationCreateResponseRequired(TypedDict):
    id: str
    status: str
    verification_url: str
    session_id: str
    expires_at: str

class VerificationCreateResponse(_VerificationCreateResponseRequired, total=False):
    session_token: str

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
    external_reference: str
    subject: dict[str, Any]
    policy: dict[str, Any]
    created_at: str

class VerificationDetail(_VerificationDetailRequired, total=False):
    completed_at: Optional[str]
    verification_subject: dict[str, Any]
    checks: dict[str, Any]
    risk_assessment: Optional[dict[str, Any]]
    evidence_report: Optional[dict[str, Any]]
    decision: Optional[dict[str, Any]]
    expires_at: str

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

class _EvidenceReportRequired(TypedDict):
    verification_id: str
    storage_key: str
    download_url: str
    pdf_storage_key: str
    pdf_download_url: str

class EvidenceReport(_EvidenceReportRequired, total=False):
    pass

class _PortalUploadCreateRequestRequired(TypedDict):
    purpose: str
    mime_type: str
    file_size_bytes: int

class PortalUploadCreateRequest(_PortalUploadCreateRequestRequired, total=False):
    pass

class _PortalUploadCreateResponseRequired(TypedDict):
    upload_id: str
    upload_url: str
    upload_headers: dict[str, Any]
    upload_transfer_path: str
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
    asset_type: str
    filename: str
    mime_type: str

class OrganizationBrandingAssetUploadRequest(_OrganizationBrandingAssetUploadRequestRequired, total=False):
    pass

class _OrganizationBrandingAssetUploadResponseRequired(TypedDict):
    asset_type: str
    storage_key: str
    bucket_name: str
    upload_url: str
    asset_url: str

class OrganizationBrandingAssetUploadResponse(_OrganizationBrandingAssetUploadResponseRequired, total=False):
    pass

class _OrganizationSupportingDocumentUploadRequestRequired(TypedDict):
    filename: str
    mime_type: str
    file_size_bytes: int

class OrganizationSupportingDocumentUploadRequest(_OrganizationSupportingDocumentUploadRequestRequired, total=False):
    pass

class _OrganizationSupportingDocumentUploadResponseRequired(TypedDict):
    document_id: str
    filename: str
    file_size_bytes: int
    status: str
    storage_key: str
    download_url: str
    upload_url: str

class OrganizationSupportingDocumentUploadResponse(_OrganizationSupportingDocumentUploadResponseRequired, total=False):
    pass

class _OrganizationSupportingDocumentCompleteResponseRequired(TypedDict):
    document_id: str
    status: str

class OrganizationSupportingDocumentCompleteResponse(_OrganizationSupportingDocumentCompleteResponseRequired, total=False):
    pass

class _OrganizationSupportingDocumentDeleteResponseRequired(TypedDict):
    document_id: str
    deleted: bool

class OrganizationSupportingDocumentDeleteResponse(_OrganizationSupportingDocumentDeleteResponseRequired, total=False):
    pass

class _ProjectSummaryRequired(TypedDict):
    id: str
    name: str
    slug: str
    environment: str
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
    environment: str
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

class _APIClientCreateRequestRequired(TypedDict):
    name: str
    scopes: list[str]

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

class _WebhookEndpointSummaryRequired(TypedDict):
    id: str
    url: str
    events: list[str]
    status: str
    created_at: str
    updated_at: str

class WebhookEndpointSummary(_WebhookEndpointSummaryRequired, total=False):
    project_id: Optional[str]
    description: str

class _WebhookEndpointCreateRequestRequired(TypedDict):
    url: str
    events: list[str]

class WebhookEndpointCreateRequest(_WebhookEndpointCreateRequestRequired, total=False):
    project_id: str
    description: str

class _WebhookEndpointCreateResponseRequired(TypedDict):
    id: str
    url: str
    events: list[str]
    status: str
    created_at: str
    updated_at: str
    secret: str

class WebhookEndpointCreateResponse(_WebhookEndpointCreateResponseRequired, total=False):
    project_id: Optional[str]
    description: str

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
    decision: str
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

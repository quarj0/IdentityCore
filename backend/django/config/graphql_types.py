import strawberry

from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES


@strawberry.type
class VerificationSubjectNode:
    id: str
    full_name: str
    email: str | None = None
    phone_number: str | None = None


@strawberry.type
class RiskAssessmentNode:
    id: str
    risk_level: str
    risk_score: float
    recommendation: str


@strawberry.type
class VerificationCheckNode:
    status: str
    score: float | None = None


@strawberry.type
class VerificationChecksNode:
    document: VerificationCheckNode
    liveness: VerificationCheckNode
    face_match: VerificationCheckNode


@strawberry.type
class VerificationDecisionNode:
    decision: str
    decision_type: str
    reason_code: str
    reason_detail: str
    decided_at: str


@strawberry.type
class VerificationNode:
    id: str
    status: str
    purpose: str
    external_reference: str
    verification_subject: VerificationSubjectNode
    checks: VerificationChecksNode
    risk_assessment: RiskAssessmentNode | None
    decision: VerificationDecisionNode | None
    created_at: str
    completed_at: str | None
    expires_at: str


@strawberry.type
class ManualReviewNode:
    verification_id: str
    status: str
    risk_level: str
    created_at: str


@strawberry.type
class VerificationPolicyNode:
    id: str
    project_id: str | None
    name: str
    description: str
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


@strawberry.type
class APIClientNode:
    public_id: str
    tenant_public_id: str
    project_id: str | None
    name: str
    client_id: str
    status: str
    scopes: list[str]
    allowed_networks: list[str]
    rate_limit_per_minute: int
    last_used_at: str | None
    created_at: str
    updated_at: str


@strawberry.type
class WebhookEndpointNode:
    id: str
    project_id: str | None
    url: str
    description: str
    events: list[str]
    status: str
    created_at: str
    updated_at: str


@strawberry.type
class AuditEventNode:
    id: str
    actor_type: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    ip_address: str | None
    user_agent: str
    metadata: strawberry.scalars.JSON
    created_at: str


@strawberry.type
class ProviderNode:
    id: str
    name: str
    code: str
    provider_type: str
    status: str
    configuration: strawberry.scalars.JSON
    created_at: str
    updated_at: str
    tenant_id: str | None = None
    tenant_name: str | None = None


@strawberry.type
class ProviderCheckNode:
    id: str
    verification_id: str
    provider_id: str
    provider_code: str
    check_type: str
    status: str
    provider_reference: str
    request_metadata: strawberry.scalars.JSON
    response_metadata: strawberry.scalars.JSON
    normalized_result: strawberry.scalars.JSON
    error_code: str
    error_message: str
    started_at: str
    completed_at: str | None


@strawberry.type
class PlatformRoleNode:
    id: str
    name: str
    description: str
    scope: str
    status: str
    member_count: int


@strawberry.type
class PlatformAdminInvitationNode:
    id: str
    email: str
    role_id: str
    role_name: str
    status: str
    expires_at: str
    accepted_at: str | None
    invited_by_email: str
    created_at: str
    updated_at: str


@strawberry.type
class PlatformSettingNode:
    id: str
    key: str
    title: str
    category: str
    status: str
    primary_value: str
    secondary_value: str
    owner_team: str
    description: str
    updated_at: str
    is_editable: bool = True
    is_secret: bool = False
    requires_restart: bool = False
    default_value: strawberry.scalars.JSON | None = None


@strawberry.type
class PlatformSettingRevisionNode:
    id: str
    setting_id: str
    old_value: strawberry.scalars.JSON
    new_value: strawberry.scalars.JSON
    change_reason: str
    changed_by_email: str | None
    created_at: str
    updated_at: str


@strawberry.type
class ProviderAssignmentNode:
    id: str
    tenant_id: str
    tenant_name: str
    assignment_key: str
    provider_id: str
    provider_name: str
    provider_code: str
    provider_type: str
    status: str
    notes: str
    created_at: str
    updated_at: str


@strawberry.type
class ManualDecisionPayload:
    verification_id: str
    decision: str
    decision_type: str
    decided_at: str


@strawberry.type
class PlatformAdminInvitationPayload:
    invitation: PlatformAdminInvitationNode
    debug_accept_token: str | None = None


@strawberry.input
class RegisterOrganizationOnboardingInput:
    full_name: str
    business_email: str
    password: str
    organization_name: str
    organization_type: str
    organization_country: str
    website: str = ""
    support_email: str
    phone_number: str


@strawberry.input
class OrganizationVerificationInput:
    business_registration_number: str
    registered_address: str
    official_website: str = ""
    tax_identification_number: str = ""
    supporting_document_keys: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class OrganizationOnboardingNode:
    organization_id: str
    organization_name: str
    organization_slug: str
    organization_type: str
    organization_country: str
    organization_country_name: str
    organization_status: str
    organization_tier: str
    tenant_id: str
    tenant_slug: str
    tenant_status: str
    administrator_user_id: str
    administrator_full_name: str
    administrator_email: str
    administrator_country: str
    administrator_status: str
    support_email: str
    phone_number: str
    website: str
    requires_email_verification: bool
    email_verified_at: str | None
    onboarding_status: str
    current_step: str
    organization_verification_submitted_at: str | None
    organization_verification_editable: bool
    organization_verification_review_status: str
    organization_verification_changed_after_approval: bool
    organization_verification_reviewed_at: str | None
    organization_verification_review_note: str
    review_priority: str | None = None
    review_summary: str | None = None
    business_registration_number: str
    tax_identification_number: str
    registered_address: str
    official_website: str
    supporting_documents: list[strawberry.scalars.JSON]
    administrator_identity_verification_status: str
    administrator_identity_verification_id: str
    administrator_identity_submitted_at: str | None
    platform_review_status: str
    platform_review_note: str
    platform_reviewed_at: str | None
    platform_review_assigned_reviewer_id: str
    platform_review_assigned_reviewer_name: str
    platform_review_assigned_at: str | None
    platform_review_escalated: bool
    platform_review_escalation_reason: str
    platform_review_escalated_at: str | None
    platform_review_required_approver_role: str


@strawberry.type
class OrganizationOnboardingPayload:
    onboarding: OrganizationOnboardingNode
    next_action: str
    message: str | None = None
    email_already_verified: bool = False
    debug_email_verification_url: str | None = None


@strawberry.type
class PlatformDashboardSummaryNode:
    organizations_total: int
    organizations_pending_review: int
    organizations_active: int
    tenants_total: int
    tenants_pending_review: int
    users_total: int
    platform_admins_total: int
    api_clients_total: int
    webhook_endpoints_total: int
    providers_total: int
    audit_events_total: int
    workflows_total: int
    workflow_versions_total: int
    billing_records_total: int
    analytics_dashboards_total: int
    incidents_total: int
    security_cases_total: int
    support_tickets_total: int
    templates_total: int
    feature_flags_total: int


@strawberry.type
class OrganizationNode:
    id: str
    name: str
    slug: str
    industry: str
    status: str
    tenant_id: str
    tenant_name: str
    tenant_status: str
    default_country_profile_id: str
    default_jurisdiction_id: str
    settings: strawberry.scalars.JSON
    sandbox_usage: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class OrganizationSupportingDocumentNode:
    id: str
    organization_id: str
    tenant_id: str
    uploaded_by_id: str
    uploaded_by_email: str
    filename: str
    mime_type: str
    file_size_bytes: int
    storage_key: str
    status: str
    created_at: str
    updated_at: str


@strawberry.type
class TenantNode:
    id: str
    organization_id: str
    organization_name: str
    organization_status: str
    name: str
    slug: str
    status: str
    settings: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class ProjectNode:
    id: str
    tenant_id: str
    tenant_name: str
    name: str
    slug: str
    environment: str
    status: str
    allowed_origins: list[str]
    is_default: bool
    created_at: str
    updated_at: str


@strawberry.type
class WorkflowNode:
    id: str
    tenant_id: str
    project_id: str
    project_name: str
    name: str
    description: str
    status: str
    steps: list[strawberry.scalars.JSON]
    settings: strawberry.scalars.JSON
    current_version: int
    created_by_id: str
    created_by_email: str
    created_at: str
    updated_at: str


@strawberry.type
class WorkflowVersionNode:
    id: str
    workflow_id: str
    workflow_name: str
    version: int
    steps: list[strawberry.scalars.JSON]
    settings: strawberry.scalars.JSON
    policy_id: str
    policy_name: str
    published_by_id: str
    published_by_email: str
    published_at: str


@strawberry.type
class BillingRecordNode:
    id: str
    organization_id: str
    tenant_id: str
    title: str
    subtitle: str
    status: str
    monthly_recurring_revenue: str
    monthly_check_count: int
    current_invoice: str
    plan: str
    billing_cycle: str
    owner_team: str
    notes: str
    created_at: str
    updated_at: str


@strawberry.type
class AnalyticsDashboardNode:
    id: str
    code: str
    title: str
    description: str
    status: str
    primary_metric: str
    secondary_metric: str
    tertiary_metric: str
    time_window: str
    owner_team: str
    config: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class IncidentNode:
    id: str
    title: str
    summary: str
    status: str
    severity: str
    owner_team: str
    affected_surface: str
    detected_at: str
    resolved_at: str | None
    metadata: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class SecurityCaseNode:
    id: str
    title: str
    summary: str
    status: str
    severity: str
    owner_team: str
    signal: str
    affected_surface: str
    detected_at: str
    resolved_at: str | None
    metadata: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class SupportTicketNode:
    id: str
    organization_id: str | None
    organization_name: str
    title: str
    summary: str
    status: str
    priority: str
    owner_team: str
    issue_type: str
    requester_email: str
    metadata: strawberry.scalars.JSON
    created_at: str
    updated_at: str


@strawberry.type
class TemplateNode:
    id: str
    name: str
    description: str
    category: str
    status: str
    version: str
    countries: list[str]
    required_checks: list[str]
    usage_count: int
    cloned_by_organizations: int
    owner_team: str
    risk_level: str
    created_by_id: str
    created_by_email: str
    created_at: str
    updated_at: str


@strawberry.type
class FeatureFlagNode:
    id: str
    key: str
    title: str
    description: str
    status: str
    rollout_percent: int
    audience: str
    owner_team: str
    channel: str
    metadata: strawberry.scalars.JSON
    created_by_id: str
    created_by_email: str
    created_at: str
    updated_at: str


@strawberry.type
class AdministratorVerificationLaunchNode:
    verification_id: str
    session_id: str
    session_token: str
    verification_url: str
    expires_at: str
    action: str


@strawberry.type
class DocumentTypeNode:
    code: str
    name: str


@strawberry.type
class SupportedDocumentTypeNode:
    document_type: str
    local_name: str


@strawberry.type
class CountryProfileNode:
    code: str
    name: str
    supported_document_types: list[SupportedDocumentTypeNode]


@strawberry.type
class CountryNode:
    code: str
    name: str


@strawberry.type
class AuthUserNode:
    public_id: str
    email: str
    first_name: str
    last_name: str
    phone_number: str
    status: str
    tenant_public_id: str | None
    tenant_name: str | None = None
    tenant_status: str | None = None
    is_platform_admin: bool
    mfa_enabled: bool
    roles: list[str]
    notification_preferences: strawberry.scalars.JSON | None = None
    last_login_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@strawberry.type
class AuthTokensNode:
    access: str
    refresh: str | None = None


@strawberry.type
class AuthPayload:
    tokens: AuthTokensNode
    user: AuthUserNode | None = None


@strawberry.type
class PublicActionPayload:
    ok: bool
    message: str
    next_action: str | None = None


@strawberry.input
class PlatformSettingChangeInput:
    key: str
    value: strawberry.scalars.JSON
    change_reason: str = ""


@strawberry.input
class ProviderRegistrationInput:
    name: str
    code: str
    provider_type: str
    tenant_id: str | None = None
    status: str = "active"
    configuration: strawberry.scalars.JSON = strawberry.field(default_factory=dict)


@strawberry.input
class ProviderAssignmentInput:
    tenant_id: str
    assignment_key: str
    provider_id: str
    status: str = "active"
    notes: str = ""


@strawberry.type
class ContactInquiryPayload:
    inquiry_id: str
    ok: bool
    message: str


@strawberry.input
class ContactInquiryInput:
    full_name: str
    business_email: str
    organization_name: str = ""
    interest: str = ""
    message: str


def to_verification_node(payload: dict) -> VerificationNode:
    risk_payload = payload["risk_assessment"]
    decision_payload = payload["decision"]
    return VerificationNode(
        id=payload["id"],
        status=payload["status"],
        purpose=payload["purpose"],
        external_reference=payload["external_reference"],
        verification_subject=VerificationSubjectNode(**payload["verification_subject"]),
        checks=VerificationChecksNode(
            document=VerificationCheckNode(**payload["checks"]["document"]),
            liveness=VerificationCheckNode(**payload["checks"]["liveness"]),
            face_match=VerificationCheckNode(**payload["checks"]["face_match"]),
        ),
        risk_assessment=RiskAssessmentNode(**risk_payload) if risk_payload else None,
        decision=(
            VerificationDecisionNode(**decision_payload) if decision_payload else None
        ),
        created_at=payload["created_at"],
        completed_at=payload["completed_at"],
        expires_at=payload["expires_at"],
    )


def to_onboarding_node(payload: dict) -> OrganizationOnboardingNode:
    return OrganizationOnboardingNode(**payload)

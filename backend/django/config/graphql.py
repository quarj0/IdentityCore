import strawberry
from django.conf import settings
from django.core.exceptions import ValidationError
from django_countries import countries
from django.shortcuts import get_object_or_404
from graphql import GraphQLError
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError as DRFValidationError,
)
from strawberry.extensions.query_depth_limiter import QueryDepthLimiter
from strawberry.types import Info

from apps.accounts.serializers import (
    LoginSerializer,
    serialize_user,
)
from apps.accounts.contact import submit_contact_inquiry
from apps.accounts.passwords import (
    request_password_reset,
    reset_password_with_token,
    change_password as perform_password_change,
)
from apps.accounts.verification import build_email_verification_url, verify_email_token
from apps.audit.serializers import serialize_audit_event
from apps.audit.services import record_audit_event
from apps.api_clients.serializers import serialize_api_client
from apps.notifications.services import queue_verification_status_notifications
from apps.organizations.models import Organization
from apps.organizations.onboarding import (
    ORGANIZATION_TYPE_CHOICES,
    confirm_onboarding_email_verification,
    register_organization_onboarding,
    resend_onboarding_email_verification,
    review_organization_onboarding,
    serialize_onboarding_state,
    submit_administrator_identity_verification,
    submit_organization_verification,
)
from apps.verification_policies.serializers import serialize_verification_policy
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.serializers import (
    ManualReviewDecisionSerializer,
    VerificationCreateSerializer,
    paginate_results,
    serialize_manual_review_summary,
    serialize_verification,
)
from apps.webhooks.serializers import serialize_webhook_endpoint
from apps.webhooks.services import queue_webhook_events
from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES


def require_tenant_user(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    if (
        getattr(user, "is_platform_admin", False)
        or getattr(user, "tenant_id", None) is None
    ):
        raise GraphQLError("A tenant-scoped platform user is required.")
    return user


def require_authenticated_user(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    return user


def require_platform_admin(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    if not getattr(user, "is_platform_admin", False):
        raise GraphQLError("A platform administrator is required.")
    return user


def raise_graphql_validation_error(exc: ValidationError) -> None:
    messages = exc.messages if hasattr(exc, "messages") else [str(exc)]
    raise GraphQLError(" ".join(message for message in messages if message))


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
class ManualDecisionPayload:
    verification_id: str
    decision: str
    decision_type: str
    decided_at: str


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
    administrator_identity_verification_status: str
    administrator_identity_verification_id: str
    administrator_identity_submitted_at: str | None
    platform_review_status: str
    platform_review_note: str
    platform_reviewed_at: str | None


@strawberry.type
class OrganizationOnboardingPayload:
    onboarding: OrganizationOnboardingNode
    next_action: str
    debug_email_verification_url: str | None = None


@strawberry.type
class AdministratorVerificationLaunchNode:
    verification_id: str
    session_id: str
    session_token: str
    verification_url: str
    expires_at: str


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
    is_platform_admin: bool
    mfa_enabled: bool
    roles: list[str]


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


@strawberry.type
class Query:
    @strawberry.field
    def document_types(self) -> list[DocumentTypeNode]:
        return [DocumentTypeNode(**item) for item in DOCUMENT_TYPES]

    @strawberry.field
    def country_profiles(self) -> list[CountryProfileNode]:
        return [
            CountryProfileNode(
                code=item["code"],
                name=item["name"],
                supported_document_types=[
                    SupportedDocumentTypeNode(**supported_document_type)
                    for supported_document_type in item["supported_document_types"]
                ],
            )
            for item in COUNTRY_PROFILES
        ]

    @strawberry.field
    def countries(self) -> list[CountryNode]:
        return [CountryNode(code=code, name=str(name)) for code, name in countries]

    @strawberry.field
    def organization_onboarding_types(self) -> list[str]:
        return list(ORGANIZATION_TYPE_CHOICES)

    @strawberry.field
    def organization_onboarding(self, info: Info) -> OrganizationOnboardingNode:
        user = require_tenant_user(info)
        return to_onboarding_node(
            serialize_onboarding_state(
                organization=user.tenant.organization,
                tenant=user.tenant,
                user=user,
            )
        )

    @strawberry.field
    def verifications(
        self,
        info: Info,
        status: str | None = None,
        external_reference: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[VerificationNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.verifications.select_related(
            "verification_subject"
        ).order_by("-created_at")
        if status:
            queryset = queryset.filter(status=status)
        if external_reference:
            queryset = queryset.filter(external_reference=external_reference)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            to_verification_node(
                serialize_verification(item, request=info.context["request"])
            )
            for item in page_obj.object_list
        ]

    @strawberry.field
    def verification(self, info: Info, verification_id: str) -> VerificationNode | None:
        user = require_tenant_user(info)
        verification = (
            user.tenant.verifications.select_related("verification_subject")
            .filter(public_id=verification_id)
            .first()
        )
        return (
            to_verification_node(
                serialize_verification(verification, request=info.context["request"])
            )
            if verification
            else None
        )

    @strawberry.field
    def manual_reviews(
        self, info: Info, page: int = 1, page_size: int = 20
    ) -> list[ManualReviewNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.verifications.filter(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        ).order_by("-created_at")
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            ManualReviewNode(**serialize_manual_review_summary(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def policies(self, info: Info) -> list[VerificationPolicyNode]:
        user = require_tenant_user(info)
        return [
            VerificationPolicyNode(**serialize_verification_policy(policy))
            for policy in user.tenant.verification_policies.order_by("name", "-version")
        ]

    @strawberry.field
    def api_clients(self, info: Info) -> list[APIClientNode]:
        user = require_tenant_user(info)
        return [
            APIClientNode(**serialize_api_client(api_client))
            for api_client in user.tenant.api_clients.select_related("tenant").order_by(
                "name"
            )
        ]

    @strawberry.field
    def webhook_endpoints(self, info: Info) -> list[WebhookEndpointNode]:
        user = require_tenant_user(info)
        return [
            WebhookEndpointNode(**serialize_webhook_endpoint(endpoint))
            for endpoint in user.tenant.webhook_endpoints.order_by("url")
        ]

    @strawberry.field
    def audit_events(
        self,
        info: Info,
        actor_type: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuditEventNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.audit_events.order_by("-created_at")
        if actor_type:
            queryset = queryset.filter(actor_type=actor_type)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            AuditEventNode(
                id=payload["id"],
                actor_type=payload["actor_type"],
                actor_id=payload["actor_id"],
                action=payload["action"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                ip_address=payload["ip_address"],
                user_agent=payload["user_agent"],
                metadata=payload["metadata"],
                created_at=payload["created_at"],
            )
            for payload in (
                serialize_audit_event(item) for item in page_obj.object_list
            )
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_administrator_onboarding_verification(
        self, info: Info
    ) -> AdministratorVerificationLaunchNode:
        request = info.context["request"]
        user = require_tenant_user(info)
        serializer = VerificationCreateSerializer(
            data={
                "purpose": "Administrator identity onboarding",
                "verification_subject": {
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                },
                "metadata": {"workflow": "administrator_onboarding"},
            },
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as exc:
            raise GraphQLError(str(exc.detail))
        verification = serializer.save()
        return AdministratorVerificationLaunchNode(
            verification_id=verification.public_id,
            session_id=verification._initial_session.public_id,
            session_token=verification._initial_session_token,
            verification_url=verification._verification_url,
            expires_at=verification.expires_at.isoformat(),
        )

    @strawberry.mutation
    def login(self, info: Info, email: str, password: str) -> AuthPayload:
        request = info.context["request"]
        serializer = LoginSerializer(
            data={"email": email, "password": password},
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except (DRFValidationError, AuthenticationFailed) as exc:
            raise GraphQLError(str(exc.detail))
        user = serializer.validated_data["user"]
        if user.tenant is not None:
            record_audit_event(
                tenant=user.tenant,
                actor=user,
                request=request,
                action="user.login",
                target_type="platform_user",
                target_id=user.public_id,
                metadata={"email": user.email},
                sensitive_metadata={"email": user.email},
            )
        return AuthPayload(
            tokens=AuthTokensNode(
                access=serializer.validated_data["tokens"]["access"]
            ),
            user=AuthUserNode(**serialize_user(user)),
        )

    @strawberry.mutation
    def request_password_reset(
        self,
        info: Info,
        email: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        sent = request_password_reset(email=email, request=request)
        return PublicActionPayload(
            ok=sent,
            message="If that email exists, a password reset link has been sent.",
            next_action="reset_password",
        )

    @strawberry.mutation
    def reset_password(
        self,
        info: Info,
        token: str,
        new_password: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        try:
            reset_password_with_token(
                token=token,
                new_password=new_password,
                request=request,
            )
        except (ValidationError, ValueError) as exc:
            raise GraphQLError(str(exc))
        return PublicActionPayload(
            ok=True,
            message="Your password has been reset successfully.",
            next_action="sign_in",
        )

    @strawberry.mutation
    def change_password(
        self,
        info: Info,
        current_password: str,
        new_password: str,
    ) -> PublicActionPayload:
        user = require_authenticated_user(info)
        request = info.context["request"]
        try:
            perform_password_change(
                user=user,
                current_password=current_password,
                new_password=new_password,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return PublicActionPayload(
            ok=True,
            message="Your password has been changed successfully.",
            next_action="account_updated",
        )

    @strawberry.mutation
    def register_organization_onboarding(
        self,
        info: Info,
        input: RegisterOrganizationOnboardingInput,
    ) -> OrganizationOnboardingPayload:
        request = info.context["request"]
        try:
            organization, tenant, user, raw_verification_token = (
                register_organization_onboarding(
                    full_name=input.full_name,
                    business_email=input.business_email,
                    password=input.password,
                    organization_name=input.organization_name,
                    organization_type=input.organization_type,
                    organization_country=input.organization_country,
                    website=input.website,
                    support_email=input.support_email,
                    phone_number=input.phone_number,
                    request=request,
                )
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=user,
                )
            ),
            next_action="verify_email",
            debug_email_verification_url=(
                build_email_verification_url(raw_verification_token)
                if settings.DEBUG
                else None
            ),
        )

    @strawberry.mutation
    def resend_organization_onboarding_email_verification(
        self,
        info: Info,
        business_email: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        try:
            sent = resend_onboarding_email_verification(
                business_email=business_email,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return PublicActionPayload(
            ok=sent,
            message=(
                "If the workspace is still awaiting email verification, a new link has been sent."
                if sent
                else "No pending onboarding email verification was found for that address."
            ),
            next_action="verify_email",
        )

    @strawberry.mutation
    def submit_contact_inquiry(
        self,
        info: Info,
        input: ContactInquiryInput,
    ) -> ContactInquiryPayload:
        try:
            inquiry = submit_contact_inquiry(
                full_name=input.full_name,
                business_email=input.business_email,
                organization_name=input.organization_name,
                interest=input.interest,
                message=input.message,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return ContactInquiryPayload(
            inquiry_id=inquiry.public_id,
            ok=True,
            message="Your message has been received. Our team will follow up soon.",
        )

    @strawberry.mutation
    def verify_organization_onboarding_email(
        self, info: Info, token: str
    ) -> OrganizationOnboardingPayload:
        request = info.context["request"]
        try:
            user = verify_email_token(token)
            organization, tenant, verified_user = confirm_onboarding_email_verification(
                user=user,
                actor=user,
                request=request,
            )
        except (ValidationError, ValueError) as exc:
            raise GraphQLError(str(exc))
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=verified_user,
                )
            ),
            next_action="submit_organization_verification",
        )

    @strawberry.mutation
    def submit_organization_onboarding_verification(
        self,
        info: Info,
        input: OrganizationVerificationInput,
    ) -> OrganizationOnboardingPayload:
        user = require_tenant_user(info)
        request = info.context["request"]
        try:
            organization, tenant, tenant_user = submit_organization_verification(
                user=user,
                business_registration_number=input.business_registration_number,
                registered_address=input.registered_address,
                official_website=input.official_website,
                tax_identification_number=input.tax_identification_number,
                supporting_document_keys=input.supporting_document_keys,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=tenant_user,
                )
            ),
            next_action="submit_administrator_identity_verification",
        )

    @strawberry.mutation
    def submit_administrator_identity_onboarding_verification(
        self, info: Info, verification_id: str = ""
    ) -> OrganizationOnboardingPayload:
        user = require_tenant_user(info)
        request = info.context["request"]
        try:
            organization, tenant, tenant_user = (
                submit_administrator_identity_verification(
                    user=user,
                    verification_id=verification_id,
                    request=request,
                )
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=tenant_user,
                )
            ),
            next_action="await_platform_review",
        )

    @strawberry.mutation
    def review_organization_onboarding(
        self,
        info: Info,
        organization_id: str,
        decision: str,
        note: str = "",
    ) -> OrganizationOnboardingPayload:
        actor = require_platform_admin(info)
        request = info.context["request"]
        organization = get_object_or_404(Organization, public_id=organization_id)
        try:
            reviewed_organization, tenant, user = review_organization_onboarding(
                organization=organization,
                actor=actor,
                decision=decision,
                note=note,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        if user is None:
            raise GraphQLError(
                "Onboarding organization does not have an administrator."
            )
        next_action = (
            "organization_active"
            if decision == "approved"
            else (
                "provide_additional_information"
                if decision == "needs_information"
                else "contact_support"
            )
        )
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=reviewed_organization,
                    tenant=tenant,
                    user=user,
                )
            ),
            next_action=next_action,
        )

    @strawberry.mutation
    def record_manual_decision(
        self,
        info: Info,
        verification_id: str,
        decision: str,
        reason_code: str,
        reason_detail: str = "",
    ) -> ManualDecisionPayload:
        user = require_tenant_user(info)
        request = info.context["request"]
        verification = get_object_or_404(
            Verification,
            tenant=user.tenant,
            public_id=verification_id,
        )
        serializer = ManualReviewDecisionSerializer(
            data={
                "decision": decision,
                "reason_code": reason_code,
                "reason_detail": reason_detail,
            }
        )
        serializer.is_valid(raise_exception=True)
        decision_record = serializer.save(verification=verification, decided_by=user)
        record_audit_event(
            tenant=user.tenant,
            actor=user,
            request=request,
            action=f"verification.{decision_record.decision}",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "decision_id": decision_record.public_id,
                "decision_type": decision_record.decision_type,
            },
            sensitive_metadata={"reason_detail": decision_record.reason_detail},
        )
        if decision_record.decision in {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        }:
            queue_webhook_events(
                tenant=user.tenant,
                event_type=f"verification.{decision_record.decision}",
                payload={
                    "verification_id": verification.public_id,
                    "external_reference": verification.external_reference,
                    "status": verification.status,
                },
            )
            risk_assessment = getattr(verification, "risk_assessment", None)
            queue_verification_status_notifications(
                verification=verification,
                decision=decision_record.decision,
                risk_level=(
                    risk_assessment.risk_level if risk_assessment is not None else ""
                ),
            )
        return ManualDecisionPayload(
            verification_id=verification.public_id,
            decision=decision_record.decision,
            decision_type=decision_record.decision_type,
            decided_at=decision_record.decided_at.isoformat(),
        )


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[QueryDepthLimiter(max_depth=6)],
)

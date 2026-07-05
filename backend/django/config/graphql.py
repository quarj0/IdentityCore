import strawberry
from django.shortcuts import get_object_or_404
from graphql import GraphQLError
from strawberry.extensions.query_depth_limiter import QueryDepthLimiter
from strawberry.types import Info

from apps.audit.serializers import serialize_audit_event
from apps.audit.services import record_audit_event
from apps.api_clients.serializers import serialize_api_client
from apps.notifications.services import queue_verification_status_notifications
from apps.verification_policies.serializers import serialize_verification_policy
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.serializers import (
    ManualReviewDecisionSerializer,
    paginate_results,
    serialize_manual_review_summary,
    serialize_verification,
)
from apps.webhooks.serializers import serialize_webhook_endpoint
from apps.webhooks.services import queue_webhook_events


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


@strawberry.type
class Query:
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
            to_verification_node(serialize_verification(item))
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
            to_verification_node(serialize_verification(verification))
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

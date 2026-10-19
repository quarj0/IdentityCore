from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from graphql import GraphQLError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import PlatformUser
from apps.audit.services import lock_audit_chain
from apps.platform_settings.services import get_platform_setting_value
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.evidence import (
    build_verification_evidence_download_url,
    build_verification_evidence_pdf_download_url,
)
from apps.verifications.models import (
    VERIFICATION_SESSION_ACTIONS,
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationApprovalStatus,
    VerificationReviewOwner,
    VerificationSession,
    VerificationStatus,
)
from apps.verifications.transitions import transition_verification
from apps.verifications.decision_contract import (
    DECISION_CONTRACT_VERSION,
    build_decision_input_snapshot,
)
from apps.verifications.review_access import (
    PLATFORM_REVIEW_WORKFLOWS,
    can_approve_review,
)
from common.pagination import MAX_PAGE_SIZE


def paginate_results(queryset, page: int, page_size: int):
    """Preserve GraphQL page clamping while bounding the result size."""
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise GraphQLError(f"pageSize must be between 1 and {MAX_PAGE_SIZE}.")
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return page_obj, {
        "page": page_obj.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
    }


def get_request_tenant(request):
    tenant = getattr(request, "tenant", None)
    if tenant is not None:
        return tenant
    user = getattr(request, "user", None)
    return getattr(user, "tenant", None)


def serialize_risk_assessment(verification: Verification) -> dict | None:
    risk_assessment = getattr(verification, "risk_assessment", None)
    if risk_assessment is None:
        return None
    return {
        "id": risk_assessment.public_id,
        "risk_level": risk_assessment.risk_level,
        "risk_score": float(risk_assessment.risk_score),
        "recommendation": risk_assessment.recommendation,
    }


def serialize_document_classification(verification: Verification) -> dict | None:
    latest_identity_document = verification.identity_documents.order_by(
        "-created_at"
    ).first()
    if latest_identity_document is None:
        return None
    classification = (latest_identity_document.extracted_data_json or {}).get(
        "document_classification"
    )
    return classification if isinstance(classification, dict) else None


def serialize_verification_subject(subject: VerificationSubject) -> dict:
    return {
        "id": subject.public_id,
        "external_reference": subject.external_reference,
        "full_name": subject.full_name,
        "email": subject.email,
        "phone_number": subject.phone_number,
    }


def serialize_verification(verification: Verification, request=None) -> dict:
    latest_liveness_check = (
        verification.liveness_checks.order_by("-checked_at").first()
        if hasattr(verification, "liveness_checks")
        else None
    )
    latest_face_match = (
        verification.face_matches.order_by("-matched_at").first()
        if hasattr(verification, "face_matches")
        else None
    )
    decision_record = getattr(verification, "decision_record", None)
    latest_identity_document = verification.identity_documents.order_by(
        "-created_at"
    ).first()
    result = {
        "id": verification.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "policy": {
            "id": verification.policy_public_id,
            "name": verification.policy_snapshot_json.get("name", ""),
            "version": verification.policy_snapshot_json.get("version"),
            "review_reason_rules": verification.policy_snapshot_json.get(
                "review_reason_rules", {}
            ),
        },
        "workflow": {
            "id": verification.workflow_snapshot_json.get("workflow_id"),
            "version_id": verification.workflow_snapshot_json.get("id"),
            "version": verification.workflow_snapshot_json.get("version"),
        },
        "external_reference": verification.external_reference,
        "verification_subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
        },
        "checks": {
            "document": {
                "status": (
                    latest_identity_document.status
                    if latest_identity_document is not None
                    else "pending"
                )
            },
            "liveness": {
                "status": (
                    latest_liveness_check.status if latest_liveness_check else "pending"
                ),
                "score": (
                    float(latest_liveness_check.score)
                    if latest_liveness_check and latest_liveness_check.score is not None
                    else None
                ),
            },
            "face_match": {
                "status": latest_face_match.status if latest_face_match else "pending",
                "score": (
                    float(latest_face_match.match_score)
                    if latest_face_match and latest_face_match.match_score is not None
                    else None
                ),
            },
        },
        "risk_assessment": serialize_risk_assessment(verification),
        "document_classification": serialize_document_classification(verification),
        "evidence_report": (
            {
                "storage_key": verification.metadata_json.get(
                    "evidence_report_storage_key", ""
                ),
                "download_url": build_verification_evidence_download_url(
                    verification, request=request
                ),
                "pdf_storage_key": verification.metadata_json.get(
                    "evidence_report_pdf_storage_key", ""
                ),
                "pdf_download_url": build_verification_evidence_pdf_download_url(
                    verification, request=request
                ),
            }
            if verification.metadata_json.get("evidence_report_storage_key")
            else None
        ),
        "decision": (
            {
                "decision": decision_record.decision,
                "proposed_decision": (
                    decision_record.proposed_decision or decision_record.decision
                ),
                "decision_type": decision_record.decision_type,
                "reason_code": decision_record.reason_code,
                "reason_detail": decision_record.reason_detail,
                "contract_version": decision_record.contract_version,
                "reason_codes": decision_record.reason_codes_json,
                "approval_status": decision_record.approval_status,
                "can_approve": can_approve_review(
                    getattr(request, "user", None), verification, decision_record
                ),
                "decided_at": decision_record.decided_at.isoformat(),
            }
            if decision_record is not None
            else None
        ),
        "created_at": verification.created_at.isoformat(),
        "completed_at": (
            verification.completed_at.isoformat() if verification.completed_at else None
        ),
        "expires_at": verification.expires_at.isoformat(),
    }
    from apps.verifications.models import SandboxSimulation

    marker = SandboxSimulation.objects.filter(verification=verification).first()
    if marker is not None:
        result["simulation"] = {"scenario": marker.scenario, "version": marker.version}
    return result


def serialize_verification_summary(verification: Verification) -> dict:
    return {
        "id": verification.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "external_reference": verification.external_reference,
        "subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
            "email": verification.verification_subject.email,
        },
        "assigned_reviewer_id": (
            verification.assigned_reviewer.public_id
            if verification.assigned_reviewer_id
            else None
        ),
        "policy": {
            "id": verification.policy_public_id,
            "name": verification.policy_snapshot_json.get("name", ""),
            "version": verification.policy_snapshot_json.get("version"),
        },
        "workflow": {
            "id": verification.workflow_snapshot_json.get("workflow_id"),
            "version_id": verification.workflow_snapshot_json.get("id"),
            "version": verification.workflow_snapshot_json.get("version"),
        },
        "created_at": verification.created_at.isoformat(),
        "completed_at": (
            verification.completed_at.isoformat() if verification.completed_at else None
        ),
    }


class VerificationSubjectInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(
        max_length=32, required=False, allow_blank=True
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, default=dict)


class PolicyEnvironmentScopeDenied(serializers.ValidationError):
    def __init__(self, policy_id):
        self.policy_id = policy_id
        super().__init__({"policy_id": "Choose an active verification template."})


class VerificationCreateSerializer(serializers.Serializer):
    project_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    external_reference = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    purpose = serializers.CharField(max_length=255)
    verification_subject = VerificationSubjectInputSerializer()
    policy_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    redirect_url = serializers.URLField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        request = self.context["request"]
        tenant = get_request_tenant(request)
        is_api_client_request = getattr(request, "api_client", None) is not None
        workflow = attrs.get("metadata", {}).get("workflow")
        if (
            isinstance(workflow, str)
            and workflow in PLATFORM_REVIEW_WORKFLOWS
            and self.context.get("trusted_review_owner")
            != VerificationReviewOwner.PLATFORM
        ):
            raise serializers.ValidationError(
                {"metadata": "This workflow is reserved for platform onboarding."}
            )
        policy_id = attrs.get("policy_id", "").strip()
        if is_api_client_request and not policy_id:
            raise serializers.ValidationError(
                {"policy_id": "Choose an active verification template."}
            )
        if policy_id:
            policies = tenant.verification_policies.filter(
                public_id=policy_id, status="active"
            )
            if is_api_client_request:
                client_project = request.api_client.project
                environment = (
                    client_project.environment
                    if client_project is not None
                    else "sandbox"
                )
                environment_filter = Q(project__environment=environment)
                if environment == "sandbox":
                    environment_filter |= Q(project__isnull=True)
                policies = policies.filter(environment_filter)
            policy = policies.first()
            if policy is None:
                if (
                    is_api_client_request
                    and tenant.verification_policies.filter(
                        public_id=policy_id, status="active"
                    ).exists()
                ):
                    self.environment_scope_denied_policy_id = policy_id
                    raise PolicyEnvironmentScopeDenied(policy_id)
                raise serializers.ValidationError(
                    {"policy_id": "Choose an active verification template."}
                )
            attrs["policy"] = policy
        if is_api_client_request:
            attrs["resolved_project"] = request.api_client.project
        project_id = attrs.get("project_id", "").strip()
        if project_id:
            project = tenant.projects.filter(
                public_id=project_id, status="active", deleted_at__isnull=True
            ).first()
            if project is None:
                raise serializers.ValidationError(
                    {"project_id": "Choose an active project in this workspace."}
                )
            policy = attrs.get("policy")
            if policy is not None and policy.project_id != project.pk:
                raise serializers.ValidationError(
                    {"project_id": "The project must match the verification template."}
                )
            if (
                is_api_client_request
                and policy is None
                and request.api_client.project_id != project.pk
            ):
                raise serializers.ValidationError(
                    {"project_id": "The project must match the API client."}
                )
            attrs["resolved_project"] = project
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        tenant = get_request_tenant(request)
        # Deletion takes the audit lock before capturing its case snapshot.
        # Serialize lookup and insertion with that snapshot, then lock only a
        # live subject; otherwise an invisible new case can escape erasure.
        lock_audit_chain(tenant.pk)
        subject_data = validated_data["verification_subject"]
        external_reference = validated_data.get("external_reference", "")
        policy = validated_data.get("policy")

        verification_subject = None
        if external_reference:
            verification_subject = (
                tenant.verification_subjects.select_for_update(no_key=True)
                .filter(external_reference=external_reference, deleted_at__isnull=True)
                .order_by("created_at")
                .first()
            )

        if verification_subject is None:
            verification_subject = VerificationSubject.objects.create(
                tenant=tenant,
                external_reference=external_reference,
                full_name=subject_data.get("full_name", ""),
                email=subject_data.get("email", ""),
                phone_number=subject_data.get("phone_number", ""),
                date_of_birth=subject_data.get("date_of_birth"),
                metadata_json=subject_data.get("metadata", {}),
            )

        if policy is not None:
            expires_at = timezone.now() + timedelta(
                minutes=policy.verification_expiry_minutes
            )
            policy_public_id = policy.public_id
            policy_snapshot_json = policy.snapshot()
            workflow_version = getattr(policy, "workflow_version", None)
            workflow_snapshot_json = (
                workflow_version.snapshot() if workflow_version is not None else {}
            )
        else:
            expires_at = timezone.now() + timedelta(hours=24)
            policy_public_id = validated_data.get("policy_id", "")
            policy_snapshot_json = {}
            workflow_snapshot_json = {}
        verification = Verification.objects.create(
            tenant=tenant,
            project=(
                policy.project
                if policy is not None
                else validated_data.get("resolved_project")
                or tenant.projects.filter(
                    public_id=validated_data.get("project_id")
                ).first()
                or tenant.projects.filter(is_default=True).first()
            ),
            organization=tenant.organization,
            verification_subject=verification_subject,
            policy_public_id=policy_public_id,
            policy_snapshot_json=policy_snapshot_json,
            workflow_snapshot_json=workflow_snapshot_json,
            purpose=validated_data["purpose"],
            external_reference=external_reference,
            metadata_json=validated_data.get("metadata", {}),
            review_owner=self.context.get(
                "trusted_review_owner", VerificationReviewOwner.TENANT
            ),
            redirect_url=validated_data.get("redirect_url", ""),
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=expires_at,
            created_by=(
                request.user
                if getattr(request.user, "is_authenticated", False)
                and isinstance(request.user, PlatformUser)
                else None
            ),
        )

        raw_session_token = VerificationSession.generate_session_token()
        session = VerificationSession(
            verification=verification,
            tenant=tenant,
            expires_at=expires_at,
            allowed_actions_json=list(VERIFICATION_SESSION_ACTIONS),
        )
        session.set_session_token(raw_session_token, generated=True)
        session.save()
        verification._initial_session = session
        verification._initial_session_token = raw_session_token
        verification._verification_url = (
            f"{str(get_platform_setting_value('integrations.verification_portal_base_url', settings.VERIFICATION_PORTAL_BASE_URL)).rstrip('/')}/{session.public_id}"
            f"#token={raw_session_token}&verification_id={verification.public_id}"
        )
        return verification


class VerificationCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class VerificationResendLinkSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=[("email", "Email")], default="email")


def serialize_manual_review_summary(verification: Verification) -> dict:
    risk_assessment = getattr(verification, "risk_assessment", None)
    document_classification = serialize_document_classification(verification) or {}
    return {
        "verification_id": verification.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
            "email": verification.verification_subject.email,
        },
        "risk_level": (
            risk_assessment.risk_level if risk_assessment is not None else "medium"
        ),
        "document_classification": (
            {
                "classification_status": document_classification.get(
                    "classification_status"
                ),
                "workflow_action": document_classification.get("workflow_action"),
                "requires_manual_review": document_classification.get(
                    "requires_manual_review"
                ),
                "manual_review": document_classification.get("manual_review"),
                "issues": document_classification.get("issues", []),
            }
            if document_classification
            else None
        ),
        "created_at": verification.created_at.isoformat(),
    }


class ManualReviewDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (VerificationStatus.VERIFIED, "Verified"),
            (VerificationStatus.REJECTED, "Rejected"),
            (VerificationStatus.FAILED, "Failed"),
        ]
    )
    reason_code = serializers.CharField(max_length=80)
    reason_detail = serializers.CharField(
        required=False, allow_blank=True, max_length=4000
    )

    @transaction.atomic
    def save(self, *, verification: Verification, decided_by):
        from apps.audit.services import lock_audit_chain

        caller_verification = verification
        lock_audit_chain(verification.tenant_id)
        verification = (
            Verification.objects.select_for_update(of=("self",), no_key=True)
            .select_related("verification_subject")
            .get(pk=verification.pk)
        )
        from apps.accounts.models import PlatformUser
        from apps.verifications.review_access import can_review_verification

        actor = (
            PlatformUser.objects.filter(pk=decided_by.pk).first()
            if isinstance(decided_by, PlatformUser)
            else None
        )
        if actor is None or not can_review_verification(actor, verification):
            raise serializers.ValidationError(
                {"decision": "Current reviewer authority is required."}
            )
        decided_by = actor
        terminal_statuses = {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.FAILED,
            VerificationStatus.EXPIRED,
            VerificationStatus.CANCELLED,
        }
        existing_decision = VerificationDecision.objects.filter(
            verification=verification
        ).first()
        review_routing = bool(
            existing_decision
            and existing_decision.decision_type
            in {VerificationDecisionType.AUTOMATIC, VerificationDecisionType.SYSTEM}
            and existing_decision.decision == VerificationStatus.MANUAL_REVIEW_REQUIRED
            and existing_decision.approval_status
            == VerificationApprovalStatus.NOT_REQUIRED
        )
        if verification.status in terminal_statuses or (
            existing_decision and not review_routing
        ):
            raise serializers.ValidationError(
                {"decision": "This verification already has a final outcome."}
            )
        if verification.status != VerificationStatus.MANUAL_REVIEW_REQUIRED:
            raise serializers.ValidationError(
                {
                    "decision": "Only a verification awaiting manual review can be decided."
                }
            )

        if verification.assigned_reviewer_id not in {
            None,
            getattr(decided_by, "pk", None),
        }:
            raise serializers.ValidationError(
                {"decision": "This verification is assigned to another reviewer."}
            )
        from apps.verifications.models import ReviewQueue
        from apps.verifications.review_queues import case_environment

        if (
            verification.review_owner == "tenant"
            and verification.assigned_reviewer_id is None
            and ReviewQueue.objects.filter(
                tenant_id=verification.tenant_id,
                environment=case_environment(verification),
                active=True,
                deleted_at__isnull=True,
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    "decision": "Use the queue to assign this verification before deciding."
                }
            )
        from apps.verifications.models import ReviewQueueEntry, ReviewQueueMember
        from apps.verifications.review_queues import eligible

        entry = ReviewQueueEntry.objects.filter(verification=verification).first()
        if entry:
            member = (
                ReviewQueueMember.objects.filter(queue=entry.queue, user=decided_by)
                .select_related("user")
                .first()
            )
            if (
                member is None
                or not entry.queue.active
                or not eligible(member, verification, entry.required_skills)
            ):
                raise serializers.ValidationError(
                    {"decision": "Current queue reviewer eligibility is required."}
                )
        assigned_now = verification.assigned_reviewer_id is None
        if assigned_now:
            verification.assigned_reviewer = decided_by
            verification.assigned_at = timezone.now()
            verification.save(
                update_fields=["assigned_reviewer", "assigned_at", "updated_at"]
            )

        reviewer_email = (getattr(decided_by, "email", "") or "").strip().lower()
        subject_email = (verification.verification_subject.email or "").strip().lower()
        if verification.created_by_id == getattr(decided_by, "pk", None) or (
            reviewer_email and reviewer_email == subject_email
        ):
            raise serializers.ValidationError(
                {"decision": "You cannot review your own verification."}
            )

        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.verifications.review_reasons import validate_reviewer_input

        try:
            validate_reviewer_input(
                verification,
                self.validated_data["decision"],
                self.validated_data["reason_code"],
                self.validated_data.get("reason_detail", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"reason_code": exc.messages}) from exc

        now = timezone.now()
        risk_assessment = getattr(verification, "risk_assessment", None)
        approval_required = bool(
            (verification.policy_snapshot_json or {}).get("maker_checker_required")
            or (
                risk_assessment is not None
                and risk_assessment.risk_level in {"high", "critical"}
            )
        )
        decision_values = {
            "tenant": verification.tenant,
            "decision": self.validated_data["decision"],
            "proposed_decision": self.validated_data["decision"],
            "decision_type": VerificationDecisionType.MANUAL,
            "reason_code": self.validated_data["reason_code"],
            "reason_detail": self.validated_data.get("reason_detail", ""),
            "contract_version": DECISION_CONTRACT_VERSION,
            "reason_codes_json": [self.validated_data["reason_code"]],
            "input_snapshot_json": build_decision_input_snapshot(
                verification, risk_assessment=risk_assessment
            ),
            "approval_status": (
                VerificationApprovalStatus.PENDING
                if approval_required
                else VerificationApprovalStatus.NOT_REQUIRED
            ),
            "evidence_summary_json": {
                "liveness_status": (
                    verification.liveness_checks.order_by("-checked_at").first().status
                    if verification.liveness_checks.exists()
                    else "pending"
                ),
                "face_match_status": (
                    verification.face_matches.order_by("-matched_at").first().status
                    if verification.face_matches.exists()
                    else "pending"
                ),
            },
            "decided_by": decided_by,
            "decided_at": now,
        }
        if review_routing:
            decision_values["evidence_summary_json"]["automatic_review"] = {
                "reason_code": existing_decision.reason_code,
                "reason_codes": existing_decision.reason_codes_json,
                "input_snapshot": existing_decision.input_snapshot_json,
                "evidence_summary": existing_decision.evidence_summary_json,
            }
        decision_record, _ = VerificationDecision.objects.update_or_create(
            verification=verification, defaults=decision_values
        )
        verification.decision_revision += 1
        verification.save(update_fields=["decision_revision", "updated_at"])
        if not approval_required:
            transition_verification(
                verification,
                self.validated_data["decision"],
                completed_at=now,
            )
        from apps.verifications.review_quality import sample_final_decision

        sample_final_decision(verification, decision_record)
        caller_verification.refresh_from_db(
            fields=[
                "status",
                "completed_at",
                "decision_revision",
                "assigned_reviewer",
                "assigned_at",
            ]
        )
        decision_record._review_assigned_now = assigned_now
        return decision_record


class ManualReviewApprovalSerializer(serializers.Serializer):
    reason_code = serializers.CharField(max_length=80, required=False)
    reason_detail = serializers.CharField(
        required=False, allow_blank=True, max_length=4000
    )
    decision = serializers.ChoiceField(
        choices=[
            (VerificationStatus.VERIFIED, "Verified"),
            (VerificationStatus.REJECTED, "Rejected"),
            (VerificationStatus.FAILED, "Failed"),
        ]
    )

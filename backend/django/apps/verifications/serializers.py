from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import PlatformUser
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.evidence import (
    build_verification_evidence_download_url,
    build_verification_evidence_pdf_download_url,
)
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationSession,
    VerificationStatus,
)


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
    latest_identity_document = verification.identity_documents.order_by("-created_at").first()
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
    return {
        "id": verification.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "policy": {
            "id": verification.policy_public_id,
            "name": verification.policy_snapshot_json.get("name", ""),
            "version": verification.policy_snapshot_json.get("version"),
        },
        "external_reference": verification.external_reference,
        "verification_subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
        },
        "checks": {
            "document": {"status": "pending"},
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
                "decision_type": decision_record.decision_type,
                "reason_code": decision_record.reason_code,
                "reason_detail": decision_record.reason_detail,
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
        "policy": {
            "id": verification.policy_public_id,
            "name": verification.policy_snapshot_json.get("name", ""),
            "version": verification.policy_snapshot_json.get("version"),
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
        policy_id = attrs.get("policy_id", "").strip()
        if is_api_client_request and not policy_id:
            raise serializers.ValidationError(
                {"policy_id": "Choose an active verification template."}
            )
        if policy_id:
            policy = tenant.verification_policies.filter(
                public_id=policy_id, status="active"
            ).first()
            if policy is None:
                raise serializers.ValidationError(
                    {"policy_id": "Choose an active verification template."}
                )
            attrs["policy"] = policy
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        tenant = get_request_tenant(request)
        subject_data = validated_data["verification_subject"]
        external_reference = validated_data.get("external_reference", "")
        policy = validated_data.get("policy")

        verification_subject = None
        if external_reference:
            verification_subject = (
                tenant.verification_subjects.filter(
                    external_reference=external_reference
                )
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
        else:
            expires_at = timezone.now() + timedelta(hours=24)
            policy_public_id = validated_data.get("policy_id", "")
            policy_snapshot_json = {}
        verification = Verification.objects.create(
            tenant=tenant,
            project=(
                policy.project
                if policy is not None
                else tenant.projects.filter(
                    public_id=validated_data.get("project_id")
                ).first()
                or tenant.projects.filter(is_default=True).first()
            ),
            organization=tenant.organization,
            verification_subject=verification_subject,
            policy_public_id=policy_public_id,
            policy_snapshot_json=policy_snapshot_json,
            purpose=validated_data["purpose"],
            external_reference=external_reference,
            metadata_json=validated_data.get("metadata", {}),
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
        )
        session.set_session_token(raw_session_token)
        session.save()
        verification._initial_session = session
        verification._initial_session_token = raw_session_token
        verification._verification_url = (
            f"{settings.VERIFICATION_PORTAL_BASE_URL.rstrip('/')}/{session.public_id}"
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
        "document_classification": {
            "classification_status": document_classification.get("classification_status"),
            "workflow_action": document_classification.get("workflow_action"),
            "requires_manual_review": document_classification.get("requires_manual_review"),
            "manual_review": document_classification.get("manual_review"),
            "issues": document_classification.get("issues", []),
        }
        if document_classification
        else None,
        "created_at": verification.created_at.isoformat(),
    }


class ManualReviewDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (VerificationStatus.VERIFIED, "Verified"),
            (VerificationStatus.REJECTED, "Rejected"),
            (VerificationStatus.MANUAL_REVIEW_REQUIRED, "Manual Review Required"),
            (VerificationStatus.FAILED, "Failed"),
        ]
    )
    reason_code = serializers.CharField(max_length=120)
    reason_detail = serializers.CharField(required=False, allow_blank=True)

    def save(self, *, verification: Verification, decided_by):
        now = timezone.now()
        decision_record, _ = VerificationDecision.objects.update_or_create(
            verification=verification,
            defaults={
                "tenant": verification.tenant,
                "decision": self.validated_data["decision"],
                "decision_type": VerificationDecisionType.MANUAL,
                "reason_code": self.validated_data["reason_code"],
                "reason_detail": self.validated_data["reason_detail"],
                "evidence_summary_json": {
                    "liveness_status": (
                        verification.liveness_checks.order_by("-checked_at")
                        .first()
                        .status
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
            },
        )
        verification.status = self.validated_data["decision"]
        if verification.status in {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.FAILED,
        }:
            verification.completed_at = now
            verification.save(update_fields=["status", "completed_at", "updated_at"])
        else:
            verification.save(update_fields=["status", "updated_at"])
        return decision_record


def paginate_results(queryset, page: int, page_size: int):
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return page_obj, {
        "page": page_obj.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
    }

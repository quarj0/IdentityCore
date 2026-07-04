from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework import serializers

from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationSession, VerificationStatus


def serialize_verification_subject(subject: VerificationSubject) -> dict:
    return {
        "id": subject.public_id,
        "external_reference": subject.external_reference,
        "full_name": subject.full_name,
        "email": subject.email,
        "phone_number": subject.phone_number,
    }


def serialize_verification(verification: Verification) -> dict:
    return {
        "id": verification.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "external_reference": verification.external_reference,
        "verification_subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
        },
        "checks": {
            "document": {"status": "pending"},
            "liveness": {"status": "pending", "score": None},
            "face_match": {"status": "pending", "score": None},
        },
        "decision": None,
        "created_at": verification.created_at.isoformat(),
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None,
        "expires_at": verification.expires_at.isoformat(),
    }


def serialize_verification_summary(verification: Verification) -> dict:
    return {
        "id": verification.public_id,
        "status": verification.status,
        "external_reference": verification.external_reference,
        "created_at": verification.created_at.isoformat(),
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None,
    }


class VerificationSubjectInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, default=dict)


class VerificationCreateSerializer(serializers.Serializer):
    external_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    purpose = serializers.CharField(max_length=255)
    verification_subject = VerificationSubjectInputSerializer()
    policy_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    redirect_url = serializers.URLField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)

    def create(self, validated_data):
        request = self.context["request"]
        api_client = request.api_client
        tenant = request.tenant
        subject_data = validated_data["verification_subject"]
        external_reference = validated_data.get("external_reference", "")

        verification_subject = None
        if external_reference:
            verification_subject = (
                tenant.verification_subjects.filter(external_reference=external_reference)
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

        expires_at = timezone.now() + timedelta(hours=24)
        verification = Verification.objects.create(
            tenant=tenant,
            organization=tenant.organization,
            verification_subject=verification_subject,
            policy_public_id=validated_data.get("policy_id", ""),
            policy_snapshot_json={},
            purpose=validated_data["purpose"],
            external_reference=external_reference,
            metadata_json=validated_data.get("metadata", {}),
            redirect_url=validated_data.get("redirect_url", ""),
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=expires_at,
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
        verification._verification_url = (
            f"{settings.VERIFICATION_PORTAL_BASE_URL.rstrip('/')}/{session.public_id}"
        )
        return verification


class VerificationCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


def paginate_results(queryset, page: int, page_size: int):
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return page_obj, {
        "page": page_obj.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
    }

"""Reviewer-only bounded authenticity previews; raw provider output stays encrypted."""

import base64
from io import BytesIO

from django.shortcuts import get_object_or_404
from django.http import Http404
from apps.providers.adapters import ProviderContractError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from PIL import Image, ImageOps

from apps.audit.services import record_audit_event
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.authenticity import source_size_for_capture
from apps.identity_documents.models import IdentityDocument
from apps.verifications.review_access import manual_review_queryset_for_user
from common.responses import success_response
from common.storage import get_object_bytes


def review_verification(request, verification_id):
    return get_object_or_404(
        manual_review_queryset_for_user(request.user),
        public_id=verification_id,
        deleted_at__isnull=True,
        verification_subject__deleted_at__isnull=True,
    )


class AuthenticityReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, verification_id):
        verification = review_verification(request, verification_id)
        document = (
            IdentityDocument.objects.filter(
                verification=verification,
                tenant_id=verification.tenant_id,
                deleted_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        evidence = (
            (document.extracted_data_json or {}).get("document_authenticity")
            if document
            else None
        )
        captures = []
        for entry in (evidence or {}).get("captures", [])[:20]:
            result = entry.get("result", {})
            if (
                not document.captures.filter(
                    public_id=entry.get("capture_id"), deleted_at__isnull=True
                )
                .exclude(status="deleted")
                .exists()
            ):
                continue
            captures.append(
                {
                    "capture_id": entry["capture_id"],
                    "provider_check_id": entry.get("provider_check_id"),
                    "verdict": result.get("verdict", "inconclusive"),
                    "confidence": result.get("confidence"),
                    "model_name": result.get("model_name"),
                    "model_version": result.get("model_version"),
                    "source_size": result.get("source_size"),
                    "regions": result.get("regions", []),
                    "coordinate_space": result.get("coordinate_space"),
                }
            )
        record_audit_event(
            tenant=verification.tenant,
            actor=request.user,
            request=request,
            action="document.authenticity_reviewed",
            target_type="Verification",
            target_id=verification.public_id,
            metadata={"capture_count": len(captures)},
        )
        response = success_response(
            {
                "authenticity_version": "1",
                "requires_manual_review": (evidence or {}).get(
                    "requires_manual_review"
                ),
                "captures": captures,
            },
            request=request,
        )
        response["Cache-Control"] = "no-store"
        return response


class AuthenticityPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, verification_id, capture_id):
        verification = review_verification(request, verification_id)
        capture = get_object_or_404(
            DocumentCapture.objects.select_related(
                "identity_document__verification",
                "identity_document__verification_subject",
            ),
            public_id=capture_id,
            tenant_id=verification.tenant_id,
            identity_document__verification=verification,
            deleted_at__isnull=True,
            identity_document__deleted_at__isnull=True,
        )
        try:
            _, bucket = source_size_for_capture(capture)
        except (ProviderContractError, OSError, ValueError):
            raise Http404("Document capture is unavailable.")
        content, _ = get_object_bytes(
            bucket_name=bucket, key=capture.storage_key, max_bytes=20 * 1024 * 1024
        )
        with Image.open(BytesIO(content)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1600, 1600))
            output = BytesIO()
            image.save(output, format="JPEG", quality=85)
        record_audit_event(
            tenant=verification.tenant,
            actor=request.user,
            request=request,
            action="document.capture_previewed",
            target_type="DocumentCapture",
            target_id=capture.public_id,
        )
        response = success_response(
            {
                "image": "data:image/jpeg;base64,"
                + base64.b64encode(output.getvalue()).decode("ascii")
            },
            request=request,
        )
        response["Cache-Control"] = "no-store"
        return response

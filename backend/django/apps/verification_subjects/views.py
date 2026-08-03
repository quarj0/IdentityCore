from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.verification_subjects.serializers import serialize_verification_subject
from apps.verification_subjects.models import VerificationSubjectExport
from apps.verification_subjects.services import (
    create_subject_export,
    download_subject_export,
    request_subject_deletion,
)
from common.pagination import paginate_results, pagination_params
from common.permissions import IsTenantUser
from common.responses import error_response, success_response


class VerificationSubjectListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        subjects = request.user.tenant.verification_subjects.order_by(
            "-created_at", "-pk"
        )
        search = request.query_params.get("search", "").strip()
        if search:
            subjects = subjects.filter(full_name__icontains=search)
        page, page_size = pagination_params(request.query_params)
        page_obj, pagination = paginate_results(subjects, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_verification_subject(subject)
                    for subject in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class VerificationSubjectDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, subject_id):
        subject = get_object_or_404(
            request.user.tenant.verification_subjects, public_id=subject_id
        )
        payload = serialize_verification_subject(subject)
        payload["verifications"] = [
            {
                "id": x.public_id,
                "status": x.status,
                "purpose": x.purpose,
                "created_at": x.created_at.isoformat(),
            }
            for x in subject.verifications.all()[:20]
        ]
        return success_response(payload, request=request)

    def post(self, request, subject_id):
        action = request.data.get("action")
        if action == "export":
            subject = get_object_or_404(
                request.user.tenant.verification_subjects, public_id=subject_id
            )
            return success_response(
                create_subject_export(subject=subject, actor=request.user, request=request),
                request=request,
                status=201,
            )
        if action != "delete" or request.data.get("confirm") is not True:
            return error_response(
                "confirmation_required",
                "Explicit deletion confirmation is required.",
                request=request,
                status=400,
            )
        subject = get_object_or_404(
            request.user.tenant.verification_subjects, public_id=subject_id
        )
        return success_response(
            request_subject_deletion(subject=subject, actor=request.user, request=request),
            request=request,
        )


class VerificationSubjectExportDownloadView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, export_id):
        export = get_object_or_404(
            VerificationSubjectExport.objects.select_related("subject"),
            tenant=request.user.tenant,
            public_id=export_id,
        )
        token = request.query_params.get("token", "")
        try:
            payload = download_subject_export(export=export, raw_token=token, request=request)
        except ValueError:
            return error_response(
                "export_unavailable",
                "The export token is invalid or expired.",
                request=request,
                status=404,
            )
        return success_response(payload, request=request)

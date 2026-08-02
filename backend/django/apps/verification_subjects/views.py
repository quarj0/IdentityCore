from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.verification_subjects.serializers import serialize_verification_subject
from common.pagination import paginate_results, pagination_params
from common.permissions import IsTenantUser
from common.responses import success_response


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

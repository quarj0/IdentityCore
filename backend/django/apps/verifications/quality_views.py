"""Independent QA workflow with outcome-only reports."""

from django.db.models import Count, F
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.verifications.queue_views import tenant_for
from apps.verifications.review_quality import (
    allocate_sample,
    complete_sample,
    sample_summary,
    visible_samples,
)
from common.authorization import AuthorizationAction, decide_user_access
from common.pagination import paginate_results, pagination_params
from common.responses import success_response


def scoped_samples(request, *, manage=False):
    tenant = tenant_for(request, manage=manage)
    queryset = (
        visible_samples(request.user)
        .filter(
            tenant=tenant,
            verification__deleted_at__isnull=True,
            verification__verification_subject__deleted_at__isnull=True,
        )
        .select_related("queue", "verification", "reviewer")
    )
    environment = request.query_params.get("environment", "sandbox")
    if environment not in {"sandbox", "production"}:
        raise ValidationError("Use sandbox or production environment.")
    queryset = queryset.filter(queue__environment=environment)
    if (
        not manage
        and not decide_user_access(
            request.user,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=tenant,
            review_owner="tenant",
            permission_code="manage_team",
        ).allowed
    ):
        queryset = queryset.filter(reviewer=request.user)
    return queryset


class ReviewQualityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = scoped_samples(request).order_by("created_at", "pk")
        if request.query_params.get("pending") == "true":
            queryset = queryset.filter(completed_at__isnull=True)
        elif (
            "pending" in request.query_params
            and request.query_params["pending"] != "false"
        ):
            raise ValidationError("pending must be true or false.")
        page, size = pagination_params(request.query_params)
        page_obj, pagination = paginate_results(queryset, page, size)
        return success_response(
            {
                "results": [
                    sample_summary(sample, actor=request.user)
                    for sample in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class QualityDecisionInput(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=["verified", "rejected", "failed"])
    reason_code = serializers.CharField(max_length=80)
    notes = serializers.CharField(
        max_length=4000, required=False, default="", allow_blank=True
    )


class ReviewQualityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sample_id):
        sample = get_object_or_404(scoped_samples(request), public_id=sample_id)
        return success_response(
            sample_summary(sample, actor=request.user), request=request
        )

    def post(self, request, sample_id):
        sample = get_object_or_404(scoped_samples(request), public_id=sample_id)
        serializer = QualityDecisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        sample = complete_sample(
            sample, actor=request.user, request=request, **serializer.validated_data
        )
        return success_response(
            sample_summary(sample, actor=request.user), request=request
        )


class ReviewQualityAllocateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sample_id):
        tenant_for(request, manage=True)
        sample = get_object_or_404(
            scoped_samples(request, manage=True), public_id=sample_id
        )
        sample = allocate_sample(sample, actor=request.user)
        return success_response(
            sample_summary(sample, actor=request.user), request=request
        )


class ReviewQualityReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        samples = scoped_samples(request, manage=True)
        completed = samples.filter(completed_at__isnull=False)
        outcomes = list(
            completed.values("original_outcome", "outcome")
            .annotate(count=Count("id"))
            .order_by("original_outcome", "outcome")
        )
        return success_response(
            {
                "environment": request.query_params.get("environment", "sandbox"),
                "sampled": samples.count(),
                "pending": samples.filter(completed_at__isnull=True).count(),
                "completed": completed.count(),
                "agreements": completed.filter(outcome=F("original_outcome")).count(),
                "disagreements": completed.exclude(
                    outcome=F("original_outcome")
                ).count(),
                "outcomes": outcomes,
            },
            request=request,
        )

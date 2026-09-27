from datetime import timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.verifications.models import Verification, VerificationStatus
from common.permissions import IsTenantUser
from common.responses import success_response


MIN_COHORT_SIZE = 10
SUPPORTED_WINDOWS_DAYS = {7, 30, 90}
FAILURE_REASON_GROUPS = {
    "document_quality": ("document_", "ocr_", "quality_"),
    "liveness": ("liveness_", "face_", "biometric_"),
    "provider": ("provider_",),
    "policy": ("policy_", "verification_"),
}


def _failure_group(reason_code: str) -> str:
    code = reason_code.strip().lower()
    for group, prefixes in FAILURE_REASON_GROUPS.items():
        if code.startswith(prefixes):
            return group
    return "other"


def _published_count(value: int) -> int | None:
    return value if value == 0 or value >= MIN_COHORT_SIZE else None


class ProductMetricsView(APIView):
    """Tenant-scoped aggregate metrics; source records remain the system of record."""

    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        tenant = request.user.tenant
        if (tenant.settings_json or {}).get("product_metrics_opt_out") is True:
            return success_response(
                {"status": "disabled", "reason": "tenant_opt_out"},
                request=request,
            )

        try:
            days = int(request.query_params.get("days", "30"))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"days": "Choose a 7, 30, or 90 day window."}) from exc
        if days not in SUPPORTED_WINDOWS_DAYS:
            raise ValidationError({"days": "Choose a 7, 30, or 90 day window."})

        verifications = Verification.objects.filter(
            tenant=tenant,
            created_at__gte=timezone.now() - timedelta(days=days),
        )
        cohort_size = verifications.count()
        response = {
            "status": "available",
            "window_days": days,
            "suppressed": cohort_size < MIN_COHORT_SIZE,
            "cohort_size": None,
            "completed_count": None,
            "abandoned_count": None,
            "manual_review_count": None,
            "failure_count": None,
            "completion_rate": None,
            "average_completion_latency_seconds": None,
            "failure_reason_counts": [],
        }
        if cohort_size < MIN_COHORT_SIZE:
            return success_response(response, request=request)

        completed_statuses = (
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        completed = verifications.filter(
            Q(completed_at__isnull=False) | Q(status__in=completed_statuses)
        )
        completed_count = completed.count()
        abandoned_count = verifications.filter(
            status__in=(VerificationStatus.EXPIRED, VerificationStatus.CANCELLED)
        ).count()
        review_count = verifications.filter(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        ).count()
        failures = verifications.filter(
            status__in=(VerificationStatus.REJECTED, VerificationStatus.FAILED)
        )
        failure_count = failures.count()

        latency = completed.filter(completed_at__isnull=False).aggregate(
            average=Avg(
                ExpressionWrapper(
                    F("completed_at") - F("created_at"),
                    output_field=DurationField(),
                )
            )
        )["average"]
        latency_count = completed.filter(completed_at__isnull=False).count()

        grouped_reasons: dict[str, int] = {}
        for reason_code in failures.values_list(
            "decision_record__reason_code", flat=True
        ):
            group = _failure_group(reason_code or "")
            grouped_reasons[group] = grouped_reasons.get(group, 0) + 1

        response.update(
            {
                "cohort_size": cohort_size,
                "completed_count": _published_count(completed_count),
                "abandoned_count": _published_count(abandoned_count),
                "manual_review_count": _published_count(review_count),
                "failure_count": _published_count(failure_count),
                "completion_rate": (
                    round(completed_count / cohort_size, 4)
                    if completed_count == 0 or completed_count >= MIN_COHORT_SIZE
                    else None
                ),
                "average_completion_latency_seconds": (
                    round(latency.total_seconds(), 2)
                    if latency is not None and latency_count >= MIN_COHORT_SIZE
                    else None
                ),
                "failure_reason_counts": [
                    {"category": group, "count": count}
                    for group, count in sorted(grouped_reasons.items())
                    if count >= MIN_COHORT_SIZE
                ],
            }
        )
        return success_response(response, request=request)

    def patch(self, request):
        value = request.data.get("product_metrics_opt_out")
        if type(value) is not bool:
            raise ValidationError(
                {"product_metrics_opt_out": "A boolean value is required."}
            )
        tenant = request.user.tenant
        settings_json = dict(tenant.settings_json or {})
        settings_json["product_metrics_opt_out"] = value
        tenant.settings_json = settings_json
        tenant.save(update_fields=["settings_json", "updated_at"])
        return success_response(
            {"product_metrics_opt_out": value},
            request=request,
        )

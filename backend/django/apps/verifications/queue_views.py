"""Session-authenticated tenant queue configuration and work allocation."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import PlatformUser
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.models import ReviewQueue, ReviewQueueEntry, ReviewQueueMember
from apps.verifications.review_queues import (
    COUNTRY,
    SKILL,
    admit_tenant,
    assign_next,
    entry_summary,
    validate_list,
)
from common.authorization import AuthorizationAction, decide_user_access
from common.pagination import paginate_results, pagination_params
from common.responses import success_response


def tenant_for(request, *, manage=False):
    user = request.user
    tenant = getattr(user, "tenant", None)
    if (
        tenant is None
        or user.is_platform_admin
        or not decide_user_access(
            user,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=tenant,
            review_owner="tenant",
            permission_code="manage_team" if manage else None,
        ).allowed
    ):
        raise PermissionDenied("Tenant review queue access is required.")
    if tenant.status != "active" or tenant.deleted_at is not None:
        raise PermissionDenied("The tenant is inactive.")
    return tenant


class QueueInput(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    environment = serializers.ChoiceField(choices=["sandbox", "production"])
    priority = serializers.IntegerField(min_value=0, max_value=1000, default=0)
    sla_minutes = serializers.IntegerField(min_value=1, max_value=43200, default=60)
    country_codes = serializers.JSONField(default=list)
    required_skills = serializers.JSONField(default=list)
    active = serializers.BooleanField(default=True)

    def validate_country_codes(self, value):
        return validate_list(value, COUNTRY, "country_codes")

    def validate_required_skills(self, value):
        return validate_list(value, SKILL, "required_skills")


def queue_summary(queue):
    return {
        "queue_id": queue.public_id,
        **{
            field: getattr(queue, field)
            for field in (
                "name",
                "environment",
                "priority",
                "sla_minutes",
                "country_codes",
                "required_skills",
                "active",
            )
        },
    }


class ReviewQueueListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = tenant_for(request)
        queues = ReviewQueue.objects.filter(
            tenant=tenant, deleted_at__isnull=True
        ).order_by("-priority", "created_at", "pk")
        return success_response(
            {"queues": [queue_summary(queue) for queue in queues[:100]]},
            request=request,
        )

    @transaction.atomic
    def post(self, request):
        tenant = tenant_for(request, manage=True)
        serializer = QueueInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        lock_audit_chain(tenant.pk)
        if (
            ReviewQueue.objects.filter(tenant=tenant, deleted_at__isnull=True).count()
            >= 100
        ):
            raise ValidationError("A tenant can configure at most 100 queues.")
        queue = ReviewQueue.objects.create(tenant=tenant, **serializer.validated_data)
        record_audit_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="review_queue.created",
            target_type="review_queue",
            target_id=queue.public_id,
            metadata=queue_summary(queue),
        )
        return success_response(queue_summary(queue), request=request, status=201)


class ReviewQueueDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, queue_id):
        tenant = tenant_for(request, manage=True)
        lock_audit_chain(tenant.pk)
        queue = get_object_or_404(
            ReviewQueue.objects.select_for_update(),
            tenant=tenant,
            public_id=queue_id,
            deleted_at__isnull=True,
        )
        serializer = QueueInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if (
            "environment" in serializer.validated_data
            and serializer.validated_data["environment"] != queue.environment
        ):
            raise ValidationError("Create a separate queue for another environment.")
        for field, value in serializer.validated_data.items():
            setattr(queue, field, value)
        queue.save()
        record_audit_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="review_queue.updated",
            target_type="review_queue",
            target_id=queue.public_id,
            metadata=queue_summary(queue),
        )
        return success_response(queue_summary(queue), request=request)


class QueueMemberInput(serializers.Serializer):
    user_id = serializers.CharField(max_length=64)
    skills = serializers.JSONField(default=list)
    available = serializers.BooleanField(default=True)

    def validate_skills(self, value):
        return validate_list(value, SKILL, "skills")


class ReviewQueueMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, queue_id):
        tenant = tenant_for(request, manage=True)
        queue = get_object_or_404(
            ReviewQueue, tenant=tenant, public_id=queue_id, deleted_at__isnull=True
        )
        return success_response(
            {
                "members": [
                    {
                        "user_id": member.user.public_id,
                        "skills": member.skills,
                        "available": member.available,
                    }
                    for member in queue.members.filter(
                        deleted_at__isnull=True
                    ).select_related("user")[:1000]
                ]
            },
            request=request,
        )

    @transaction.atomic
    def put(self, request, queue_id):
        tenant = tenant_for(request, manage=True)
        serializer = QueueMemberInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        lock_audit_chain(tenant.pk)
        queue = get_object_or_404(
            ReviewQueue.objects.select_for_update(),
            tenant=tenant,
            public_id=queue_id,
            deleted_at__isnull=True,
        )
        user = get_object_or_404(
            PlatformUser,
            tenant=tenant,
            public_id=serializer.validated_data["user_id"],
            status="active",
            is_platform_admin=False,
            deleted_at__isnull=True,
        )
        member, _ = ReviewQueueMember.objects.update_or_create(
            queue=queue,
            user=user,
            defaults={
                "skills": serializer.validated_data["skills"],
                "available": serializer.validated_data["available"],
            },
        )
        record_audit_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="review_queue.member_updated",
            target_type="review_queue",
            target_id=queue.public_id,
            metadata={
                "reviewer_id": user.public_id,
                "available": member.available,
                "skills": member.skills,
            },
        )
        return success_response(
            {
                "user_id": user.public_id,
                "skills": member.skills,
                "available": member.available,
            },
            request=request,
        )


class ReviewQueueCasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, queue_id):
        tenant = tenant_for(request)
        queue = get_object_or_404(
            ReviewQueue, tenant=tenant, public_id=queue_id, deleted_at__isnull=True
        )
        if (
            not queue.members.filter(
                user=request.user, deleted_at__isnull=True
            ).exists()
            and not decide_user_access(
                request.user,
                action=AuthorizationAction.MANUAL_REVIEW,
                tenant=tenant,
                review_owner="tenant",
                permission_code="manage_team",
            ).allowed
        ):
            raise PermissionDenied("Queue membership is required.")
        admit_tenant(tenant.pk, queue.environment)
        entries = (
            ReviewQueueEntry.objects.filter(
                queue=queue,
                verification__status="manual_review_required",
                verification__deleted_at__isnull=True,
            )
            .select_related("queue", "verification__assigned_reviewer")
            .order_by("-priority", "due_at", "created_at", "pk")
        )
        if "overdue" in request.query_params:
            from django.utils import timezone

            if request.query_params["overdue"] not in {"true", "false"}:
                raise ValidationError("overdue must be true or false.")
            entries = (
                entries.filter(due_at__lt=timezone.now())
                if request.query_params["overdue"] == "true"
                else entries.filter(due_at__gte=timezone.now())
            )
        if "country" in request.query_params:
            country = request.query_params["country"]
            if not COUNTRY.fullmatch(country):
                raise ValidationError("Use a two-letter country code.")
            entries = entries.filter(country_code=country)
        if "skill" in request.query_params:
            from django.db.models import TextField
            from django.db.models.functions import Cast

            skill = request.query_params["skill"]
            if not SKILL.fullmatch(skill):
                raise ValidationError("Use a valid skill code.")
            entries = entries.annotate(
                _skills=Cast("required_skills", TextField())
            ).filter(_skills__contains='"' + skill + '"')
        page, size = pagination_params(request.query_params)
        page_obj, pagination = paginate_results(entries, page, size)
        return success_response(
            {
                "results": [entry_summary(entry) for entry in page_obj.object_list],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request, queue_id):
        tenant = tenant_for(request)
        queue = get_object_or_404(
            ReviewQueue, tenant=tenant, public_id=queue_id, deleted_at__isnull=True
        )
        case = assign_next(queue, actor=request.user, request=request)
        return success_response(
            {"assignment": entry_summary(case.queue_entry) if case else None},
            request=request,
        )

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.serializers import serialize_audit_event
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.verifications.serializers import paginate_results


class AuditEventListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        queryset = request.user.tenant.audit_events.exclude(action="graphql.query").order_by("-created_at")

        actor_type = request.query_params.get("actor_type")
        action = request.query_params.get("action")
        target_type = request.query_params.get("target_type")
        target_id = request.query_params.get("target_id")
        created_from = request.query_params.get("created_from")
        created_to = request.query_params.get("created_to")

        if actor_type:
            queryset = queryset.filter(actor_type=actor_type)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_obj, pagination = paginate_results(queryset, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_audit_event(event) for event in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class AuditEventDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, event_id):
        return success_response(
            serialize_audit_event(
                request.user.tenant.audit_events.get(public_id=event_id)
            ),
            request=request,
        )

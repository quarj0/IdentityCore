from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import serialize_notification
from common.permissions import IsTenantUser
from common.responses import success_response


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        tenant_id = request.user.tenant_id
        if tenant_id is None:
            return success_response({"results": []}, request=request)
        notifications = Notification.objects.filter(
            tenant_id=tenant_id,
            channel="in_app",
            recipient_type="platform_user",
        ).order_by("-created_at")
        return success_response(
            {
                "results": [
                    serialize_notification(notification)
                    for notification in notifications
                ]
            },
            request=request,
        )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, notification_id):
        tenant_id = request.user.tenant_id
        if tenant_id is None:
            return success_response(
                {"detail": "Notification not found."},
                request=request,
                status=404,
            )
        return success_response(
            serialize_notification(
                Notification.objects.get(tenant_id=tenant_id, public_id=notification_id)
            ),
            request=request,
        )

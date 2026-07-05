from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.notifications.serializers import serialize_notification
from common.permissions import IsTenantUser
from common.responses import success_response


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        notifications = request.user.tenant.notifications.order_by("-created_at")
        return success_response(
            {
                "results": [
                    serialize_notification(notification)
                    for notification in notifications
                ]
            },
            request=request,
        )

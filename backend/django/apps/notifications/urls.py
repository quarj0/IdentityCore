from django.urls import path

from apps.notifications.views import NotificationDetailView, NotificationListView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<str:notification_id>", NotificationDetailView.as_view()),
]

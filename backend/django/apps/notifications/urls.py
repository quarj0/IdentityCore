from django.urls import path

from apps.notifications.views import NotificationListView


urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
]

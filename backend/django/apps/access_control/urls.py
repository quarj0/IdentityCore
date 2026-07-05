from django.urls import path

from apps.access_control.views import PermissionListView, RoleListView


urlpatterns = [
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
]

from django.urls import path

from apps.tenants.views import TenantDetailView


urlpatterns = [
    path("me/", TenantDetailView.as_view(), name="tenant-detail"),
]

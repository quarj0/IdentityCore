from django.urls import path

from apps.tenants.views import TenantDetailView
from apps.tenants.kms_views import TenantKMSListView, TenantKMSActionView
from common.public_api import internal_api_path


urlpatterns = [
    internal_api_path("kms-bindings", TenantKMSListView.as_view(), name="tenant-kms-list"),
    internal_api_path("kms-bindings/<str:binding_id>/<str:action>", TenantKMSActionView.as_view(), name="tenant-kms-action"),
    path("me/", TenantDetailView.as_view(), name="tenant-detail"),
]

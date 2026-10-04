from django.urls import path

from apps.analytics.views import ProductMetricsView
from common.public_api import public_api_path


urlpatterns = [
    public_api_path(
        "product-metrics",
        ProductMetricsView.as_view(),
        methods=("GET", "PATCH"),
        name="tenant-product-metrics",
    ),
]

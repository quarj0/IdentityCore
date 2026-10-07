from django.urls import path
from common.public_api import internal_api_path

from apps.consent.views import ConsentRecordListView, ConsentTemplateListView, ConsentWithdrawView


urlpatterns = [
    internal_api_path("records/<str:record_id>/withdraw", ConsentWithdrawView.as_view(), name="consent-withdraw"),
    path("templates/", ConsentTemplateListView.as_view(), name="consent-template-list"),
    path("records/", ConsentRecordListView.as_view(), name="consent-record-list"),
]

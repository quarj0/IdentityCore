from django.urls import path

from apps.consent.views import ConsentRecordListView, ConsentTemplateListView


urlpatterns = [
    path("templates/", ConsentTemplateListView.as_view(), name="consent-template-list"),
    path("records/", ConsentRecordListView.as_view(), name="consent-record-list"),
]

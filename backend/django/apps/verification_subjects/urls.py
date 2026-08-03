from django.urls import path

from apps.verification_subjects.views import (
    VerificationSubjectDetailView,
    VerificationSubjectExportDownloadView,
    VerificationSubjectListView,
)

urlpatterns = [
    path("", VerificationSubjectListView.as_view(), name="verification-subject-list"),
    path("exports/<str:export_id>", VerificationSubjectExportDownloadView.as_view()),
    path("<str:subject_id>", VerificationSubjectDetailView.as_view()),
]

from django.urls import path

from apps.verification_subjects.views import (
    VerificationSubjectDetailView,
    VerificationSubjectListView,
)

urlpatterns = [
    path("", VerificationSubjectListView.as_view(), name="verification-subject-list"),
    path("<str:subject_id>", VerificationSubjectDetailView.as_view()),
]

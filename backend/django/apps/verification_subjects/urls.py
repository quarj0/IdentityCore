from django.urls import path

from apps.verification_subjects.views import VerificationSubjectListView


urlpatterns = [
    path("", VerificationSubjectListView.as_view(), name="verification-subject-list"),
]

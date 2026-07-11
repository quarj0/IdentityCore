from django.urls import path
from .views import (
    WorkflowActionView,
    WorkflowDetailView,
    WorkflowListCreateView,
    WorkflowVersionsView,
)

urlpatterns = [
    path("", WorkflowListCreateView.as_view()),
    path("<str:workflow_id>", WorkflowDetailView.as_view()),
    path("<str:workflow_id>/versions", WorkflowVersionsView.as_view()),
    path("<str:workflow_id>/<str:action>", WorkflowActionView.as_view()),
]

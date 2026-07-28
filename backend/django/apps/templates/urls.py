from django.urls import path

from apps.templates.views import WorkflowTemplateDetailView, WorkflowTemplateListView

urlpatterns = [
    path("", WorkflowTemplateListView.as_view()),
    path("<str:template_id>", WorkflowTemplateDetailView.as_view()),
]

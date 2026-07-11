from django.urls import path
from .views import ProjectDetailView, ProjectListCreateView, ProjectStatusView

urlpatterns = [
    path("", ProjectListCreateView.as_view()),
    path("<str:project_id>", ProjectDetailView.as_view()),
    path("<str:project_id>/<str:action>", ProjectStatusView.as_view()),
]

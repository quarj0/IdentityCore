from common.public_api import public_api_path
from .views import (
    ProjectDetailView,
    ProjectListCreateView,
    ProjectStatusView,
    ProjectWorkflowInstantiationView,
)

urlpatterns = [
    public_api_path("", ProjectListCreateView.as_view(), methods=("GET", "POST")),
    public_api_path(
        "<str:project_id>/workflows:instantiate",
        ProjectWorkflowInstantiationView.as_view(),
        methods=("POST",),
    ),
    public_api_path(
        "<str:project_id>", ProjectDetailView.as_view(), methods=("GET", "PATCH")
    ),
    public_api_path(
        "<str:project_id>/<str:action>", ProjectStatusView.as_view(), methods=("POST",)
    ),
]

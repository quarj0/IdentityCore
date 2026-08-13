from common.public_api import public_api_path

from apps.audit.views import AuditEventDetailView, AuditEventListView

urlpatterns = [
    public_api_path(
        "", AuditEventListView.as_view(), methods=("GET",), name="audit-event-list"
    ),
    public_api_path(
        "<str:event_id>", AuditEventDetailView.as_view(), methods=("GET",)
    ),
]

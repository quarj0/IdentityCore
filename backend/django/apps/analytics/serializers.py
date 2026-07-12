from apps.analytics.models import AnalyticsDashboard


def serialize_analytics_dashboard(dashboard: AnalyticsDashboard) -> dict:
    return {
        "id": dashboard.public_id,
        "code": dashboard.code,
        "title": dashboard.title,
        "description": dashboard.description,
        "status": dashboard.status,
        "primary_metric": dashboard.primary_metric,
        "secondary_metric": dashboard.secondary_metric,
        "tertiary_metric": dashboard.tertiary_metric,
        "time_window": dashboard.time_window,
        "owner_team": dashboard.owner_team,
        "config": dashboard.config_json,
        "created_at": dashboard.created_at.isoformat(),
        "updated_at": dashboard.updated_at.isoformat(),
    }

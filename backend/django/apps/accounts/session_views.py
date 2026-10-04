from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from common.permissions import IsTenantUser
from rest_framework.views import APIView

from apps.accounts.models import DashboardSession, PlatformUser
from apps.accounts.sessions import _revoke_family, revoke_user_sessions
from apps.audit.services import lock_audit_chain, record_audit_event
from common.responses import success_response


def current_session(request):
    return request.auth.get("session_id") if request.auth is not None else None


class SessionListView(APIView):
    permission_classes = [IsTenantUser]

    def get(self, request):
        sessions = DashboardSession.objects.filter(
            user=request.user, deleted_at__isnull=True
        ).order_by("-last_seen_at")[:100]
        return success_response(
            {
                "results": [
                    {
                        "id": session.public_id,
                        "scope": session.scope,
                        "device_label": session.device_label,
                        "peer_network": session.peer_network,
                        "created_at": session.created_at.isoformat(),
                        "last_seen_at": session.last_seen_at.isoformat(),
                        "expires_at": session.expires_at.isoformat(),
                        "revoked_at": (
                            session.revoked_at.isoformat()
                            if session.revoked_at
                            else None
                        ),
                        "current": session.public_id == current_session(request),
                    }
                    for session in sessions
                ]
            },
            request=request,
        )


class SessionRevokeView(APIView):
    permission_classes = [IsTenantUser]

    @transaction.atomic
    def post(self, request, session_id):
        lock_audit_chain(request.user.tenant_id)
        PlatformUser.objects.select_for_update().get(pk=request.user.pk)
        session = DashboardSession.objects.filter(
            user=request.user, public_id=session_id, deleted_at__isnull=True
        ).first()
        if session is None:
            raise NotFound("Session not found.")
        _revoke_family(session.family_id)
        PlatformUser.objects.filter(pk=request.user.pk).update(
            auth_valid_after=timezone.now()
        )
        record_audit_event(
            tenant_id=request.user.tenant_id,
            actor=request.user,
            request=request,
            action="user.session_revoked",
            target_type="dashboard_session",
            target_id=session.public_id,
        )
        return success_response({"revoked": True}, request=request)


class SessionRevokeOthersView(APIView):
    permission_classes = [IsTenantUser]

    @transaction.atomic
    def post(self, request):
        session_id = current_session(request)
        if not session_id:
            raise ValidationError(
                "Refresh your session before revoking other sessions."
            )
        lock_audit_chain(request.user.tenant_id)
        revoke_user_sessions(request.user, except_session_id=session_id)
        record_audit_event(
            tenant_id=request.user.tenant_id,
            actor=request.user,
            request=request,
            action="user.other_sessions_revoked",
            target_type="platform_user",
            target_id=request.user.public_id,
        )
        return success_response({"revoked": True}, request=request)

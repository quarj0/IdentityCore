from common.observability import ENVIRONMENT, environment, set_verification_environment
import logging
from ipaddress import ip_address, ip_network

from common.credential_proofs import verify_bearer_secret
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.api_clients.models import APIClient, APIClientStatus
from apps.verifications.models import VerificationSession, VerificationSessionStatus

logger = logging.getLogger(__name__)
VERIFICATION_SESSION_REJECTION = "Invalid or expired verification session credentials."


def _verification_session_rejected(reason: str) -> AuthenticationFailed:
    logger.info(
        "Verification session authentication rejected.", extra={"reason": reason}
    )
    return AuthenticationFailed(VERIFICATION_SESSION_REJECTION)


class APIClientAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        client_id = request.headers.get("X-Client-Id")
        authorization = request.headers.get("Authorization", "")

        # A normal dashboard JWT also uses the Bearer scheme. X-Client-Id is
        # the discriminator for API-client authentication; without it, defer
        # to the configured JWT authenticator instead of rejecting the user.
        if not client_id:
            return None
        if not authorization.startswith(f"{self.keyword} "):
            raise AuthenticationFailed("Missing API client credentials.")

        raw_secret = authorization[len(self.keyword) + 1 :].strip()
        try:
            api_client = APIClient.objects.select_related("tenant", "project").get(
                client_id=client_id,
                deleted_at__isnull=True,
                tenant__deleted_at__isnull=True,
            )
        except APIClient.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid API client credentials.") from exc

        if api_client.project_id and api_client.project.deleted_at:
            raise AuthenticationFailed("Invalid API client credentials.")
        if api_client.status != APIClientStatus.ACTIVE:
            raise AuthenticationFailed("API client is not active.")
        if not api_client.verify_client_secret(raw_secret):
            raise AuthenticationFailed("Invalid API client credentials.")
        if api_client.allowed_ips and not self._is_request_ip_allowed(
            request, api_client.allowed_ips
        ):
            raise AuthenticationFailed("Request IP is not allowed for this API client.")

        api_client.last_used_at = timezone.now()
        api_client.save(update_fields=["last_used_at", "updated_at"])
        request.api_client = api_client
        request.tenant = api_client.tenant
        ENVIRONMENT.set(
            environment(
                api_client.project.environment if api_client.project else "sandbox"
            )
        )
        return (api_client, raw_secret)

    def _is_request_ip_allowed(self, request, allowed_networks: list[str]) -> bool:
        remote_addr = request.META.get("REMOTE_ADDR")
        if not remote_addr:
            return False

        address = ip_address(remote_addr)
        return any(
            address in ip_network(network, strict=False) for network in allowed_networks
        )


class VerificationSessionAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        authorization = request.headers.get("Authorization", "")
        parser_context = getattr(request, "parser_context", {}) or {}
        session_id = parser_context.get("kwargs", {}).get(
            "session_id"
        ) or request.headers.get("X-Session-Id")

        if not authorization and not session_id:
            return None
        if not authorization.startswith(f"{self.keyword} ") or not session_id:
            raise _verification_session_rejected("credentials_missing")

        raw_token = authorization[len(self.keyword) + 1 :].strip()
        try:
            verification_session = VerificationSession.objects.select_related(
                "tenant",
                "verification",
                "verification__organization",
                "verification__verification_subject",
            ).get(public_id=session_id)
        except VerificationSession.DoesNotExist as exc:
            raise _verification_session_rejected("session_not_found") from exc

        if (
            verification_session.tenant.deleted_at is not None
            or verification_session.tenant.status in {"suspended", "closed"}
            or verification_session.verification.deleted_at is not None
            or verification_session.verification.organization.deleted_at is not None
            or verification_session.tenant_id
            != verification_session.verification.tenant_id
        ):
            raise _verification_session_rejected("source_inactive")

        if not verify_bearer_secret(raw_token, verification_session.session_token_hash):
            raise _verification_session_rejected("token_mismatch")

        if verification_session.expires_at <= timezone.now():
            if verification_session.status != VerificationSessionStatus.EXPIRED:
                verification_session.status = VerificationSessionStatus.EXPIRED
                verification_session.save(update_fields=["status", "updated_at"])
            raise _verification_session_rejected("session_expired")

        # Only the withdrawal endpoint may replay an already committed withdrawal.
        # The original token, expiry and source checks above still apply, and no
        # active acceptance may remain. Revocation never restores other actions.
        view = parser_context.get("view")
        withdrawal_replay = (
            verification_session.status == VerificationSessionStatus.REVOKED
            and request.method == "POST"
            and getattr(view, "allow_consent_withdrawal_replay", False)
            and verification_session.verification.consent_records.filter(
                accepted=True, withdrawn_at__isnull=False
            ).exists()
            and not verification_session.verification.consent_records.filter(
                accepted=True, withdrawn_at__isnull=True
            ).exists()
        )
        if not withdrawal_replay and verification_session.status in {
            VerificationSessionStatus.REVOKED,
            VerificationSessionStatus.COMPLETED,
            VerificationSessionStatus.EXPIRED,
        }:
            raise _verification_session_rejected("session_inactive")

        from apps.verifications.models import SandboxSimulation
        if SandboxSimulation.objects.filter(verification=verification_session.verification).exists():
            raise _verification_session_rejected("synthetic_case")

        request.verification_session = verification_session
        request.verification = verification_session.verification
        set_verification_environment(verification_session.verification)
        request.tenant = verification_session.tenant
        return (verification_session, raw_token)


def require_verification_session_action(request, action: str) -> None:
    """Enforce the action set bound to an authenticated subject session."""
    verification_session = getattr(request, "verification_session", None)
    if verification_session is None:
        raise AuthenticationFailed("Verification session authentication is required.")
    if action not in verification_session.allowed_actions:
        raise AuthenticationFailed(
            "This verification session cannot perform that action."
        )

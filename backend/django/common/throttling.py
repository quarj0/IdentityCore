from rest_framework.throttling import BaseThrottle, SimpleRateThrottle


class APIClientRateThrottle(BaseThrottle):
    def allow_request(self, request, view):
        from apps.api_clients.usage import reserve_request

        client = getattr(request, "api_client", None)
        if client is None:
            return True
        allowed, headers, self.retry_seconds = reserve_request(client)
        raw = getattr(request, "_request", request)
        raw.api_usage_headers = headers
        return allowed

    def wait(self):
        return getattr(self, "retry_seconds", None)


class VerificationSessionRateThrottle(SimpleRateThrottle):
    scope = "verification_session"

    def get_cache_key(self, request, view):
        verification_session = getattr(request, "verification_session", None)
        if (
            verification_session is None
            or getattr(request, "api_client", None) is not None
        ):
            return None
        ident = verification_session.public_id
        return self.cache_format % {"scope": self.scope, "ident": ident}


class DashboardUserRateThrottle(SimpleRateThrottle):
    scope = "dashboard_user"

    def get_cache_key(self, request, view):
        if (
            getattr(request, "api_client", None) is not None
            or getattr(request, "verification_session", None) is not None
        ):
            return None
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return self.cache_format % {"scope": self.scope, "ident": user.public_id}


class SensitivePublicRateThrottle(SimpleRateThrottle):
    """Rate-limit public auth flows without keying on claimed identity."""

    scope = "sensitive_public"

    def get_cache_key(self, request, view):
        # REMOTE_ADDR is supplied by the immediate peer. Unlike
        # X-Forwarded-For, it cannot be rotated by an untrusted client when
        # Django's trusted proxy count is not explicitly configured.
        ident = request.META.get("REMOTE_ADDR") or "unknown"
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class MobileHandoffRateThrottle(SensitivePublicRateThrottle):
    """Verified 256-bit grants have individual buckets behind a shared BFF.

    Unauthenticated guesses retain the peer-address limit. An arbitrary claimed
    session, handoff ID or forwarded address can never select a fresh bucket.
    """

    def get_cache_key(self, request, view):
        from django.utils import timezone
        from apps.verifications.models import VerificationMobileHandoff

        data = request.data
        claim = data.get("handoff", "") if isinstance(data, dict) else ""
        source = data.get("session_id", "") if isinstance(data, dict) else ""
        if (
            isinstance(claim, str)
            and len(claim) <= 192
            and isinstance(source, str)
            and 0 < len(source) <= 64
        ):
            handoff_id, separator, secret = claim.partition(".")
            if separator and 0 < len(secret) <= 128:
                handoff = VerificationMobileHandoff.objects.filter(
                    public_id=handoff_id,
                    source_session__public_id=source,
                    redeemed_at__isnull=True,
                    expires_at__gt=timezone.now(),
                    token_hash__startswith="bearer_sha256$",
                ).first()
                if handoff and handoff.matches_token(secret):
                    return self.cache_format % {
                        "scope": self.scope,
                        "ident": f"handoff_verified:{handoff.pk}",
                    }
        peer = request.META.get("REMOTE_ADDR") or "unknown"
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"handoff_invalid:{peer}",
        }


class MFATransactionRateThrottle(SensitivePublicRateThrottle):
    """Password-verified live transactions share a user bucket; guesses use the peer."""

    def get_cache_key(self, request, view):
        from apps.accounts.mfa import resolve_mfa_token

        data = request.data
        token = data.get("mfa_token", "") if isinstance(data, dict) else ""
        purpose = getattr(view, "mfa_purpose", None)
        if (
            isinstance(token, str)
            and 0 < len(token) <= 4096
            and purpose in {"enrollment", "challenge"}
        ):
            try:
                user = resolve_mfa_token(token, purpose=purpose)
            except ValueError:
                pass
            else:
                return self.cache_format % {
                    "scope": self.scope,
                    "ident": f"mfa_verified:{user.pk}",
                }
        peer = request.META.get("REMOTE_ADDR") or "unknown"
        return self.cache_format % {"scope": self.scope, "ident": f"mfa_invalid:{peer}"}

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
        if verification_session is None:
            session_id = request.headers.get("X-Session-Id")
            if not session_id:
                return None
            ident = session_id
        else:
            ident = verification_session.public_id
        return self.cache_format % {"scope": self.scope, "ident": ident}


class DashboardUserRateThrottle(SimpleRateThrottle):
    scope = "dashboard_user"

    def get_cache_key(self, request, view):
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

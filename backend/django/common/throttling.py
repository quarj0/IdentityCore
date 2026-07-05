from rest_framework.throttling import SimpleRateThrottle


class APIClientRateThrottle(SimpleRateThrottle):
    scope = "api_client"

    def get_cache_key(self, request, view):
        api_client = getattr(request, "api_client", None)
        if api_client is None:
            return None
        return self.cache_format % {"scope": self.scope, "ident": api_client.client_id}


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

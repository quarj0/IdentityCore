import json

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from strawberry.django.views import GraphQLView

from apps.audit.services import record_audit_event
from common.responses import error_payload
from common.throttling import DashboardUserRateThrottle


class AuthenticatedGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        if not getattr(request.user, "is_authenticated", False):
            authorization = request.headers.get("Authorization")
            if authorization:
                try:
                    authenticated = JWTAuthentication().authenticate(request)
                except InvalidToken:
                    return JsonResponse(
                        error_payload(
                            "authentication_failed",
                            "Invalid authentication token.",
                            request=request,
                        ),
                        status=401,
                    )
                if authenticated is not None:
                    request.user, request.auth = authenticated
        if request.method == "POST" and getattr(
            request.user, "is_authenticated", False
        ):
            throttle = DashboardUserRateThrottle()
            if not throttle.allow_request(request, self):
                return JsonResponse(
                    error_payload(
                        "rate_limit_exceeded",
                        "Request was throttled. Please try again later.",
                        request=request,
                    ),
                    status=429,
                )
            if getattr(request.user, "tenant_id", None) is not None:
                try:
                    payload = json.loads(request.body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    payload = {}
                operation_name = payload.get("operationName") or ""
                record_audit_event(
                    tenant=request.user.tenant,
                    actor=request.user,
                    request=request,
                    action="graphql.query",
                    target_type="graphql",
                    target_id=operation_name or "anonymous",
                    metadata={"operation_name": operation_name},
                )
        return super().dispatch(request, *args, **kwargs)

    def get_context(self, request, response):
        return {"request": request, "response": response}

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from strawberry.django.views import GraphQLView

from common.responses import error_payload


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
        return super().dispatch(request, *args, **kwargs)

    def get_context(self, request, response):
        return {"request": request, "response": response}

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.serializers import LoginSerializer, RefreshInputSerializer, serialize_user
from common.responses import success_response


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return success_response(
            {
                "tokens": serializer.validated_data["tokens"],
                "user": serialize_user(user),
            },
            request=request,
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(
            {"tokens": {"access": serializer.validated_data["access"]}},
            request=request,
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response({"user": serialize_user(request.user)}, request=request)

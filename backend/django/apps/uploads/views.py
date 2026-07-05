from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.uploads.serializers import UploadCreateSerializer
from common.authentication import VerificationSessionAuthentication
from common.responses import success_response


class UploadCreateView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return success_response(payload, request=request, status=status.HTTP_201_CREATED)

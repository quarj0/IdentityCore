from django_countries import countries
from rest_framework.views import APIView

from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES
from common.responses import success_response


class DocumentTypeListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return success_response(DOCUMENT_TYPES, request=request)


class CountryProfileListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return success_response(COUNTRY_PROFILES, request=request)


class CountryListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        data = [{"code": code, "name": str(name)} for code, name in countries]
        return success_response(data, request=request)

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.templates.models import Template, TemplateStatus
from apps.templates.serializers import serialize_template
from common.permissions import IsTenantUser
from common.responses import success_response


class WorkflowTemplateListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        templates = Template.objects.select_related("created_by").filter(
            status=TemplateStatus.PUBLISHED
        )
        category = request.query_params.get("category", "").strip()
        country = request.query_params.get("country", "").strip().upper()
        search = request.query_params.get("search", "").strip()
        if category:
            templates = templates.filter(category=category)
        if search:
            templates = templates.filter(name__icontains=search)
        if country:
            templates = [
                item
                for item in templates
                if country in {code.upper() for code in item.countries_json}
            ]
        return success_response(
            {"results": [serialize_template(item) for item in templates]},
            request=request,
        )


class WorkflowTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, template_id):
        template = get_object_or_404(
            Template.objects.select_related("created_by"),
            public_id=template_id,
            status=TemplateStatus.PUBLISHED,
        )
        return success_response(serialize_template(template), request=request)

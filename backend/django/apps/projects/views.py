from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.audit.services import record_audit_event
from apps.projects.models import ProjectStatus
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer, serialize_project
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.templates.models import Template
from apps.templates.services import instantiate_workflow_template
from apps.workflows.serializers import serialize_workflow
from common.pagination import paginate_results, pagination_params


class ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        if not request.user.tenant.projects.exists():
            Project.objects.create(
                tenant=request.user.tenant,
                created_by=request.user,
                name="Default Sandbox",
                slug="default-sandbox",
                environment="sandbox",
                is_default=True,
            )
        projects = request.user.tenant.projects.all()
        environment = request.query_params.get("environment", "")
        project_status = request.query_params.get("status", "")
        if environment:
            projects = projects.filter(environment=environment)
        if project_status:
            projects = projects.filter(status=project_status)
        page, page_size = pagination_params(request.query_params)
        page_obj, pagination = paginate_results(projects, page, page_size)
        return success_response(
            {
                "results": [serialize_project(project) for project in page_obj],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        serializer = ProjectSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="project.created",
            target_type="project",
            target_id=project.public_id,
        )
        return success_response(
            serialize_project(project), request=request, status=status.HTTP_201_CREATED
        )


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get_object(self, request, project_id):
        return get_object_or_404(
            request.user.tenant.projects,
            public_id=project_id,
        )

    def get(self, request, project_id):
        return success_response(
            serialize_project(self.get_object(request, project_id)), request=request
        )

    def patch(self, request, project_id):
        project = self.get_object(request, project_id)
        serializer = ProjectSerializer(
            project, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="project.updated",
            target_type="project",
            target_id=project.public_id,
        )
        return success_response(serialize_project(project), request=request)


class ProjectStatusView(ProjectDetailView):
    def post(self, request, project_id, action):
        project = self.get_object(request, project_id)
        statuses = {
            "activate": ProjectStatus.ACTIVE,
            "reactivate": ProjectStatus.ACTIVE,
            "suspend": ProjectStatus.SUSPENDED,
        }
        if action not in statuses:
            return success_response(
                {"detail": "Unsupported action."},
                request=request,
                status=status.HTTP_400_BAD_REQUEST,
            )
        project.status = statuses[action]
        project.save(update_fields=["status", "updated_at"])
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action=f"project.{action}d",
            target_type="project",
            target_id=project.public_id,
        )
        return success_response(serialize_project(project), request=request)


class ProjectWorkflowInstantiationView(ProjectDetailView):
    def post(self, request, project_id):
        project = self.get_object(request, project_id)
        template = get_object_or_404(
            Template, public_id=request.data.get("template_id", "")
        )
        workflow, created = instantiate_workflow_template(
            request=request,
            project=project,
            template=template,
            template_version=str(request.data.get("template_version", "")),
            name=str(request.data.get("name", "")),
            idempotency_key=request.headers.get("Idempotency-Key", "").strip(),
        )
        return success_response(
            {**serialize_workflow(workflow), "created": created},
            request=request,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

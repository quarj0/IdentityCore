from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.projects.models import ProjectStatus
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer, serialize_project
from common.permissions import IsTenantUser
from common.responses import success_response


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
        return success_response(
            {
                "results": [
                    serialize_project(x) for x in request.user.tenant.projects.all()
                ]
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
        return request.user.tenant.projects.get(public_id=project_id)

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
        project.status = (
            ProjectStatus.SUSPENDED if action == "suspend" else ProjectStatus.ACTIVE
        )
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

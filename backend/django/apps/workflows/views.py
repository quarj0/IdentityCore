from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.audit.services import record_audit_event
from apps.workflows.models import WorkflowStatus
from apps.workflows.serializers import (
    WorkflowSerializer,
    publish_workflow,
    serialize_workflow,
)
from common.permissions import IsTenantUser
from common.responses import success_response


class WorkflowListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        qs = request.user.tenant.workflows.select_related("project")
        project = request.query_params.get("project_id")
        qs = qs.filter(project__public_id=project) if project else qs
        return success_response(
            {"results": [serialize_workflow(x) for x in qs]}, request=request
        )

    def post(self, request):
        s = WorkflowSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        x = s.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="workflow.created",
            target_type="workflow",
            target_id=x.public_id,
        )
        return success_response(
            serialize_workflow(x), request=request, status=status.HTTP_201_CREATED
        )


class WorkflowDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def obj(self, r, i):
        return r.user.tenant.workflows.select_related("project").get(public_id=i)

    def get(self, r, workflow_id):
        return success_response(serialize_workflow(self.obj(r, workflow_id)), request=r)

    def patch(self, r, workflow_id):
        x = self.obj(r, workflow_id)
        s = WorkflowSerializer(x, data=r.data, partial=True, context={"request": r})
        s.is_valid(raise_exception=True)
        s.save()
        return success_response(serialize_workflow(x), request=r)


class WorkflowActionView(WorkflowDetailView):
    def post(self, r, workflow_id, action):
        x = self.obj(r, workflow_id)
        if action == "publish":
            publish_workflow(x, r.user)
        elif action == "archive":
            x.status = WorkflowStatus.ARCHIVED
            x.save(update_fields=["status", "updated_at"])
        elif action == "clone":
            x.pk = None
            x.public_id = None
            x.name = f"{x.name} Copy"
            x.status = WorkflowStatus.DRAFT
            x.current_version = 0
            x.created_by = r.user
            x.save()
        else:
            return success_response(
                {"detail": "Unsupported action."}, request=r, status=400
            )
        record_audit_event(
            tenant=r.user.tenant,
            actor=r.user,
            request=r,
            action=f"workflow.{action}",
            target_type="workflow",
            target_id=x.public_id,
        )
        return success_response(serialize_workflow(x), request=r)


class WorkflowVersionsView(WorkflowDetailView):
    def get(self, r, workflow_id):
        x = self.obj(r, workflow_id)
        return success_response(
            {
                "results": [
                    {
                        "id": v.public_id,
                        "version": v.version,
                        "policy_id": v.policy.public_id,
                        "steps": v.steps_json,
                        "settings": v.settings_json,
                        "published_at": v.published_at.isoformat(),
                    }
                    for v in x.versions.select_related("policy")
                ]
            },
            request=r,
        )

import strawberry
from django_countries import countries
from django.db import models
from strawberry.types import Info

from apps.access_control.models import Role, RoleScope
from apps.accounts.models import PlatformUser
from apps.api_clients.models import APIClient
from apps.api_clients.serializers import serialize_api_client
from apps.audit.models import AuditEvent
from apps.audit.serializers import serialize_audit_event
from apps.organizations.models import Organization
from apps.organizations.models import OrganizationSupportingDocument
from apps.organizations.onboarding import (
    ORGANIZATION_TYPE_CHOICES,
    serialize_organization_review_state,
    serialize_onboarding_state,
)
from apps.organizations.serializers import serialize_organization
from apps.providers.models import Provider
from apps.providers.serializers import serialize_provider
from apps.reviewers.models import PlatformAdminInvitation
from apps.accounts.serializers import serialize_user
from apps.verification_policies.models import VerificationPolicy
from apps.verification_policies.serializers import serialize_verification_policy
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.serializers import paginate_results, serialize_manual_review_summary, serialize_verification
from apps.webhooks.models import WebhookEndpoint
from apps.webhooks.serializers import serialize_webhook_endpoint
from apps.tenants.models import Tenant
from apps.tenants.serializers import serialize_tenant
from apps.projects.models import Project
from apps.organizations.models import OrganizationSupportingDocument
from apps.workflows.models import Workflow, WorkflowVersion

from config.graphql_auth import require_platform_admin, require_tenant_user, serialize_platform_admin_invitation
from config.graphql_types import (
    APIClientNode,
    AuditEventNode,
    CountryNode,
    CountryProfileNode,
    DocumentTypeNode,
    ManualReviewNode,
    OrganizationOnboardingNode,
    PlatformAdminInvitationNode,
    PlatformRoleNode,
    ProviderNode,
    SupportedDocumentTypeNode,
    VerificationNode,
    VerificationPolicyNode,
    WebhookEndpointNode,
    VerificationSubjectNode,
    RiskAssessmentNode,
    VerificationCheckNode,
    VerificationChecksNode,
    VerificationDecisionNode,
    AuthUserNode,
    OrganizationNode,
    OrganizationSupportingDocumentNode,
    PlatformDashboardSummaryNode,
    to_onboarding_node,
    to_verification_node,
    TenantNode,
    ProjectNode,
    WorkflowNode,
    WorkflowVersionNode,
)
from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES


@strawberry.type
class Query:
    @strawberry.field
    def document_types(self) -> list[DocumentTypeNode]:
        return [DocumentTypeNode(**item) for item in DOCUMENT_TYPES]

    @strawberry.field
    def country_profiles(self) -> list[CountryProfileNode]:
        return [
            CountryProfileNode(
                code=item["code"],
                name=item["name"],
                supported_document_types=[
                    SupportedDocumentTypeNode(**supported_document_type)
                    for supported_document_type in item["supported_document_types"]
                ],
            )
            for item in COUNTRY_PROFILES
        ]

    @strawberry.field
    def countries(self) -> list[CountryNode]:
        return [CountryNode(code=code, name=str(name)) for code, name in countries]

    @strawberry.field
    def organization_onboarding_types(self) -> list[str]:
        return list(ORGANIZATION_TYPE_CHOICES)

    @strawberry.field
    def organization_onboarding(self, info: Info) -> OrganizationOnboardingNode:
        user = require_tenant_user(info)
        return to_onboarding_node(
            serialize_onboarding_state(
                organization=user.tenant.organization,
                tenant=user.tenant,
                user=user,
            )
        )

    @strawberry.field
    def organization_review_queue(
        self, info: Info, page: int = 1, page_size: int = 20
    ) -> list[OrganizationOnboardingNode]:
        require_platform_admin(info)
        queryset = (
            Organization.objects.filter(status="pending_review")
            .select_related("tenant")
            .order_by("-updated_at")
        )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            to_onboarding_node(serialize_organization_review_state(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def organization_review(
        self, info: Info, organization_id: str
    ) -> OrganizationOnboardingNode | None:
        require_platform_admin(info)
        organization = (
            Organization.objects.select_related("tenant")
            .filter(public_id=organization_id, status="pending_review")
            .first()
        )
        if organization is None:
            return None
        return to_onboarding_node(serialize_organization_review_state(organization))

    @strawberry.field
    def platform_audit_events(
        self,
        info: Info,
        actor_type: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuditEventNode]:
        require_platform_admin(info)
        queryset = AuditEvent.objects.select_related("tenant").order_by("-created_at")
        if actor_type:
            queryset = queryset.filter(actor_type=actor_type)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            AuditEventNode(
                id=payload["id"],
                actor_type=payload["actor_type"],
                actor_id=payload["actor_id"],
                action=payload["action"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                ip_address=payload["ip_address"],
                user_agent=payload["user_agent"],
                metadata=payload["metadata"],
                created_at=payload["created_at"],
            )
            for payload in (
                serialize_audit_event(item) for item in page_obj.object_list
            )
        ]

    @strawberry.field
    def platform_providers(self, info: Info) -> list[ProviderNode]:
        require_platform_admin(info)
        return [
            ProviderNode(**serialize_provider(provider))
            for provider in Provider.objects.order_by("provider_type", "name")
        ]

    @strawberry.field
    def platform_provider(self, info: Info, provider_id: str) -> ProviderNode | None:
        require_platform_admin(info)
        provider = Provider.objects.filter(public_id=provider_id).first()
        return ProviderNode(**serialize_provider(provider)) if provider else None

    @strawberry.field
    def platform_verification_policies(
        self, info: Info, page: int = 1, page_size: int = 50
    ) -> list[VerificationPolicyNode]:
        require_platform_admin(info)
        queryset = VerificationPolicy.objects.select_related("tenant", "project").order_by(
            "name", "-version"
        )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            VerificationPolicyNode(**serialize_verification_policy(policy))
            for policy in page_obj.object_list
        ]

    @strawberry.field
    def platform_verification_policy(
        self, info: Info, policy_id: str
    ) -> VerificationPolicyNode | None:
        require_platform_admin(info)
        policy = VerificationPolicy.objects.filter(public_id=policy_id).first()
        return VerificationPolicyNode(**serialize_verification_policy(policy)) if policy else None

    @strawberry.field
    def platform_api_clients(
        self, info: Info, page: int = 1, page_size: int = 50
    ) -> list[APIClientNode]:
        require_platform_admin(info)
        queryset = APIClient.objects.select_related("tenant").order_by("name")
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            APIClientNode(**serialize_api_client(api_client))
            for api_client in page_obj.object_list
        ]

    @strawberry.field
    def platform_api_client(
        self, info: Info, client_id: str
    ) -> APIClientNode | None:
        require_platform_admin(info)
        api_client = APIClient.objects.filter(public_id=client_id).first()
        return APIClientNode(**serialize_api_client(api_client)) if api_client else None

    @strawberry.field
    def platform_webhook_endpoints(
        self, info: Info, page: int = 1, page_size: int = 50
    ) -> list[WebhookEndpointNode]:
        require_platform_admin(info)
        queryset = WebhookEndpoint.objects.select_related("tenant").order_by("url")
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            WebhookEndpointNode(**serialize_webhook_endpoint(endpoint))
            for endpoint in page_obj.object_list
        ]

    @strawberry.field
    def platform_webhook_endpoint(
        self, info: Info, webhook_id: str
    ) -> WebhookEndpointNode | None:
        require_platform_admin(info)
        endpoint = WebhookEndpoint.objects.filter(public_id=webhook_id).first()
        return WebhookEndpointNode(**serialize_webhook_endpoint(endpoint)) if endpoint else None

    @strawberry.field
    def platform_admins(self, info: Info) -> list[AuthUserNode]:
        require_platform_admin(info)
        users = (
            PlatformUser.objects.filter(is_platform_admin=True)
            .prefetch_related("user_roles__role")
            .order_by("email")
        )
        return [AuthUserNode(**serialize_user(user)) for user in users]

    @strawberry.field
    def platform_admin_invitations(self, info: Info) -> list[PlatformAdminInvitationNode]:
        require_platform_admin(info)
        return [
            PlatformAdminInvitationNode(**serialize_platform_admin_invitation(invitation))
            for invitation in PlatformAdminInvitation.objects.select_related("role", "invited_by").order_by("-created_at")
        ]

    @strawberry.field
    def platform_admin_invitation(
        self, info: Info, invitation_id: str
    ) -> PlatformAdminInvitationNode | None:
        require_platform_admin(info)
        invitation = (
            PlatformAdminInvitation.objects.select_related("role", "invited_by")
            .filter(public_id=invitation_id)
            .first()
        )
        return (
            PlatformAdminInvitationNode(
                **serialize_platform_admin_invitation(invitation)
            )
            if invitation
            else None
        )

    @strawberry.field
    def platform_roles(self, info: Info) -> list[PlatformRoleNode]:
        require_platform_admin(info)
        queryset = Role.objects.filter(scope=RoleScope.PLATFORM).order_by("name")
        return [
            PlatformRoleNode(
                id=role.public_id,
                name=role.name,
                description=role.description,
                scope=role.scope,
                status=role.status,
                member_count=role.user_roles.count(),
            )
            for role in queryset
        ]

    @strawberry.field
    def platform_role(self, info: Info, role_id: str) -> PlatformRoleNode | None:
        require_platform_admin(info)
        role = Role.objects.filter(public_id=role_id, scope=RoleScope.PLATFORM).first()
        return (
            PlatformRoleNode(
                id=role.public_id,
                name=role.name,
                description=role.description,
                scope=role.scope,
                status=role.status,
                member_count=role.user_roles.count(),
            )
            if role
            else None
        )

    @strawberry.field
    def platform_audit_event(self, info: Info, audit_id: str) -> AuditEventNode | None:
        require_platform_admin(info)
        event = AuditEvent.objects.filter(public_id=audit_id).first()
        if event is None:
            return None
        payload = serialize_audit_event(event)
        return AuditEventNode(
            id=payload["id"],
            actor_type=payload["actor_type"],
            actor_id=payload["actor_id"],
            action=payload["action"],
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            ip_address=payload["ip_address"],
            user_agent=payload["user_agent"],
            metadata=payload["metadata"],
            created_at=payload["created_at"],
        )

    @strawberry.field
    def platform_dashboard_summary(self, info: Info) -> PlatformDashboardSummaryNode:
        require_platform_admin(info)
        return PlatformDashboardSummaryNode(
            organizations_total=Organization.objects.count(),
            organizations_pending_review=Organization.objects.filter(
                status="pending_review"
            ).count(),
            organizations_active=Organization.objects.filter(status="active").count(),
            tenants_total=Tenant.objects.count(),
            tenants_pending_review=Tenant.objects.filter(status="pending_review").count(),
            users_total=PlatformUser.objects.count(),
            platform_admins_total=PlatformUser.objects.filter(
                is_platform_admin=True
            ).count(),
            api_clients_total=APIClient.objects.count(),
            webhook_endpoints_total=WebhookEndpoint.objects.count(),
            providers_total=Provider.objects.count(),
            audit_events_total=AuditEvent.objects.count(),
            workflows_total=Workflow.objects.count(),
            workflow_versions_total=WorkflowVersion.objects.count(),
        )

    @strawberry.field
    def platform_organizations(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[OrganizationNode]:
        require_platform_admin(info)
        queryset = Organization.objects.select_related("tenant").order_by("-updated_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(slug__icontains=search)
                | models.Q(industry__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [OrganizationNode(**serialize_organization(item)) for item in page_obj.object_list]

    @strawberry.field
    def platform_organization(
        self, info: Info, organization_id: str
    ) -> OrganizationNode | None:
        require_platform_admin(info)
        organization = (
            Organization.objects.select_related("tenant")
            .filter(public_id=organization_id)
            .first()
        )
        return OrganizationNode(**serialize_organization(organization)) if organization else None

    @strawberry.field
    def platform_organization_supporting_documents(
        self, info: Info, organization_id: str
    ) -> list[OrganizationSupportingDocumentNode]:
        require_platform_admin(info)
        queryset = (
            OrganizationSupportingDocument.objects.select_related("organization", "tenant", "uploaded_by")
            .filter(organization__public_id=organization_id)
            .order_by("-created_at")
        )
        return [
            OrganizationSupportingDocumentNode(
                id=document.public_id,
                organization_id=document.organization.public_id,
                tenant_id=document.tenant.public_id,
                uploaded_by_id=document.uploaded_by.public_id,
                uploaded_by_email=document.uploaded_by.email,
                filename=document.filename,
                mime_type=document.mime_type,
                file_size_bytes=document.file_size_bytes,
                storage_key=document.storage_key,
                status=document.status,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat(),
            )
            for document in queryset
        ]

    @strawberry.field
    def platform_tenants(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[TenantNode]:
        require_platform_admin(info)
        queryset = Tenant.objects.select_related("organization").order_by("-updated_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(slug__icontains=search)
                | models.Q(organization__name__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [TenantNode(**serialize_tenant(item)) for item in page_obj.object_list]

    @strawberry.field
    def platform_tenant(self, info: Info, tenant_id: str) -> TenantNode | None:
        require_platform_admin(info)
        tenant = (
            Tenant.objects.select_related("organization")
            .filter(public_id=tenant_id)
            .first()
        )
        return TenantNode(**serialize_tenant(tenant)) if tenant else None

    @strawberry.field
    def platform_users(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuthUserNode]:
        require_platform_admin(info)
        queryset = PlatformUser.objects.select_related("tenant").prefetch_related("user_roles__role").order_by("email")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [AuthUserNode(**serialize_user(item)) for item in page_obj.object_list]

    @strawberry.field
    def platform_user(self, info: Info, user_id: str) -> AuthUserNode | None:
        require_platform_admin(info)
        user = (
            PlatformUser.objects.select_related("tenant")
            .prefetch_related("user_roles__role")
            .filter(public_id=user_id)
            .first()
        )
        return AuthUserNode(**serialize_user(user)) if user else None

    @strawberry.field
    def platform_projects(
        self,
        info: Info,
        environment: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ProjectNode]:
        require_platform_admin(info)
        queryset = Project.objects.select_related("tenant", "tenant__organization").order_by("environment", "name")
        if environment:
            queryset = queryset.filter(environment=environment)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(slug__icontains=search)
                | models.Q(tenant__name__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            ProjectNode(
                id=project.public_id,
                tenant_id=project.tenant.public_id,
                tenant_name=project.tenant.name,
                name=project.name,
                slug=project.slug,
                environment=project.environment,
                status=project.status,
                allowed_origins=project.allowed_origins,
                is_default=project.is_default,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
            )
            for project in page_obj.object_list
        ]

    @strawberry.field
    def platform_workflows(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[WorkflowNode]:
        require_platform_admin(info)
        queryset = Workflow.objects.select_related("tenant", "project", "created_by").order_by("name")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(project__name__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            WorkflowNode(
                id=workflow.public_id,
                tenant_id=workflow.tenant.public_id,
                project_id=workflow.project.public_id,
                project_name=workflow.project.name,
                name=workflow.name,
                description=workflow.description,
                status=workflow.status,
                steps=workflow.steps_json,
                settings=workflow.settings_json,
                current_version=workflow.current_version,
                created_by_id=workflow.created_by.public_id,
                created_by_email=workflow.created_by.email,
                created_at=workflow.created_at.isoformat(),
                updated_at=workflow.updated_at.isoformat(),
            )
            for workflow in page_obj.object_list
        ]

    @strawberry.field
    def platform_workflow(
        self, info: Info, workflow_id: str
    ) -> WorkflowNode | None:
        require_platform_admin(info)
        workflow = (
            Workflow.objects.select_related("tenant", "project", "created_by")
            .filter(public_id=workflow_id)
            .first()
        )
        if workflow is None:
            return None
        return WorkflowNode(
            id=workflow.public_id,
            tenant_id=workflow.tenant.public_id,
            project_id=workflow.project.public_id,
            project_name=workflow.project.name,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status,
            steps=workflow.steps_json,
            settings=workflow.settings_json,
            current_version=workflow.current_version,
            created_by_id=workflow.created_by.public_id,
            created_by_email=workflow.created_by.email,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat(),
        )

    @strawberry.field
    def platform_workflow_versions(
        self,
        info: Info,
        workflow_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[WorkflowVersionNode]:
        require_platform_admin(info)
        queryset = WorkflowVersion.objects.select_related(
            "workflow", "policy", "published_by"
        ).order_by("-version")
        if workflow_id:
            queryset = queryset.filter(workflow__public_id=workflow_id)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            WorkflowVersionNode(
                id=item.public_id,
                workflow_id=item.workflow.public_id,
                workflow_name=item.workflow.name,
                version=item.version,
                steps=item.steps_json,
                settings=item.settings_json,
                policy_id=item.policy.public_id,
                policy_name=item.policy.name,
                published_by_id=item.published_by.public_id,
                published_by_email=item.published_by.email,
                published_at=item.published_at.isoformat(),
            )
            for item in page_obj.object_list
        ]

    @strawberry.field
    def verifications(
        self,
        info: Info,
        status: str | None = None,
        external_reference: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[VerificationNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.verifications.select_related(
            "verification_subject"
        ).order_by("-created_at")
        if status:
            queryset = queryset.filter(status=status)
        if external_reference:
            queryset = queryset.filter(external_reference=external_reference)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            to_verification_node(
                serialize_verification(item, request=info.context["request"])
            )
            for item in page_obj.object_list
        ]

    @strawberry.field
    def verification(self, info: Info, verification_id: str) -> VerificationNode | None:
        user = require_tenant_user(info)
        verification = (
            user.tenant.verifications.select_related("verification_subject")
            .filter(public_id=verification_id)
            .first()
        )
        return (
            to_verification_node(
                serialize_verification(verification, request=info.context["request"])
            )
            if verification
            else None
        )

    @strawberry.field
    def manual_reviews(
        self, info: Info, page: int = 1, page_size: int = 20
    ) -> list[ManualReviewNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.verifications.filter(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        ).order_by("-created_at")
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            ManualReviewNode(**serialize_manual_review_summary(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def policies(self, info: Info) -> list[VerificationPolicyNode]:
        user = require_tenant_user(info)
        return [
            VerificationPolicyNode(**serialize_verification_policy(policy))
            for policy in user.tenant.verification_policies.order_by("name", "-version")
        ]

    @strawberry.field
    def api_clients(self, info: Info) -> list[APIClientNode]:
        user = require_tenant_user(info)
        return [
            APIClientNode(**serialize_api_client(api_client))
            for api_client in user.tenant.api_clients.select_related("tenant").order_by(
                "name"
            )
        ]

    @strawberry.field
    def webhook_endpoints(self, info: Info) -> list[WebhookEndpointNode]:
        user = require_tenant_user(info)
        return [
            WebhookEndpointNode(**serialize_webhook_endpoint(endpoint))
            for endpoint in user.tenant.webhook_endpoints.order_by("url")
        ]

    @strawberry.field
    def audit_events(
        self,
        info: Info,
        actor_type: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuditEventNode]:
        user = require_tenant_user(info)
        queryset = user.tenant.audit_events.order_by("-created_at")
        if actor_type:
            queryset = queryset.filter(actor_type=actor_type)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            AuditEventNode(
                id=payload["id"],
                actor_type=payload["actor_type"],
                actor_id=payload["actor_id"],
                action=payload["action"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                ip_address=payload["ip_address"],
                user_agent=payload["user_agent"],
                metadata=payload["metadata"],
                created_at=payload["created_at"],
            )
            for payload in (
                serialize_audit_event(item) for item in page_obj.object_list
            )
        ]

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
from apps.platform_settings.models import PlatformSetting
from apps.platform_settings.services import get_platform_setting_record, list_platform_settings
from apps.platform_settings.serializers import (
    serialize_platform_setting,
    serialize_platform_setting_revision,
)
from apps.providers.models import Provider
from apps.providers.models import ProviderAssignment
from apps.providers.models import ProviderCheck
from apps.providers.serializers import serialize_provider
from apps.providers.serializers import serialize_provider_assignment
from apps.providers.serializers import serialize_provider_check
from apps.reviewers.models import PlatformAdminInvitation
from apps.accounts.serializers import serialize_user
from apps.analytics.models import AnalyticsDashboard
from apps.analytics.serializers import serialize_analytics_dashboard
from apps.billing.models import BillingRecord
from apps.billing.serializers import serialize_billing_record
from apps.feature_flags.models import FeatureFlag
from apps.feature_flags.serializers import serialize_feature_flag
from apps.incidents.models import Incident
from apps.incidents.serializers import serialize_incident
from apps.verification_policies.models import VerificationPolicy
from apps.verification_policies.serializers import serialize_verification_policy
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.serializers import paginate_results, serialize_manual_review_summary, serialize_verification
from apps.security.models import SecurityCase
from apps.security.serializers import serialize_security_case
from apps.support.models import SupportTicket
from apps.support.serializers import serialize_support_ticket
from apps.templates.models import Template
from apps.templates.serializers import serialize_template
from apps.webhooks.models import WebhookEndpoint
from apps.webhooks.serializers import serialize_webhook_endpoint
from apps.tenants.models import Tenant
from apps.tenants.serializers import serialize_tenant
from apps.projects.models import Project
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
    PlatformSettingNode,
    PlatformSettingRevisionNode,
    ProviderNode,
    ProviderAssignmentNode,
    ProviderCheckNode,
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
    BillingRecordNode,
    AnalyticsDashboardNode,
    IncidentNode,
    SecurityCaseNode,
    SupportTicketNode,
    TemplateNode,
    FeatureFlagNode,
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
        queryset = (
            AuditEvent.objects.select_related("tenant")
            .exclude(action="graphql.query")
            .order_by("-created_at")
        )
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
                action_label=payload["action_label"],
                actor_display_name=payload["actor_display_name"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                target_label=payload["target_label"],
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
    def platform_ai_providers(
        self,
        info: Info,
        provider_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[ProviderNode]:
        require_platform_admin(info)
        queryset = Provider.objects.filter(
            provider_type__in=[
                "document",
                "biometric",
                "liveness",
                "risk",
                "identity_database",
            ]
        ).order_by("provider_type", "name")
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(code__icontains=search)
                | models.Q(provider_type__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [ProviderNode(**serialize_provider(provider)) for provider in page_obj.object_list]

    @strawberry.field
    def platform_ai_provider(self, info: Info, provider_id: str) -> ProviderNode | None:
        require_platform_admin(info)
        provider = Provider.objects.filter(public_id=provider_id).first()
        return ProviderNode(**serialize_provider(provider)) if provider else None

    @strawberry.field
    def platform_provider_checks(
        self,
        info: Info,
        provider_id: str | None = None,
        check_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[ProviderCheckNode]:
        require_platform_admin(info)
        queryset = ProviderCheck.objects.select_related("verification", "provider").order_by(
            "-started_at"
        )
        if provider_id:
            queryset = queryset.filter(provider__public_id=provider_id)
        if check_type:
            queryset = queryset.filter(check_type=check_type)
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            ProviderCheckNode(**serialize_provider_check(item))
            for item in page_obj.object_list
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
    def platform_settings(self, info: Info) -> list[PlatformSettingNode]:
        require_platform_admin(info)
        return [
            PlatformSettingNode(
                id=item["id"],
                key=item["key"],
                title=item["title"],
                category=item["group"],
                status=item["status"],
                primary_value=str(item["value"]),
                secondary_value=str(item["default_value"]),
                owner_team="Platform Ops",
                description=item["description"],
                updated_at=item["updated_at"] or "",
                is_editable=item["is_editable"],
                is_secret=item["is_secret"],
                requires_restart=item["requires_restart"],
                default_value=item["default_value"],
            )
            for item in list_platform_settings()
        ]

    @strawberry.field
    def platform_setting(self, info: Info, setting_id: str) -> PlatformSettingNode | None:
        require_platform_admin(info)
        setting = (
            PlatformSetting.objects.filter(public_id=setting_id).first()
            or get_platform_setting_record(setting_id)
            or get_platform_setting_record(setting_id.strip().lower())
        )
        if setting is None:
            return None
        payload = serialize_platform_setting(setting)
        return PlatformSettingNode(
            id=payload["id"],
            key=payload["key"],
            title=payload["title"],
            category=payload["group"],
            status=payload["status"],
            primary_value=str(payload["value"]),
            secondary_value=str(payload["default_value"]),
            owner_team="Platform Ops",
            description=payload["description"],
            updated_at=payload["updated_at"],
            is_editable=payload["is_editable"],
            is_secret=payload["is_secret"],
            requires_restart=payload["requires_restart"],
            default_value=payload["default_value"],
        )

    @strawberry.field
    def platform_setting_revisions(
        self, info: Info, setting_id: str
    ) -> list[PlatformSettingRevisionNode]:
        require_platform_admin(info)
        setting = (
            PlatformSetting.objects.filter(public_id=setting_id).first()
            or get_platform_setting_record(setting_id)
            or get_platform_setting_record(setting_id.strip().lower())
        )
        if setting is None:
            return []
        return [
            PlatformSettingRevisionNode(
                id=item["id"],
                setting_id=item["setting_id"],
                old_value=item["old_value"],
                new_value=item["new_value"],
                change_reason=item["change_reason"],
                changed_by_email=item["changed_by_email"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            for item in (
                serialize_platform_setting_revision(revision)
                for revision in setting.revisions.select_related("changed_by")
            )
        ]

    @strawberry.field
    def platform_provider_assignments(
        self,
        info: Info,
        tenant_id: str | None = None,
        assignment_key: str | None = None,
    ) -> list[ProviderAssignmentNode]:
        require_platform_admin(info)
        queryset = ProviderAssignment.objects.select_related("tenant", "provider").order_by(
            "tenant_id", "assignment_key"
        )
        if tenant_id:
            queryset = queryset.filter(tenant__public_id=tenant_id)
        if assignment_key:
            queryset = queryset.filter(assignment_key=assignment_key)
        return [
            ProviderAssignmentNode(**serialize_provider_assignment(item))
            for item in queryset
        ]

    @strawberry.field
    def platform_provider_assignment(
        self, info: Info, assignment_id: str
    ) -> ProviderAssignmentNode | None:
        require_platform_admin(info)
        assignment = (
            ProviderAssignment.objects.select_related("tenant", "provider")
            .filter(public_id=assignment_id)
            .first()
        )
        return (
            ProviderAssignmentNode(**serialize_provider_assignment(assignment))
            if assignment
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
            action_label=payload["action_label"],
            actor_display_name=payload["actor_display_name"],
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            target_label=payload["target_label"],
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
            billing_records_total=BillingRecord.objects.count(),
            analytics_dashboards_total=AnalyticsDashboard.objects.count(),
            incidents_total=Incident.objects.count(),
            security_cases_total=SecurityCase.objects.count(),
            support_tickets_total=SupportTicket.objects.count(),
            templates_total=Template.objects.count(),
            feature_flags_total=FeatureFlag.objects.count(),
        )

    @strawberry.field
    def platform_billing_records(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[BillingRecordNode]:
        require_platform_admin(info)
        queryset = BillingRecord.objects.select_related("organization", "tenant").order_by("-updated_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(subtitle__icontains=search)
                | models.Q(organization__name__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            BillingRecordNode(**serialize_billing_record(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def platform_billing_record(
        self, info: Info, billing_id: str
    ) -> BillingRecordNode | None:
        require_platform_admin(info)
        record = (
            BillingRecord.objects.select_related("organization", "tenant")
            .filter(public_id=billing_id)
            .first()
        )
        return BillingRecordNode(**serialize_billing_record(record)) if record else None

    @strawberry.field
    def platform_analytics_dashboards(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AnalyticsDashboardNode]:
        require_platform_admin(info)
        queryset = AnalyticsDashboard.objects.order_by("title")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(code__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            AnalyticsDashboardNode(**serialize_analytics_dashboard(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def platform_analytics_dashboard(
        self, info: Info, dashboard_id: str
    ) -> AnalyticsDashboardNode | None:
        require_platform_admin(info)
        dashboard = AnalyticsDashboard.objects.filter(public_id=dashboard_id).first()
        return (
            AnalyticsDashboardNode(**serialize_analytics_dashboard(dashboard))
            if dashboard
            else None
        )

    @strawberry.field
    def platform_incidents(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[IncidentNode]:
        require_platform_admin(info)
        queryset = Incident.objects.order_by("-detected_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(summary__icontains=search)
                | models.Q(owner_team__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [IncidentNode(**serialize_incident(item)) for item in page_obj.object_list]

    @strawberry.field
    def platform_incident(self, info: Info, incident_id: str) -> IncidentNode | None:
        require_platform_admin(info)
        incident = Incident.objects.filter(public_id=incident_id).first()
        return IncidentNode(**serialize_incident(incident)) if incident else None

    @strawberry.field
    def platform_security_cases(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[SecurityCaseNode]:
        require_platform_admin(info)
        queryset = SecurityCase.objects.order_by("-detected_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(summary__icontains=search)
                | models.Q(owner_team__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            SecurityCaseNode(**serialize_security_case(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def platform_security_case(
        self, info: Info, security_id: str
    ) -> SecurityCaseNode | None:
        require_platform_admin(info)
        case = SecurityCase.objects.filter(public_id=security_id).first()
        return SecurityCaseNode(**serialize_security_case(case)) if case else None

    @strawberry.field
    def platform_support_tickets(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[SupportTicketNode]:
        require_platform_admin(info)
        queryset = SupportTicket.objects.select_related("organization").order_by("-updated_at")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(summary__icontains=search)
                | models.Q(owner_team__icontains=search)
                | models.Q(issue_type__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            SupportTicketNode(**serialize_support_ticket(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def platform_support_ticket(
        self, info: Info, ticket_id: str
    ) -> SupportTicketNode | None:
        require_platform_admin(info)
        ticket = (
            SupportTicket.objects.select_related("organization")
            .filter(public_id=ticket_id)
            .first()
        )
        return SupportTicketNode(**serialize_support_ticket(ticket)) if ticket else None

    @strawberry.field
    def platform_templates(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[TemplateNode]:
        require_platform_admin(info)
        queryset = Template.objects.select_related("created_by").order_by("name")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(category__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [TemplateNode(**serialize_template(item)) for item in page_obj.object_list]

    @strawberry.field
    def platform_template(
        self, info: Info, template_id: str
    ) -> TemplateNode | None:
        require_platform_admin(info)
        template = (
            Template.objects.select_related("created_by")
            .filter(public_id=template_id)
            .first()
        )
        return TemplateNode(**serialize_template(template)) if template else None

    @strawberry.field
    def platform_feature_flags(
        self,
        info: Info,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[FeatureFlagNode]:
        require_platform_admin(info)
        queryset = FeatureFlag.objects.select_related("created_by").order_by("key")
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(key__icontains=search)
                | models.Q(title__icontains=search)
                | models.Q(owner_team__icontains=search)
            )
        page_obj, _ = paginate_results(queryset, page, page_size)
        return [
            FeatureFlagNode(**serialize_feature_flag(item))
            for item in page_obj.object_list
        ]

    @strawberry.field
    def platform_feature_flag(
        self, info: Info, flag_id: str
    ) -> FeatureFlagNode | None:
        require_platform_admin(info)
        flag = (
            FeatureFlag.objects.select_related("created_by")
            .filter(public_id=flag_id)
            .first()
        )
        return FeatureFlagNode(**serialize_feature_flag(flag)) if flag else None

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
        queryset = (
            user.tenant.verifications.filter(
                status=VerificationStatus.MANUAL_REVIEW_REQUIRED
            )
            .exclude(metadata_json__workflow="administrator_onboarding")
            .order_by("-created_at")
        )
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
        queryset = user.tenant.audit_events.exclude(action="graphql.query").order_by("-created_at")
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
                action_label=payload["action_label"],
                actor_display_name=payload["actor_display_name"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                target_label=payload["target_label"],
                ip_address=payload["ip_address"],
                user_agent=payload["user_agent"],
                metadata=payload["metadata"],
                created_at=payload["created_at"],
            )
            for payload in (
                serialize_audit_event(item) for item in page_obj.object_list
            )
        ]

import logging
from datetime import timedelta

import strawberry
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from graphql import GraphQLError
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError as DRFValidationError,
)
from rest_framework_simplejwt.tokens import RefreshToken
from strawberry.types import Info

from apps.access_control.models import Role, RoleScope, UserRole
from apps.accounts.contact import submit_contact_inquiry
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.accounts.passwords import (
    request_password_reset,
    reset_password_with_token,
    change_password as perform_password_change,
)
from apps.accounts.serializers import LoginSerializer, serialize_user
from apps.accounts.verification import (
    build_email_verification_url,
    verify_email_token_with_status,
)
from apps.audit.services import record_audit_event
from apps.platform_settings.services import (
    get_platform_setting_value,
    reset_platform_setting,
    upsert_platform_setting,
)
from apps.platform_settings.serializers import serialize_platform_setting
from apps.notifications.services import queue_verification_status_notifications
from apps.organizations.models import Organization
from apps.organizations.onboarding import (
    confirm_onboarding_email_verification,
    register_organization_onboarding,
    resend_onboarding_email_verification,
    review_organization_onboarding,
    serialize_organization_review_state,
    serialize_onboarding_state,
    submit_administrator_identity_verification,
    submit_organization_verification,
    assign_platform_review_reviewer,
    escalate_platform_review,
)
from apps.reviewers.models import PlatformAdminInvitation, PlatformAdminInvitationStatus
from apps.providers.models import Provider, ProviderAssignment
from apps.providers.serializers import serialize_provider, serialize_provider_assignment
from apps.verifications.models import (
    Verification,
    VerificationSession,
    VerificationSessionStatus,
    VerificationStatus,
)
from apps.verifications.review_access import manual_review_queryset_for_user
from apps.tenants.models import Tenant
from apps.projects.models import Project
from apps.templates.models import Template, TemplateStatus, TemplateCategory
from apps.templates.serializers import serialize_template
from apps.workflows.models import Workflow, WorkflowStatus, WorkflowVersion
from apps.verification_policies.models import VerificationPolicy, VerificationPolicyStatus
from apps.verifications.serializers import (
    ManualReviewDecisionSerializer,
    VerificationCreateSerializer,
    serialize_manual_review_summary,
    serialize_verification,
    paginate_results,
)
from apps.webhooks.services import queue_webhook_events

from config.graphql_auth import (
    ensure_platform_role,
    raise_graphql_validation_error,
    require_authenticated_user,
    require_platform_admin,
    require_tenant_user,
    serialize_platform_admin_invitation,
)
from config.graphql_types import (
    AdministratorVerificationLaunchNode,
    AuthPayload,
    AuthTokensNode,
    AuthUserNode,
    ContactInquiryInput,
    ContactInquiryPayload,
    ManualDecisionPayload,
    PlatformSettingChangeInput,
    PlatformSettingNode,
    OrganizationOnboardingPayload,
    OrganizationVerificationInput,
    PlatformAdminInvitationNode,
    PlatformAdminInvitationPayload,
    PublicActionPayload,
    RegisterOrganizationOnboardingInput,
    ProviderAssignmentInput,
    ProviderAssignmentNode,
    ProviderRegistrationInput,
    ProviderNode,
    to_onboarding_node,
    TemplateNode,
    WorkflowNode,
    WorkflowVersionNode,
)


logger = logging.getLogger(__name__)


@strawberry.type
class Mutation:

    def _template_node(self, template: Template) -> TemplateNode:
        return TemplateNode(**serialize_template(template))

    def _workflow_node(self, workflow: Workflow) -> WorkflowNode:
        return WorkflowNode(
            id=workflow.public_id, tenant_id=workflow.tenant.public_id,
            project_id=workflow.project.public_id, project_name=workflow.project.name,
            name=workflow.name, description=workflow.description, status=workflow.status,
            steps=workflow.steps_json, settings=workflow.settings_json,
            current_version=workflow.current_version, created_by_id=workflow.created_by.public_id,
            created_by_email=workflow.created_by.email, created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat(),
        )

    @strawberry.mutation
    def create_platform_template(self, info: Info, name: str, description: str, category: str, countries: list[str] | None = None, required_checks: list[str] | None = None, owner_team: str = "", risk_level: str = "") -> TemplateNode:
        actor = require_platform_admin(info)
        if category not in TemplateCategory.values or not name.strip() or not description.strip():
            raise GraphQLError("A name, description, and valid category are required.")
        template = Template.objects.create(name=name.strip(), description=description.strip(), category=category, status=TemplateStatus.DRAFT, version="1.0", countries_json=countries or [], required_checks_json=required_checks or [], owner_team=owner_team.strip(), risk_level=risk_level.strip(), created_by=actor)
        record_audit_event(actor=actor, request=info.context["request"], action="template.created", target_type="template", target_id=template.public_id)
        return self._template_node(template)

    @strawberry.mutation
    def update_platform_template(self, info: Info, template_id: str, name: str | None = None, description: str | None = None, category: str | None = None, countries: list[str] | None = None, required_checks: list[str] | None = None, owner_team: str | None = None, risk_level: str | None = None) -> TemplateNode:
        actor = require_platform_admin(info)
        template = get_object_or_404(Template, public_id=template_id)
        if template.status == TemplateStatus.ARCHIVED:
            raise GraphQLError("Archived templates cannot be edited.")
        if category is not None and category not in TemplateCategory.values:
            raise GraphQLError("Choose a valid template category.")
        for field, value in {"name": name.strip() if name else None, "description": description.strip() if description else None, "category": category, "countries_json": countries, "required_checks_json": required_checks, "owner_team": owner_team.strip() if owner_team is not None else None, "risk_level": risk_level.strip() if risk_level is not None else None}.items():
            if value is not None: setattr(template, field, value)
        template.save()
        record_audit_event(actor=actor, request=info.context["request"], action="template.updated", target_type="template", target_id=template.public_id)
        return self._template_node(template)

    @strawberry.mutation
    def clone_platform_template(self, info: Info, template_id: str, name: str) -> TemplateNode:
        actor = require_platform_admin(info); source = get_object_or_404(Template, public_id=template_id)
        if not name.strip(): raise GraphQLError("A clone name is required.")
        clone = Template.objects.create(name=name.strip(), description=source.description, category=source.category, status=TemplateStatus.DRAFT, version="1.0", countries_json=source.countries_json, required_checks_json=source.required_checks_json, owner_team=source.owner_team, risk_level=source.risk_level, created_by=actor)
        record_audit_event(actor=actor, request=info.context["request"], action="template.cloned", target_type="template", target_id=clone.public_id, metadata={"source_id": source.public_id})
        return self._template_node(clone)

    @strawberry.mutation
    def publish_platform_template(self, info: Info, template_id: str) -> TemplateNode:
        actor = require_platform_admin(info); template = get_object_or_404(Template, public_id=template_id)
        if not template.required_checks_json: raise GraphQLError("Add at least one required check before publishing.")
        template.status = TemplateStatus.PUBLISHED; template.save(update_fields=["status", "updated_at"])
        record_audit_event(actor=actor, request=info.context["request"], action="template.published", target_type="template", target_id=template.public_id)
        return self._template_node(template)

    @strawberry.mutation
    def archive_platform_template(self, info: Info, template_id: str) -> TemplateNode:
        actor = require_platform_admin(info); template = get_object_or_404(Template, public_id=template_id)
        template.status = TemplateStatus.ARCHIVED; template.save(update_fields=["status", "updated_at"])
        record_audit_event(actor=actor, request=info.context["request"], action="template.archived", target_type="template", target_id=template.public_id)
        return self._template_node(template)

    @strawberry.mutation
    def create_platform_workflow(self, info: Info, tenant_id: str, project_id: str, name: str, description: str = "", steps: list[strawberry.scalars.JSON] | None = None, settings: strawberry.scalars.JSON | None = None) -> WorkflowNode:
        actor = require_platform_admin(info); tenant = get_object_or_404(Tenant, public_id=tenant_id); project = get_object_or_404(Project, public_id=project_id)
        if project.tenant_id != tenant.id or not name.strip(): raise GraphQLError("Choose a project in the selected tenant and provide a name.")
        workflow = Workflow.objects.create(tenant=tenant, project=project, name=name.strip(), description=description.strip(), steps_json=steps or [], settings_json=settings or {}, created_by=actor)
        record_audit_event(tenant=tenant, actor=actor, request=info.context["request"], action="workflow.created", target_type="workflow", target_id=workflow.public_id)
        return self._workflow_node(workflow)

    @strawberry.mutation
    def clone_platform_workflow(self, info: Info, workflow_id: str, name: str) -> WorkflowNode:
        actor = require_platform_admin(info)
        source = get_object_or_404(
            Workflow.objects.select_related("tenant", "project", "created_by"),
            public_id=workflow_id,
        )
        if not name.strip():
            raise GraphQLError("A clone name is required.")
        clone = Workflow.objects.create(
            tenant=source.tenant, project=source.project, name=name.strip(),
            description=source.description, steps_json=source.steps_json,
            settings_json=source.settings_json, status=WorkflowStatus.DRAFT,
            created_by=actor,
        )
        record_audit_event(
            tenant=clone.tenant, actor=actor, request=info.context["request"],
            action="workflow.cloned", target_type="workflow", target_id=clone.public_id,
            metadata={"source_id": source.public_id},
        )
        return self._workflow_node(clone)

    @strawberry.mutation
    def update_platform_workflow(self, info: Info, workflow_id: str, name: str | None = None, description: str | None = None, steps: list[strawberry.scalars.JSON] | None = None, settings: strawberry.scalars.JSON | None = None) -> WorkflowNode:
        actor = require_platform_admin(info); workflow = get_object_or_404(Workflow.objects.select_related("tenant", "project", "created_by"), public_id=workflow_id)
        if workflow.status == WorkflowStatus.ARCHIVED: raise GraphQLError("Archived workflows cannot be edited.")
        if name is not None: workflow.name = name.strip()
        if description is not None: workflow.description = description.strip()
        if steps is not None: workflow.steps_json = steps
        if settings is not None: workflow.settings_json = settings
        workflow.save(); record_audit_event(tenant=workflow.tenant, actor=actor, request=info.context["request"], action="workflow.updated", target_type="workflow", target_id=workflow.public_id)
        return self._workflow_node(workflow)

    @strawberry.mutation
    def publish_platform_workflow(self, info: Info, workflow_id: str) -> WorkflowVersionNode:
        actor = require_platform_admin(info)
        workflow = get_object_or_404(
            Workflow.objects.select_related("tenant", "project", "created_by"),
            public_id=workflow_id,
        )
        if not workflow.steps_json:
            raise GraphQLError("Add at least one workflow step before publishing.")
        version = workflow.current_version + 1
        policy = VerificationPolicy.objects.create(
            tenant=workflow.tenant, project=workflow.project,
            name=f"{workflow.name} workflow policy", version=version,
            status=VerificationPolicyStatus.ACTIVE, created_by=actor,
        )
        workflow_version = WorkflowVersion.objects.create(
            workflow=workflow, version=version, steps_json=workflow.steps_json,
            settings_json=workflow.settings_json, policy=policy, published_by=actor,
        )
        workflow.current_version = version
        workflow.status = WorkflowStatus.PUBLISHED
        workflow.save(update_fields=["current_version", "status", "updated_at"])
        record_audit_event(
            tenant=workflow.tenant, actor=actor, request=info.context["request"],
            action="workflow.published", target_type="workflow", target_id=workflow.public_id,
            metadata={"version": version, "policy_id": policy.public_id},
        )
        return WorkflowVersionNode(
            id=workflow_version.public_id, workflow_id=workflow.public_id,
            workflow_name=workflow.name, version=version, steps=workflow.steps_json,
            settings=workflow.settings_json, policy_id=policy.public_id, policy_name=policy.name,
            published_by_id=actor.public_id, published_by_email=actor.email,
            published_at=workflow_version.published_at.isoformat(),
        )

    @strawberry.mutation
    def archive_platform_workflow(self, info: Info, workflow_id: str) -> WorkflowNode:
        actor = require_platform_admin(info); workflow = get_object_or_404(Workflow.objects.select_related("tenant", "project", "created_by"), public_id=workflow_id)
        workflow.status = WorkflowStatus.ARCHIVED; workflow.save(update_fields=["status", "updated_at"]); record_audit_event(tenant=workflow.tenant, actor=actor, request=info.context["request"], action="workflow.archived", target_type="workflow", target_id=workflow.public_id)
        return self._workflow_node(workflow)

    @strawberry.mutation
    def create_administrator_onboarding_verification(
        self, info: Info, reason: str = ""
    ) -> AdministratorVerificationLaunchNode:
        request = info.context["request"]
        user = require_tenant_user(info)
        allowed_reasons = {
            "previous_attempt_failed_or_expired",
            "periodic_compliance_renewal",
            "identity_document_changed",
            "suspected_evidence_compromise",
        }
        normalized_reason = reason.strip()
        if normalized_reason and normalized_reason not in allowed_reasons:
            raise GraphQLError("Choose a valid reason for reverification.")

        latest = (
            user.created_verifications.filter(
                purpose="Administrator identity onboarding"
            )
            .order_by("-created_at")
            .first()
        )
        terminal_statuses = {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.EXPIRED,
            VerificationStatus.CANCELLED,
            VerificationStatus.FAILED,
        }
        if (
            latest is not None
            and latest.expires_at <= timezone.now()
            and latest.status not in terminal_statuses
        ):
            latest.status = VerificationStatus.EXPIRED
            latest.save(update_fields=["status", "updated_at"])
        if latest is not None and latest.status not in terminal_statuses:
            latest.sessions.exclude(status=VerificationSessionStatus.REVOKED).update(
                status=VerificationSessionStatus.REVOKED
            )
            raw_token = VerificationSession.generate_session_token()
            session = VerificationSession(
                verification=latest,
                tenant=latest.tenant,
                expires_at=latest.expires_at,
            )
            session.set_session_token(raw_token)
            session.save()
            verification_portal_base_url = str(
                get_platform_setting_value(
                    "integrations.verification_portal_base_url",
                    settings.VERIFICATION_PORTAL_BASE_URL,
                )
            )
            url = (
                f"{verification_portal_base_url.rstrip('/')}/{session.public_id}"
                f"#token={raw_token}&verification_id={latest.public_id}"
            )
            record_audit_event(
                tenant=latest.tenant,
                actor=user,
                request=request,
                action="onboarding.administrator_verification_resumed",
                target_type="verification",
                target_id=latest.public_id,
                metadata={"session_id": session.public_id},
            )
            return AdministratorVerificationLaunchNode(
                verification_id=latest.public_id,
                session_id=session.public_id,
                session_token=raw_token,
                verification_url=url,
                expires_at=session.expires_at.isoformat(),
                action="resume",
            )
        if (
            latest is not None
            and latest.status == VerificationStatus.VERIFIED
            and not normalized_reason
        ):
            raise GraphQLError(
                "Administrator identity is already verified. Choose a reason to start reverification."
            )
        if latest is not None and not normalized_reason:
            normalized_reason = "previous_attempt_failed_or_expired"
        serializer = VerificationCreateSerializer(
            data={
                "purpose": "Administrator identity onboarding",
                "verification_subject": {
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                },
                "metadata": {
                    "workflow": "administrator_onboarding",
                    "country_code": serialize_onboarding_state(
                        organization=user.tenant.organization,
                        tenant=user.tenant,
                        user=user,
                    )["administrator_country"],
                    "document_type": "national_id",
                    "reverification_reason": normalized_reason,
                },
            },
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as exc:
            raise GraphQLError(str(exc.detail))
        verification = serializer.save()
        action = "reverify" if latest is not None else "initial"
        record_audit_event(
            tenant=verification.tenant,
            actor=user,
            request=request,
            action=f"onboarding.administrator_verification_{action}",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"reason": normalized_reason},
        )
        return AdministratorVerificationLaunchNode(
            verification_id=verification.public_id,
            session_id=verification._initial_session.public_id,
            session_token=verification._initial_session_token,
            verification_url=verification._verification_url,
            expires_at=verification.expires_at.isoformat(),
            action=action,
        )

    @strawberry.mutation
    def invite_platform_admin(
        self,
        info: Info,
        email: str,
        role_name: str = "Platform Admin",
        role_description: str = "",
        expires_in_days: int = 7,
    ) -> PlatformAdminInvitationPayload:
        actor = require_platform_admin(info)
        request = info.context["request"]
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise GraphQLError("Email is required.")
        if PlatformUser.objects.filter(email=normalized_email).exists():
            raise GraphQLError("An account already exists for this email address.")
        if PlatformAdminInvitation.objects.filter(
            email=normalized_email,
            status=PlatformAdminInvitationStatus.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise GraphQLError("A pending invitation already exists for this email address.")
        role = ensure_platform_role(
            name=role_name.strip() or "Platform Admin",
            description=role_description.strip(),
            created_by=actor,
        )
        raw_token = PlatformAdminInvitation.generate_token()
        invitation = PlatformAdminInvitation.objects.create(
            email=normalized_email,
            role=role,
            invited_by=actor,
            expires_at=timezone.now() + timedelta(days=max(expires_in_days, 1)),
        )
        invitation.set_token(raw_token)
        invitation.save(update_fields=["token_hash", "updated_at"])
        if getattr(actor, "tenant_id", None) is not None:
            record_audit_event(
                tenant=actor.tenant,
                actor=actor,
                request=request,
                action="platform_admin.invited",
                target_type="platform_admin_invitation",
                target_id=invitation.public_id,
                metadata={"email": normalized_email, "role": role.name},
            )
        return PlatformAdminInvitationPayload(
            invitation=PlatformAdminInvitationNode(
                **serialize_platform_admin_invitation(invitation)
            ),
            debug_accept_token=raw_token if settings.DEBUG else None,
        )

    @strawberry.mutation
    def accept_platform_admin_invitation(
        self,
        info: Info,
        token: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> AuthPayload:
        request = info.context["request"]
        digest = PlatformAdminInvitation.digest_token(token.strip())
        invitation = (
            PlatformAdminInvitation.objects.select_related("role")
            .filter(
                token_hash=digest,
                status=PlatformAdminInvitationStatus.PENDING,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if invitation is None:
            raise GraphQLError("Invitation is invalid or expired.")
        if PlatformUser.objects.filter(email=invitation.email).exists():
            raise GraphQLError("An account already exists for this email address.")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        user = PlatformUser.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            status=PlatformUserStatus.ACTIVE,
            is_platform_admin=True,
        )
        UserRole.objects.create(user=user, role=invitation.role, tenant=None)
        invitation.status = PlatformAdminInvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at", "updated_at"])
        refresh = RefreshToken.for_user(user)
        if getattr(user, "tenant_id", None) is not None:
            record_audit_event(
                tenant=user.tenant,
                actor=user,
                request=request,
                action="platform_admin.invitation_accepted",
                target_type="platform_admin_invitation",
                target_id=invitation.public_id,
                metadata={"email": invitation.email, "role": invitation.role.name},
            )
        return AuthPayload(
            tokens=AuthTokensNode(
                access=str(refresh.access_token), refresh=str(refresh)
            ),
            user=AuthUserNode(**serialize_user(user)),
        )

    @strawberry.mutation
    def deactivate_platform_admin(
        self, info: Info, user_id: str, reason: str = ""
    ) -> AuthUserNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        if actor.public_id == user_id:
            raise GraphQLError("You cannot deactivate your own platform administrator account.")
        user = get_object_or_404(
            PlatformUser, public_id=user_id, is_platform_admin=True
        )
        if user.status != PlatformUserStatus.ACTIVE:
            raise GraphQLError("This platform administrator is already inactive.")
        if PlatformUser.objects.filter(
            is_platform_admin=True, status=PlatformUserStatus.ACTIVE
        ).count() <= 1:
            raise GraphQLError("The final active platform administrator cannot be deactivated.")
        user.status = PlatformUserStatus.INACTIVE
        user.save(update_fields=["status", "updated_at"])
        if getattr(actor, "tenant_id", None) is not None:
            record_audit_event(
                tenant=actor.tenant,
                actor=actor,
                request=request,
                action="platform_admin.deactivated",
                target_type="platform_user",
                target_id=user.public_id,
                metadata={"email": user.email, "reason": reason.strip()},
            )
        return AuthUserNode(**serialize_user(user))

    @strawberry.mutation
    def assign_platform_role(
        self, info: Info, user_id: str, role_id: str
    ) -> AuthUserNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        user = get_object_or_404(
            PlatformUser, public_id=user_id, is_platform_admin=True
        )
        role = get_object_or_404(Role, public_id=role_id, scope=RoleScope.PLATFORM)
        UserRole.objects.get_or_create(user=user, role=role, tenant=None)
        if getattr(actor, "tenant_id", None) is not None:
            record_audit_event(
                tenant=actor.tenant,
                actor=actor,
                request=request,
                action="platform_admin.role_assigned",
                target_type="platform_user",
                target_id=user.public_id,
                metadata={"role": role.name},
            )
        return AuthUserNode(**serialize_user(user))

    @strawberry.mutation
    def upsert_platform_setting(
        self, info: Info, input: PlatformSettingChangeInput
    ) -> PlatformSettingNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        setting = upsert_platform_setting(
            key=input.key.strip().lower(),
            value=input.value,
            changed_by=actor,
            change_reason=input.change_reason.strip(),
        )
        record_audit_event(
            tenant=actor.tenant,
            actor=actor,
            request=request,
            action="platform_setting.updated",
            target_type="platform_setting",
            target_id=setting.public_id,
            metadata={"key": setting.key},
        )
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

    @strawberry.mutation
    def reset_platform_setting(self, info: Info, setting_key: str) -> PlatformSettingNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        setting = reset_platform_setting(
            key=setting_key.strip().lower(),
            changed_by=actor,
            change_reason="reset to default",
        )
        record_audit_event(
            tenant=actor.tenant,
            actor=actor,
            request=request,
            action="platform_setting.reset",
            target_type="platform_setting",
            target_id=setting.public_id,
            metadata={"key": setting.key},
        )
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

    @strawberry.mutation
    def register_platform_provider(
        self, info: Info, input: ProviderRegistrationInput
    ) -> ProviderNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        tenant = (
            get_object_or_404(Tenant, public_id=input.tenant_id)
            if input.tenant_id
            else None
        )
        provider, _ = Provider.objects.update_or_create(
            code=input.code.strip(),
            defaults={
                "tenant": tenant,
                "name": input.name.strip(),
                "provider_type": input.provider_type,
                "status": input.status,
                "configuration_json": input.configuration,
            },
        )
        record_audit_event(
            tenant=actor.tenant,
            actor=actor,
            request=request,
            action="provider.registered",
            target_type="provider",
            target_id=provider.public_id,
            metadata={"code": provider.code, "tenant_id": tenant.public_id if tenant else None},
        )
        return ProviderNode(**serialize_provider(provider))

    @strawberry.mutation
    def assign_tenant_provider(
        self, info: Info, input: ProviderAssignmentInput
    ) -> ProviderAssignmentNode:
        actor = require_platform_admin(info)
        request = info.context["request"]
        tenant = get_object_or_404(Tenant, public_id=input.tenant_id)
        provider = get_object_or_404(Provider, public_id=input.provider_id)
        assignment, _ = ProviderAssignment.objects.update_or_create(
            tenant=tenant,
            assignment_key=input.assignment_key,
            defaults={
                "provider": provider,
                "status": input.status,
                "notes": input.notes.strip(),
            },
        )
        record_audit_event(
            tenant=actor.tenant,
            actor=actor,
            request=request,
            action="provider.assignment_updated",
            target_type="provider_assignment",
            target_id=assignment.public_id,
            metadata={
                "tenant_id": tenant.public_id,
                "provider_id": provider.public_id,
                "assignment_key": assignment.assignment_key,
            },
        )
        return ProviderAssignmentNode(**serialize_provider_assignment(assignment))

    @strawberry.mutation
    def assign_organization_review_reviewer(
        self, info: Info, organization_id: str, reviewer_id: str
    ) -> OrganizationOnboardingPayload:
        actor = require_platform_admin(info)
        request = info.context["request"]
        organization = get_object_or_404(Organization, public_id=organization_id)
        reviewer = get_object_or_404(
            PlatformUser, public_id=reviewer_id, is_platform_admin=True
        )
        try:
            reviewed = assign_platform_review_reviewer(
                organization=organization,
                reviewer=reviewer,
                actor=actor,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_organization_review_state(reviewed)
            ),
            next_action="await_platform_review",
        )

    @strawberry.mutation
    def escalate_organization_review(
        self, info: Info, organization_id: str, reason: str
    ) -> OrganizationOnboardingPayload:
        actor = require_platform_admin(info)
        request = info.context["request"]
        organization = get_object_or_404(Organization, public_id=organization_id)
        try:
            escalated = escalate_platform_review(
                organization=organization, actor=actor, reason=reason, request=request
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_organization_review_state(escalated)
            ),
            next_action="await_platform_review",
        )

    @strawberry.mutation
    def login(self, info: Info, email: str, password: str) -> AuthPayload:
        request = info.context["request"]
        serializer = LoginSerializer(
            data={"email": email, "password": password},
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except (DRFValidationError, AuthenticationFailed) as exc:
            raise GraphQLError(str(exc.detail))
        user = serializer.validated_data["user"]
        if user.tenant is not None:
            record_audit_event(
                tenant=user.tenant,
                actor=user,
                request=request,
                action="user.login",
                target_type="platform_user",
                target_id=user.public_id,
                metadata={"email": user.email},
                sensitive_metadata={"email": user.email},
            )
        return AuthPayload(
            tokens=AuthTokensNode(access=serializer.validated_data["tokens"]["access"]),
            user=AuthUserNode(**serialize_user(user)),
        )

    @strawberry.mutation
    def request_password_reset(
        self,
        info: Info,
        email: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        sent = request_password_reset(email=email, request=request)
        return PublicActionPayload(
            ok=sent,
            message="If that email exists, a password reset link has been sent.",
            next_action="reset_password",
        )

    @strawberry.mutation
    def reset_password(
        self,
        info: Info,
        token: str,
        new_password: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        try:
            reset_password_with_token(
                token=token,
                new_password=new_password,
                request=request,
            )
        except (ValidationError, ValueError) as exc:
            raise GraphQLError(str(exc))
        return PublicActionPayload(
            ok=True,
            message="Your password has been reset successfully.",
            next_action="sign_in",
        )

    @strawberry.mutation
    def change_password(
        self,
        info: Info,
        current_password: str,
        new_password: str,
    ) -> PublicActionPayload:
        user = require_authenticated_user(info)
        request = info.context["request"]
        try:
            perform_password_change(
                user=user,
                current_password=current_password,
                new_password=new_password,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return PublicActionPayload(
            ok=True,
            message="Your password has been changed successfully.",
            next_action="account_updated",
        )

    @strawberry.mutation
    def register_organization_onboarding(
        self,
        info: Info,
        input: RegisterOrganizationOnboardingInput,
    ) -> OrganizationOnboardingPayload:
        request = info.context["request"]
        try:
            organization, tenant, user, raw_verification_token = (
                register_organization_onboarding(
                    full_name=input.full_name,
                    business_email=input.business_email,
                    password=input.password,
                    organization_name=input.organization_name,
                    organization_type=input.organization_type,
                    organization_country=input.organization_country,
                    website=input.website,
                    support_email=input.support_email,
                    phone_number=input.phone_number,
                    request=request,
                )
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=user,
                )
            ),
            next_action="verify_email",
            debug_email_verification_url=(
                build_email_verification_url(raw_verification_token)
                if settings.DEBUG
                else None
            ),
        )

    @strawberry.mutation
    def resend_organization_onboarding_email_verification(
        self,
        info: Info,
        business_email: str,
    ) -> PublicActionPayload:
        request = info.context["request"]
        try:
            sent = resend_onboarding_email_verification(
                business_email=business_email,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return PublicActionPayload(
            ok=sent,
            message=(
                "A new onboarding verification link has been sent."
                if sent
                else "Unable to resend the onboarding verification link for that address."
            ),
            next_action="verify_email",
        )

    @strawberry.mutation
    def submit_contact_inquiry(
        self,
        info: Info,
        input: ContactInquiryInput,
    ) -> ContactInquiryPayload:
        try:
            inquiry = submit_contact_inquiry(
                full_name=input.full_name,
                business_email=input.business_email,
                organization_name=input.organization_name,
                interest=input.interest,
                message=input.message,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return ContactInquiryPayload(
            inquiry_id=inquiry.public_id,
            ok=True,
            message="Your message has been received. Our team will follow up soon.",
        )

    @strawberry.mutation
    def verify_organization_onboarding_email(
        self, info: Info, token: str
    ) -> OrganizationOnboardingPayload:
        request = info.context["request"]
        try:
            verification = verify_email_token_with_status(token)
            user = verification.user
            if verification.already_verified:
                tenant = user.tenant
                organization = tenant.organization
                verified_user = user
            else:
                organization, tenant, verified_user = (
                    confirm_onboarding_email_verification(
                        user=user,
                        actor=user,
                        request=request,
                    )
                )
        except (ValidationError, ValueError) as exc:
            raise GraphQLError(str(exc))
        except Exception as exc:
            logger.exception(
                "Unexpected failure while verifying an organization onboarding email",
                exc_info=exc,
            )
            raise GraphQLError(
                "We could not verify this email link right now. Please try again shortly."
            ) from exc
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=verified_user,
                )
            ),
            next_action="submit_organization_verification",
            message=(
                "Email already verified. You can continue onboarding."
                if verification.already_verified
                else "Email verified. You can continue onboarding."
            ),
            email_already_verified=verification.already_verified,
        )

    @strawberry.mutation
    def submit_organization_onboarding_verification(
        self,
        info: Info,
        input: OrganizationVerificationInput,
    ) -> OrganizationOnboardingPayload:
        user = require_tenant_user(info)
        request = info.context["request"]
        try:
            organization, tenant, tenant_user = submit_organization_verification(
                user=user,
                business_registration_number=input.business_registration_number,
                registered_address=input.registered_address,
                official_website=input.official_website,
                tax_identification_number=input.tax_identification_number,
                supporting_document_keys=input.supporting_document_keys,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        onboarding = serialize_onboarding_state(
            organization=organization,
            tenant=tenant,
            user=tenant_user,
        )
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(onboarding),
            next_action=(
                "await_platform_review"
                if onboarding["current_step"] == "platform_review"
                else "submit_administrator_identity_verification"
            ),
        )

    @strawberry.mutation
    def submit_administrator_identity_onboarding_verification(
        self, info: Info, verification_id: str = ""
    ) -> OrganizationOnboardingPayload:
        user = require_tenant_user(info)
        request = info.context["request"]
        try:
            organization, tenant, tenant_user = (
                submit_administrator_identity_verification(
                    user=user,
                    verification_id=verification_id,
                    request=request,
                )
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=organization,
                    tenant=tenant,
                    user=tenant_user,
                )
            ),
            next_action="await_platform_review",
        )

    @strawberry.mutation
    def review_organization_onboarding(
        self,
        info: Info,
        organization_id: str,
        decision: str,
        note: str = "",
    ) -> OrganizationOnboardingPayload:
        actor = require_platform_admin(info)
        request = info.context["request"]
        organization = get_object_or_404(Organization, public_id=organization_id)
        try:
            reviewed_organization, tenant, user = review_organization_onboarding(
                organization=organization,
                actor=actor,
                decision=decision,
                note=note,
                request=request,
            )
        except ValidationError as exc:
            raise_graphql_validation_error(exc)
        if user is None:
            raise GraphQLError(
                "Onboarding organization does not have an administrator."
            )
        next_action = (
            "organization_active"
            if decision == "approved"
            else "provide_additional_information"
        )
        return OrganizationOnboardingPayload(
            onboarding=to_onboarding_node(
                serialize_onboarding_state(
                    organization=reviewed_organization,
                    tenant=tenant,
                    user=user,
                )
            ),
            next_action=next_action,
        )

    @strawberry.mutation
    def record_manual_decision(
        self,
        info: Info,
        verification_id: str,
        decision: str,
        reason_code: str,
        reason_detail: str = "",
    ) -> ManualDecisionPayload:
        user = require_authenticated_user(info)
        request = info.context["request"]
        verification = get_object_or_404(
            manual_review_queryset_for_user(user),
            public_id=verification_id,
        )
        serializer = ManualReviewDecisionSerializer(
            data={
                "decision": decision,
                "reason_code": reason_code,
                "reason_detail": reason_detail,
            }
        )
        serializer.is_valid(raise_exception=True)
        decision_record = serializer.save(verification=verification, decided_by=user)
        record_audit_event(
            tenant=verification.tenant,
            actor=user,
            request=request,
            action=f"verification.{decision_record.decision}",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "decision_id": decision_record.public_id,
                "decision_type": decision_record.decision_type,
            },
            sensitive_metadata={"reason_detail": decision_record.reason_detail},
        )
        if decision_record.decision in {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        }:
            queue_webhook_events(
                tenant=verification.tenant,
                event_type=f"verification.{decision_record.decision}",
                payload={
                    "verification_id": verification.public_id,
                    "external_reference": verification.external_reference,
                    "status": verification.status,
                },
            )
            risk_assessment = getattr(verification, "risk_assessment", None)
            queue_verification_status_notifications(
                verification=verification,
                decision=decision_record.decision,
                risk_level=(
                    risk_assessment.risk_level if risk_assessment is not None else ""
                ),
            )
        return ManualDecisionPayload(
            verification_id=verification.public_id,
            decision=decision_record.decision,
            decision_type=decision_record.decision_type,
            decided_at=decision_record.decided_at.isoformat(),
        )

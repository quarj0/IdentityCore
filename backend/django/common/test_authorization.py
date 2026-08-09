from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from graphql import GraphQLError

from apps.access_control.models import (
    Permission,
    Role,
    RolePermission,
    RoleScope,
    RoleStatus,
    UserRole,
)
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from common.authorization import (
    AuthorizationAction,
    ReviewOwner,
    ServicePrincipal,
    decide_api_client_access,
    decide_service_access,
    decide_user_access,
    require_service_access,
)
from common.permissions import IsTenantUser
from config.graphql_auth import require_tenant_user


class AuthorizationPolicyTests(TestCase):
    permission_code = "review_verification"

    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(name="Acme", slug="auth-acme")
        cls.tenant = Tenant.objects.create(
            organization=organization,
            name="Acme Tenant",
            slug="auth-acme-tenant",
            status="active",
        )
        other_organization = Organization.objects.create(name="Beta", slug="auth-beta")
        cls.other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Beta Tenant",
            slug="auth-beta-tenant",
            status="active",
        )
        cls.user = PlatformUser.objects.create_user(
            email="authorization-user@example.com",
            password="StrongPassword123!",
            tenant=cls.tenant,
            status=PlatformUserStatus.ACTIVE,
        )
        cls.platform_admin = PlatformUser.objects.create_user(
            email="authorization-admin@example.com",
            password="StrongPassword123!",
            is_platform_admin=True,
            status=PlatformUserStatus.ACTIVE,
        )
        cls.permission = Permission.objects.create(
            code=cls.permission_code,
            name="Review verification",
        )

    def _assign_role(self, *, status=RoleStatus.ACTIVE, with_permission=False):
        role = Role.objects.create(
            tenant=self.tenant,
            name=f"Reviewer {status} {with_permission}",
            scope=RoleScope.TENANT,
            status=status,
        )
        if with_permission:
            RolePermission.objects.create(role=role, permission=self.permission)
        UserRole.objects.create(user=self.user, role=role, tenant=self.tenant)
        return role

    def _rbac_decision(self, *, tenant=None):
        return decide_user_access(
            self.user,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=tenant or self.tenant,
            permission_code=self.permission_code,
        )

    def test_anonymous_user_is_denied(self):
        decision = decide_user_access(
            AnonymousUser(), action=AuthorizationAction.TENANT_ACCESS
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "authentication_required")

    def test_tenant_role_without_permission_is_denied(self):
        self._assign_role()

        self.assertFalse(self._rbac_decision().allowed)

    def test_inactive_tenant_role_is_denied(self):
        self._assign_role(status=RoleStatus.INACTIVE, with_permission=True)

        self.assertFalse(self._rbac_decision().allowed)

    def test_active_tenant_role_with_permission_is_tenant_scoped(self):
        self._assign_role(with_permission=True)

        self.assertTrue(self._rbac_decision().allowed)
        self.assertFalse(self._rbac_decision(tenant=self.other_tenant).allowed)

    def test_platform_admin_is_denied_tenant_action_and_allowed_platform_action(self):
        tenant_decision = decide_user_access(
            self.platform_admin,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=self.tenant,
        )
        platform_decision = decide_user_access(
            self.platform_admin,
            action=AuthorizationAction.PLATFORM_ACCESS,
        )

        self.assertFalse(tenant_decision.allowed)
        self.assertTrue(platform_decision.allowed)

    def test_platform_role_does_not_grant_a_tenant_permission(self):
        role = Role.objects.create(
            name="Platform Reviewer",
            scope=RoleScope.PLATFORM,
            status=RoleStatus.ACTIVE,
        )
        RolePermission.objects.create(role=role, permission=self.permission)
        UserRole.objects.create(user=self.platform_admin, role=role, tenant=None)

        decision = decide_user_access(
            self.platform_admin,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=self.tenant,
            permission_code=self.permission_code,
        )

        self.assertFalse(decision.allowed)

    def test_manual_review_owner_is_explicit_for_each_role(self):
        tenant_review = decide_user_access(
            self.user,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=self.tenant,
            review_owner=ReviewOwner.TENANT,
        )
        platform_review = decide_user_access(
            self.platform_admin,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=self.tenant,
            review_owner=ReviewOwner.PLATFORM,
        )
        tenant_on_platform_review = decide_user_access(
            self.user,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=self.tenant,
            review_owner=ReviewOwner.PLATFORM,
        )
        platform_on_tenant_review = decide_user_access(
            self.platform_admin,
            action=AuthorizationAction.MANUAL_REVIEW,
            tenant=self.tenant,
            review_owner=ReviewOwner.TENANT,
        )

        self.assertTrue(tenant_review.allowed)
        self.assertTrue(platform_review.allowed)
        self.assertFalse(tenant_on_platform_review.allowed)
        self.assertFalse(platform_on_tenant_review.allowed)

    def test_api_client_requires_scope_and_matching_tenant(self):
        api_client = SimpleNamespace(
            is_authenticated=True,
            tenant_id=self.tenant.id,
            scopes=["verifications:read"],
        )

        self.assertTrue(
            decide_api_client_access(
                api_client,
                required_scopes=("verifications:read",),
                tenant=self.tenant,
            ).allowed
        )
        self.assertFalse(
            decide_api_client_access(
                api_client,
                required_scopes=("verifications:write",),
                tenant=self.tenant,
            ).allowed
        )
        self.assertFalse(
            decide_api_client_access(
                api_client,
                required_scopes=("verifications:read",),
                tenant=self.other_tenant,
            ).allowed
        )

    def test_rest_and_graphql_use_the_same_rbac_decision(self):
        view = SimpleNamespace(required_permission_code=self.permission_code)
        request = SimpleNamespace(user=self.user)
        info = SimpleNamespace(context={"request": request})

        self.assertFalse(IsTenantUser().has_permission(request, view))
        with self.assertRaises(GraphQLError):
            require_tenant_user(info, permission_code=self.permission_code)

        self._assign_role(with_permission=True)

        self.assertTrue(IsTenantUser().has_permission(request, view))
        self.assertEqual(
            require_tenant_user(info, permission_code=self.permission_code), self.user
        )

    def test_rest_object_permission_normalizes_tenant_objects(self):
        request = SimpleNamespace(user=self.user)
        view = SimpleNamespace(required_permission_code=None)

        self.assertTrue(
            IsTenantUser().has_object_permission(request, view, self.tenant)
        )
        self.assertFalse(
            IsTenantUser().has_object_permission(request, view, self.other_tenant)
        )

    def test_service_principal_denies_unknown_actions_and_unscoped_resources(self):
        principal = ServicePrincipal(
            name="test-worker", allowed_actions=frozenset({"resource.process"})
        )
        resource = SimpleNamespace(tenant_id=self.tenant.id)

        self.assertTrue(
            decide_service_access(
                principal, action="resource.process", resource=resource
            ).allowed
        )
        self.assertFalse(
            decide_service_access(
                principal, action="resource.delete", resource=resource
            ).allowed
        )
        with self.assertRaises(PermissionDenied):
            require_service_access(principal, action="resource.process")

    def test_only_explicit_batch_principals_can_cross_tenants(self):
        regular = ServicePrincipal(
            name="regular-worker", allowed_actions=frozenset({"resource.batch"})
        )
        batch = ServicePrincipal(
            name="batch-worker",
            allowed_actions=frozenset({"resource.batch"}),
            allow_cross_tenant=True,
        )

        self.assertFalse(
            decide_service_access(regular, action="resource.batch").allowed
        )
        self.assertTrue(decide_service_access(batch, action="resource.batch").allowed)

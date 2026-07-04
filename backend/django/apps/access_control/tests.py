from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.access_control.models import Permission, Role, RolePermission, RoleScope, UserRole
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class AccessControlModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="user@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )

    def test_role_scope_rules_are_enforced(self):
        role = Role(name="Org Admin", scope=RoleScope.TENANT)
        with self.assertRaises(ValidationError):
            role.full_clean()

    def test_user_role_tenant_mismatch_is_rejected(self):
        other_org = Organization.objects.create(name="Beta", slug="beta")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Beta Tenant",
            slug="beta-tenant",
            status="active",
        )
        role = Role.objects.create(
            tenant=other_tenant,
            name="Officer",
            scope=RoleScope.TENANT,
            status="active",
        )
        assignment = UserRole(user=self.user, role=role, tenant=self.tenant)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_role_permission_is_unique(self):
        role = Role.objects.create(
            tenant=self.tenant,
            name="Officer",
            scope=RoleScope.TENANT,
            status="active",
        )
        permission = Permission.objects.create(code="view_verification", name="View verification")
        RolePermission.objects.create(role=role, permission=permission)

        with self.assertRaises(Exception):
            RolePermission.objects.create(role=role, permission=permission)

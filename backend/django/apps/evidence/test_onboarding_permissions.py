from django.test import TestCase
from rest_framework.test import APIClient

from apps.access_control.governed_permissions import GOVERNED_PERMISSIONS
from apps.access_control.models import Role, RolePermission
from apps.evidence import tests as fixtures
from apps.organizations.onboarding import ensure_tenant_administrator_role


class FreshAdministratorCapabilityTests(TestCase):
    propose = fixtures.EvidenceServiceTests.propose
    create = fixtures.EvidenceServiceTests.create

    def setUp(self):
        fixtures.EvidenceServiceTests.setUp(self)

    def test_fresh_onboarding_administrator_can_use_governed_resources(self):
        ensure_tenant_administrator_role(tenant=self.tenant, user=self.member)
        client = APIClient()
        client.force_authenticate(self.member)
        schemas = client.get("/api/v1/evidence/schemas")
        policies = client.get(
            "/api/v1/claims/policies", {"project_id": self.project.public_id}
        )
        self.assertEqual(schemas.status_code, 200, schemas.data)
        self.assertEqual(policies.status_code, 200, policies.data)
        role = Role.objects.get(tenant=self.tenant, name="Tenant Administrator")
        codes = set(
            RolePermission.objects.filter(role=role).values_list(
                "permission__code", flat=True
            )
        )
        self.assertTrue(set(GOVERNED_PERMISSIONS) <= codes)

    def test_custom_role_name_collision_does_not_gain_the_new_privileges(self):
        role = Role.objects.create(
            tenant=self.tenant,
            name="Tenant Administrator",
            scope="tenant",
            is_system_role=False,
        )
        ensure_tenant_administrator_role(tenant=self.tenant, user=self.member)
        codes = set(
            RolePermission.objects.filter(role=role).values_list(
                "permission__code", flat=True
            )
        )
        self.assertFalse(set(GOVERNED_PERMISSIONS) & codes)
        client = APIClient()
        client.force_authenticate(self.member)
        self.assertEqual(client.get("/api/v1/evidence/schemas").status_code, 403)

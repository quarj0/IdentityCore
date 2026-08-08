from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.accounts.models import PlatformUser
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, VerificationStatus


class SeedLocalCommandTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuses_to_run_outside_development(self):
        with self.assertRaisesMessage(CommandError, "restricted to DEBUG"):
            call_command("seed_local")

        self.assertFalse(Organization.objects.exists())

    @override_settings(DEBUG=True)
    def test_is_idempotent_and_seeds_every_verification_status(self):
        output = StringIO()
        call_command("seed_local", stdout=output)
        first_counts = self._counts()
        call_command("seed_local", stdout=output)

        self.assertEqual(self._counts(), first_counts)
        self.assertEqual(Tenant.objects.count(), 2)
        self.assertEqual(VerificationPolicy.objects.count(), 2)
        self.assertEqual(
            set(Verification.objects.values_list("status", flat=True)),
            set(VerificationStatus.values),
        )
        owner = PlatformUser.objects.get(email="owner@local.identitycore.test")
        self.assertTrue(owner.check_password("IdentityCoreLocal123!"))
        self.assertIn("Development-only password", output.getvalue())

    @staticmethod
    def _counts():
        return {
            "organizations": Organization.objects.count(),
            "tenants": Tenant.objects.count(),
            "users": PlatformUser.objects.count(),
            "policies": VerificationPolicy.objects.count(),
            "verifications": Verification.objects.count(),
        }

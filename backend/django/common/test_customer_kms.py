import os
from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.audit.models import AuditEvent
from apps.tenants.models import TenantDataKey, TenantKMSBinding
from apps.verifications import tests as fixtures
from common.customer_kms import activate, disable, validate_connection
from common.tenant_crypto import decrypt_tenant_json, encrypt_tenant_json

ARN = "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000001"


class MemoryKMS:
    def __init__(self):
        self.store = {}
        self.decrypt_calls = 0
        self.offline = False
        self.metadata = {
            "Arn": ARN,
            "KeyState": "Enabled",
            "KeyUsage": "ENCRYPT_DECRYPT",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "KeyManager": "CUSTOMER",
            "Origin": "AWS_CLOUDHSM",
        }

    def allowed(self, kwargs):
        if (
            self.offline
            or self.metadata["KeyState"] != "Enabled"
            or kwargs.get("GrantTokens") != ["synthetic-grant-token"]
        ):
            raise RuntimeError("Synthetic provider secret must not escape errors")

    def describe_key(self, **kwargs):
        self.allowed(kwargs)
        return {"KeyMetadata": deepcopy(self.metadata)}

    def encrypt(self, **kwargs):
        self.allowed(kwargs)
        token = os.urandom(32)
        self.store[token] = (
            kwargs["Plaintext"],
            kwargs["EncryptionContext"],
            kwargs["KeyId"],
        )
        return {"CiphertextBlob": token, "KeyId": kwargs["KeyId"]}

    def decrypt(self, **kwargs):
        self.decrypt_calls += 1
        self.allowed(kwargs)
        plaintext, context, arn = self.store[kwargs["CiphertextBlob"]]
        if context != kwargs["EncryptionContext"] or arn != kwargs["KeyId"]:
            raise RuntimeError("Synthetic authenticated context mismatch")
        return {"Plaintext": plaintext, "KeyId": arn}


class CustomerKMSContractTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def binding(self):
        return TenantKMSBinding.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            key_arn=ARN,
            grant_tokens_json=["synthetic-grant-token"],
        )

    def grant(self, code="manage_encryption"):
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": code}
        )
        role = Role.objects.create(tenant=self.tenant, name=code, scope="tenant")
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(
            user=self.tenant_reviewer, role=role, tenant=self.tenant
        )

    def test_hsm_connection_validates_effective_grants_before_rotation(self):
        binding = self.binding()
        fake = MemoryKMS()
        with patch("common.customer_kms.client_for", return_value=fake):
            binding, job = activate(binding, actor=self.tenant_reviewer)
            key = job.target_key
            self.assertEqual(key.wrapping_provider, "aws_kms")
            value = encrypt_tenant_json(
                {"synthetic": "customer-encrypted"},
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.customer",
            )
            self.assertEqual(value["kid"], key.public_id)
            self.assertEqual(
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                ),
                {"synthetic": "customer-encrypted"},
            )
        self.assertTrue(
            AuditEvent.objects.filter(action="encryption.kms_activated").exists()
        )
        self.assertNotIn(
            "synthetic-grant-token",
            str(list(AuditEvent.objects.values_list("metadata_json", flat=True))),
        )

    def test_binding_substitution_cannot_bypass_disablement(self):
        first = self.binding()
        fake = MemoryKMS()
        with patch("common.customer_kms.client_for", return_value=fake):
            first, job = activate(first)
            value = encrypt_tenant_json(
                {"synthetic": "bound"},
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.customer",
            )
            replacement, _ = activate(self.binding())
            disable(first)
            altered = deepcopy(job.target_key.wrapped_key_json)
            altered["binding_id"] = replacement.public_id
            TenantDataKey.objects.filter(pk=job.target_key_id).update(
                wrapped_key_json=altered
            )
            with self.assertRaises(ValueError):
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                )

    def test_customer_rotation_migrates_fields_and_remote_disablement_blocks_reads(
        self,
    ):
        from common.tenant_key_rotation import resume_database_batch
        from apps.verifications.models import Verification

        binding = self.binding()
        fake = MemoryKMS()
        self.tenant_case.metadata_json = {"synthetic": "migrated"}
        self.tenant_case.save(update_fields=["metadata_json"])
        with patch("common.customer_kms.client_for", return_value=fake):
            binding, job = activate(binding)
            for _ in range(100):
                job = resume_database_batch(job.public_id, batch_size=100)
                if job.status == "objects_pending":
                    break
            self.assertEqual(job.status, "objects_pending")
            case = Verification.objects.get(pk=self.tenant_case.pk)
            self.assertEqual(
                case.__dict__["metadata_json"].envelope["kid"], job.target_key.public_id
            )
            self.assertEqual(case.metadata_json, {"synthetic": "migrated"})
            fake.metadata["KeyState"] = "Disabled"
            with self.assertRaises(ValueError):
                Verification.objects.get(pk=case.pk).metadata_json
            with self.assertRaises(ValueError):
                encrypt_tenant_json(
                    {},
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                )

    def test_batch_reuses_two_customer_keys_and_clears_cache_at_exit(self):
        from common.tenant_key_rotation import resume_database_batch, rotation_fields
        from common.tenant_crypto import operation_deks

        fake = MemoryKMS()
        with patch("common.customer_kms.client_for", return_value=fake):
            activate(self.binding())
            for index in range(20):
                self._create_case("Cache " + str(index), metadata={"synthetic": index})
            _, job = activate(self.binding())
            job.positions_json = {
                label: "done"
                for label, _, _ in rotation_fields()
                if label != "verifications.verification.metadata_json"
            }
            job.save(update_fields=["positions_json"])
            before = fake.decrypt_calls
            result = resume_database_batch(job.public_id, batch_size=100)
            self.assertEqual(fake.decrypt_calls - before, 2)
            self.assertGreaterEqual(result.migrated_count, 20)
            self.assertIsNone(operation_deks.get())

    def test_operation_cache_rechecks_disable_expires_and_does_not_cross_requests(self):
        from common.tenant_crypto import key_operation, operation_deks

        fake = MemoryKMS()
        binding = self.binding()
        with patch("common.customer_kms.client_for", return_value=fake):
            binding, _ = activate(binding)
            value = encrypt_tenant_json(
                {},
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.customer",
            )

            def read():
                return decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                )

            with key_operation(), patch(
                "common.tenant_crypto.monotonic", return_value=0
            ) as clock:
                self.assertEqual(read(), {})
                entries = operation_deks.get()
                before = fake.decrypt_calls
                self.assertEqual(read(), {})
                self.assertEqual(fake.decrypt_calls, before)
                fake.offline = True
                clock.return_value = 6
                with self.assertRaises(ValueError):
                    read()
            self.assertEqual(entries, {})
            self.assertIsNone(operation_deks.get())
            fake.offline = False
            with key_operation():
                self.assertEqual(read(), {})
                disable(binding)
                with self.assertRaises(ValueError):
                    read()
            self.assertIsNone(operation_deks.get())

    def test_missing_grants_or_disabled_provider_key_never_activate(self):
        binding = self.binding()
        fake = MemoryKMS()
        binding.grant_tokens_json = []
        binding.save(update_fields=["grant_tokens_json"])
        with patch("common.customer_kms.client_for", return_value=fake):
            with self.assertRaisesRegex(
                ValueError, "^Customer key provider is unavailable.$"
            ):
                activate(binding)
        binding.refresh_from_db()
        self.assertFalse(binding.active)
        binding.grant_tokens_json = ["synthetic-grant-token"]
        binding.save(update_fields=["grant_tokens_json"])
        fake.metadata["KeyState"] = "Disabled"
        with patch("common.customer_kms.client_for", return_value=fake):
            with self.assertRaises(ValueError):
                validate_connection(binding)
        self.assertEqual(
            TenantDataKey.objects.filter(
                tenant_scope=self.tenant.public_id, environment="sandbox", active=True
            )
            .get()
            .wrapping_provider,
            "platform",
        )

    def test_disable_and_outage_fail_closed_without_platform_fallback(self):
        binding = self.binding()
        fake = MemoryKMS()
        with patch("common.customer_kms.client_for", return_value=fake):
            binding, _ = activate(binding)
            value = encrypt_tenant_json(
                {"synthetic": "retained"},
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.customer",
            )
            fake.offline = True
            for operation in (
                lambda: decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                ),
                lambda: encrypt_tenant_json(
                    {},
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "^Tenant encrypted content is unavailable.$|^Tenant encryption key is unavailable.$",
                ):
                    operation()
            fake.offline = False
            disable(binding)
            with self.assertRaises(ValueError):
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                )
            with self.assertRaises(ValueError):
                encrypt_tenant_json(
                    {},
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                )
            binding, _ = activate(binding)
            self.assertEqual(
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                ),
                {"synthetic": "retained"},
            )

    def test_rotation_retains_old_binding_reads_and_enforces_environment_context(self):
        first = self.binding()
        fake = MemoryKMS()
        with patch("common.customer_kms.client_for", return_value=fake):
            first, first_job = activate(first)
            value = encrypt_tenant_json(
                {"synthetic": "old"},
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.customer",
            )
            second, second_job = activate(self.binding())
            self.assertNotEqual(first_job.target_key_id, second_job.target_key_id)
            first.refresh_from_db()
            self.assertEqual(first.status, "retired")
            self.assertEqual(
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                    purpose="synthetic.customer",
                ),
                {"synthetic": "old"},
            )
            with self.assertRaises(ValueError):
                decrypt_tenant_json(
                    value,
                    tenant_scope=self.tenant.public_id,
                    environment="production",
                    purpose="synthetic.customer",
                )
            self.assertEqual(
                TenantDataKey.objects.get(
                    tenant_scope=self.tenant.public_id,
                    environment="shared",
                    active=True,
                ).wrapping_provider,
                "platform",
            )

    def test_configuration_requires_dedicated_permission_and_tokens_are_write_only(
        self,
    ):
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        self.grant("manage_team")
        data = {
            "environment": "sandbox",
            "key_arn": ARN,
            "grant_tokens": ["synthetic-grant-token"],
        }
        url = reverse("tenant-kms-list")
        self.assertEqual(client.post(url, data, format="json").status_code, 403)
        self.grant()
        response = client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("grant_tokens", response.data["data"])
        self.assertNotIn("synthetic-grant-token", str(client.get(url).data))
        binding = TenantKMSBinding.objects.get(public_id=response.data["data"]["id"])
        fake = MemoryKMS()
        action = reverse(
            "tenant-kms-action",
            kwargs={"binding_id": binding.public_id, "action": "activate"},
        )
        with patch("common.customer_kms.client_for", return_value=fake):
            self.assertEqual(client.post(action, {}, format="json").status_code, 200)
        client.force_authenticate(self.platform_reviewer)
        self.assertEqual(client.get(url).status_code, 403)

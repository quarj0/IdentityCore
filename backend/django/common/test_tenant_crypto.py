import json
from copy import deepcopy
from unittest import skipUnless
from django.test import TransactionTestCase
from io import BytesIO
from hashlib import sha256
from unittest.mock import patch
from django.test import override_settings

from django.db import connection
from django.test import TestCase

from apps.projects.models import Project
from apps.tenants.models import TenantDataKey
from apps.verifications import tests as fixtures
from apps.verifications.models import Verification
from common.crypto import decrypt_object_bytes, encrypt_json_value, encrypt_object_bytes
from common.fields import StoredTenantEnvelope
from common.tenant_crypto import decrypt_tenant_json, encrypt_tenant_json
from common.tenant_key_rotation import (
    resume_database_batch,
    resume_object_batch,
    start_rotation,
)


class TenantEnvelopeTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def raw(self, case, field="metadata_json"):
        quote = connection.ops.quote_name
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {quote(field)} FROM {quote(Verification._meta.db_table)} WHERE id = %s",
                [case.pk],
            )
            value = cursor.fetchone()[0]
        return json.loads(value) if isinstance(value, str) else value

    def replace_raw(self, case, envelope, field="metadata_json"):
        quote = connection.ops.quote_name
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {quote(Verification._meta.db_table)} SET {quote(field)} = %s WHERE id = %s",
                [json.dumps(envelope), case.pk],
            )

    def test_provider_credentials_are_owned_scoped_and_rotated(self):
        from apps.providers.models import Provider, ProviderEnvironmentConfiguration

        provider = Provider.objects.create(
            tenant=self.tenant,
            name="Synthetic",
            code="synthetic-crypto",
            provider_type="document",
        )
        configs = [
            ProviderEnvironmentConfiguration.objects.create(
                provider=provider,
                environment=environment,
                version=1,
                requested_by=self.tenant_reviewer,
                public_configuration_json={"synthetic": True},
                manifest_snapshot_json={"synthetic": True},
                credentials_json={"synthetic": environment},
            )
            for environment in ("sandbox", "production")
        ]
        quote = connection.ops.quote_name
        table = quote(ProviderEnvironmentConfiguration._meta.db_table)

        def raw(config):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT credentials_json FROM {table} WHERE id = %s", [config.pk]
                )
                value = cursor.fetchone()[0]
            return json.loads(value) if isinstance(value, str) else value

        sandbox, production = configs
        original = raw(sandbox)
        self.assertEqual(original["tenant"], self.tenant.public_id)
        self.assertEqual(original["environment"], "sandbox")
        self.assertNotEqual(original["kid"], raw(production)["kid"])
        production_before = raw(production)
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET credentials_json = %s WHERE id = %s",
                [json.dumps(original), production.pk],
            )
        with self.assertRaises(ValueError):
            ProviderEnvironmentConfiguration.objects.get(
                pk=production.pk
            ).credentials_json
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET credentials_json = %s WHERE id = %s",
                [json.dumps(production_before), production.pk],
            )
        legacy = encrypt_json_value(
            {"synthetic": "legacy"}, purpose="providers.environment.credentials"
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET credentials_json = %s WHERE id = %s",
                [json.dumps(legacy), sandbox.pk],
            )
        job = start_rotation(self.tenant.public_id, "sandbox")
        for _ in range(100):
            job = resume_database_batch(job.public_id, batch_size=100)
            if job.status == "objects_pending":
                break
        self.assertEqual(job.status, "objects_pending")
        self.assertEqual(raw(sandbox)["kid"], job.target_key.public_id)
        self.assertEqual(
            ProviderEnvironmentConfiguration.objects.get(
                pk=sandbox.pk
            ).credentials_json,
            {"synthetic": "legacy"},
        )
        self.assertEqual(raw(production), production_before)

    def test_backup_inventory_queries_are_bounded_for_shared_keys(self):
        from common.backup import required_object_refs
        from django.test.utils import CaptureQueriesContext
        from common.tenant_crypto import read_key_records

        project = Project.objects.create(
            tenant=self.tenant,
            name="Inventory",
            slug="inventory",
            environment="sandbox",
            created_by=self.tenant_reviewer,
        )
        for case in Verification.objects.all():
            # Re-encrypt each field when assigning an environment.
            case.metadata_json = {
                "evidence_report_storage_key": "synthetic/" + case.public_id
            }
            case.project = project if case.tenant_id == self.tenant.pk else None
            case.save(update_fields=["metadata_json", "project"])
        buckets = {
            role: "synthetic-" + role
            for role in ("media", "temp", "evidence", "public")
        }
        with patch("common.backup.storage_buckets", return_value=buckets):
            with CaptureQueriesContext(connection) as queries:
                before = required_object_refs()
            baseline = len(queries)
            for index in range(8):
                case = self._create_case(
                    "Inventory " + str(index),
                    metadata={
                        "evidence_report_storage_key": "synthetic/extra-" + str(index)
                    },
                )
                case.project = project
                case.save(update_fields=["project", "metadata_json"])
            with CaptureQueriesContext(connection) as queries:
                after = required_object_refs()
        self.assertEqual(len(queries), baseline)
        self.assertEqual(len(after), len(before) + 8)
        self.assertIsNone(read_key_records.get())

    def test_database_fields_bind_owning_tenant_environment_and_purpose(self):
        self.tenant_case.metadata_json = {"synthetic": "isolated"}
        self.tenant_case.save(update_fields=["metadata_json"])
        envelope = self.raw(self.tenant_case)
        self.assertEqual(envelope["__enc__"], "ic-tenant-field-v2")
        self.assertEqual(envelope["environment"], "sandbox")
        self.assertEqual(
            decrypt_tenant_json(
                envelope,
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="verifications.metadata",
            ),
            {"synthetic": "isolated"},
        )
        for context in [
            {
                "tenant_scope": "ten_00000000000000000000000000",
                "environment": "sandbox",
                "purpose": "verifications.metadata",
            },
            {
                "tenant_scope": self.tenant.public_id,
                "environment": "production",
                "purpose": "verifications.metadata",
            },
            {
                "tenant_scope": self.tenant.public_id,
                "environment": "sandbox",
                "purpose": "another.purpose",
            },
        ]:
            with self.assertRaises(ValueError):
                decrypt_tenant_json(envelope, **context)
        project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=self.tenant_reviewer,
        )
        other = self._create_case("Production Case", metadata={})
        other.project = project
        other.metadata_json = {"synthetic": "production"}
        other.policy_snapshot_json = {}
        other.workflow_snapshot_json = {}
        other.save()
        self.replace_raw(other, envelope)
        with self.assertRaises(ValueError):
            Verification.objects.get(pk=other.pk).metadata_json

    def test_old_versions_read_and_rotation_resumes_without_touching_other_environments(
        self,
    ):
        case = self.tenant_case
        case.metadata_json = {"synthetic": "retained"}
        case.save(update_fields=["metadata_json"])
        old = self.raw(case)
        job = start_rotation(self.tenant.public_id, "sandbox")
        self.assertNotEqual(old["kid"], job.target_key.public_id)
        self.assertEqual(
            Verification.objects.get(pk=case.pk).metadata_json,
            {"synthetic": "retained"},
        )
        newer = self._create_case("New Version", metadata={"synthetic": "new"})
        self.assertEqual(self.raw(newer)["kid"], job.target_key.public_id)
        admin_key = TenantDataKey.objects.get(
            tenant_scope=self.tenant.public_id, environment="shared", active=True
        )
        partial = resume_database_batch(job.public_id, batch_size=1)
        self.assertEqual(partial.status, "running")
        for _ in range(100):
            job = resume_database_batch(job.public_id, batch_size=1)
            if job.status == "objects_pending":
                break
        self.assertEqual(job.status, "objects_pending")
        self.assertEqual(self.raw(case)["kid"], job.target_key.public_id)
        self.assertEqual(
            Verification.objects.get(pk=case.pk).metadata_json,
            {"synthetic": "retained"},
        )
        admin_key.refresh_from_db()
        self.assertTrue(admin_key.active)
        self.assertEqual(
            decrypt_tenant_json(
                old,
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="verifications.metadata",
            ),
            {"synthetic": "retained"},
        )

    def test_legacy_platform_envelope_remains_readable_and_is_upgraded(self):
        legacy = encrypt_json_value(
            {"synthetic": "legacy"}, purpose="verifications.metadata"
        )
        self.replace_raw(self.tenant_case, legacy)
        case = Verification.objects.get(pk=self.tenant_case.pk)
        self.assertEqual(case.metadata_json, {"synthetic": "legacy"})
        case.save(update_fields=["metadata_json"])
        self.assertEqual(self.raw(case)["__enc__"], "ic-tenant-field-v2")

    def test_raw_queries_do_not_decrypt_and_bulk_writes_require_ownership(self):
        raw = (
            Verification.objects.filter(pk=self.tenant_case.pk)
            .values_list("metadata_json", flat=True)
            .get()
        )
        self.assertIsInstance(raw, StoredTenantEnvelope)
        with self.assertRaises(ValueError):
            Verification.objects.filter(pk=self.tenant_case.pk).update(
                metadata_json={"synthetic": "unbound"}
            )

    def test_objects_authenticate_content_type_and_require_owner_environment(self):
        payload = encrypt_object_bytes(
            content=b"synthetic report",
            content_type="application/pdf",
            purpose="evidence.reports",
            tenant_scope=self.tenant.public_id,
            environment="sandbox",
        )
        self.assertEqual(
            decrypt_object_bytes(
                payload=payload,
                purpose="evidence.reports",
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
            ),
            (b"synthetic report", "application/pdf"),
        )
        with self.assertRaises(ValueError):
            decrypt_object_bytes(payload=payload, purpose="evidence.reports")
        with self.assertRaises(ValueError):
            decrypt_object_bytes(
                payload=payload,
                purpose="evidence.reports",
                tenant_scope=self.tenant.public_id,
                environment="production",
            )
        changed = json.loads(payload)
        changed["content_type"] = "text/html"
        with self.assertRaises(ValueError):
            decrypt_object_bytes(
                payload=json.dumps(changed).encode(),
                purpose="evidence.reports",
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
            )

    def test_invalid_wrapping_material_and_tampered_payload_fail_with_fixed_errors(
        self,
    ):
        value = encrypt_tenant_json(
            {"synthetic": "sensitive"},
            tenant_scope=self.tenant.public_id,
            environment="sandbox",
            purpose="synthetic.test",
        )
        tampered = deepcopy(value)
        tampered["nonce"] = "invalid"
        with self.assertRaisesRegex(
            ValueError, "^Tenant encrypted content is unavailable.$"
        ):
            decrypt_tenant_json(
                tampered,
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.test",
            )
        record = TenantDataKey.objects.get(public_id=value["kid"])
        record.wrapped_key_json = {"key": "unprotected synthetic material"}
        record.save(update_fields=["wrapped_key_json"])
        with self.assertRaisesRegex(
            ValueError, "^Tenant encrypted content is unavailable.$"
        ):
            decrypt_tenant_json(
                value,
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
                purpose="synthetic.test",
            )

    @override_settings(OBJECT_STORAGE_EVIDENCE_BUCKET="synthetic-evidence")
    def test_interrupted_conditional_object_rotation_remains_readable_and_resumes(self):
        from apps.verifications.evidence import download_verification_evidence_object

        class MemoryStorage:
            def __init__(self):
                self.data = {
                    "synthetic/report.json": b'{"synthetic":"json"}',
                    "synthetic/report.pdf": b"%PDF-synthetic",
                }
                self.types = {
                    "synthetic/report.json": "application/json",
                    "synthetic/report.pdf": "application/pdf",
                }
                self.puts = 0

            def get_object(self, *, Bucket, Key):
                body = self.data[Key]
                return {
                    "Body": BytesIO(body),
                    "ContentType": self.types[Key],
                    "ETag": sha256(body).hexdigest(),
                }

            def put_object(self, *, Bucket, Key, Body, ContentType, IfMatch, **kwargs):
                self.puts += 1
                if self.puts == 2 or IfMatch != sha256(self.data[Key]).hexdigest():
                    raise RuntimeError("Synthetic conditional-write failure")
                self.data[Key], self.types[Key] = Body, ContentType

        storage = MemoryStorage()
        case = self.tenant_case
        case.metadata_json = {
            "evidence_report_storage_key": "synthetic/report.json",
            "evidence_report_pdf_storage_key": "synthetic/report.pdf",
            "evidence_report_encrypted": False,
            "evidence_report_pdf_encrypted": False,
        }
        case.save(update_fields=["metadata_json"])
        job = start_rotation(self.tenant.public_id, "sandbox")
        for _ in range(100):
            job = resume_database_batch(job.public_id, batch_size=100)
            if job.status == "objects_pending":
                break
        self.assertEqual(job.status, "objects_pending")
        with patch("common.storage.get_object_storage_client", return_value=storage):
            with self.assertRaisesRegex(
                ValueError, "Conditional evidence rotation failed"
            ):
                resume_object_batch(job.public_id)
            # First object committed before the second failed, while metadata
            # rolled back. Tenant-context reads still detect and decrypt it.
            case.refresh_from_db()
            self.assertFalse(case.metadata_json["evidence_report_encrypted"])
            content, content_type, _ = download_verification_evidence_object(case)
            self.assertEqual(
                (content, content_type), (b'{"synthetic":"json"}', "application/json")
            )
            for _ in range(10):
                job = resume_object_batch(job.public_id)
                if job.status == "completed":
                    break
        self.assertEqual(job.status, "completed")
        case.refresh_from_db()
        self.assertTrue(case.metadata_json["evidence_report_encrypted"])
        self.assertTrue(case.metadata_json["evidence_report_pdf_encrypted"])
        for body in storage.data.values():
            self.assertEqual(json.loads(body)["kid"], job.target_key.public_id)

    def test_failed_tenant_insert_rolls_back_its_initial_wrapped_key(self):
        from django.db import IntegrityError
        from apps.tenants.models import Tenant

        before = TenantDataKey.objects.count()
        with self.assertRaises(IntegrityError):
            Tenant.objects.create(
                organization=self.organization, name="Duplicate", slug=self.tenant.slug
            )
        self.assertEqual(TenantDataKey.objects.count(), before)

    def test_rotation_compare_and_swap_preserves_a_concurrent_content_update(self):
        case = self.tenant_case
        case.metadata_json = {"synthetic": "before"}
        case.save(update_fields=["metadata_json"])
        job = start_rotation(self.tenant.public_id, "sandbox")
        real_encrypt = encrypt_tenant_json
        raced = False

        def encrypt_with_update(value, **kwargs):
            nonlocal raced
            if (
                not raced
                and kwargs["purpose"] == "verifications.metadata"
                and value == {"synthetic": "before"}
            ):
                raced = True
                current = Verification.objects.get(pk=case.pk)
                current.metadata_json = {"synthetic": "concurrent"}
                current.save(update_fields=["metadata_json"])
            return real_encrypt(value, **kwargs)

        with patch(
            "common.tenant_key_rotation.encrypt_tenant_json",
            side_effect=encrypt_with_update,
        ):
            for _ in range(100):
                job = resume_database_batch(job.public_id, batch_size=100)
                if job.status == "objects_pending":
                    break
        self.assertTrue(raced)
        self.assertEqual(job.conflict_count, 1)
        self.assertEqual(
            Verification.objects.get(pk=case.pk).metadata_json,
            {"synthetic": "concurrent"},
        )
        for _ in range(100):
            job = (
                resume_object_batch(job.public_id)
                if job.status == "objects_pending"
                else resume_database_batch(job.public_id)
            )
            if job.status == "completed":
                break
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.conflict_count, 1)
        self.assertEqual(
            Verification.objects.get(pk=case.pk).metadata_json,
            {"synthetic": "concurrent"},
        )


class TenantEnvelopeRaceTests(TransactionTestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    @skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL transactions")
    def test_simultaneous_first_environment_writes_share_one_wrapped_key(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections

        ready = Barrier(2)
        scope = self.tenant.public_id

        def encrypt(number):
            close_old_connections()
            try:
                ready.wait(timeout=15)
                return encrypt_tenant_json(
                    {"synthetic": number},
                    tenant_scope=scope,
                    environment="production",
                    purpose="synthetic.concurrent",
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            values = list(pool.map(encrypt, [1, 2]))
        self.assertEqual(values[0]["kid"], values[1]["kid"])
        self.assertEqual(
            TenantDataKey.objects.filter(
                tenant_scope=scope, environment="production"
            ).count(),
            1,
        )
        for number, value in enumerate(values, 1):
            self.assertEqual(
                decrypt_tenant_json(
                    value,
                    tenant_scope=scope,
                    environment="production",
                    purpose="synthetic.concurrent",
                ),
                {"synthetic": number},
            )

    @skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL transactions")
    def test_first_writer_commit_between_active_and_existence_reads_is_reused(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event, current_thread
        from django.db import close_old_connections
        from django.db.models.query import QuerySet

        missing, committed = Event(), Event()
        real_first = QuerySet.first
        scope = self.tenant.public_id
        paused = False

        def first(query):
            nonlocal paused
            value = real_first(query)
            if (
                query.model is TenantDataKey
                and value is None
                and current_thread().name.startswith("delayed")
                and not paused
            ):
                paused = True
                missing.set()
                if not committed.wait(15):
                    raise RuntimeError("Synthetic concurrency timeout")
            return value

        def write(number):
            close_old_connections()
            try:
                if number == 2 and not missing.wait(15):
                    raise RuntimeError("Synthetic concurrency timeout")
                result = encrypt_tenant_json(
                    {"synthetic": number},
                    tenant_scope=scope,
                    environment="production",
                    purpose="synthetic.concurrent",
                )
                if number == 2:
                    committed.set()
                return result
            finally:
                close_old_connections()

        with patch.object(QuerySet, "first", first), ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="delayed"
        ) as delayed, ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="creator"
        ) as creator:
            waiting = delayed.submit(write, 1)
            creating = creator.submit(write, 2)
            second, first_value = creating.result(timeout=20), waiting.result(
                timeout=20
            )
        self.assertEqual(first_value["kid"], second["kid"])
        self.assertEqual(
            TenantDataKey.objects.filter(
                tenant_scope=scope, environment="production"
            ).count(),
            1,
        )

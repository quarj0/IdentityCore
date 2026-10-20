from datetime import timedelta

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.accounts.models import PlatformUser
from apps.audit.services import verify_audit_chain
from apps.evidence.models import Evidence, EvidenceSource
from apps.evidence.services import (
    approve_authorization,
    ancestry,
    create_evidence,
    create_schema,
    propose_authorization,
)
from apps.evidence.validation import validate_schema
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject


class EvidenceServiceTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Evidence", slug="evidence", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=organization, name="Evidence", slug="evidence", status="active"
        )
        self.maker = PlatformUser.objects.create_user(
            email="maker@example.test",
            password="unused",
            tenant=self.tenant,
            status="active",
        )
        self.checker = PlatformUser.objects.create_user(
            email="checker@example.test",
            password="unused",
            tenant=self.tenant,
            status="active",
        )
        self.member = PlatformUser.objects.create_user(
            email="member@example.test",
            password="unused",
            tenant=self.tenant,
            status="active",
        )
        role = Role.objects.create(
            tenant=self.tenant, name="Evidence officer", scope="tenant"
        )
        for code in ("manage_evidence", "read_evidence", "manage_subject_privacy"):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.create(role=role, permission=permission)
        for user in (self.maker, self.checker):
            UserRole.objects.create(tenant=self.tenant, user=user, role=role)
        self.project = Project.objects.create(
            tenant=self.tenant, name="Workload", slug="workload", created_by=self.maker
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic subject"
        )
        self.now = timezone.now()
        self.schema = create_schema(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            name="assertion",
            version=1,
            kind="evidence",
            definition={
                "type": "object",
                "properties": {"name": {"type": "string", "maxLength": 120}},
                "required": ["name"],
                "additionalProperties": False,
            },
            disclosure_fields=["name"],
        )
        self.authorization = self.propose()
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=self.authorization.public_id,
        )

    def propose(self, **overrides):
        return propose_authorization(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    subject_id=self.subject.public_id,
                    purpose="eligibility",
                    legal_basis="contract",
                    justification={"reference": "synthetic-contract"},
                    operations=["evidence:read", "evidence:write"],
                    valid_from=self.now - timedelta(minutes=1),
                    valid_until=self.now + timedelta(days=2),
                ),
                **overrides,
            }
        )

    def create(self, **overrides):
        return create_evidence(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    subject_id=self.subject.public_id,
                    authorization_id=self.authorization.public_id,
                    schema_id=self.schema.public_id,
                    evidence_type="submitted",
                    operation_reference="synthetic-operation",
                    payload={"name": "Synthetic applicant"},
                    provenance={"source": "synthetic-fixture", "contract_version": "1"},
                    observed_at=self.now,
                    valid_until=self.now + timedelta(days=1),
                    delete_after=self.now + timedelta(days=2),
                ),
                **overrides,
            }
        )

    def test_nonconsent_authorization_requires_an_independent_current_privacy_officer(
        self,
    ):
        proposed = self.propose()
        with self.assertRaises(PermissionDenied):
            self.create(authorization_id=proposed.public_id)
        with self.assertRaises(PermissionDenied):
            approve_authorization(
                tenant_id=self.tenant.pk,
                actor=self.maker,
                authorization_id=proposed.public_id,
            )
        with self.assertRaises(PermissionDenied):
            approve_authorization(
                tenant_id=self.tenant.pk,
                actor=self.member,
                authorization_id=proposed.public_id,
            )
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=proposed.public_id,
        )
        self.create(authorization_id=proposed.public_id)

    def test_ciphertext_at_rest_retains_provenance_without_plaintext_payload(self):
        evidence = self.create()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT payload_json, provenance_json FROM evidence_evidence WHERE id=%s",
                [evidence.pk],
            )
            raw = str(cursor.fetchone())
        self.assertNotIn("Synthetic applicant", raw)
        self.assertNotIn("synthetic-fixture", raw)
        evidence.refresh_from_db()
        self.assertEqual(evidence.payload_json["name"], "Synthetic applicant")
        self.assertEqual(evidence.provenance_json["source"], "synthetic-fixture")
        self.assertTrue(verify_audit_chain(tenant_id=self.tenant.pk)[0])

    def test_unknown_or_foreign_source_does_not_create_evidence_or_partial_edges(self):
        before = Evidence.objects.count()
        with self.assertRaises(NotFound):
            self.create(source_ids=["evd_not_known"])
        self.assertEqual(Evidence.objects.count(), before)
        self.assertFalse(EvidenceSource.objects.exists())

    def test_current_permissions_are_rechecked_even_for_previously_authorized_actor(
        self,
    ):
        self.maker.status = "inactive"
        self.maker.save(update_fields=["status"])
        with self.assertRaises(PermissionDenied):
            self.create()

    def test_schema_violation_and_nonfinite_payload_are_rejected_before_persistence(
        self,
    ):
        for payload in (
            {"name": 12},
            {"name": "valid", "unexpected": True},
            {"name": float("nan")},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                self.create(payload=payload)
        self.assertFalse(Evidence.objects.exists())

    def test_remote_references_and_recursive_or_exponential_schema_shapes_are_rejected(
        self,
    ):
        for keyword, value in (
            ("$ref", "https://untrusted.example/schema"),
            ("anyOf", [{"type": "object"}]),
            ("pattern", "(a+)+$"),
        ):
            with self.subTest(keyword=keyword), self.assertRaises(ValidationError):
                validate_schema({"type": "object", keyword: value})

    def test_immutable_evidence_and_lineage_cannot_be_rewritten_or_deleted(self):
        root = self.create()
        child = self.create(source_ids=[root.public_id])
        for operation in (
            lambda: Evidence.objects.filter(pk=root.pk).update(payload_json={}),
            lambda: root.delete(),
            lambda: Evidence.objects.filter(pk=root.pk).delete(),
            lambda: EvidenceSource.objects.all().delete(),
        ):
            with self.assertRaises(ModelValidationError):
                operation()
        child.payload_json = {"name": "rewritten"}
        with self.assertRaises(ModelValidationError):
            child.save()
        self.assertEqual(set(ancestry(root)), {root.pk})

    def test_supersession_invalidates_existing_descendants_without_rewriting_payloads(
        self,
    ):
        root = self.create()
        child = self.create(source_ids=[root.public_id])
        correction = self.create(
            supersedes_id=root.public_id, payload={"name": "Corrected value"}
        )
        root.refresh_from_db()
        child.refresh_from_db()
        self.assertEqual(root.status, "superseded")
        self.assertEqual(child.status, "revoked")
        self.assertEqual(root.payload_json["name"], "Synthetic applicant")
        self.assertEqual(correction.supersedes_id, root.pk)
        with self.assertRaises(PermissionDenied):
            self.create(source_ids=[child.public_id])

    def test_correction_cannot_depend_on_its_invalidated_predecessor(self):
        root = self.create()
        with self.assertRaises(ValidationError):
            self.create(supersedes_id=root.public_id, source_ids=[root.public_id])
        root.refresh_from_db()
        self.assertEqual(root.status, "active")
        self.assertEqual(Evidence.objects.count(), 1)

    def test_derived_evidence_cannot_extend_source_retention_or_validity(self):
        root = self.create(valid_until=self.now + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            self.create(source_ids=[root.public_id])

    def test_different_purpose_cannot_reuse_source_even_with_the_same_subject(self):
        root = self.create()
        other = self.propose(purpose="another-purpose")
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=other.public_id,
        )
        with self.assertRaises(NotFound):
            self.create(authorization_id=other.public_id, source_ids=[root.public_id])

    def test_revoked_authorization_blocks_descendant_reads_and_further_use(self):
        from apps.evidence.services import read_evidence, revoke_authorization

        parent = self.create()
        child = self.create(source_ids=[parent.public_id])
        revoke_authorization(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            authorization_id=self.authorization.public_id,
            reason="purpose_ended",
        )
        with self.assertRaises(PermissionDenied):
            read_evidence(
                tenant_id=self.tenant.pk,
                actor=self.maker,
                project_id=self.project.public_id,
                evidence_id=child.public_id,
                purpose="eligibility",
                include_payload=True,
            )
        child.refresh_from_db()
        self.assertEqual(child.status, "revoked")
        self.assertTrue(verify_audit_chain(tenant_id=self.tenant.pk)[0])

    def test_read_requires_exact_project_and_purpose_and_audits_payload_access(self):
        from apps.evidence.services import read_evidence

        record = self.create()
        args = dict(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            project_id=self.project.public_id,
            evidence_id=record.public_id,
            purpose="eligibility",
        )
        with self.assertRaises(NotFound):
            read_evidence(**{**args, "purpose": "unrelated"})
        metadata = read_evidence(**args)
        self.assertNotIn("payload", metadata)
        disclosed = read_evidence(**args, include_payload=True)
        self.assertEqual(disclosed["payload"], {"name": "Synthetic applicant"})
        self.assertTrue(verify_audit_chain(tenant_id=self.tenant.pk)[0])


class EvidenceAPITests(TestCase):
    """Real request paths, scopes and replay behavior, not serializer-only mocks."""

    propose = EvidenceServiceTests.propose
    create = EvidenceServiceTests.create

    def setUp(self):
        EvidenceServiceTests.setUp(self)
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.client.force_authenticate(self.maker)

    def body(self):
        return dict(
            project_id=self.project.public_id,
            subject_id=self.subject.public_id,
            authorization_id=self.authorization.public_id,
            schema_id=self.schema.public_id,
            evidence_type="submitted",
            operation_reference="http-operation",
            payload={"name": "API synthetic value"},
            provenance={"source": "request-fixture"},
            observed_at=self.now.isoformat(),
            valid_until=(self.now + timedelta(days=1)).isoformat(),
            delete_after=(self.now + timedelta(days=2)).isoformat(),
        )

    def test_create_requires_idempotency_replays_one_write_and_rechecks_current_permission(
        self,
    ):
        response = self.client.post("/api/v1/evidence/", self.body(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Evidence.objects.exists())
        options = {"format": "json", "HTTP_IDEMPOTENCY_KEY": "create-once"}
        first = self.client.post("/api/v1/evidence/", self.body(), **options)
        self.assertEqual(first.status_code, 201, first.data)
        second = self.client.post("/api/v1/evidence/", self.body(), **options)
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(first.data["data"], second.data["data"])
        self.assertEqual(Evidence.objects.count(), 1)
        UserRole.objects.filter(user=self.maker).delete()
        denied = self.client.post("/api/v1/evidence/", self.body(), **options)
        self.assertEqual(denied.status_code, 403, denied.data)

    def test_actual_detail_and_lineage_are_metadata_only_until_payload_is_requested(
        self,
    ):
        record = self.create()
        query = {"project_id": self.project.public_id, "purpose": "eligibility"}
        metadata = self.client.get(f"/api/v1/evidence/{record.public_id}", query)
        self.assertEqual(metadata.status_code, 200, metadata.data)
        self.assertNotIn("payload", metadata.data["data"])
        payload = self.client.get(
            f"/api/v1/evidence/{record.public_id}", {**query, "include_payload": "true"}
        )
        self.assertEqual(payload.status_code, 200, payload.data)
        self.assertEqual(payload.data["data"]["payload"]["name"], "Synthetic applicant")
        graph = self.client.get(f"/api/v1/evidence/{record.public_id}/lineage", query)
        self.assertEqual(graph.status_code, 200, graph.data)
        self.assertEqual(graph.data["data"]["nodes"][0]["id"], record.public_id)
        self.assertNotIn("payload", graph.data["data"]["nodes"][0])

    def test_machine_credentials_cannot_read_another_project_in_the_same_environment(
        self,
    ):
        from apps.api_clients.models import APIClient

        record = self.create()
        other = Project.objects.create(
            tenant=self.tenant, name="Other", slug="other", created_by=self.maker
        )
        key = APIClient(
            tenant=self.tenant,
            project=other,
            name="Other project",
            created_by=self.maker,
            scopes_json=["evidence:read"],
        )
        key.set_client_secret("synthetic-api-credential")
        key.save()
        self.client.force_authenticate(user=None)
        headers = {
            "HTTP_X_CLIENT_ID": key.client_id,
            "HTTP_AUTHORIZATION": "Bearer synthetic-api-credential",
        }
        query = {"project_id": self.project.public_id, "purpose": "eligibility"}
        foreign = self.client.get(
            f"/api/v1/evidence/{record.public_id}", query, **headers
        )
        unknown = self.client.get("/api/v1/evidence/evd_unknown", query, **headers)
        self.assertEqual(foreign.status_code, 404, foreign.data)
        self.assertEqual(unknown.status_code, 404, unknown.data)
        for result in (foreign, unknown):
            result.data["error"].pop("request_id", None)
            result.data.pop("request_id", None)
        self.assertEqual(foreign.data, unknown.data)

    def test_schema_data_property_names_are_not_confused_with_executable_keywords(self):
        validate_schema(
            {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "$ref": {"type": "string"},
                },
                "additionalProperties": False,
            }
        )
        for definition in (
            {
                "type": "object",
                "properties": {"name": {"type": "string", "pattern": "(a+)+$"}},
            },
            {
                "type": "object",
                "properties": {"items": {"type": "array", "uniqueItems": True}},
            },
        ):
            with self.assertRaises(ValidationError):
                validate_schema(definition)

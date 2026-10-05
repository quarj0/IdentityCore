from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock, patch
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.tenants.models import TenantStorageRoute
from apps.verifications import tests as fixtures
from apps.uploads.models import UploadPurpose
from apps.uploads.services import create_upload, build_signed_upload_url
from apps.verifications.evidence import build_verification_evidence_storage_key
from common.storage import (
    get_object_bytes,
    put_object_bytes,
    delete_object,
    build_signed_download_url,
)
from common.tenant_storage import (
    configure_route,
    route_key,
    resolve_reference,
    RoutedS3Client,
    transfer_references,
)


@override_settings(
    TENANT_STORAGE_DESTINATIONS={
        "synthetic-route-one": "eu-west-1",
        "synthetic-route-two": "eu-west-1",
    }
)
class TenantStorageTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def route(self, bucket="synthetic-route-one"):
        return configure_route(self.tenant, "sandbox", bucket, "eu-west-1")

    def test_routes_bind_owner_environment_and_keep_old_locations(self):
        first = self.route()
        key = build_verification_evidence_storage_key(self.tenant_case)
        self.assertLessEqual(len(key), 255)
        original = resolve_reference(
            key, "default", tenant_scope=self.tenant.public_id, environment="sandbox"
        )
        self.assertEqual(original["bucket"], first.bucket)
        second = self.route("synthetic-route-two")
        new = build_verification_evidence_storage_key(self.tenant_case)
        self.assertNotEqual(key, new)
        self.assertEqual(resolve_reference(key, "default"), original)
        self.assertEqual(
            resolve_reference(new, "default")["route_id"], second.public_id
        )
        for tampered in (
            key.replace("/sandbox/", "/production/"),
            key.replace(self.tenant.public_id, "ten_00000000000000000000000000"),
            key + "/../escape",
        ):
            with self.assertRaises(ValueError):
                resolve_reference(tampered, "default")
        with self.assertRaises(ValueError):
            resolve_reference(
                key, "default", tenant_scope="ten_00000000000000000000000000"
            )
        first.bucket = second.bucket
        with self.assertRaises(ValidationError):
            first.save()

    def test_bulk_deletion_retains_routes_and_object_resolution(self):
        route = self.route()
        key = build_verification_evidence_storage_key(self.tenant_case)
        with self.assertRaises(ValidationError):
            TenantStorageRoute.objects.filter(pk=route.pk).delete()
        with self.assertRaises(ValidationError):
            route.delete()
        self.assertEqual(resolve_reference(key, "legacy")["route_id"], route.public_id)

    def test_bulk_updates_cannot_redirect_retained_object_references(self):
        route = self.route()
        key = build_verification_evidence_storage_key(self.tenant_case)
        original = resolve_reference(key, "legacy")
        for field, value in {"bucket": "synthetic-route-two", "residency_region": "us-east-1", "tenant_id": self.tenant.pk + 100, "environment": "production", "deleted_at": timezone.now()}.items():
            with self.assertRaises(ValidationError):
                TenantStorageRoute.objects.filter(pk=route.pk).update(**{field: value})
        route.bucket = "synthetic-route-two"
        with self.assertRaises(ValidationError), transaction.atomic():
            TenantStorageRoute.objects.bulk_update([route], ["bucket"])
        self.assertEqual(resolve_reference(key, "legacy"), original)

    def test_reads_writes_deletion_and_metadata_use_retained_bucket(self):
        self.route()
        key = build_verification_evidence_storage_key(self.tenant_case)
        raw = Mock()
        raw.get_object.return_value = {
            "Body": BytesIO(b"synthetic"),
            "ContentType": "text/plain",
        }
        with patch(
            "common.storage.get_object_storage_client", return_value=RoutedS3Client(raw)
        ):
            put_object_bytes(
                bucket_name="legacy",
                key=key,
                content=b"synthetic",
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
            )
            self.assertEqual(
                raw.put_object.call_args.kwargs["Bucket"], "synthetic-route-one"
            )
            self.assertEqual(
                raw.put_object.call_args.kwargs["Metadata"]["residency-region"],
                "eu-west-1",
            )
            self.assertEqual(
                get_object_bytes(
                    bucket_name="legacy",
                    key=key,
                    tenant_scope=self.tenant.public_id,
                    environment="sandbox",
                )[0],
                b"synthetic",
            )
            delete_object(bucket_name="legacy", key=key)
            self.assertEqual(
                raw.delete_object.call_args.kwargs["Bucket"], "synthetic-route-one"
            )
            with self.assertRaises(ValueError):
                get_object_bytes(
                    bucket_name="legacy",
                    key=key,
                    tenant_scope="ten_00000000000000000000000000",
                    environment="sandbox",
                )
            self.assertEqual(raw.get_object.call_count, 1)

    @override_settings(
        MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS=99999,
        OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS=99999,
    )
    def test_grants_are_single_object_bounded_and_expire_with_upload(self):
        self.route()
        from apps.verifications.models import VerificationSession

        session = VerificationSession.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            session_token_hash="synthetic",
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        upload = create_upload(
            verification_session=session,
            purpose=UploadPurpose.DOCUMENT_CAPTURE,
            mime_type="image/jpeg",
            file_size_bytes=123,
            expires_at=timezone.now() + timedelta(seconds=45),
        )
        self.assertLessEqual(len(upload.storage_key + ".validated." + "0" * 16), 255)
        client = Mock()
        client.generate_presigned_url.return_value = (
            "https://synthetic.example.test/grant"
        )
        with patch("common.storage.get_object_storage_client", return_value=client):
            build_signed_upload_url(upload=upload)
            args = client.generate_presigned_url.call_args
            self.assertEqual(args.args, ("put_object",))
            self.assertEqual(
                args.kwargs["Params"],
                {
                    "Bucket": "synthetic-route-one",
                    "Key": upload.storage_key,
                    "ContentType": "image/jpeg",
                    "ContentLength": 123,
                    "ServerSideEncryption": "AES256",
                },
            )
            self.assertLessEqual(args.kwargs["ExpiresIn"], 45)
            build_signed_download_url(
                storage_key=upload.storage_key,
                bucket_name="legacy",
                tenant_scope=self.tenant.public_id,
                environment="sandbox",
            )
            self.assertEqual(
                client.generate_presigned_url.call_args.kwargs["ExpiresIn"], 300
            )
            upload.expires_at = timezone.now() - timedelta(seconds=1)
            with self.assertRaises(ValueError):
                build_signed_upload_url(upload=upload)

    def test_reference_transfer_has_routing_metadata_without_media(self):
        route = self.route()
        key = route_key(self.tenant_case, "verifications/synthetic/documents/synthetic")
        original = {
            "document_storage_key": key,
            "document_storage_bucket": "legacy",
            "verification_id": self.tenant_case.public_id,
        }
        result = transfer_references(original)
        self.assertEqual(result["document_storage_bucket"], route.bucket)
        self.assertEqual(
            result["storage_routing"]["document"],
            {"route_id": route.public_id, "residency_region": "eu-west-1"},
        )
        self.assertEqual(original["document_storage_bucket"], "legacy")
        self.assertNotIn("content", result)
        with self.assertRaises(ValueError):
            configure_route(self.tenant, "sandbox", "unapproved-bucket", "eu-west-1")

    @override_settings(
        TENANT_STORAGE_BUCKET_REMAP={"synthetic-route-one": "synthetic-route-two"}
    )
    def test_trusted_restore_remap_preserves_region_and_original_route(self):
        route = TenantStorageRoute.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            bucket="synthetic-route-one",
            residency_region="eu-west-1",
        )
        key = route_key(self.tenant_case, "verifications/synthetic/reports/synthetic")
        self.assertEqual(
            resolve_reference(key, "default")["bucket"], "synthetic-route-two"
        )
        with override_settings(
            TENANT_STORAGE_DESTINATIONS={"synthetic-route-two": "us-east-1"}
        ):
            with self.assertRaises(ValueError):
                resolve_reference(key, "default")
        route.refresh_from_db()
        self.assertEqual(route.bucket, "synthetic-route-one")

    @override_settings(OBJECT_STORAGE_MEDIA_BUCKET="legacy-media", OBJECT_STORAGE_TEMP_BUCKET="legacy-temp", OBJECT_STORAGE_EVIDENCE_BUCKET="legacy-evidence", OBJECT_STORAGE_PUBLIC_BUCKET="legacy-public")
    def test_backup_keeps_retired_route_references_and_missing_active_route_fails_closed(self):
        from common.backup import required_object_refs, storage_buckets
        first = self.route()
        key = build_verification_evidence_storage_key(self.tenant_case)
        self.tenant_case.metadata_json = {"evidence_report_storage_key": key}
        self.tenant_case.save(update_fields=["metadata_json"])
        self.route("synthetic-route-two")
        self.assertIn((first.bucket, key), required_object_refs())
        self.assertEqual(storage_buckets()["tenant:" + first.bucket], first.bucket)
        TenantStorageRoute.objects.filter(tenant=self.tenant).update(active=False)
        with self.assertRaises(ValueError):
            route_key(self.tenant_case, "verifications/synthetic/reports/new")
        self.assertEqual(resolve_reference(key, "legacy")["bucket"], first.bucket)

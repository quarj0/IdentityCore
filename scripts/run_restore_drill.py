#!/usr/bin/env python3
"""Exercise encrypted backup/restore using only the dedicated synthetic stack.

Start ops/drills/compose.yaml with a private env file before invoking this.
The source and restore databases must both be new. No real tenant data is used.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--backup-key-file", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    values = dict(
        line.split("=", 1)
        for line in Path(args.env_file).read_text().splitlines()
        if line and not line.startswith("#")
    )
    os.environ.update(
        {
            "DJANGO_SECRET_KEY": values["DRILL_APPLICATION_SECRET"],
            "DJANGO_SETTINGS_MODULE": "config.settings.base",
            "DJANGO_ALLOWED_HOSTS": "testserver,localhost,127.0.0.1",
            "POSTGRES_DB": "identitycore_source",
            "POSTGRES_USER": values["POSTGRES_USER"],
            "POSTGRES_PASSWORD": values["POSTGRES_PASSWORD"],
            "POSTGRES_HOST": "127.0.0.1",
            "POSTGRES_PORT": "5444",
            "OBJECT_STORAGE_PROVIDER": "s3_compatible",
            "OBJECT_STORAGE_ENDPOINT_URL": "http://127.0.0.1:9000",
            "OBJECT_STORAGE_ACCESS_KEY_ID": values["DRILL_STORAGE_ACCESS_KEY"],
            "OBJECT_STORAGE_SECRET_ACCESS_KEY": values["DRILL_STORAGE_SECRET_KEY"],
            "OBJECT_STORAGE_REGION": "us-east-1",
            "OBJECT_STORAGE_USE_PATH_STYLE": "1",
            "BACKUP_S3_ENDPOINT_URL": "http://127.0.0.1:9000",
            "BACKUP_S3_ACCESS_KEY_ID": values["DRILL_STORAGE_ACCESS_KEY"],
            "BACKUP_S3_SECRET_ACCESS_KEY": values["DRILL_STORAGE_SECRET_KEY"],
            "IDENTITYCORE_BACKUP_KEY_FILE": str(Path(args.backup_key_file).resolve()),
            "IDENTITYCORE_PG_TOOL_PREFIX": json.dumps(
                [
                    "docker",
                    "--host=unix:///var/run/docker.sock",
                    "exec",
                    "--env",
                    "PGPASSWORD",
                    "-i",
                    "identitycore-drill-postgres",
                ]
            ),
            "IDENTITYCORE_PG_TOOL_HOST": "127.0.0.1",
            "IDENTITYCORE_PG_TOOL_PORT": "5432",
            "IDENTITYCORE_TELEMETRY_ENABLED": "0",
            "ADMIN_MFA_REQUIRED_DEFAULT": "0",
        }
    )
    for role in ("MEDIA", "TEMP", "EVIDENCE", "PUBLIC"):
        os.environ["OBJECT_STORAGE_" + role + "_BUCKET"] = "source-" + role.lower()
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/django")]
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.models import PlatformUser
    from apps.organizations.models import Organization, OrganizationSupportingDocument
    from apps.tenants.models import Tenant
    from apps.projects.models import Project
    from apps.api_clients.models import APIClient
    from apps.verification_subjects.models import VerificationSubject
    from apps.verifications.models import Verification
    from apps.biometrics.models import SelfieCapture
    from common.backup import (
        create_backup,
        download_backup,
        restore_backup,
        publish_backup,
        storage_buckets,
    )
    from common.storage import get_object_storage_client

    if connection.introspection.table_names():
        raise RuntimeError("Synthetic source must be empty; use a fresh drill volume.")
    call_command("migrate", verbosity=0, interactive=False)
    client = get_object_storage_client()
    for bucket in [
        *storage_buckets().values(),
        "encrypted-archives",
        "restore-media",
        "restore-temp",
        "restore-evidence",
        "restore-public",
    ]:
        client.create_bucket(Bucket=bucket)
    verifications, clients = [], []
    for index in (1, 2):
        organization = Organization.objects.create(
            name=f"Synthetic {index}", slug=f"synthetic-{index}", status="active"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name=f"Synthetic {index}",
            slug=f"synthetic-{index}",
            status="active",
            settings_json={"synthetic_restore_marker": index},
        )
        user = PlatformUser.objects.create_user(
            email=f"synthetic-{index}@example.invalid",
            password="SyntheticDrill123!",
            tenant=tenant,
            status="active",
        )
        project = Project.objects.create(
            tenant=tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=user,
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant, metadata_json={"synthetic_marker": index}
        )
        verification = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            project=project,
            expires_at=timezone.now() + timedelta(hours=1),
            metadata_json={
                "evidence_report_storage_key": f"synthetic/{index}/evidence.json"
            },
        )
        selfie = SelfieCapture.objects.create(
            tenant=tenant,
            verification=verification,
            verification_subject=subject,
            storage_key=f"synthetic/{index}/selfie.jpg",
            captured_at=timezone.now(),
            capture_type="image",
        )
        client.put_object(
            Bucket="source-media",
            Key=selfie.storage_key,
            Body=f"synthetic-selfie-{index}".encode(),
            ContentType="image/jpeg",
            ServerSideEncryption="AES256",
        )
        client.put_object(
            Bucket="source-evidence",
            Key=f"synthetic/{index}/evidence.json",
            Body=json.dumps({"synthetic": index}).encode(),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        api = APIClient(
            tenant=tenant,
            project=project,
            name="Synthetic drill",
            created_by=user,
            scopes_json=["verifications:read"],
        )
        api.set_client_secret("synthetic-drill-client-secret")
        api.save()
        supporting = OrganizationSupportingDocument.objects.create(
            organization=organization,
            tenant=tenant,
            uploaded_by=user,
            filename="synthetic.pdf",
            mime_type="application/pdf",
            file_size_bytes=13,
            storage_key=f"synthetic/{index}/supporting.pdf",
            status="uploaded" if index == 1 else "submitted",
        )
        client.put_object(
            Bucket="source-public",
            Key=supporting.storage_key,
            Body=b"synthetic-pdf",
            ContentType="application/pdf",
            ServerSideEncryption="AES256",
        )
        OrganizationSupportingDocument.objects.create(
            organization=organization,
            tenant=tenant,
            uploaded_by=user,
            filename="deleted.pdf",
            file_size_bytes=1,
            storage_key=f"synthetic/{index}/deleted.pdf",
            status="uploaded",
            deleted_at=timezone.now(),
        )
        verifications.append(verification.public_id)
        clients.append(api.client_id)
    prefix = [
        "docker",
        "--host=unix:///var/run/docker.sock",
        "exec",
        "identitycore-drill-postgres",
        "psql",
        "-U",
        values["POSTGRES_USER"],
        "-d",
        "postgres",
        "-c",
    ]
    quiesce = prefix + [
        "ALTER DATABASE identitycore_source SET default_transaction_read_only = on"
    ]
    resume = prefix + [
        "ALTER DATABASE identitycore_source SET default_transaction_read_only = off"
    ]
    # There are no API/worker services or external object-store clients in this
    # dedicated fixture stack. The database setting blocks additional writers.
    with tempfile.TemporaryDirectory(prefix="identitycore-restore-drill-") as workspace:
        directory, backup = create_backup(Path(workspace) / "archives", quiesce, resume)
        publish_backup(directory, "encrypted-archives")
        recovery_started = time.monotonic()
        shutil.rmtree(directory)
        directory = download_backup(
            backup["backup_id"], "encrypted-archives", Path(workspace) / "downloaded"
        )
        source_files = list(directory.glob("*.enc"))
        assert source_files and all(
            b"synthetic-selfie" not in file.read_bytes() for file in source_files
        )
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE identitycore_restore")
        connection.close()
        settings.DATABASES["default"]["NAME"] = "identitycore_restore"
        connection.settings_dict["NAME"] = "identitycore_restore"
        os.environ["IDENTITYCORE_RESTORE_ISOLATED"] = "1"
        for role in ("MEDIA", "TEMP", "EVIDENCE", "PUBLIC"):
            setattr(
                settings,
                "OBJECT_STORAGE_" + role + "_BUCKET",
                "restore-" + role.lower(),
            )
        restored = restore_backup(directory, workspace)
        # Verify decryption of application fields using separately provided keys.
        assert sorted(
            Tenant.objects.values_list("settings_json", flat=True),
            key=lambda d: d["synthetic_restore_marker"],
        ) == [{"synthetic_restore_marker": 1}, {"synthetic_restore_marker": 2}]
        api_client = Client()
        for index in (0, 1):
            headers = {
                "HTTP_X_CLIENT_ID": clients[index],
                "HTTP_AUTHORIZATION": "Bearer synthetic-drill-client-secret",
            }
            own = api_client.get(
                f"/api/v1/verifications/{verifications[index]}", **headers
            )
            other = api_client.get(
                f"/api/v1/verifications/{verifications[1-index]}", **headers
            )
            assert own.status_code == 200, own.status_code
            assert other.status_code in {403, 404}, other.status_code
        for index in (1, 2):
            assert (
                client.head_object(
                    Bucket="restore-media", Key=f"synthetic/{index}/selfie.jpg"
                )["ContentType"]
                == "image/jpeg"
            )
            assert (
                client.head_object(
                    Bucket="restore-evidence", Key=f"synthetic/{index}/evidence.json"
                )["ContentType"]
                == "application/json"
            )
        report = {
            "date": timezone.now().date().isoformat(),
            "scope": "isolated synthetic PostgreSQL 17 and HTTP S3 fixture",
            "backup": backup,
            "restore": restored,
            "archive_publication": "pass",
            "tenant_access": "both tenants can read own verification and cannot read the other tenant",
            "application_key_access": "encrypted tenant settings decoded correctly",
            "rpo_target_hours": 24,
            "rto_target_hours": 4,
            "measured_data_recovery_seconds": round(
                time.monotonic() - recovery_started, 3
            ),
            "rto_pass": (time.monotonic() - recovery_started) < 4 * 3600,
            "production_scale_claim": False,
        }
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "restore_drill": "pass",
                    "objects": restored["object_count"],
                    "restore_seconds": restored["duration_seconds"],
                    "tenant_isolation": "pass",
                }
            )
        )


if __name__ == "__main__":
    main()

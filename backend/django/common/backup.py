"""Encrypted PostgreSQL + object-store backups for a quiesced pilot deployment.

Backup encryption keys are independent from application field/media keys. No
plaintext database dump is staged during backup. Restore authenticates each
file before invoking PostgreSQL or uploading objects.
"""

import base64
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

import boto3
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from django.conf import settings
from django.db import connection
from django.utils import timezone
from datetime import datetime
from common.storage import (
    get_object_storage_client,
    get_object_storage_media_bucket_name,
    get_object_storage_temp_bucket_name,
    get_object_storage_evidence_bucket_name,
    get_object_storage_public_bucket_name,
    _get_server_side_encryption_params,
)

MAGIC = b"ICBK01"
CHUNK = 1024 * 1024


class BackupError(RuntimeError):
    """Safe, payload-free operational error."""


def load_backup_key():
    path = Path(os.environ["IDENTITYCORE_BACKUP_KEY_FILE"])
    if path.stat().st_mode & 0o077:
        raise BackupError("Backup key file must be accessible only to its owner.")
    try:
        key = base64.b64decode(path.read_bytes().strip(), validate=True)
    except (ValueError, TypeError):
        raise BackupError("Backup key encoding is invalid.") from None
    if len(key) != 32:
        raise BackupError("Backup encryption requires a separate 256-bit key.")
    return key


def encrypt_stream(source, destination, key, context):
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(context.encode())
    digest, size = hashlib.sha256(), 0
    with open(destination, "xb") as output:
        os.chmod(destination, 0o600)
        output.write(MAGIC + nonce)
        while data := source.read(CHUNK):
            digest.update(data)
            size += len(data)
            output.write(encryptor.update(data))
        output.write(encryptor.finalize())
        output.write(encryptor.tag)
        output.flush()
        os.fsync(output.fileno())
    return {"sha256": digest.hexdigest(), "size": size}


def decrypt_file(source, destination, key, context):
    try:
        with open(source, "rb") as encrypted:
            length = os.fstat(encrypted.fileno()).st_size
            if length < len(MAGIC) + 12 + 16 or encrypted.read(len(MAGIC)) != MAGIC:
                raise BackupError("Invalid encrypted backup file.")
            nonce = encrypted.read(12)
            encrypted.seek(-16, 2)
            tag = encrypted.read(16)
            encrypted.seek(len(MAGIC) + 12)
            decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(context.encode())
            remaining = length - len(MAGIC) - 12 - 16
            digest, size = hashlib.sha256(), 0
            with open(destination, "xb") as output:
                os.chmod(destination, 0o600)
                while remaining:
                    data = encrypted.read(min(CHUNK, remaining))
                    if not data:
                        raise BackupError("Truncated encrypted backup file.")
                    remaining -= len(data)
                    plaintext = decryptor.update(data)
                    digest.update(plaintext)
                    size += len(plaintext)
                    output.write(plaintext)
                output.write(decryptor.finalize())  # Authenticate before use.
            return {"sha256": digest.hexdigest(), "size": size}
    except Exception:
        Path(destination).unlink(missing_ok=True)
        raise BackupError("Backup authentication or decryption failed.") from None


def storage_buckets():
    return {
        role: bucket
        for role, bucket in {
            "media": get_object_storage_media_bucket_name(),
            "temp": get_object_storage_temp_bucket_name(),
            "evidence": get_object_storage_evidence_bucket_name(),
            "public": get_object_storage_public_bucket_name(),
        }.items()
        if bucket
    }


def required_object_refs():
    from apps.document_captures.models import DocumentCapture
    from apps.biometrics.models import SelfieCapture
    from apps.uploads.models import Upload
    from apps.organizations.models import Organization, OrganizationSupportingDocument
    from apps.verifications.models import Verification

    buckets = storage_buckets()
    refs = set()
    for model in (DocumentCapture, SelfieCapture):
        for key in (
            model.objects.filter(deleted_at__isnull=True)
            .exclude(status="deleted")
            .values_list("storage_key", flat=True)
        ):
            if key:
                refs.add((buckets.get("media", ""), key))
    for upload in Upload.objects.filter(
        deleted_at__isnull=True,
        status__in=["uploaded", "quarantined", "consumed", "promoted"],
    ):
        role = "media" if upload.status == "promoted" else "temp"
        refs.add((buckets.get(role, ""), upload.storage_key))
    for key in OrganizationSupportingDocument.objects.filter(
        deleted_at__isnull=True, status__in=["uploaded", "submitted"]
    ).values_list("storage_key", flat=True):
        refs.add((buckets.get("public", ""), key))
    for verification in Verification.objects.select_related("tenant").only("metadata_json", "tenant__public_id").iterator():
        metadata = verification.metadata_json
        for field in ("evidence_report_storage_key", "evidence_report_pdf_storage_key"):
            if metadata.get(field):
                refs.add((buckets.get("evidence", ""), metadata[field]))
    for metadata in Organization.objects.values_list("settings_json", flat=True):
        branding = metadata
        keys = [
            branding.get("logo_storage_key", ""),
            *branding.get("branding_image_storage_keys", []),
        ]
        for states in metadata.get("branding_environments", {}).values():
            for state in states.values():
                if isinstance(state, dict):
                    keys.append(state.get("logo_storage_key", ""))
        refs.update((buckets.get("public", ""), key) for key in keys if key)
    if any(not bucket for bucket, _ in refs):
        raise BackupError("Referenced storage bucket is not configured.")
    return refs


def postgres_command(tool):
    if connection.vendor != "postgresql":
        raise BackupError("Operational backups require PostgreSQL.")
    database = settings.DATABASES["default"]
    prefix = json.loads(os.getenv("IDENTITYCORE_PG_TOOL_PREFIX", "[]"))
    if not isinstance(prefix, list) or any(not isinstance(arg, str) for arg in prefix):
        raise BackupError("PostgreSQL tool prefix must be a JSON argv list.")
    args = prefix + [
        tool,
        "--host=" + os.getenv("IDENTITYCORE_PG_TOOL_HOST", database["HOST"]),
        "--port=" + os.getenv("IDENTITYCORE_PG_TOOL_PORT", str(database["PORT"])),
        "--username=" + database["USER"],
        "--dbname=" + database["NAME"],
    ]
    environment = dict(os.environ, PGPASSWORD=database["PASSWORD"])
    return args, environment


def run_hook(command):
    if (
        not command
        or not isinstance(command, list)
        or any(not isinstance(arg, str) for arg in command)
    ):
        raise BackupError("Paired quiesce/resume hooks must be JSON argv lists.")
    # Hook output may contain infrastructure credentials. Do not expose it.
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=300,
    )


@contextmanager
def quiesced(quiesce, resume):
    if not quiesce or not resume:
        raise BackupError("Backup requires paired quiesce and resume hooks.")
    try:
        run_hook(quiesce)
        yield
    finally:
        # A quiesce hook can partially stop writers before failing.
        run_hook(resume)


def create_backup(output_root, quiesce, resume):
    key = load_backup_key()
    backup_id = uuid.uuid4().hex
    started = time.monotonic()
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    partial = root / (backup_id + ".partial")
    partial.mkdir(mode=0o700)
    manifest = {
        "version": 1,
        "backup_id": backup_id,
        "started_at": timezone.now().isoformat(),
        "buckets": storage_buckets(),
        "files": [],
        "database_name": settings.DATABASES["default"]["NAME"],
    }
    try:
        with quiesced(quiesce, resume):
            refs = required_object_refs()
            args, environment = postgres_command("pg_dump")
            with subprocess.Popen(
                args + ["--format=custom", "--no-owner", "--no-acl"],
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            ) as process:
                metadata = encrypt_stream(
                    process.stdout,
                    partial / "database.enc",
                    key,
                    backup_id + "/database.enc",
                )
                if process.wait() != 0:
                    raise BackupError("PostgreSQL backup failed.")
            manifest["database"] = metadata
            client = get_object_storage_client()
            if manifest["buckets"] and client is None:
                raise BackupError("Object storage is not available for backup.")
            copied = set()
            for bucket in sorted(set(manifest["buckets"].values())):
                for page in client.get_paginator("list_objects_v2").paginate(
                    Bucket=bucket
                ):
                    for item in page.get("Contents", []):
                        object_key = item["Key"]
                        filename = (
                            hashlib.sha256(
                                (bucket + "\0" + object_key).encode()
                            ).hexdigest()
                            + ".enc"
                        )
                        response = client.get_object(Bucket=bucket, Key=object_key)
                        try:
                            metadata = encrypt_stream(
                                response["Body"],
                                partial / filename,
                                key,
                                backup_id + "/" + filename,
                            )
                        finally:
                            response["Body"].close()
                        manifest["files"].append(
                            {
                                "bucket": bucket,
                                "key": object_key,
                                "file": filename,
                                "headers": {
                                    field: response[field]
                                    for field in (
                                        "ContentType",
                                        "ContentEncoding",
                                        "ContentDisposition",
                                        "CacheControl",
                                        "Metadata",
                                    )
                                    if field in response
                                },
                                **metadata,
                            }
                        )
                        copied.add((bucket, object_key))
            if not refs.issubset(copied):
                raise BackupError(
                    "Database references objects missing from the snapshot."
                )
            manifest["required_refs"] = [list(ref) for ref in sorted(refs)]
            manifest["duration_seconds"] = round(time.monotonic() - started, 3)
            encrypt_stream(
                io.BytesIO(json.dumps(manifest).encode()),
                partial / "manifest.enc",
                key,
                backup_id + "/manifest.enc",
            )
        report = {
            "backup_id": backup_id,
            "created_at": timezone.now().isoformat(),
            "object_count": len(manifest["files"]),
            "required_object_count": len(refs),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        (partial / "SUCCESS.json").write_text(json.dumps(report) + "\n")
        os.chmod(partial / "SUCCESS.json", 0o600)
        complete = root / backup_id
        partial.rename(complete)
        return complete, report
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise


def backup_repository_client():
    # No fallback to application credentials: the archive has a separate grant.
    return boto3.client(
        "s3",
        endpoint_url=os.environ["BACKUP_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["BACKUP_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["BACKUP_S3_SECRET_ACCESS_KEY"],
        region_name=os.getenv("BACKUP_S3_REGION", "us-east-1"),
    )


def publish_backup(directory, bucket):
    client = backup_repository_client()
    source_buckets = set(storage_buckets().values())
    if (
        bucket in source_buckets
        and os.environ["BACKUP_S3_ENDPOINT_URL"] == settings.OBJECT_STORAGE_ENDPOINT_URL
    ):
        raise BackupError("Backup archive must use a separate storage bucket.")
    # Publish success last; incomplete prefixes are never considered restorable.
    for path in sorted(
        Path(directory).iterdir(), key=lambda p: p.name == "SUCCESS.json"
    ):
        client.upload_file(
            str(path),
            bucket,
            f"{Path(directory).name}/{path.name}",
            ExtraArgs=(
                {
                    "ServerSideEncryption": "aws:kms",
                    "SSEKMSKeyId": os.environ["BACKUP_S3_KMS_KEY_ID"],
                }
                if os.getenv("BACKUP_S3_KMS_KEY_ID")
                else {"ServerSideEncryption": "AES256"}
            ),
        )


def read_manifest(directory, key, staging):
    backup_id = Path(directory).name
    if len(backup_id) != 32 or any(c not in "0123456789abcdef" for c in backup_id):
        raise BackupError("Invalid backup directory identifier.")
    if not (Path(directory) / "SUCCESS.json").is_file():
        raise BackupError("Backup is incomplete.")
    manifest_path = Path(staging) / "manifest.json"
    decrypt_file(
        Path(directory) / "manifest.enc",
        manifest_path,
        key,
        backup_id + "/manifest.enc",
    )
    manifest = json.loads(manifest_path.read_bytes())
    if manifest["version"] != 1 or manifest["backup_id"] != backup_id:
        raise BackupError("Backup manifest version or identity is invalid.")
    return manifest


def restore_backup(directory, staging_root):
    if os.getenv("IDENTITYCORE_RESTORE_ISOLATED") != "1":
        raise BackupError(
            "Restore is allowed only in an explicitly isolated environment."
        )
    target = settings.DATABASES["default"]["NAME"]
    if not target.endswith(("_restore", "_drill")):
        raise BackupError("Restore database name must end in _restore or _drill.")
    if connection.introspection.table_names():
        raise BackupError("Restore database must be empty.")
    key = load_backup_key()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir=staging_root) as staging:
        manifest = read_manifest(directory, key, staging)
        if manifest["database_name"] == target:
            raise BackupError("Restore must not target the source database.")
        target_buckets = storage_buckets()
        if set(manifest["buckets"]) != set(target_buckets):
            raise BackupError("Restore bucket roles must match the backup.")
        if set(target_buckets.values()) & set(manifest["buckets"].values()):
            raise BackupError("Restore requires distinct, empty buckets.")
        client = get_object_storage_client()
        for bucket in set(target_buckets.values()):
            if client.list_objects_v2(Bucket=bucket, MaxKeys=1).get("KeyCount", 0):
                raise BackupError("Restore object buckets must be empty.")
        roles = list(target_buckets)
        for first in roles:
            for second in roles:
                if (manifest["buckets"][first] == manifest["buckets"][second]) != (
                    target_buckets[first] == target_buckets[second]
                ):
                    raise BackupError("Restore must preserve source bucket aliasing.")
        source_to_target = {
            source: target_buckets[role] for role, source in manifest["buckets"].items()
        }
        if len(source_to_target) != len(set(target_buckets.values())):
            raise BackupError("Restore must preserve source bucket aliasing.")
        # Authenticate every archive member before making any target mutation.
        members = [("database.enc", manifest["database"])] + [
            (item["file"], item) for item in manifest["files"]
        ]
        for filename, expected in members:
            if Path(filename).name != filename or not filename.endswith(".enc"):
                raise BackupError("Backup member name is invalid.")
            actual = decrypt_file(
                Path(directory) / filename,
                Path(staging) / filename,
                key,
                manifest["backup_id"] + "/" + filename,
            )
            if actual != {field: expected[field] for field in ("sha256", "size")}:
                raise BackupError("Backup content digest does not match its manifest.")
        for item in manifest["files"]:
            with open(Path(staging) / item["file"], "rb") as stream:
                client.put_object(
                    Bucket=source_to_target[item["bucket"]],
                    Key=item["key"],
                    Body=stream,
                    **item.get("headers", {}),
                    **_get_server_side_encryption_params(),
                )
        args, environment = postgres_command("pg_restore")
        with open(Path(staging) / "database.enc", "rb") as dump:
            result = subprocess.run(
                args
                + ["--no-owner", "--no-acl", "--exit-on-error", "--single-transaction"],
                env=environment,
                stdin=dump,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if result.returncode:
            raise BackupError(
                "PostgreSQL restore failed; keep the environment isolated."
            )
        connection.close()
        required = required_object_refs()
        expected = {
            (source_to_target[bucket], key) for bucket, key in manifest["required_refs"]
        }
        if required != expected:
            raise BackupError(
                "Restored database object references do not match the snapshot."
            )
        for item in manifest["files"]:
            response = client.get_object(
                Bucket=source_to_target[item["bucket"]], Key=item["key"]
            )
            digest = hashlib.sha256()
            try:
                while chunk := response["Body"].read(CHUNK):
                    digest.update(chunk)
            finally:
                response["Body"].close()
            if digest.hexdigest() != item["sha256"]:
                raise BackupError("Restored object checksum failed.")
        return {
            "backup_id": manifest["backup_id"],
            "restored_at": timezone.now().isoformat(),
            "object_count": len(manifest["files"]),
            "required_object_count": len(required),
            "database_object_consistency": "pass",
            "duration_seconds": round(time.monotonic() - started, 3),
            "backup_age_seconds": max(
                0,
                (
                    timezone.now() - datetime.fromisoformat(manifest["started_at"])
                ).total_seconds(),
            ),
        }


def download_backup(backup_id, bucket, output_root):
    if len(backup_id) != 32 or any(c not in "0123456789abcdef" for c in backup_id):
        raise BackupError("Invalid backup identifier.")
    client = backup_repository_client()
    client.head_object(Bucket=bucket, Key=backup_id + "/SUCCESS.json")
    partial = Path(output_root) / (backup_id + ".partial")
    partial.mkdir(parents=True, mode=0o700)
    try:
        for page in client.get_paginator("list_objects_v2").paginate(
            Bucket=bucket, Prefix=backup_id + "/"
        ):
            for item in page.get("Contents", []):
                filename = item["Key"][len(backup_id) + 1 :]
                if Path(filename).name != filename or not (
                    filename.endswith(".enc") or filename == "SUCCESS.json"
                ):
                    raise BackupError("Remote backup member is invalid.")
                path = partial / filename
                client.download_file(bucket, item["Key"], str(path))
                path.chmod(0o600)
        complete = Path(output_root) / backup_id
        partial.rename(complete)
        return complete
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise


def record_backup_result(failed):
    from common.observability import metrics, environment, process_instance

    meter = metrics.get_meter("identitycore")
    name = (
        "identitycore.backup.failure_timestamp"
        if failed
        else "identitycore.backup.last_success"
    )
    meter.create_gauge(name, unit="s").set(
        time.time(),
        {
            "environment": environment(
                os.getenv("IDENTITYCORE_DEPLOYMENT_ENVIRONMENT")
            ),
            "process_instance": process_instance(),
        },
    )
    provider = metrics.get_meter_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush(timeout_millis=5000)

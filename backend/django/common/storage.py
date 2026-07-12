from urllib.parse import urlencode

import boto3
from botocore.config import Config
from django.conf import settings

from apps.platform_settings.services import get_platform_setting_value
from common.crypto import (
    decrypt_object_bytes,
    encrypt_object_bytes,
    is_encrypted_object_payload,
)


def _first_non_empty(*values: object) -> str:
    for value in values:
        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return ""


def determine_storage_provider() -> str:
    configured_provider = _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_provider",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_PROVIDER", ""),
    )

    if configured_provider:
        return configured_provider

    endpoint_url = _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_endpoint_url",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", ""),
    )

    if "cloudflarestorage.com" in endpoint_url:
        return "cloudflare_r2"

    if endpoint_url:
        return "s3_compatible"

    return "local"


def _get_object_storage_bucket(
    bucket_name: str | None = None,
) -> str:
    if bucket_name:
        return bucket_name.strip()

    return _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_bucket",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_MEDIA_BUCKET", ""),
        getattr(settings, "OBJECT_STORAGE_BUCKET", ""),
    )


def get_object_storage_media_bucket_name() -> str:
    return _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_media_bucket",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_MEDIA_BUCKET", ""),
        getattr(settings, "OBJECT_STORAGE_BUCKET", ""),
    )


def get_object_storage_temp_bucket_name() -> str:
    return _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_temp_bucket",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_TEMP_BUCKET", ""),
        get_object_storage_media_bucket_name(),
        getattr(settings, "OBJECT_STORAGE_BUCKET", ""),
    )


def get_object_storage_evidence_bucket_name() -> str:
    return _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_evidence_bucket",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_EVIDENCE_BUCKET", ""),
        get_object_storage_media_bucket_name(),
        getattr(settings, "OBJECT_STORAGE_BUCKET", ""),
    )


def get_object_storage_public_bucket_name() -> str:
    return _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_public_bucket",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_PUBLIC_BUCKET", ""),
        get_object_storage_media_bucket_name(),
        getattr(settings, "OBJECT_STORAGE_BUCKET", ""),
    )


def _get_upload_bucket() -> str:
    return _first_non_empty(
        get_object_storage_temp_bucket_name(),
        get_object_storage_media_bucket_name(),
    )


def get_object_storage_client():
    endpoint_url = _first_non_empty(
        get_platform_setting_value(
            "storage.object_storage_endpoint_url",
            "",
        ),
        getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", ""),
    )

    access_key = _first_non_empty(
        getattr(settings, "OBJECT_STORAGE_ACCESS_KEY_ID", ""),
    )

    secret_key = _first_non_empty(
        getattr(settings, "OBJECT_STORAGE_SECRET_ACCESS_KEY", ""),
    )

    region_name = _first_non_empty(
        getattr(settings, "OBJECT_STORAGE_REGION", ""),
        "auto",
    )

    signature_version = _first_non_empty(
        getattr(
            settings,
            "OBJECT_STORAGE_SIGNATURE_VERSION",
            "",
        ),
        "s3v4",
    )

    use_path_style = bool(
        getattr(
            settings,
            "OBJECT_STORAGE_USE_PATH_STYLE",
            False,
        )
    )

    if not endpoint_url:
        return None

    if not access_key or not secret_key:
        return None

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
        config=Config(
            signature_version=signature_version,
            s3={"addressing_style": ("path" if use_path_style else "virtual")},
        ),
    )


def _get_server_side_encryption_params() -> dict[str, str]:
    enforce_encryption = bool(
        getattr(
            settings,
            "OBJECT_STORAGE_ENFORCE_SERVER_SIDE_ENCRYPTION",
            False,
        )
    )

    if not enforce_encryption:
        return {}

    algorithm = _first_non_empty(
        getattr(
            settings,
            "OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION",
            "",
        )
    )

    if not algorithm:
        return {}

    params: dict[str, str] = {
        "ServerSideEncryption": algorithm,
    }

    kms_key_id = _first_non_empty(
        getattr(
            settings,
            "OBJECT_STORAGE_KMS_KEY_ID",
            "",
        )
    )

    if kms_key_id:
        params["SSEKMSKeyId"] = kms_key_id

    return params


def copy_object(
    source_bucket: str,
    source_key: str,
    destination_bucket: str,
    destination_key: str | None = None,
) -> None:
    if source_bucket == destination_bucket:
        return

    client = get_object_storage_client()

    if not client:
        raise RuntimeError("Object storage is not configured for copying objects.")

    client.copy_object(
        CopySource={
            "Bucket": source_bucket,
            "Key": source_key,
        },
        Bucket=destination_bucket,
        Key=destination_key or source_key,
        **_get_server_side_encryption_params(),
    )


def move_object(
    source_bucket: str,
    source_key: str,
    destination_bucket: str,
    destination_key: str | None = None,
) -> None:
    if source_bucket == destination_bucket:
        return

    target_key = destination_key or source_key

    copy_object(
        source_bucket=source_bucket,
        source_key=source_key,
        destination_bucket=destination_bucket,
        destination_key=target_key,
    )

    delete_object(
        bucket_name=source_bucket,
        key=source_key,
    )


def delete_object(
    bucket_name: str,
    key: str,
) -> None:
    client = get_object_storage_client()

    if not client:
        raise RuntimeError("Object storage is not configured for deleting objects.")

    client.delete_object(
        Bucket=bucket_name,
        Key=key,
    )


def put_object_bytes(
    *,
    bucket_name: str,
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    encrypt: bool = False,
    encryption_purpose: str = "",
) -> None:
    client = get_object_storage_client()

    if not client:
        raise RuntimeError("Object storage is not configured for writing objects.")

    object_content = content
    object_content_type = content_type

    if encrypt:
        if not encryption_purpose:
            raise ValueError(
                "An encryption purpose is required when encrypting " "object bytes."
            )

        object_content = encrypt_object_bytes(
            content=content,
            content_type=content_type,
            purpose=encryption_purpose,
        )

        object_content_type = "application/vnd.identitycore.encrypted+json"

    client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=object_content,
        ContentType=object_content_type,
        **_get_server_side_encryption_params(),
    )


def get_object_bytes(
    *,
    bucket_name: str,
    key: str,
    decrypt: bool = False,
    encryption_purpose: str = "",
) -> tuple[bytes, str]:
    client = get_object_storage_client()

    if not client:
        raise RuntimeError("Object storage is not configured for reading objects.")

    response = client.get_object(
        Bucket=bucket_name,
        Key=key,
    )

    payload = response["Body"].read()

    content_type = response.get(
        "ContentType",
        "application/octet-stream",
    )

    if decrypt and is_encrypted_object_payload(payload):
        if not encryption_purpose:
            raise ValueError(
                "An encryption purpose is required when decrypting " "object bytes."
            )

        return decrypt_object_bytes(
            payload=payload,
            purpose=encryption_purpose,
        )

    return payload, content_type


def build_signed_download_url(
    *,
    storage_key: str,
    filename: str | None = None,
    bucket_name: str | None = None,
) -> str:
    resolved_bucket_name = _get_object_storage_bucket(bucket_name)

    expires_in = int(
        getattr(
            settings,
            "MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS",
            300,
        )
    )

    client = get_object_storage_client()

    if client and resolved_bucket_name:
        params: dict[str, str] = {
            "Bucket": resolved_bucket_name,
            "Key": storage_key,
        }

        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        return client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    query: dict[str, str | int] = {
        "expires_in": expires_in,
    }

    if filename:
        query["filename"] = filename

    base = _first_non_empty(
        getattr(settings, "MEDIA_DOWNLOAD_URL_BASE", ""),
        getattr(settings, "UPLOAD_URL_BASE", ""),
    ).rstrip("/")

    if not base:
        return ""

    return f"{base}/{storage_key}?{urlencode(query)}"


def build_signed_upload_url(
    *,
    storage_key: str,
    mime_type: str | None = None,
    bucket_name: str | None = None,
) -> str:
    resolved_bucket_name = _first_non_empty(
        bucket_name,
        _get_upload_bucket(),
    )

    default_expiry_minutes = int(
        getattr(
            settings,
            "UPLOAD_URL_EXPIRES_MINUTES",
            10,
        )
    )

    expires_in = int(
        getattr(
            settings,
            "OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS",
            default_expiry_minutes * 60,
        )
    )

    client = get_object_storage_client()

    if client and resolved_bucket_name:
        params: dict[str, str] = {
            "Bucket": resolved_bucket_name,
            "Key": storage_key,
        }

        if mime_type:
            params["ContentType"] = mime_type

        params.update(_get_server_side_encryption_params())

        return client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    query: dict[str, str | int] = {
        "expires_in": expires_in,
    }

    if mime_type:
        query["content_type"] = mime_type

    base = _first_non_empty(
        getattr(settings, "UPLOAD_URL_BASE", ""),
    ).rstrip("/")

    if not base:
        return ""

    return f"{base}/{storage_key}?{urlencode(query)}"


def build_public_asset_url(
    storage_key: str,
) -> str:
    base = _first_non_empty(
        getattr(settings, "PUBLIC_ASSET_URL_BASE", ""),
    ).rstrip("/")

    if base:
        return f"{base}/{storage_key}"

    return build_signed_download_url(
        storage_key=storage_key,
        bucket_name=get_object_storage_public_bucket_name(),
    )

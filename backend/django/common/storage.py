from urllib.parse import urlencode

import boto3
from botocore.config import Config
from django.conf import settings


def determine_storage_provider() -> str:
    configured_provider = getattr(settings, "OBJECT_STORAGE_PROVIDER", "").strip()
    if configured_provider:
        return configured_provider

    endpoint_url = getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", "")
    if "cloudflarestorage.com" in endpoint_url:
        return "cloudflare_r2"
    if endpoint_url:
        return "s3_compatible"
    return "local"


def _get_object_storage_bucket(bucket_name: str | None = None) -> str:
    if bucket_name:
        return bucket_name
    return getattr(settings, "OBJECT_STORAGE_MEDIA_BUCKET", "") or getattr(
        settings, "OBJECT_STORAGE_BUCKET", ""
    )


def get_object_storage_media_bucket_name() -> str:
    return _get_object_storage_bucket(
        getattr(settings, "OBJECT_STORAGE_MEDIA_BUCKET", "")
    )


def get_object_storage_temp_bucket_name() -> str:
    return getattr(settings, "OBJECT_STORAGE_TEMP_BUCKET", "") or getattr(
        settings, "OBJECT_STORAGE_BUCKET", ""
    )


def get_object_storage_evidence_bucket_name() -> str:
    return getattr(settings, "OBJECT_STORAGE_EVIDENCE_BUCKET", "")


def get_object_storage_public_bucket_name() -> str:
    return getattr(settings, "OBJECT_STORAGE_PUBLIC_BUCKET", "")


def _get_upload_bucket() -> str:
    return get_object_storage_temp_bucket_name() or get_object_storage_media_bucket_name()


def get_object_storage_client():
    endpoint_url = getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", "")
    access_key = getattr(settings, "OBJECT_STORAGE_ACCESS_KEY_ID", "")
    secret_key = getattr(settings, "OBJECT_STORAGE_SECRET_ACCESS_KEY", "")
    region_name = getattr(settings, "OBJECT_STORAGE_REGION", "")
    use_path_style = bool(getattr(settings, "OBJECT_STORAGE_USE_PATH_STYLE", False))
    signature_version = getattr(settings, "OBJECT_STORAGE_SIGNATURE_VERSION", "s3v4")

    if not (access_key and secret_key):
        return None

    client_kwargs = {
        "service_name": "s3",
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": region_name or None,
        "config": Config(
            signature_version=signature_version,
            s3={"addressing_style": "path" if use_path_style else "virtual"},
        ),
    }
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    return boto3.client(**client_kwargs)


def copy_object(
    source_bucket: str,
    source_key: str,
    destination_bucket: str,
    destination_key: str | None = None,
) -> None:
    client = get_object_storage_client()
    if not client:
        raise RuntimeError("Object storage is not configured for copying objects.")
    if source_bucket == destination_bucket:
        return

    client.copy_object(
        CopySource={"Bucket": source_bucket, "Key": source_key},
        Bucket=destination_bucket,
        Key=destination_key or source_key,
    )


def move_object(
    source_bucket: str,
    source_key: str,
    destination_bucket: str,
    destination_key: str | None = None,
) -> None:
    if source_bucket == destination_bucket:
        return

    copy_object(
        source_bucket=source_bucket,
        source_key=source_key,
        destination_bucket=destination_bucket,
        destination_key=destination_key,
    )
    delete_object(bucket_name=source_bucket, key=source_key)


def delete_object(bucket_name: str, key: str) -> None:
    client = get_object_storage_client()
    if not client:
        raise RuntimeError("Object storage is not configured for deleting objects.")
    client.delete_object(Bucket=bucket_name, Key=key)


def put_object_bytes(
    *,
    bucket_name: str,
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    client = get_object_storage_client()
    if not client:
        raise RuntimeError("Object storage is not configured for writing objects.")
    client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=content,
        ContentType=content_type,
    )


def build_signed_download_url(
    *, storage_key: str, filename: str | None = None, bucket_name: str | None = None
) -> str:
    bucket_name = _get_object_storage_bucket(bucket_name)
    expires_in = int(getattr(settings, "MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS", 300))
    client = get_object_storage_client()

    if client and bucket_name:
        params = {"Bucket": bucket_name, "Key": storage_key}
        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
        return client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    query = {"expires_in": expires_in}
    if filename:
        query["filename"] = filename
    base = getattr(
        settings, "MEDIA_DOWNLOAD_URL_BASE", settings.UPLOAD_URL_BASE
    ).rstrip("/")
    return f"{base}/{storage_key}?{urlencode(query)}"


def build_signed_upload_url(
    *, storage_key: str, mime_type: str | None = None, bucket_name: str | None = None
) -> str:
    bucket_name = bucket_name or _get_upload_bucket()
    expires_in = int(
        getattr(
            settings,
            "OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS",
            settings.UPLOAD_URL_EXPIRES_MINUTES * 60,
        )
    )
    client = get_object_storage_client()

    if client and bucket_name:
        params = {"Bucket": bucket_name, "Key": storage_key}
        if mime_type:
            params["ContentType"] = mime_type
        return client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    query = {"expires_in": expires_in}
    if mime_type:
        query["content_type"] = mime_type
    base = getattr(settings, "UPLOAD_URL_BASE", "").rstrip("/")
    return f"{base}/{storage_key}?{urlencode(query)}"


def build_public_asset_url(storage_key: str) -> str:
    base = getattr(settings, "PUBLIC_ASSET_URL_BASE", "").rstrip("/")
    if base:
        return f"{base}/{storage_key}"
    return build_signed_download_url(
        storage_key=storage_key,
        bucket_name=get_object_storage_public_bucket_name(),
    )

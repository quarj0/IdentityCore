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


def _build_object_storage_client():
    bucket_name = getattr(settings, "OBJECT_STORAGE_BUCKET", "")
    endpoint_url = getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", "")
    access_key = getattr(settings, "OBJECT_STORAGE_ACCESS_KEY_ID", "")
    secret_key = getattr(settings, "OBJECT_STORAGE_SECRET_ACCESS_KEY", "")
    region_name = getattr(settings, "OBJECT_STORAGE_REGION", "")
    use_path_style = bool(getattr(settings, "OBJECT_STORAGE_USE_PATH_STYLE", False))
    signature_version = getattr(settings, "OBJECT_STORAGE_SIGNATURE_VERSION", "s3v4")

    if not (bucket_name and access_key and secret_key):
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


def build_signed_download_url(*, storage_key: str, filename: str | None = None) -> str:
    bucket_name = getattr(settings, "OBJECT_STORAGE_BUCKET", "")
    expires_in = int(getattr(settings, "MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS", 300))
    client = _build_object_storage_client()

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


def build_signed_upload_url(*, storage_key: str, mime_type: str | None = None) -> str:
    bucket_name = getattr(settings, "OBJECT_STORAGE_BUCKET", "")
    expires_in = int(
        getattr(
            settings,
            "OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS",
            settings.UPLOAD_URL_EXPIRES_MINUTES * 60,
        )
    )
    client = _build_object_storage_client()

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

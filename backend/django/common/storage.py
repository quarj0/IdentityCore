from urllib.parse import urlencode

import boto3
from django.conf import settings


def build_signed_download_url(*, storage_key: str, filename: str | None = None) -> str:
    bucket_name = getattr(settings, "OBJECT_STORAGE_BUCKET", "")
    endpoint_url = getattr(settings, "OBJECT_STORAGE_ENDPOINT_URL", "")
    access_key = getattr(settings, "OBJECT_STORAGE_ACCESS_KEY_ID", "")
    secret_key = getattr(settings, "OBJECT_STORAGE_SECRET_ACCESS_KEY", "")
    region_name = getattr(settings, "OBJECT_STORAGE_REGION", "")
    expires_in = int(getattr(settings, "MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS", 300))

    if bucket_name and access_key and secret_key:
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region_name or None,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        client = boto3.client(**client_kwargs)
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

from functools import lru_cache

import boto3
from botocore.config import Config

from app.settings import get_settings


class StorageConfigurationError(RuntimeError):
    pass


def get_object_storage_temp_bucket_name() -> str:
    settings = get_settings()
    return settings.object_storage_temp_bucket or settings.object_storage_bucket


def get_object_storage_media_bucket_name() -> str:
    settings = get_settings()
    return settings.object_storage_media_bucket or settings.object_storage_bucket


def get_object_storage_evidence_bucket_name() -> str:
    return get_settings().object_storage_evidence_bucket


def get_object_storage_public_bucket_name() -> str:
    return get_settings().object_storage_public_bucket


@lru_cache
def get_storage_client():
    settings = get_settings()
    if not (
        get_object_storage_media_bucket_name()
        and settings.object_storage_access_key_id
        and settings.object_storage_secret_access_key
    ):
        raise StorageConfigurationError(
            "Object storage is not configured for the AI service."
        )

    client_kwargs = {
        "service_name": "s3",
        "aws_access_key_id": settings.object_storage_access_key_id,
        "aws_secret_access_key": settings.object_storage_secret_access_key,
        "region_name": settings.object_storage_region or None,
        "config": Config(
            signature_version=settings.object_storage_signature_version,
            s3={
                "addressing_style": (
                    "path" if settings.object_storage_use_path_style else "virtual"
                )
            },
        ),
    }
    if settings.object_storage_endpoint_url:
        client_kwargs["endpoint_url"] = settings.object_storage_endpoint_url
    return boto3.client(**client_kwargs)


def fetch_object_bytes(storage_key: str, *, bucket_name: str | None = None) -> bytes:
    client = get_storage_client()
    resolved_bucket_name = bucket_name or get_object_storage_media_bucket_name()
    if not resolved_bucket_name:
        raise StorageConfigurationError("No object storage bucket is configured for media reads.")
    response = client.get_object(
        Bucket=resolved_bucket_name,
        Key=storage_key,
    )
    return response["Body"].read()

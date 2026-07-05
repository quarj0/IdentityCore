from functools import lru_cache

import boto3
from botocore.config import Config

from app.settings import get_settings


class StorageConfigurationError(RuntimeError):
    pass


@lru_cache
def get_storage_client():
    settings = get_settings()
    if not (
        settings.object_storage_bucket
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


def fetch_object_bytes(storage_key: str) -> bytes:
    settings = get_settings()
    client = get_storage_client()
    response = client.get_object(
        Bucket=settings.object_storage_bucket,
        Key=storage_key,
    )
    return response["Body"].read()

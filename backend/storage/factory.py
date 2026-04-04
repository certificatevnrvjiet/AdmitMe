from __future__ import annotations

from config.settings import (
    STORAGE_PROVIDER,
    LOCAL_STORAGE_ROOT,
    S3_BUCKET,
    AWS_REGION,
    S3_ENDPOINT_URL,
)

from .base import StorageProvider
from .gdrive import GoogleDriveStorageProvider
from .local import LocalStorageProvider
from .s3 import S3StorageProvider


def get_storage_provider(drive_service=None) -> StorageProvider:
    provider = (STORAGE_PROVIDER or "local").lower()

    if provider == "local":
        return LocalStorageProvider(LOCAL_STORAGE_ROOT)

    if provider == "gdrive":
        return GoogleDriveStorageProvider(drive_service)

    if provider == "s3":
        return S3StorageProvider(
            bucket=S3_BUCKET,
            region=AWS_REGION,
            endpoint_url=S3_ENDPOINT_URL,
        )

    raise ValueError(f"Unsupported STORAGE_PROVIDER: {STORAGE_PROVIDER}")

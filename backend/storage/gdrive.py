from __future__ import annotations

import re
from io import BytesIO

from GoogleService import download_drive_image_as_bytes

from .base import StorageProvider


class GoogleDriveStorageProvider(StorageProvider):
    name = "gdrive"

    def __init__(self, drive_service):
        self.drive_service = drive_service

    @staticmethod
    def extract_file_id(value: str) -> str | None:
        if not value:
            return None

        if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
            return value

        match = re.search(r"[?&]id=([A-Za-z0-9_-]+)", value)
        if match:
            return match.group(1)

        match = re.search(r"/d/([A-Za-z0-9_-]+)", value)
        if match:
            return match.group(1)

        return None

    def save(self, key: str, content: bytes, content_type: str | None = None) -> str:
        raise NotImplementedError("Google Drive writes are disabled in compatibility mode")

    def get_bytes(self, key: str) -> bytes | None:
        file_id = self.extract_file_id(key)
        if not file_id or not self.drive_service:
            return None
        return download_drive_image_as_bytes(file_id, self.drive_service)

    def get_stream(self, key: str):
        payload = self.get_bytes(key)
        if payload is None:
            return None
        return BytesIO(payload)

    def delete(self, key: str) -> bool:
        return False

    def exists(self, key: str) -> bool:
        return self.get_bytes(key) is not None

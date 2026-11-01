from __future__ import annotations

import re
import threading
from io import BytesIO

from GoogleService import download_drive_image_as_bytes, get_drive_service

from .base import StorageProvider

_thread_local = threading.local()

def _get_thread_drive_service(fallback=None):
    if not hasattr(_thread_local, "drive_service"):
        try:
            _thread_local.drive_service = get_drive_service()
        except Exception:
            _thread_local.drive_service = fallback
    return _thread_local.drive_service


class GoogleDriveStorageProvider(StorageProvider):
    name = "gdrive"

    def __init__(self, drive_service=None):
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
        if not file_id:
            return None
        service = _get_thread_drive_service(self.drive_service)
        if not service:
            return None
        return download_drive_image_as_bytes(file_id, service)

    def get_stream(self, key: str):
        payload = self.get_bytes(key)
        if payload is None:
            return None
        return BytesIO(payload)

    def delete(self, key: str) -> bool:
        return False

    def exists(self, key: str) -> bool:
        return self.get_bytes(key) is not None

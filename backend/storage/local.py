from __future__ import annotations

from io import BytesIO
from os.path import commonpath
from pathlib import Path

from .base import StorageProvider


class LocalStorageProvider(StorageProvider):
    name = "local"

    def __init__(self, root_dir: str):
        self.root = Path(root_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        clean_key = key.lstrip("/")
        path = (self.root / clean_key).resolve()
        if commonpath([str(self.root), str(path)]) != str(self.root):
            raise ValueError("Invalid object key")
        return path

    def save(self, key: str, content: bytes, content_type: str | None = None) -> str:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def get_bytes(self, key: str) -> bytes | None:
        path = self._path_for(key)
        if not path.exists() or not path.is_file():
            return None
        return path.read_bytes()

    def get_stream(self, key: str):
        payload = self.get_bytes(key)
        if payload is None:
            return None
        return BytesIO(payload)

    def delete(self, key: str) -> bool:
        path = self._path_for(key)
        if not path.exists():
            return False
        path.unlink(missing_ok=True)
        return True

    def exists(self, key: str) -> bool:
        path = self._path_for(key)
        return path.exists() and path.is_file()

from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import BinaryIO


@dataclass(frozen=True)
class DocumentRef:
    provider: str
    key: str

    def as_string(self) -> str:
        return f"{self.provider}:{self.key}"


class StorageProvider(ABC):
    name: str

    @abstractmethod
    def save(self, key: str, content: bytes, content_type: str | None = None) -> str:
        """Persist bytes and return canonical key."""

    @abstractmethod
    def get_bytes(self, key: str) -> bytes | None:
        """Return full object bytes, or None if missing."""

    @abstractmethod
    def get_stream(self, key: str) -> BinaryIO | None:
        """Return readable stream, or None if missing."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete object if present."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if object exists."""

    def signed_url(self, key: str, expires_in_seconds: int = 3600) -> str | None:
        """Optional signed URL support."""
        return None

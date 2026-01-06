from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from connectors.base.types import SessionBlob


class SessionStore(ABC):
    """
    Store/retrieve platform sessions by (platform, user_key).
    DEV: encrypted file store
    QS/PROD: Redis / Cosmos / KeyVault-backed secrets (depends on policy)
    """

    @abstractmethod
    def load(self, platform: str, user_key: str) -> Optional[SessionBlob]:
        raise NotImplementedError

    @abstractmethod
    def save(self, blob: SessionBlob, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, platform: str, user_key: str) -> None:
        raise NotImplementedError

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from connectors.base.session_store import SessionStore
from connectors.base.types import SessionBlob
from core.config.settings import AppSettings, load_settings


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FileSessionStoreConfig:
    base_dir: Path
    fernet_key: bytes


class FileEncryptedSessionStore(SessionStore):
    def __init__(self, settings: Optional[AppSettings] = None):
        settings = settings or load_settings("dev")

        key = (settings.security.session_enc_key or "").strip()
        if not key:
            raise RuntimeError("security.session_enc_key missing in infra/env/dev.yaml")

        base_dir = Path(settings.sessions.base_dir)
        if not base_dir.is_absolute():
            base_dir = _project_root() / base_dir

        self._cfg = FileSessionStoreConfig(
            base_dir=base_dir,
            fernet_key=key.encode("utf-8"),
        )
        self._fernet = Fernet(self._cfg.fernet_key)
        self._cfg.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, platform: str, user_key: str) -> Path:
        safe_platform = platform.lower().strip()
        safe_user = user_key.replace("/", "_").replace("\\", "_").replace(":", "_")
        pdir = self._cfg.base_dir / safe_platform
        pdir.mkdir(parents=True, exist_ok=True)
        return pdir / f"{safe_user}.json.enc"

    def load(self, platform: str, user_key: str) -> Optional[SessionBlob]:
        path = self._path(platform, user_key)
        if not path.exists():
            return None

        try:
            encrypted = path.read_bytes()
            raw = self._fernet.decrypt(encrypted)
            data = json.loads(raw.decode("utf-8"))
            blob = SessionBlob.model_validate(data)

            if blob.is_expired():
                self.delete(platform, user_key)
                return None

            return blob
        except Exception:
            self.delete(platform, user_key)
            return None

    def save(self, blob: SessionBlob, ttl_seconds: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(ttl_seconds))
        blob_to_save = blob.model_copy(update={"expires_at": expires_at})

        path = self._path(blob_to_save.platform, blob_to_save.user_key)
        raw = json.dumps(blob_to_save.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")
        encrypted = self._fernet.encrypt(raw)
        path.write_bytes(encrypted)

    def delete(self, platform: str, user_key: str) -> None:
        path = self._path(platform, user_key)
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

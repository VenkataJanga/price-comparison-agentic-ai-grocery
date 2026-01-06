from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from connectors.base.session_store import SessionStore
from connectors.base.types import SessionBlob
from core.config.settings import load_settings

def _project_root() -> Path:
    # file lives at <root>/connectors/base/session_store_file_encrypted.py
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FileSessionStoreConfig:
    base_dir: Path
    fernet_key: bytes




class FileEncryptedSessionStore(SessionStore):
    def __init__(self, settings=None):
        settings = settings or load_settings("dev")

        base_dir = Path(settings.sessions.base_dir)
        key = settings.security.session_enc_key


        if not key:
            raise RuntimeError("session_enc_key missing in dev.yaml")

        self._cfg = FileSessionStoreConfig(
            base_dir=base_dir,
            fernet_key=key.encode("utf-8"),
        )
        self._fernet = Fernet(self._cfg.fernet_key)
        self._cfg.base_dir.mkdir(parents=True, exist_ok=True)

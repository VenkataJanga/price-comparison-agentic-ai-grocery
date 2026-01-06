from __future__ import annotations

from connectors.base.session_store_file_encrypted import FileEncryptedSessionStore
from core.config.settings import load_settings


def get_session_store(env: str | None = None):
    settings = load_settings(env)
    if settings.sessions.store == "file_encrypted":
        return FileEncryptedSessionStore(settings=settings)
    raise RuntimeError(f"Unknown session store: {settings.sessions.store}")

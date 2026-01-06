from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field


class SessionSettings(BaseModel):
    store: str = Field(default="file_encrypted")
    base_dir: str = Field(default="./sessions")
    ttl_seconds: int = Field(default=3600)


class SecuritySettings(BaseModel):
    session_enc_key: str = Field(default="")


class AppSettings(BaseModel):
    sessions: SessionSettings = Field(default_factory=SessionSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    model_config = {"extra": "allow"}  # pydantic v2


def _project_root() -> Path:
    # core/config/settings.py -> <root>/core/config/settings.py
    return Path(__file__).resolve().parents[2]


def _config_dir() -> Path:
    # your repo layout: <root>/infra/env/<env>.yaml
    return _project_root() / "infra" / "env"


def load_settings(env: Optional[str] = None) -> AppSettings:
    resolved_env = env or os.getenv("APP_ENV", "dev")

    cfg_path = _config_dir() / f"{resolved_env}.yaml"
    if not cfg_path.exists():
        raise RuntimeError(f"Config file not found: {cfg_path}")

    raw: Dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return AppSettings.model_validate(raw)

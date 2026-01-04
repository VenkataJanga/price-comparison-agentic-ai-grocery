from __future__ import annotations
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import structlog


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AuditConfig:
    path: Path


_default_path = Path(os.getenv("AUDIT_LOG_PATH", str(_project_root() / "audit.log.jsonl")))
_config = AuditConfig(path=_default_path)


def _safe_ctx() -> Dict[str, Any]:
    try:
        ctxmod = structlog.contextvars
        getter = getattr(ctxmod, "get_merged_contextvars", None)
        if callable(getter):
            return dict(getter(structlog.get_logger()))
    except Exception:
        pass
    return {}


def emit(
    event_type: str,
    *,
    actor: str = "SYSTEM",
    platform: Optional[str] = None,
    item_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    ctx = _safe_ctx()
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor": actor,
        "platform": platform,
        "item_id": item_id,
        "correlation_id": ctx.get("correlation_id"),
        "path": ctx.get("path"),
        "method": ctx.get("method"),
        "payload": payload or {},
    }

    _config.path.parent.mkdir(parents=True, exist_ok=True)
    with _config.path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

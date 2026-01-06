from __future__ import annotations

from typing import Optional, Dict, Any

from core.config.settings import load_settings
from observability import audit_logger

from connectors.worker.models import (
    WorkerHealthResponse,
    WorkerAuthStartRequest,
    WorkerAuthStartResponse,
    WorkerAuthSubmitRequest,
    WorkerAuthSubmitResponse,
    WorkerSearchRequest,
    WorkerSearchResponse,
)


class WorkerClient:
    """
    HTTP-only client to a remote Automation Worker.
    Worker will run browser automation in QS/PROD where installs are allowed.
    """

    def __init__(self, env: str = "dev"):
        self._settings = load_settings(env)
        self._worker = getattr(self._settings, "worker", {})  # extra="allow" safe
        self.enabled: bool = bool(self._worker.get("enabled", False))
        self.base_url: str = str(self._worker.get("base_url", "")).rstrip("/")
        self.timeout_seconds: int = int(self._worker.get("timeout_seconds", 30))
        self.api_key: str = str(self._worker.get("api_key", "") or "")

    def _headers(self, correlation_id: Optional[str]) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if correlation_id:
            h["X-Correlation-ID"] = correlation_id
        if self.api_key:
            h["X-Worker-Api-Key"] = self.api_key
        return h

    def _call(self, method: str, path: str, payload: Optional[Dict[str, Any]], correlation_id: Optional[str]) -> Dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Worker is disabled in config (worker.enabled=false).")
        if not self.base_url:
            raise RuntimeError("Worker base_url is missing in config.")

        url = f"{self.base_url}{path}"

        audit_logger.emit(
            "WORKER_CALL_STARTED",
            platform=None,
            payload={"method": method, "url": url, "has_payload": bool(payload)},
        )

        try:
            import httpx  # imported here to avoid import-time failure if httpx missing

            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.request(method, url, json=payload, headers=self._headers(correlation_id))
                resp.raise_for_status()
                data = resp.json()

            audit_logger.emit(
                "WORKER_CALL_COMPLETED",
                platform=None,
                payload={"method": method, "url": url, "status_code": 200},
            )
            return data

        except Exception as e:
            audit_logger.emit(
                "WORKER_CALL_FAILED",
                platform=None,
                payload={"method": method, "url": url, "error": str(e)},
            )
            raise

    def health(self, correlation_id: Optional[str] = None) -> WorkerHealthResponse:
        data = self._call("GET", "/health", None, correlation_id)
        return WorkerHealthResponse.model_validate(data)

    def auth_start(self, req: WorkerAuthStartRequest, correlation_id: Optional[str] = None) -> WorkerAuthStartResponse:
        data = self._call("POST", "/auth/start", req.model_dump(mode="json"), correlation_id)
        return WorkerAuthStartResponse.model_validate(data)

    def auth_submit(self, req: WorkerAuthSubmitRequest, correlation_id: Optional[str] = None) -> WorkerAuthSubmitResponse:
        data = self._call("POST", "/auth/submit", req.model_dump(mode="json"), correlation_id)
        return WorkerAuthSubmitResponse.model_validate(data)

    def search(self, req: WorkerSearchRequest, correlation_id: Optional[str] = None) -> WorkerSearchResponse:
        data = self._call("POST", "/search", req.model_dump(mode="json"), correlation_id)
        return WorkerSearchResponse.model_validate(data)

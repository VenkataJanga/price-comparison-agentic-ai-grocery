from __future__ import annotations

from typing import List, Optional

from connectors.base.platform_client import PlatformClient
from connectors.base.types import AuthState, AuthStatus, PlatformHealth, UserContext, SessionBlob
from connectors.base.session_store_factory import get_session_store
from core.config.settings import load_settings
from core.schemas.grocery_item import GroceryItem
from core.schemas.platform_price import PlatformPrice
from observability import audit_logger

from connectors.worker.client import WorkerClient
from connectors.worker.models import WorkerAuthStartRequest, WorkerAuthSubmitRequest, WorkerSearchRequest


class JiomartClient(PlatformClient):
    platform = "JIOMART"

    def __init__(self, env: str = "dev"):
        self._env = env
        self._settings = load_settings(env)
        self._store = get_session_store(env=env)
        self._worker = WorkerClient(env=env)

    def health(self) -> PlatformHealth:
        # Local connector health depends on worker health (if enabled)
        if not self._worker.enabled:
            return PlatformHealth(platform=self.platform, status="DEGRADED", message="Worker disabled in config")
        try:
            self._worker.health()
            return PlatformHealth(platform=self.platform, status="OK")
        except Exception as e:
            return PlatformHealth(platform=self.platform, status="DOWN", message=str(e))

    def ensure_authenticated(self, ctx: UserContext) -> AuthState:
        blob = self._store.load(self.platform, ctx.user_key)
        if blob:
            audit_logger.emit("SESSION_REUSED", platform=self.platform, payload={"user_key": ctx.user_key})
            return AuthState(platform=self.platform, status=AuthStatus.AUTHENTICATED)

        return AuthState(platform=self.platform, status=AuthStatus.NOT_AUTHENTICATED)

    def start_login(self, ctx: UserContext) -> AuthState:
        # If session exists, short-circuit
        existing = self._store.load(self.platform, ctx.user_key)
        if existing:
            audit_logger.emit("SESSION_REUSED", platform=self.platform, payload={"user_key": ctx.user_key})
            return AuthState(platform=self.platform, status=AuthStatus.AUTHENTICATED)

        # Call worker
        req = WorkerAuthStartRequest(user_key=ctx.user_key, pincode=ctx.pincode, platform=self.platform)
        resp = self._worker.auth_start(req)

        audit_logger.emit("PLATFORM_AUTH_START", platform=self.platform, payload={"status": resp.status})

        return AuthState(platform=self.platform, status=resp.status, auth_session_id=resp.auth_session_id, message=resp.message)

    def submit_otp(self, ctx: UserContext, auth_session_id: str, otp: str) -> AuthState:
        req = WorkerAuthSubmitRequest(
            user_key=ctx.user_key,
            auth_session_id=auth_session_id,
            otp=otp,
            platform=self.platform,
        )
        resp = self._worker.auth_submit(req)

        audit_logger.emit("PLATFORM_AUTH_SUBMIT", platform=self.platform, payload={"status": resp.status})

        if resp.status == AuthStatus.AUTHENTICATED:
            blob = SessionBlob(platform=self.platform, user_key=ctx.user_key, data={"authenticated": True})
            self._store.save(blob, ttl_seconds=self._settings.sessions.ttl_seconds)
            audit_logger.emit("SESSION_SAVED", platform=self.platform, payload={"user_key": ctx.user_key})

        return AuthState(platform=self.platform, status=resp.status, auth_session_id=None, message=resp.message)

    def search(self, item: GroceryItem, ctx: UserContext) -> List[PlatformPrice]:
        # Ensure authenticated first (worker might allow guest search; keep strict for now)
        state = self.ensure_authenticated(ctx)
        if state.status != AuthStatus.AUTHENTICATED:
            audit_logger.emit("PLATFORM_SEARCH_BLOCKED_NOT_AUTH", platform=self.platform, payload={"item_id": item.id})
            return []

        req = WorkerSearchRequest(user_key=ctx.user_key, pincode=ctx.pincode, item=item, platform=self.platform)
        resp = self._worker.search(req)

        audit_logger.emit(
            "PLATFORM_SEARCH_RESULTS",
            platform=self.platform,
            payload={"item_id": item.id, "candidate_count": len(resp.candidates)},
        )

        return resp.candidates

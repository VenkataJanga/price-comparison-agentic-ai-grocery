from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from connectors.base.types import AuthStatus, UserContext
from connectors.base.session_store_factory import get_session_store
from core.config.settings import load_settings
from core.security.user_key import get_user_key
from observability import audit_logger

from connectors.jiomart import JiomartClient

router = APIRouter(tags=["auth"])


class AuthStartResponse(BaseModel):
    platform: str
    status: AuthStatus
    auth_session_id: Optional[str] = None
    message: Optional[str] = None


class AuthOtpSubmitRequest(BaseModel):
    auth_session_id: str = Field(..., description="Returned by /start")
    otp: str = Field(..., min_length=1, max_length=12)


class AuthSubmitResponse(BaseModel):
    platform: str
    status: AuthStatus
    message: Optional[str] = None


class AuthStatusResponse(BaseModel):
    platform: str
    status: AuthStatus


def _ctx(request: Request) -> UserContext:
    # pincode is currently in compare payload; for auth we take default/dev value from config or header
    settings = load_settings("dev")
    pincode = request.headers.get("X-Pincode") or "560001"
    return UserContext(user_key=get_user_key(request), pincode=pincode)


@router.post("/auth/jiomart/start", response_model=AuthStartResponse)
def jiomart_start(request: Request) -> AuthStartResponse:
    client = JiomartClient(env="dev")
    ctx = _ctx(request)

    # If already authenticated, return immediately
    existing = client.ensure_authenticated(ctx)
    if existing.status == AuthStatus.AUTHENTICATED:
        return AuthStartResponse(platform=client.platform, status=AuthStatus.AUTHENTICATED)

    try:
        state = client.start_login(ctx)
        return AuthStartResponse(
            platform=client.platform,
            status=state.status,
            auth_session_id=state.auth_session_id,
            message=state.message,
        )
    except Exception as e:
        audit_logger.emit("AUTH_START_FAILED", platform=client.platform, payload={"error": str(e)})
        raise HTTPException(status_code=502, detail=f"Worker auth start failed: {e}")


@router.post("/auth/jiomart/submit", response_model=AuthSubmitResponse)
def jiomart_submit(request: Request, body: AuthOtpSubmitRequest) -> AuthSubmitResponse:
    client = JiomartClient(env="dev")
    ctx = _ctx(request)

    try:
        state = client.submit_otp(ctx, body.auth_session_id, body.otp)
        return AuthSubmitResponse(platform=client.platform, status=state.status, message=state.message)
    except Exception as e:
        audit_logger.emit("AUTH_SUBMIT_FAILED", platform=client.platform, payload={"error": str(e)})
        raise HTTPException(status_code=502, detail=f"Worker auth submit failed: {e}")


@router.get("/auth/jiomart/status", response_model=AuthStatusResponse)
def jiomart_status(request: Request) -> AuthStatusResponse:
    store = get_session_store(env="dev")
    user_key = get_user_key(request)
    blob = store.load("JIOMART", user_key)
    if blob:
        return AuthStatusResponse(platform="JIOMART", status=AuthStatus.AUTHENTICATED)
    return AuthStatusResponse(platform="JIOMART", status=AuthStatus.NOT_AUTHENTICATED)


@router.post("/auth/jiomart/logout", response_model=AuthStatusResponse)
def jiomart_logout(request: Request) -> AuthStatusResponse:
    store = get_session_store(env="dev")
    user_key = get_user_key(request)
    store.delete("JIOMART", user_key)
    audit_logger.emit("SESSION_DELETED", platform="JIOMART", payload={"user_key": user_key})
    return AuthStatusResponse(platform="JIOMART", status=AuthStatus.NOT_AUTHENTICATED)

import time
from typing import Any, Dict, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from observability import audit_logger

router = APIRouter(prefix="/auth", tags=["auth"])
log = structlog.get_logger("auth")

# In-memory mock store (Module 1 only)
_AUTH_STATE: Dict[str, Dict[str, Any]] = {}


class AuthStartResponse(BaseModel):
    platform: str
    status: str  # AUTHENTICATED | OTP_REQUIRED
    auth_session_id: Optional[str] = None


class OtpSubmitRequest(BaseModel):
    auth_session_id: str
    otp: str


@router.post("/{platform}/start", response_model=AuthStartResponse)
async def auth_start(platform: str) -> AuthStartResponse:
    platform_u = platform.upper()
    log.info("auth_start", platform=platform_u)
    audit_logger.emit("AUTH_START_REQUESTED", platform=platform_u)

    if platform_u == "JIOMART":
        auth_session_id = f"{platform_u}-{int(time.time())}"
        _AUTH_STATE[platform_u] = {"status": "OTP_REQUIRED", "auth_session_id": auth_session_id}
        log.info("auth_otp_required", platform=platform_u)
        audit_logger.emit("AUTH_OTP_REQUIRED", platform=platform_u, payload={"auth_session_id": auth_session_id})
        return AuthStartResponse(platform=platform_u, status="OTP_REQUIRED", auth_session_id=auth_session_id)

    _AUTH_STATE[platform_u] = {"status": "AUTHENTICATED"}
    log.info("auth_authenticated", platform=platform_u)
    audit_logger.emit("AUTH_SUCCESS", platform=platform_u)
    return AuthStartResponse(platform=platform_u, status="AUTHENTICATED")


@router.post("/{platform}/submit")
async def auth_submit(platform: str, payload: OtpSubmitRequest) -> Dict[str, Any]:
    platform_u = platform.upper()
    # DO NOT log OTP
    log.info("otp_submit_received", platform=platform_u, auth_session_id=payload.auth_session_id)
    audit_logger.emit("AUTH_OTP_SUBMIT_RECEIVED", platform=platform_u, payload={"auth_session_id": payload.auth_session_id})

    st = _AUTH_STATE.get(platform_u)
    if not st or st.get("status") != "OTP_REQUIRED":
        audit_logger.emit("AUTH_FAILURE", platform=platform_u, payload={"reason": "no_challenge"})
        raise HTTPException(status_code=400, detail="No OTP challenge in progress.")

    if st.get("auth_session_id") != payload.auth_session_id:
        audit_logger.emit("AUTH_FAILURE", platform=platform_u, payload={"reason": "invalid_auth_session_id"})
        raise HTTPException(status_code=400, detail="Invalid auth_session_id.")

    if len(payload.otp.strip()) < 4:
        log.info("otp_submit_failed", platform=platform_u, reason="otp_too_short")
        audit_logger.emit("AUTH_FAILURE", platform=platform_u, payload={"reason": "otp_too_short"})
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    _AUTH_STATE[platform_u] = {"status": "AUTHENTICATED"}
    log.info("otp_submit_success", platform=platform_u)
    audit_logger.emit("AUTH_SUCCESS", platform=platform_u)
    return {"platform": platform_u, "status": "AUTHENTICATED"}


@router.get("/{platform}/status")
async def auth_status(platform: str) -> Dict[str, Any]:
    platform_u = platform.upper()
    status = _AUTH_STATE.get(platform_u, {"status": "NOT_AUTHENTICATED"})["status"]
    log.info("auth_status", platform=platform_u, status=status)
    audit_logger.emit("AUTH_STATUS_CHECKED", platform=platform_u, payload={"status": status})
    return {"platform": platform_u, "status": status}

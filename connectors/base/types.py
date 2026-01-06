from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuthStatus(str, Enum):
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    AUTHENTICATED = "AUTHENTICATED"
    OTP_REQUIRED = "OTP_REQUIRED"
    FAILED = "FAILED"


class PlatformHealthStatus(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class UserContext(BaseModel):
    """
    Minimal user context for platform operations.
    Later: add dynamic pincode, city, user_id, device fingerprint, etc.
    """
    user_key: str = Field(..., description="Stable key per user/device. E.g. email hash or 'local-dev'")
    pincode: str = Field(..., description="Delivery pincode")
    headed: bool = Field(default=True, description="Used by real browser workers later; keep for compatibility")


class AuthState(BaseModel):
    platform: str
    status: AuthStatus
    auth_session_id: Optional[str] = None
    message: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionBlob(BaseModel):
    """
    Opaque storage for platform session/cookies/token.
    For DEV w/out browser: still useful to store worker token/session id.
    """
    platform: str
    user_key: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        return bool(self.expires_at and datetime.now(timezone.utc) >= self.expires_at)


class PlatformHealth(BaseModel):
    platform: str
    status: PlatformHealthStatus = PlatformHealthStatus.OK
    message: Optional[str] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

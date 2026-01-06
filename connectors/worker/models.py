from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from connectors.base.types import AuthStatus
from core.schemas.grocery_item import GroceryItem
from core.schemas.platform_price import PlatformPrice


class WorkerHealthResponse(BaseModel):
    status: str = "ok"
    message: Optional[str] = None


class WorkerAuthStartRequest(BaseModel):
    platform: str = Field(default="JIOMART")
    user_key: str
    pincode: str


class WorkerAuthStartResponse(BaseModel):
    platform: str
    status: AuthStatus
    auth_session_id: Optional[str] = None
    message: Optional[str] = None


class WorkerAuthSubmitRequest(BaseModel):
    platform: str = Field(default="JIOMART")
    user_key: str
    auth_session_id: str
    otp: str


class WorkerAuthSubmitResponse(BaseModel):
    platform: str
    status: AuthStatus
    message: Optional[str] = None


class WorkerSearchRequest(BaseModel):
    platform: str = Field(default="JIOMART")
    user_key: str
    pincode: str
    item: GroceryItem


class WorkerSearchResponse(BaseModel):
    platform: str
    item_id: str
    candidates: List[PlatformPrice] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None

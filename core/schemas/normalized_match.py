from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field
from core.schemas.platform_price import PlatformPrice


MatchType = Literal["EXACT", "CLOSE", "SUBSTITUTE", "UNAVAILABLE", "MOCK"]


class NormalizedMatch(BaseModel):
    item_id: str
    item_name: str
    requested_quantity: str = Field(..., description="Original requested quantity string, e.g., 1L")
    platform: str
    matched: Optional[PlatformPrice] = None

    match_type: MatchType = "MOCK"
    match_score: float = Field(default=0.8, ge=0, le=1)
    conversion_notes: Optional[str] = None

    availability: str = Field(default="IN_STOCK")
    effective_price: float = Field(default=0.0, ge=0, description="Final item price used in totals")

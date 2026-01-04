from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


Availability = Literal["IN_STOCK", "OUT_OF_STOCK", "NOT_FOUND", "UNKNOWN"]


class PlatformPrice(BaseModel):
    platform: str = Field(..., description="Platform name, e.g., JIOMART")
    price: float = Field(..., ge=0, description="Item price")
    currency: str = Field(default="INR")
    pack_size: float = Field(..., gt=0, description="Pack size numeric value (normalized if possible)")
    unit: str = Field(..., min_length=1, description="Pack unit, e.g., kg, g, L, ml, pcs")
    availability: Availability = Field(default="UNKNOWN")

    delivery_fee: Optional[float] = Field(default=None, ge=0, description="If known at item-level")
    product_url: Optional[str] = None

    raw_title: Optional[str] = Field(default=None, description="Raw product title text from platform")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extraction_confidence: float = Field(default=0.5, ge=0, le=1, description="Confidence of extraction/parsing")

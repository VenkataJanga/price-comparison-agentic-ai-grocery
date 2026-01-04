from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel, Field


class PlatformCartTotals(BaseModel):
    items_total: float = Field(default=0.0, ge=0)
    delivery: float = Field(default=0.0, ge=0)
    total: float = Field(default=0.0, ge=0)


class CartPlan(BaseModel):
    strategy: str = Field(default="BEST_PER_ITEM_SPLIT_CART")
    platform_allocations: Dict[str, List[str]] = Field(default_factory=dict, description="platform -> list[item_id]")
    platform_totals: Dict[str, PlatformCartTotals] = Field(default_factory=dict)
    delivery_total: float = Field(default=0.0, ge=0)
    grand_total: float = Field(default=0.0, ge=0)

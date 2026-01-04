from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field
from core.schemas.normalized_match import NormalizedMatch
from core.schemas.cart_plan import CartPlan


class BestRecommendation(BaseModel):
    cheapest_overall_strategy: str = Field(default="BEST_PER_ITEM_SPLIT_CART")
    grand_total: float = Field(default=0.0, ge=0)
    notes: List[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    item_wise_comparison: List[NormalizedMatch]
    cart_summary: CartPlan
    best_recommendation: BestRecommendation

    total_savings_compared_to_highest_price: float = Field(default=0.0, ge=0)
    notes: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0, le=1)

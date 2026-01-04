from __future__ import annotations
from typing import Dict, List

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.schemas.grocery_item import GroceryItem
from core.schemas.platform_price import PlatformPrice
from core.schemas.normalized_match import NormalizedMatch
from core.schemas.cart_plan import CartPlan, PlatformCartTotals
from core.schemas.comparison_result import ComparisonResult, BestRecommendation
from observability import audit_logger

router = APIRouter(prefix="/compare", tags=["compare"])
log = structlog.get_logger("compare")


class CompareRequest(BaseModel):
    pincode: str = Field(..., description="User delivery pincode (DEV can use one static value)")
    items: List[GroceryItem]


@router.post("", response_model=ComparisonResult)
async def compare_prices(payload: CompareRequest) -> ComparisonResult:
    """
    Module 1: typed domain models, still mocked pricing logic.
    Module 2+: replace mocks with connector/agent results.
    """
    log.info("compare_requested", pincode=payload.pincode, item_count=len(payload.items))
    audit_logger.emit("COMPARE_REQUESTED", payload={"pincode": payload.pincode, "item_count": len(payload.items)})

    platforms = ["JIOMART", "BIGBASKET"]
    matches: List[NormalizedMatch] = []

    # MOCK: create a fake PlatformPrice + NormalizedMatch per item
    for i, item in enumerate(payload.items):
        chosen_platform = platforms[i % len(platforms)]
        mock_price = round(50 + (i * 7.5), 2)

        pp = PlatformPrice(
            platform=chosen_platform,
            price=mock_price,
            pack_size=item.quantity,
            unit=item.unit,
            availability="IN_STOCK",
            product_url=None,
            raw_title=f"{item.brand + ' ' if item.brand else ''}{item.itemname} {item.quantity}{item.unit}",
            extraction_confidence=0.8,
        )

        m = NormalizedMatch(
            item_id=item.id,
            item_name=item.itemname,
            requested_quantity=f"{item.quantity}{item.unit}",
            platform=chosen_platform,
            matched=pp,
            match_type="MOCK",
            match_score=0.8,
            conversion_notes=None,
            availability="IN_STOCK",
            effective_price=mock_price,
        )
        matches.append(m)

    # Build split-cart plan (platform allocations & totals)
    allocations: Dict[str, List[str]] = {}
    totals: Dict[str, PlatformCartTotals] = {}

    # Mock delivery fees per platform
    delivery_fee_map = {"JIOMART": 25.0, "BIGBASKET": 30.0}

    for m in matches:
        allocations.setdefault(m.platform, []).append(m.item_id)

    for platform, item_ids in allocations.items():
        items_total = round(sum(x.effective_price for x in matches if x.platform == platform), 2)
        delivery = float(delivery_fee_map.get(platform, 0.0))
        total = round(items_total + delivery, 2)
        totals[platform] = PlatformCartTotals(items_total=items_total, delivery=delivery, total=total)

    delivery_total = round(sum(t.delivery for t in totals.values()), 2)
    grand_total = round(sum(t.total for t in totals.values()), 2)

    cart_plan = CartPlan(
        strategy="BEST_PER_ITEM_SPLIT_CART",
        platform_allocations=allocations,
        platform_totals=totals,
        delivery_total=delivery_total,
        grand_total=grand_total,
    )

    reco = BestRecommendation(
        cheapest_overall_strategy="BEST_PER_ITEM_SPLIT_CART",
        grand_total=grand_total,
        notes=["Module 1: typed models. Pricing & delivery are mocked."],
    )

    result = ComparisonResult(
        item_wise_comparison=matches,
        cart_summary=cart_plan,
        best_recommendation=reco,
        total_savings_compared_to_highest_price=0.0,
        notes=["Delivery fees mocked.", "No substitutions in Module 1 yet."],
        confidence=0.8,
    )

    log.info("compare_completed", grand_total=grand_total, platforms=list(totals.keys()))
    audit_logger.emit("COMPARE_COMPLETED", payload={"grand_total": grand_total, "platforms": list(totals.keys())})
    return result

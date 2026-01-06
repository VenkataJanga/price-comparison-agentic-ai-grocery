from __future__ import annotations

from typing import Dict, List

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core.schemas.grocery_item import GroceryItem
from core.schemas.platform_price import PlatformPrice
from core.schemas.normalized_match import NormalizedMatch
from core.schemas.cart_plan import CartPlan, PlatformCartTotals
from core.schemas.comparison_result import ComparisonResult, BestRecommendation
from core.security.user_key import get_user_key
from connectors.base.types import UserContext, AuthStatus
from connectors.jiomart import JiomartClient
from observability import audit_logger

router = APIRouter(prefix="/compare", tags=["compare"])
log = structlog.get_logger("compare")


class CompareRequest(BaseModel):
    pincode: str = Field(..., description="User delivery pincode")
    items: List[GroceryItem]


@router.post("", response_model=ComparisonResult)
async def compare_prices(payload: CompareRequest, request: Request) -> ComparisonResult:
    """
    Module 2.2.2:
    - Use worker-backed JioMart search when authenticated
    - Fallback to Module 1 mock prices otherwise
    """
    log.info("compare_requested", pincode=payload.pincode, item_count=len(payload.items))
    audit_logger.emit(
        "COMPARE_REQUESTED",
        payload={"pincode": payload.pincode, "item_count": len(payload.items)},
    )

    # Build user context
    ctx = UserContext(
        user_key=get_user_key(request),
        pincode=payload.pincode,
    )

    jiomart = JiomartClient(env="dev")
    jiomart_auth = jiomart.ensure_authenticated(ctx)

    matches: List[NormalizedMatch] = []

    # Mock fallback prices (Module 1 behavior)
    mock_platforms = ["JIOMART", "BIGBASKET"]
    delivery_fee_map = {"JIOMART": 25.0, "BIGBASKET": 30.0}

    for idx, item in enumerate(payload.items):
        best_match: NormalizedMatch | None = None

        # --- Try JioMart via worker if authenticated ---
        if jiomart_auth.status == AuthStatus.AUTHENTICATED:
            try:
                audit_logger.emit(
                    "PLATFORM_SEARCH_STARTED",
                    platform="JIOMART",
                    item_id=item.id,
                )

                candidates = jiomart.search(item, ctx)

                if candidates:
                    # Pick cheapest candidate from worker
                    best_price = min(candidates, key=lambda p: p.price)

                    best_match = NormalizedMatch(
                        item_id=item.id,
                        item_name=item.itemname,
                        requested_quantity=f"{item.quantity}{item.unit}",
                        platform="JIOMART",
                        matched=best_price,
                        match_type="EXACT",
                        match_score=best_price.extraction_confidence,
                        availability=best_price.availability,
                        effective_price=best_price.price,
                    )

                    audit_logger.emit(
                        "PLATFORM_SEARCH_RESULTS",
                        platform="JIOMART",
                        item_id=item.id,
                        payload={"candidate_count": len(candidates)},
                    )

            except Exception as e:
                audit_logger.emit(
                    "PLATFORM_SEARCH_FAILED",
                    platform="JIOMART",
                    item_id=item.id,
                    payload={"error": str(e)},
                )

        # --- Fallback to mock pricing (Module 1 logic) ---
        if best_match is None:
            chosen_platform = mock_platforms[idx % len(mock_platforms)]
            mock_price = round(50 + (idx * 7.5), 2)

            pp = PlatformPrice(
                platform=chosen_platform,
                price=mock_price,
                pack_size=item.quantity,
                unit=item.unit,
                availability="IN_STOCK",
                product_url=None,
                raw_title=f"{item.brand + ' ' if item.brand else ''}{item.itemname} {item.quantity}{item.unit}",
                extraction_confidence=0.5,
            )

            best_match = NormalizedMatch(
                item_id=item.id,
                item_name=item.itemname,
                requested_quantity=f"{item.quantity}{item.unit}",
                platform=chosen_platform,
                matched=pp,
                match_type="MOCK",
                match_score=0.5,
                availability="IN_STOCK",
                effective_price=mock_price,
            )

        matches.append(best_match)

    # ---- Build split-cart plan (unchanged logic) ----
    allocations: Dict[str, List[str]] = {}
    totals: Dict[str, PlatformCartTotals] = {}

    for m in matches:
        allocations.setdefault(m.platform, []).append(m.item_id)

    for platform, item_ids in allocations.items():
        items_total = round(sum(x.effective_price for x in matches if x.platform == platform), 2)
        delivery = float(delivery_fee_map.get(platform, 0.0))
        total = round(items_total + delivery, 2)

        totals[platform] = PlatformCartTotals(
            items_total=items_total,
            delivery=delivery,
            total=total,
        )

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
        notes=["JioMart via Worker when authenticated, fallback to mock otherwise."],
    )

    result = ComparisonResult(
        item_wise_comparison=matches,
        cart_summary=cart_plan,
        best_recommendation=reco,
        total_savings_compared_to_highest_price=0.0,
        notes=["Worker-backed JioMart enabled.", "Fallback pricing used when needed."],
        confidence=0.85 if jiomart_auth.status == AuthStatus.AUTHENTICATED else 0.6,
    )

    log.info(
        "compare_completed",
        grand_total=grand_total,
        platforms=list(totals.keys()),
    )
    audit_logger.emit(
        "COMPARE_COMPLETED",
        payload={"grand_total": grand_total, "platforms": list(totals.keys())},
    )

    return result

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

from connectors.base.types import AuthStatus
from connectors.worker.models import (
    WorkerHealthResponse,
    WorkerAuthStartRequest,
    WorkerAuthStartResponse,
    WorkerAuthSubmitRequest,
    WorkerAuthSubmitResponse,
    WorkerSearchRequest,
)

app = FastAPI(title="AI Grocery Worker (Stub)")

# In-memory session store for OTP flows (stub only)
_AUTH: dict[str, dict] = {}


@app.get("/health", response_model=WorkerHealthResponse)
def health():
    return WorkerHealthResponse(status="ok", message="stub-worker")


@app.post("/auth/start", response_model=WorkerAuthStartResponse)
def auth_start(req: WorkerAuthStartRequest, x_correlation_id: Optional[str] = Header(default=None)):
    auth_session_id = f"{req.platform}-{int(time.time())}"
    _AUTH[auth_session_id] = {
        "platform": req.platform,
        "user_key": req.user_key,
        "pincode": req.pincode,
    }
    return WorkerAuthStartResponse(
        platform=req.platform,
        status=AuthStatus.OTP_REQUIRED,
        auth_session_id=auth_session_id,
        message="stub: OTP_REQUIRED",
    )


@app.post("/auth/submit", response_model=WorkerAuthSubmitResponse)
def auth_submit(req: WorkerAuthSubmitRequest, x_correlation_id: Optional[str] = Header(default=None)):
    if req.auth_session_id not in _AUTH:
        raise HTTPException(status_code=400, detail="stub: invalid auth_session_id")

    if req.otp != "1234":
        return WorkerAuthSubmitResponse(
            platform=req.platform,
            status=AuthStatus.NOT_AUTHENTICATED,
            message="stub: invalid otp",
        )

    return WorkerAuthSubmitResponse(
        platform=req.platform,
        status=AuthStatus.AUTHENTICATED,
        message="stub: authenticated",
    )


@app.post("/search")
def search(req: WorkerSearchRequest, x_correlation_id: Optional[str] = Header(default=None)):
    """
    Returns a JSON payload shaped like WorkerSearchResponse but as plain dict,
    so the worker never fails due to local schema mismatches.
    """
    name = (req.item.itemname or "").strip()
    qty = float(req.item.quantity or 1)
    base = (len(name) * 10.0) + qty

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    candidate = {
        "platform": req.platform,
        "price": round(base, 2),
        "currency": "INR",
        "pack_size": float(req.item.quantity or 1),
        "unit": req.item.unit or "",
        "availability": "IN_STOCK",
        "delivery_fee": None,
        "product_url": None,
        "raw_title": f"stub match: {(req.item.brand or '').strip()} {name} {req.item.quantity}{req.item.unit}",
        "extracted_at": now,
        "extraction_confidence": 0.7,
    }

    return {
        "platform": req.platform,
        "item_id": req.item.id,
        "candidates": [candidate],
        "warnings": ["stub worker response"],
        "raw": None,
    }

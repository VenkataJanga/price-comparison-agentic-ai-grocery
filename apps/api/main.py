from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from apps.api.middleware.correlation_id import CorrelationIdMiddleware
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.routers.auth import router as auth_router
from apps.api.routers.compare import router as compare_router
from apps.api.routers.history import router as history_router
from apps.api.routers.platforms import router as platforms_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Grocery Price Compare")

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Inline health endpoint (no missing import issues)
    @app.get("/health")
    def health():
        return JSONResponse({"status": "ok"})

    # Routers that exist in your repo
    app.include_router(auth_router)
    app.include_router(compare_router)
    app.include_router(history_router)
    app.include_router(platforms_router)

    return app


app = create_app()

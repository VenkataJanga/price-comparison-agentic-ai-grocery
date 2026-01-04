from fastapi import FastAPI
import structlog

from core.utils.logging import setup_logging
from apps.api.middleware.correlation_id import CorrelationIdMiddleware
from apps.api.routers.compare import router as compare_router
from apps.api.routers.auth import router as auth_router

setup_logging()
log = structlog.get_logger("api")

app = FastAPI(title="Grocery Price Compare API", version="0.0.1")

app.add_middleware(CorrelationIdMiddleware)

app.include_router(compare_router)
app.include_router(auth_router)


@app.get("/health")
async def health():
    log.info("health_check")
    return {"status": "ok"}

import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        clear_contextvars()

        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        bind_contextvars(correlation_id=correlation_id, path=request.url.path, method=request.method)

        logger = structlog.get_logger("api")
        logger.info("request_started")

        # Fail-open audit (never break the API)
        try:
            from observability import audit_logger
            try:
                audit_logger.emit("REQUEST_STARTED", payload={"client": request.client.host if request.client else None})
            except Exception as e:
                logger.warning("audit_emit_failed", where="REQUEST_STARTED", error=str(e))
        except Exception as e:
            logger.warning("audit_import_failed", error=str(e))

        try:
            response = await call_next(request)
            response.headers[CORRELATION_HEADER] = correlation_id
            logger.info("request_completed", status_code=response.status_code)

            try:
                from observability import audit_logger
                try:
                    audit_logger.emit("REQUEST_COMPLETED", payload={"status_code": response.status_code})
                except Exception as e:
                    logger.warning("audit_emit_failed", where="REQUEST_COMPLETED", error=str(e))
            except Exception as e:
                logger.warning("audit_import_failed", error=str(e))

            return response

        except Exception as e:
            logger.exception("request_failed")

            try:
                from observability import audit_logger
                try:
                    audit_logger.emit("REQUEST_FAILED", payload={"error": str(e)})
                except Exception as ee:
                    logger.warning("audit_emit_failed", where="REQUEST_FAILED", error=str(ee))
            except Exception as ee:
                logger.warning("audit_import_failed", error=str(ee))

            raise
        finally:
            clear_contextvars()

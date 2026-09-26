from __future__ import annotations

import logging
import time
import uuid
from collections import Counter

from fastapi import Request

logger = logging.getLogger("campuscart.api")
_metrics = Counter()


def request_metrics() -> dict[str, int]:
    return dict(_metrics)


async def observe_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _metrics["http_requests_total"] += 1
        _metrics[f"http_requests_{request.method}_5xx"] += 1
        logger.exception("Unhandled request error request_id=%s path=%s", request_id, request.url.path)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    _metrics["http_requests_total"] += 1
    _metrics[f"http_requests_{request.method}_{response.status_code // 100}xx"] += 1
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{duration_ms:.1f}"
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    return response

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.observability import request_metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    lines = [
        "# HELP campuscart_http_requests_total Total HTTP requests handled by this process",
        "# TYPE campuscart_http_requests_total counter",
    ]
    data = request_metrics()
    lines.append(f"campuscart_http_requests_total {data.get('http_requests_total', 0)}")
    for key, value in sorted(data.items()):
        if key == "http_requests_total":
            continue
        metric = key.replace("http_requests_", "campuscart_http_requests_")
        lines.append(f"{metric} {value}")
    return "\n".join(lines) + "\n"

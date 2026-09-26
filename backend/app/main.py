
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
import app.campus_models  # register campus domain/verification tables for Alembic metadata
from app.routers import health, auth, campuses, sellers, addresses, listings, offers, messages, wanted, swaps, transactions, payments, demand, recommendations, courses, course_inventory, favorites, notifications, reports, lost_found, analytics, webhooks, admin, listing_tools, metrics, uploads
from app.observability import observe_request

settings.validate()

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

if sentry_sdk and settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=float(__import__("os").getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")))


app = FastAPI(title=settings.app_name, version="3.1.0")
Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(Path(settings.media_dir))), name="uploads")

@app.middleware("http")
async def request_observer(request: Request, call_next):
    return await observe_request(request, call_next)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger = __import__("logging").getLogger("campuscart.api")
    logger.exception("Unhandled application error path=%s", request.url.path)
    detail = "Internal server error" if settings.app_env == "production" else str(exc)
    return JSONResponse(status_code=500, content={"detail": detail})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routers = [
    health.router, auth.router, campuses.router, sellers.router, addresses.router,
    listings.router, offers.router, messages.router, wanted.router, swaps.router,
    transactions.router, payments.router, demand.router, recommendations.router,
    courses.router, course_inventory.router, favorites.router, notifications.router, reports.router, lost_found.router,
    analytics.router, webhooks.router, admin.router, listing_tools.router, metrics.router, uploads.router
]
for r in routers:
    app.include_router(r)

@app.get("/")
def root():
    return {"service": settings.app_name, "version": "3.1.0", "environment": settings.app_env, "docs": "/docs", "metrics": "/metrics"}

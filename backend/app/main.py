import os
import time
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.auth_routes import auth_router, get_current_user
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Price Monitoring System",
    description="Track product prices across Grailed, Fashionphile, and 1stDibs "
                "with price history, analytics, notifications, and API-key auth.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def track_customer_usage(request: Request, call_next):
    """
    Per-customer usage tracking and rate limiting middleware.
    
    Executes for EVERY request to:
    1. Extract and validate JWT token (Bearer {token})
    2. Check daily rate limit (default: 1,000 requests/day per customer)
    3. Check monthly rate limit (default: 50,000 requests/month per customer)
    4. Log usage asynchronously to user_usage_logs table (non-blocking)
    
    Rate Limits:
    - Daily: Based on timestamp >= today at 00:00 UTC
    - Monthly: Based on timestamp >= 1st of month at 00:00 UTC
    
    Resets:
    - Daily: Automatically at midnight UTC
    - Monthly: Automatically on 1st of each month UTC
    
    Logged Details (stored in user_usage_logs):
    - user_id: Customer ID from JWT token
    - endpoint: Extracted endpoint name for analytics
    - method: HTTP method (GET, POST, PUT, DELETE, etc.)
    - path: Full URL path with query string
    - status_code: HTTP response status
    - response_time_ms: Request processing time
    - request_size_kb: Request body size (optional)
    - response_size_kb: Response body size (optional)
    - ip_address: Client IP address
    - user_agent: Client user agent string
    - query_params: URL query parameters as JSON dict
    - timestamp: Precise request completion time (UTC)
    """
    start_time = time.time()
    user_id: Optional[str] = None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.replace("Bearer ", "")
            from app.customer_auth import get_user_from_token
            from app.database import AsyncSessionLocal
            from app.models import User, UserUsageLog
            from sqlalchemy import select, func

            user_id = get_user_from_token(token)

            async with AsyncSessionLocal() as db:
                stmt = select(User).where(User.id == user_id, User.is_active == True)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    raise HTTPException(status_code=401, detail="User not found")

                # ===== DAILY RATE LIMIT CHECK =====
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                count_result = await db.execute(
                    select(func.count(UserUsageLog.id)).where(
                        UserUsageLog.user_id == user_id,
                        UserUsageLog.timestamp >= today_start,
                    )
                )
                daily_requests = count_result.scalar() or 0
                if daily_requests >= user.max_requests_per_day:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Daily limit of {user.max_requests_per_day} requests exceeded. Resets at midnight UTC.",
                    )

                # ===== MONTHLY RATE LIMIT CHECK =====
                month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                count_result = await db.execute(
                    select(func.count(UserUsageLog.id)).where(
                        UserUsageLog.user_id == user_id,
                        UserUsageLog.timestamp >= month_start,
                    )
                )
                monthly_requests = count_result.scalar() or 0
                if monthly_requests >= user.max_requests_per_month:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Monthly limit of {user.max_requests_per_month} requests exceeded. Resets on the 1st of each month UTC.",
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking rate limits: {e}")

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        # Log JWT-authenticated customer usage
        if user_id:
            asyncio.create_task(
                _log_customer_usage(user_id, request, response.status_code, process_time)
            )

        # Log API key consumer usage (separate from JWT users)
        x_api_key = request.headers.get("X-API-Key", "")
        if x_api_key and not user_id:  # avoid double-logging if both headers present
            asyncio.create_task(
                _log_api_key_request(x_api_key, request, response.status_code, process_time)
            )

        return response

    except Exception as e:
        logger.error(f"Error in request tracking middleware: {e}")
        raise


async def _log_customer_usage(
    user_id: str,
    request: Request,
    status_code: int,
    response_time_ms: float,
):
    """
    Async fire-and-forget: write one row to user_usage_logs.
    
    Per-request usage tracking for API quota enforcement and analytics.
    Captures all request/response details for customer usage analysis.
    
    Tracked fields:
    - endpoint: Extracted endpoint name (e.g., "products", "analytics")
    - method: HTTP method (GET, POST, etc.)
    - path: Full URL path (e.g., /api/products?brand=Chanel)
    - status_code: HTTP response status (200, 404, 429, etc.)
    - response_time_ms: Response latency in milliseconds
    - ip_address: Client IP address
    - user_agent: Browser/client user agent string
    - query_params: URL query parameters as JSON
    - timestamp: Request completion time (UTC)
    """
    try:
        from app.database import AsyncSessionLocal
        from app.models import UserUsageLog

        async with AsyncSessionLocal() as db:
            db.add(
                UserUsageLog(
                    user_id=user_id,
                    endpoint=request.url.path.split("/")[-1] or "root",
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    query_params=dict(request.query_params) or None,
                    timestamp=datetime.utcnow(),  # Explicit timestamp for accuracy
                )
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to log customer usage: {e}")


async def _log_api_key_request(
    api_key_value: str,
    request: Request,
    status_code: int,
    response_time_ms: float,
):
    """
    Async fire-and-forget: write one row to request_logs for API key consumers.
    Looks up the key by value to get the key ID — uses a separate session
    so it never blocks the response.
    """
    try:
        from app.database import AsyncSessionLocal
        from app.models import APIKey, RequestLog
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            stmt = select(APIKey).where(
                APIKey.key == api_key_value,
                APIKey.is_active == True,
            )
            result = await db.execute(stmt)
            api_key_obj = result.scalar_one_or_none()
            if api_key_obj:
                db.add(
                    RequestLog(
                        api_key_id=api_key_obj.id,
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        response_time_ms=response_time_ms,
                    )
                )
                await db.commit()
    except Exception as e:
        logger.error(f"Failed to log API key request: {e}")

app.include_router(auth_router)   # /api/auth/*
app.include_router(router)        # /api/*

@app.on_event("startup")
async def startup_event():
    """
    1. Create / migrate all DB tables
    2. Register notification handlers
       - EventLogNotificationHandler  → always active (guaranteed fallback)
       - WebhookNotificationHandler   → active when WEBHOOK_URLS env var is set
    """
    logger.info("=" * 60)
    logger.info("🚀 Product Price Monitoring System — starting up")
    logger.info("=" * 60)

    # --- Database ----------------------------------------------------------
    logger.info("Initialising database…")
    await init_db()
    logger.info("✓ Database ready")

    # --- Notification handlers --------------------------------------------
    from app.notifications import notification_manager, WebhookNotificationHandler

    webhook_urls_raw = os.getenv("WEBHOOK_URLS", "")
    if webhook_urls_raw.strip():
        webhook_urls = [u.strip() for u in webhook_urls_raw.split(",") if u.strip()]
        if webhook_urls:
            notification_manager.register_handler(WebhookNotificationHandler(webhook_urls))
            logger.info(f"✓ Webhook handler registered ({len(webhook_urls)} URL(s))")
        else:
            logger.info("ℹ  WEBHOOK_URLS set but empty after parsing — webhook handler skipped")
    else:
        logger.info("ℹ  WEBHOOK_URLS not configured — webhook notifications disabled")

    logger.info("✓ Notification system ready")
    logger.info("✓ API authentication enabled")
    logger.info("✓ Request logging enabled")
    logger.info("=" * 60)


@app.get("/")
async def root():
    return {
        "message": "Product Price Monitoring System API",
        "docs": "/docs",
        "version": "1.0.0",
        "authentication": "Use X-API-Key header or Bearer JWT",
        "create_key": "POST /api/api-keys",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Product Price Monitoring System",
    }

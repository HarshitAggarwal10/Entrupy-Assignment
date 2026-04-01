from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import asyncio
from datetime import datetime
from typing import Optional
from app.routes import router
from app.auth_routes import auth_router, get_current_user
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Product Price Monitoring System",
    description="Track product prices across multiple marketplaces with customer authentication",
    version="1.0.0"
)

# Add CORS middleware
# NOTE: allow_origins=["*"] is incompatible with allow_credentials=True per the CORS spec.
# Must list allowed origins explicitly when credentials are enabled.
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


# Customer request tracking middleware
@app.middleware("http")
async def track_customer_usage(request: Request, call_next):
    """
    Middleware to track customer API usage and enforce rate limits
    Logs every request to UserUsageLog table
    """
    start_time = time.time()
    user_id = None
    
    # Extract authorization token if present
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.replace("Bearer ", "")
            from app.customer_auth import get_user_from_token
            from app.database import AsyncSessionLocal
            from app.models import User, UserUsageLog
            from sqlalchemy import select, func
            
            user_id = get_user_from_token(token)
            
            # Check rate limits in background
            async with AsyncSessionLocal() as db:
                # Get user
                stmt = select(User).where(User.id == user_id, User.is_active == True)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                
                # Check daily limit
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                stmt = select(func.count(UserUsageLog.id)).where(
                    UserUsageLog.user_id == user_id,
                    UserUsageLog.timestamp >= today_start
                )
                count_result = await db.execute(stmt)
                requests_today = count_result.scalar() or 0
                
                if requests_today >= user.max_requests_per_day:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Daily limit of {user.max_requests_per_day} requests exceeded"
                    )
                
                # Check monthly limit
                month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                stmt = select(func.count(UserUsageLog.id)).where(
                    UserUsageLog.user_id == user_id,
                    UserUsageLog.timestamp >= month_start
                )
                count_result = await db.execute(stmt)
                requests_this_month = count_result.scalar() or 0
                
                if requests_this_month >= user.max_requests_per_month:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Monthly limit of {user.max_requests_per_month} requests exceeded"
                    )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking rate limits: {e}")
    
    try:
        # Process request
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log usage if authenticated customer
        if user_id:
            asyncio.create_task(
                log_customer_usage(
                    user_id,
                    request,
                    response.status_code,
                    process_time
                )
            )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in request tracking: {e}")
        raise


async def log_customer_usage(
    user_id: str,
    request: Request,
    status_code: int,
    response_time_ms: float
):
    """Log customer API usage to database"""
    try:
        from app.database import AsyncSessionLocal
        from app.models import UserUsageLog
        
        async with AsyncSessionLocal() as db:
            log_entry = UserUsageLog(
                user_id=user_id,
                endpoint=request.url.path.split('/')[-1] if request.url.path else 'root',
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                query_params=dict(request.query_params) if request.query_params else None,
            )
            db.add(log_entry)
            await db.commit()
            logger.debug(f"Logged usage for user {user_id[:8]}... - {request.method} {request.url.path}")
    
    except Exception as e:
        logger.error(f"Failed to log customer usage: {e}")


# Include routers
app.include_router(auth_router)  # Customer authentication routes
app.include_router(router)  # Product routes


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("=" * 60)
    logger.info("🚀 Product Price Monitoring System - Starting up")
    logger.info("=" * 60)
    logger.info("Initializing database...")
    await init_db()
    logger.info("✓ Database initialized successfully")
    logger.info("✓ API authentication enabled")
    logger.info("✓ Request logging enabled")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Product Price Monitoring System API",
        "docs": "/docs",
        "version": "1.0.0",
        "authentication": "Use X-API-Key header",
        "create_key": "POST /api/api-keys"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Product Price Monitoring System"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Product Price Monitoring System API"}

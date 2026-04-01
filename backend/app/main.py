from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
import time
from app.routes import router
from app.database import init_db
from app.auth import log_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Product Price Monitoring System",
    description="Track product prices across multiple marketplaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Middleware to log all API requests"""
    start_time = time.time()
    api_key_id = None
    
    # Extract API key if provided
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        from app.models import APIKey
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            stmt = select(APIKey.id).where(APIKey.key == api_key_header)
            result = await db.execute(stmt)
            key_result = result.scalar_one_or_none()
            if key_result:
                api_key_id = key_result
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log to database asynchronously
        import asyncio
        asyncio.create_task(
            log_request(request, api_key_id, response.status_code, process_time)
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise


# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Product Price Monitoring System API"}

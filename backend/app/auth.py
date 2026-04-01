"""
Authentication and request logging utilities
Manages API key validation, request logging, and usage tracking
"""

import uuid
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict
import asyncio

from app.models import APIKey, RequestLog
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# In-memory rate limiting cache (can be replaced with Redis)
request_cache = defaultdict(list)
RATE_LIMIT_REQUESTS = 1000
RATE_LIMIT_WINDOW = timedelta(hours=1)


async def validate_api_key(x_api_key: str = Header(None)) -> Optional[str]:
    """
    Validate API key from request header.
    Returns API key ID if valid, raises HTTPException if invalid.
    API key is REQUIRED for authenticated endpoints.
    """
    if not x_api_key:
        return None
    
    try:
        async with AsyncSessionLocal() as db:
            # Query for active API key
            stmt = select(APIKey).where(
                APIKey.key == x_api_key,
                APIKey.is_active == True
            )
            result = await db.execute(stmt)
            api_key_obj = result.scalar_one_or_none()
            
            if not api_key_obj:
                logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or inactive API key"
                )
            
            # Check rate limit
            await check_rate_limit(api_key_obj.id)
            
            # Update last_used timestamp
            api_key_obj.last_used = datetime.utcnow()
            db.add(api_key_obj)
            await db.commit()
            
            logger.info(f"✓ API Key validated: {api_key_obj.name}")
            return api_key_obj.id
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


async def check_rate_limit(api_key_id: str) -> bool:
    """
    Check if API key exceeds rate limit.
    Rate limit: 1000 requests per hour
    """
    now = datetime.utcnow()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    request_cache[api_key_id] = [
        ts for ts in request_cache[api_key_id] 
        if ts > window_start
    ]
    
    # Check limit
    if len(request_cache[api_key_id]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for key: {api_key_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per hour"
        )
    
    # Add current request
    request_cache[api_key_id].append(now)
    return True


async def log_request(
    request: Request,
    api_key_id: Optional[str],
    status_code: int,
    response_time_ms: float,
    error_detail: Optional[str] = None
) -> bool:
    """
    Log API request to database with full details.
    Tracks: method, path, status, response time, timestamp, API key
    """
    try:
        async with AsyncSessionLocal() as db:
            log_entry = RequestLog(
                api_key_id=api_key_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                response_time_ms=response_time_ms,
            )
            db.add(log_entry)
            await db.commit()
            
            # Log to console as well
            key_info = f"Key: {api_key_id[:8]}..." if api_key_id else "No Key"
            logger.info(
                f"[{request.method}] {request.url.path} → {status_code} "
                f"({response_time_ms:.2f}ms) | {key_info}"
            )
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to log request: {e}")
        return False


async def create_api_key(name: str, db: AsyncSession) -> Tuple[str, str]:
    """
    Create new API key for a consumer.
    Returns: (api_key_id, api_key_value)
    """
    if not name or len(name) == 0:
        raise ValueError("API key name is required")
    
    if len(name) > 100:
        raise ValueError("API key name must be less than 100 characters")
    
    try:
        # Check if name already exists
        stmt = select(APIKey).where(APIKey.name == name)
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            raise ValueError(f"API key name '{name}' already exists")
        
        key_value = str(uuid.uuid4())
        api_key = APIKey(
            key=key_value,
            name=name,
            created_at=datetime.utcnow()
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        logger.info(f"✓ Created API key: {name}")
        return api_key.id, key_value
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise


async def get_api_key_usage(api_key_id: str, db: AsyncSession) -> dict:
    """
    Get comprehensive usage statistics for an API key.
    Includes: total requests, requests by endpoint, status codes, avg response time
    """
    try:
        # Get all logs for this key
        stmt = select(RequestLog).where(
            RequestLog.api_key_id == api_key_id
        ).order_by(RequestLog.timestamp.desc())
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        if not logs:
            return {
                "total_requests": 0,
                "status_codes": {},
                "endpoints": {},
                "average_response_time_ms": 0,
                "requests": []
            }
        
        # Aggregate statistics
        status_codes = defaultdict(int)
        endpoints = defaultdict(int)
        total_response_time = 0
        
        for log in logs:
            status_codes[log.status_code] += 1
            endpoints[log.path] += 1
            total_response_time += log.response_time_ms
        
        avg_response_time = total_response_time / len(logs) if logs else 0
        
        return {
            "total_requests": len(logs),
            "status_codes": dict(status_codes),
            "endpoints": dict(endpoints),
            "average_response_time_ms": round(avg_response_time, 2),
            "requests": [
                {
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "response_time_ms": log.response_time_ms,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting API key usage: {e}")
        raise


async def revoke_api_key(api_key_id: str, db: AsyncSession) -> bool:
    """Revoke an API key (disable it)"""
    try:
        stmt = select(APIKey).where(APIKey.id == api_key_id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise ValueError("API key not found")
        
        api_key.is_active = False
        db.add(api_key)
        await db.commit()
        
        logger.info(f"✓ Revoked API key: {api_key.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise


async def get_request_logs_summary(db: AsyncSession, hours: int = 24) -> dict:
    """Get summary of all requests in past X hours"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get logs from past X hours
        stmt = select(RequestLog).where(
            RequestLog.timestamp >= cutoff_time
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        # Aggregate by status code
        status_codes = defaultdict(int)
        total_response_time = 0
        methods = defaultdict(int)
        
        for log in logs:
            status_codes[log.status_code] += 1
            methods[log.method] += 1
            total_response_time += log.response_time_ms
        
        return {
            "time_range_hours": hours,
            "total_requests": len(logs),
            "by_status_code": dict(status_codes),
            "by_method": dict(methods),
            "average_response_time_ms": round(
                total_response_time / len(logs) if logs else 0, 2
            ),
            "requests_per_hour": round(len(logs) / hours, 2) if hours > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting logs summary: {e}")
        raise

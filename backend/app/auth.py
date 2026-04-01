"""
Authentication and request logging utilities
"""

import uuid
from typing import Optional
from fastapi import HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time
import logging

from app.models import APIKey, RequestLog
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def validate_api_key(x_api_key: str = Header(None)) -> Optional[str]:
    """Validate API key from request header"""
    if not x_api_key:
        # For now, allow requests without API key for development
        return None
    
    async with AsyncSessionLocal() as db:
        stmt = select(APIKey).where(
            APIKey.key == x_api_key,
            APIKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj:
            raise HTTPException(
                status_code=401,
                detail="Invalid or inactive API key"
            )
        
        # Update last_used
        from datetime import datetime
        api_key_obj.last_used = datetime.utcnow()
        await db.commit()
        
        return api_key_obj.id


async def log_request(
    request: Request,
    api_key_id: Optional[str],
    status_code: int,
    response_time_ms: float
):
    """Log API request to database"""
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
    except Exception as e:
        logger.error(f"Failed to log request: {e}")


async def create_api_key(name: str, db: AsyncSession) -> str:
    """Create new API key"""
    key_value = str(uuid.uuid4())
    api_key = APIKey(
        key=key_value,
        name=name
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return key_value


async def get_api_key_usage(api_key_id: str, db: AsyncSession) -> dict:
    """Get usage statistics for an API key"""
    stmt = select(RequestLog).where(RequestLog.api_key_id == api_key_id)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return {
        "total_requests": len(logs),
        "requests": [
            {
                "method": log.method,
                "path": log.path,
                "status": log.status_code,
                "response_time_ms": log.response_time_ms,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }

"""
Customer authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.database import get_db
from app.models import User, UserUsageLog
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, UserUsageResponse
from app.customer_auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_user_from_token,
    decode_token
)

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


async def get_current_user(
    authorization: str = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    user_id = get_user_from_token(token)
    
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user


@auth_router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new customer account"""
    
    # Check if username exists
    stmt = select(User).where(User.username == user_data.username)
    existing_user = await db.execute(stmt)
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    stmt = select(User).where(User.email == user_data.email)
    existing_email = await db.execute(stmt)
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        last_login=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username}")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user),
        message=f"Welcome {new_user.full_name or new_user.username}! Account created successfully."
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login customer and get JWT token"""
    
    # Find user
    stmt = select(User).where(User.username == credentials.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    logger.info(f"User logged in: {user.username}")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user),
        message=f"Welcome back, {user.full_name or user.username}!"
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    user = await get_current_user(authorization, db)
    return UserResponse.from_orm(user)


@auth_router.get("/usage", response_model=UserUsageResponse)
async def get_user_usage(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get user's API usage statistics and limits"""
    user = await get_current_user(authorization, db)
    
    # Get usage stats
    stmt = select(func.count(UserUsageLog.id)).where(UserUsageLog.user_id == user.id)
    result = await db.execute(stmt)
    total_requests = result.scalar() or 0
    
    # Get today's requests (reset at midnight UTC)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.count(UserUsageLog.id)).where(
        UserUsageLog.user_id == user.id,
        UserUsageLog.timestamp >= today_start
    )
    result = await db.execute(stmt)
    requests_today = result.scalar() or 0
    
    # Get this month's requests
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.count(UserUsageLog.id)).where(
        UserUsageLog.user_id == user.id,
        UserUsageLog.timestamp >= month_start
    )
    result = await db.execute(stmt)
    requests_this_month = result.scalar() or 0
    
    # Get average response time
    stmt = select(func.avg(UserUsageLog.response_time_ms)).where(UserUsageLog.user_id == user.id)
    result = await db.execute(stmt)
    avg_response_time = result.scalar() or 0.0
    
    # Get top endpoints
    stmt = select(
        UserUsageLog.endpoint,
        func.count(UserUsageLog.id).label("count")
    ).where(UserUsageLog.user_id == user.id).group_by(UserUsageLog.endpoint).order_by(desc("count")).limit(5)
    result = await db.execute(stmt)
    top_endpoints = [{"endpoint": row[0], "requests": row[1]} for row in result.all()]
    
    # Get last request
    stmt = select(UserUsageLog).where(UserUsageLog.user_id == user.id).order_by(desc(UserUsageLog.timestamp)).limit(1)
    result = await db.execute(stmt)
    last_log = result.scalar_one_or_none()
    
    return UserUsageResponse(
        user_id=user.id,
        total_requests=total_requests,
        requests_today=requests_today,
        requests_this_month=requests_this_month,
        limit_today=user.max_requests_per_day,
        limit_this_month=user.max_requests_per_month,
        requests_remaining_today=max(0, user.max_requests_per_day - requests_today),
        requests_remaining_month=max(0, user.max_requests_per_month - requests_this_month),
        average_response_time_ms=float(avg_response_time),
        top_endpoints=top_endpoints,
        last_request_timestamp=last_log.timestamp if last_log else None
    )


@auth_router.get("/usage/history")
async def get_usage_history(
    authorization: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed usage history for user"""
    user = await get_current_user(authorization, db)
    
    # Get usage logs
    stmt = select(UserUsageLog).where(
        UserUsageLog.user_id == user.id
    ).order_by(desc(UserUsageLog.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # Get total count
    count_stmt = select(func.count(UserUsageLog.id)).where(UserUsageLog.user_id == user.id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "endpoint": log.endpoint,
                "method": log.method,
                "status": log.status_code,
                "response_time_ms": log.response_time_ms,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }


@auth_router.post("/refresh-token", response_model=dict)
async def refresh_token(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Refresh JWT token"""
    user = await get_current_user(authorization, db)
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Token refreshed successfully"
    }


@auth_router.post("/logout", response_model=dict)
async def logout(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Logout user (client should discard token)"""
    user = await get_current_user(authorization, db)
    
    logger.info(f"User logged out: {user.username}")
    
    return {"message": "Logged out successfully. Please discard your token."}

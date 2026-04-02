from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
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
    get_user_from_token
)

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token in Authorization header"""
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
    
    logger.info(f"Registration attempt for username: {user_data.username}, email: {user_data.email}")
    
    # Check if username exists
    stmt = select(User).where(User.username == user_data.username)
    existing_user = await db.execute(stmt)
    if existing_user.scalar_one_or_none():
        logger.warning(f"Registration failed: Username already exists - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    stmt = select(User).where(User.email == user_data.email)
    existing_email = await db.execute(stmt)
    if existing_email.scalar_one_or_none():
        logger.warning(f"Registration failed: Email already exists - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_pwd = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_pwd,
        last_login=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")
    
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
    
    logger.info(f"Login attempt for username: {credentials.username}")
    
    # Find user
    stmt = select(User).where(User.username == credentials.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"Login failed: User not found - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid password for user - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        logger.warning(f"Login failed: User account inactive - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    logger.info(f"User logged in successfully: {user.username}")
    
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
    user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return UserResponse.from_orm(user)


@auth_router.get("/usage", response_model=UserUsageResponse)
async def get_user_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's API usage statistics and limits"""
    
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
    user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed usage history for user"""
    
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refresh JWT token"""
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Token refreshed successfully"
    }


@auth_router.post("/logout", response_model=dict)
async def logout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user (client should discard token)"""
    
    logger.info(f"User logged out: {user.username}")
    
    return {"message": "Logged out successfully. Please discard your token."}

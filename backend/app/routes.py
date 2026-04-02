from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime
import time
import logging

from app.database import get_db
from app.models import Product, PriceHistory, NotificationEvent, RequestLog, APIKey
from app.schemas import (
    ProductResponse,
    ProductListResponse,
    ProductCreate,
    ProductUpdate,
    PriceHistoryResponse,
    AnalyticsResponse,
    DataRefreshResponse,
    NotificationEventResponse,
    ProductFilterParams,
)
from app.import_products import load_products_from_json_files, get_product_stats
from app.notifications import notification_manager
from app.auth import validate_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["products"])


@router.post("/data/refresh", response_model=DataRefreshResponse)
async def refresh_data(
    background_tasks: BackgroundTasks,
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Trigger data refresh from sample products"""
    start_time = time.time()
    
    sample_products_dir = "../sample_products"
    imported_count, updated_count, error_count = await load_products_from_json_files(
        sample_products_dir, db
    )
    
    # Get new price change events
    stmt = select(func.count(NotificationEvent.id)).where(
        NotificationEvent.is_processed == False
    )
    result = await db.execute(stmt)
    new_price_changes = result.scalar() or 0
    
    # Send notifications in background
    background_tasks.add_task(notification_manager.send_notifications, db)
    
    duration = time.time() - start_time
    
    return DataRefreshResponse(
        message="Data refresh completed",
        imported_count=imported_count,
        updated_count=updated_count,
        error_count=error_count,
        new_price_changes=new_price_changes,
        duration_seconds=duration,
    )


@router.get("/products", response_model=dict)
async def get_products(
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(price|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Get products with filtering and pagination"""
    try:
        # Build query
        query = select(Product)
        
        # Apply filters
        filters = []
        if brand:
            filters.append(Product.brand == brand)
        if category:
            filters.append(Product.category == category)
        if source:
            filters.append(Product.source == source)
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Apply sorting
        if sort_by == "price":
            query = query.order_by(Product.price.desc() if sort_order == "desc" else Product.price.asc())
        else:
            query = query.order_by(Product.created_at.desc() if sort_order == "desc" else Product.created_at.asc())
        
        # Get total count
        count_result = await db.execute(select(func.count(Product.id)).select_from(query.subquery()))
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return {
            "data": [ProductListResponse.from_orm(p).dict() for p in products],
            "total": total_count,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific product with price history"""
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.from_orm(product)


@router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_price_history(
    product_id: str,
    limit: int = Query(50, ge=1, le=100),
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Get price history for a product"""
    # Verify product exists
    product_stmt = select(Product).where(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get price history
    stmt = select(PriceHistory).where(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.recorded_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    return [PriceHistoryResponse.from_orm(h) for h in history]


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_in: ProductCreate,
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product manually (useful for testing or direct API users)"""
    import uuid
    # Check if URL already exists
    stmt = select(Product).where(Product.url == product_in.url)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this URL already exists")
    
    # Create product
    new_product = Product(
        id=str(uuid.uuid4()),
        url=product_in.url,
        name=product_in.name,
        brand=product_in.brand,
        category=product_in.category,
        source=product_in.source,
        price=product_in.price,
        size=product_in.size,
        condition=product_in.condition,
        description=product_in.description,
        main_image_url=product_in.main_image_url,
        all_images=product_in.all_images,
        product_metadata=product_in.product_metadata,
        is_sold=product_in.is_sold
    )
    db.add(new_product)
    await db.flush()
    
    # Record initial price in history
    price_history = PriceHistory(
        product_id=new_product.id,
        old_price=None,
        new_price=new_product.price,
        change_percentage=0.0,
        change_reason="manual_creation"
    )
    db.add(price_history)
    
    await db.commit()
    await db.refresh(new_product)
    
    return ProductResponse.from_orm(new_product)


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregate analytics"""
    stats = await get_product_stats(db)
    
    return AnalyticsResponse(
        total_products=stats.get("total_products", 0),
        products_by_source=stats.get("products_by_source", {}),
        products_by_brand=stats.get("products_by_brand", {}),
        products_by_category=stats.get("products_by_category", {}),
        price_statistics=stats.get("price_statistics", {}),
        average_prices_by_source=stats.get("average_prices_by_source", {}),
        average_prices_by_category=stats.get("average_prices_by_category", {}),
    )


@router.get("/notifications", response_model=dict)
async def get_notifications(
    is_processed: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    api_key_id: Optional[str] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Get notification events"""
    query = select(NotificationEvent)
    
    if is_processed is not None:
        query = query.where(NotificationEvent.is_processed == is_processed)
    
    # Get total count
    count_result = await db.execute(select(func.count(NotificationEvent.id)).select_from(query.subquery()))
    total_count = count_result.scalar() or 0
    
    # Apply sorting and pagination
    query = query.order_by(NotificationEvent.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return {
        "data": [NotificationEventResponse.from_orm(e).dict() for e in events],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.post("/notifications/process", response_model=dict)
async def process_notifications(
    db: AsyncSession = Depends(get_db)
):
    """Process and send all pending notifications"""
    try:
        # Get count before
        before_stmt = select(func.count(NotificationEvent.id)).where(
            NotificationEvent.is_processed == False
        )
        before_result = await db.execute(before_stmt)
        before_count = before_result.scalar() or 0
        
        # Send notifications
        await notification_manager.send_notifications(db)
        
        # Get count after
        after_stmt = select(func.count(NotificationEvent.id)).where(
            NotificationEvent.is_processed == False
        )
        after_result = await db.execute(after_stmt)
        after_count = after_result.scalar() or 0
        
        processed_count = before_count - after_count
        
        return {
            "message": "Notifications processed",
            "processed_count": processed_count,
            "remaining_count": after_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics"""
    stats = await get_product_stats(db)
    return stats


# API Key Management Endpoints
@router.post("/api-keys", response_model=dict)
async def create_api_key_endpoint(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key for consumer authentication"""
    if not name or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="API key name is required")
    
    if len(name) > 100:
        raise HTTPException(status_code=400, detail="API key name must be less than 100 characters")
    
    try:
        from app.auth import create_api_key
        key_id, key_value = await create_api_key(name.strip(), db)
        
        return {
            "success": True,
            "id": key_id,
            "name": name.strip(),
            "api_key": key_value,
            "message": "API key created successfully. Use this key in X-API-Key header.",
            "warning": "⚠️ Save this key securely. You won't be able to see it again.",
            "usage_example": "curl -H 'X-API-Key: {api_key}' http://localhost:8000/api/products"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/api-keys", response_model=dict)
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    """List all API keys (masking sensitive values)"""
    stmt = select(APIKey).where(APIKey.is_active == True)
    result = await db.execute(stmt)
    keys = result.scalars().all()
    
    return {
        "total": len(keys),
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "created_at": k.created_at.isoformat(),
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "key": f"{k.key[:8]}...{k.key[-4:]}"  # Masked
            }
            for k in keys
        ]
    }


@router.get("/api-keys/{key_id}/usage", response_model=dict)
async def get_api_key_usage_endpoint(
    key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for an API key"""
    from app.auth import get_api_key_usage
    
    stmt = select(APIKey).where(APIKey.id == key_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="API key not found")
    
    usage = await get_api_key_usage(key_id, db)
    return usage


@router.post("/api-keys/{key_id}/revoke", response_model=dict)
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key"""
    stmt = select(APIKey).where(APIKey.id == key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.add(api_key)
    await db.commit()
    
    return {"message": f"API key '{api_key.name}' has been revoked"}


@router.get("/request-logs", response_model=dict)
async def get_request_logs(
    api_key_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get request logs (admin endpoint)"""
    query = select(RequestLog)
    
    if api_key_id:
        query = query.where(RequestLog.api_key_id == api_key_id)
    
    # Get total count
    count_result = await db.execute(select(func.count(RequestLog.id)).select_from(query.subquery()))
    total_count = count_result.scalar() or 0
    
    # Apply sorting and pagination
    query = query.order_by(RequestLog.timestamp.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "method": log.method,
                "path": log.path,
                "status_code": log.status_code,
                "response_time_ms": log.response_time_ms,
                "timestamp": log.timestamp.isoformat(),
                "api_key_id": log.api_key_id
            }
            for log in logs
        ]
    }

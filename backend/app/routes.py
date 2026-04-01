from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime
import time

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

router = APIRouter(prefix="/api", tags=["products"])


@router.post("/data/refresh", response_model=DataRefreshResponse)
async def refresh_data(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger data refresh from sample products"""
    start_time = time.time()
    
    sample_products_dir = "sample_products"
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
    sort_by: str = Query("created_at", regex="^(price|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
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


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
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

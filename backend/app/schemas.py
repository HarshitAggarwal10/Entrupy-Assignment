from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: str
    old_price: Optional[float]
    new_price: float
    change_percentage: Optional[float]
    recorded_at: datetime
    change_reason: Optional[str]

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    url: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    source: str
    price: float
    size: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    main_image_url: Optional[str] = None
    all_images: Optional[List[Dict[str, Any]]] = None
    product_metadata: Optional[Dict[str, Any]] = None
    is_sold: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    price: Optional[float] = None
    is_sold: Optional[bool] = None
    condition: Optional[str] = None


class ProductListResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    price_history: List[PriceHistoryResponse] = []

    class Config:
        from_attributes = True


class ProductFilterParams(BaseModel):
    brand: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(price|created_at)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class AnalyticsResponse(BaseModel):
    total_products: int
    products_by_source: Dict[str, int]
    products_by_brand: Dict[str, int]
    products_by_category: Dict[str, int]
    price_statistics: Dict[str, float]
    average_prices_by_source: Dict[str, float]
    average_prices_by_category: Dict[str, float]


class NotificationEventResponse(BaseModel):
    id: str
    product_id: str
    event_type: str
    old_price: Optional[float]
    new_price: Optional[float]
    change_percentage: Optional[float]
    is_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DataRefreshResponse(BaseModel):
    message: str
    imported_count: int
    updated_count: int
    error_count: int
    new_price_changes: int
    duration_seconds: float


# Customer Authentication Schemas
class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    requests_today: int
    max_requests_per_day: int
    requests_this_month: int
    max_requests_per_month: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str
    user: UserResponse
    message: str


class UserUsageResponse(BaseModel):
    """User API usage statistics"""
    user_id: str
    total_requests: int
    requests_today: int
    requests_this_month: int
    limit_today: int
    limit_this_month: int
    requests_remaining_today: int
    requests_remaining_month: int
    average_response_time_ms: float
    top_endpoints: List[Dict[str, Any]]
    last_request_timestamp: Optional[datetime]

    class Config:
        from_attributes = True


class RequestLogDetail(BaseModel):
    """Request log entry"""
    id: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

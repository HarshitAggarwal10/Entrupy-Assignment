from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String, index=True)
    category = Column(String, index=True)
    source = Column(String, index=True, nullable=False)  # grailed, fashionphile, 1stdibs
    price = Column(Float, nullable=False)
    size = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=True)
    all_images = Column(JSON, nullable=True)
    product_metadata = Column(JSON, nullable=True)
    is_sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_source_brand_category', 'source', 'brand', 'category'),
        Index('idx_product_created', 'created_at'),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=False)
    change_percentage = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    change_reason = Column(String, nullable=True)  # e.g., "data_refresh", "import"

    # Relationships
    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index('idx_price_history_date', 'recorded_at'),
        Index('idx_price_history_product_date', 'product_id', 'recorded_at'),
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True)
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_request_log_timestamp', 'timestamp'),
        Index('idx_request_log_api_key', 'api_key_id'),
    )


class User(Base):
    """Customer user account for web authentication"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)
    
    # Rate limiting
    requests_today = Column(Integer, default=0)
    max_requests_per_day = Column(Integer, default=1000)
    requests_this_month = Column(Integer, default=0)
    max_requests_per_month = Column(Integer, default=50000)
    
    # Relationships
    usage_logs = relationship("UserUsageLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_active', 'is_active'),
    )


class UserUsageLog(Base):
    """Track API usage per customer"""
    __tablename__ = "user_usage_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_size_kb = Column(Float, nullable=True)
    response_size_kb = Column(Float, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    query_params = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    
    __table_args__ = (
        Index('idx_user_usage_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_user_usage_endpoint', 'endpoint'),
        Index('idx_user_usage_timestamp', 'timestamp'),
    )


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    event_type = Column(String, index=True)  # "price_drop", "price_increase", "new_product"
    old_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    is_processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_notification_event_status', 'is_processed'),
        Index('idx_notification_event_created', 'created_at'),
    )

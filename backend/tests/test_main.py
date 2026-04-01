import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models import Product, PriceHistory, NotificationEvent
from app.import_products import normalize_product_data, load_products_from_json_files
from app.notifications import notification_manager
from datetime import datetime


# Test database setup
@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestSessionLocal
    
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Test 1: Product normalization from different sources
@pytest.mark.asyncio
async def test_normalize_product_1stdibs():
    """Test product normalization for 1stdibs source"""
    raw_data = {
        "product_url": "https://www.1stdibs.com/product123",
        "model": "Test Model",
        "price": 100.0,
        "brand": "Test Brand",
        "size": "M",
        "full_description": "Test description",
        "main_images": [{"url": "https://example.com/image.jpg"}]
    }
    
    normalized = normalize_product_data("1stdibs", raw_data)
    
    assert normalized is not None
    assert normalized["url"] == "https://www.1stdibs.com/product123"
    assert normalized["name"] == "Test Model"
    assert normalized["price"] == 100.0
    assert normalized["brand"] == "Test Brand"
    assert normalized["source"] == "1stdibs"


# Test 2: Product normalization for fashionphile
@pytest.mark.asyncio
async def test_normalize_product_fashionphile():
    """Test product normalization for fashionphile source"""
    raw_data = {
        "product_url": "https://www.fashionphile.com/product123",
        "product_id": "fancy-id",
        "brand_id": "tiffany",
        "price": 500.0,
        "condition": "Shows Wear",
        "image_url": "https://example.com/image.jpg",
        "metadata": {"description": "Test description"}
    }
    
    normalized = normalize_product_data("fashionphile", raw_data)
    
    assert normalized is not None
    assert normalized["price"] == 500.0
    assert normalized["source"] == "fashionphile"
    assert normalized["condition"] == "Shows Wear"
    assert normalized["brand"] == "tiffany"


# Test 3: Product normalization for grailed
@pytest.mark.asyncio
async def test_normalize_product_grailed():
    """Test product normalization for grailed source"""
    raw_data = {
        "product_url": "https://www.grailed.com/listings/123",
        "model": "Washed T-Shirt",
        "brand": "Amiri",
        "price": 250.0,
        "image_url": "https://example.com/image.jpg",
        "metadata": {}
    }
    
    normalized = normalize_product_data("grailed", raw_data)
    
    assert normalized is not None
    assert normalized["source"] == "grailed"
    assert normalized["price"] == 250.0
    assert normalized["brand"] == "Amiri"


# Test 4: Health check endpoint
@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# Test 5: Get empty products list
@pytest.mark.asyncio
async def test_get_products_empty(client):
    """Test getting products when none exist"""
    response = await client.get("/api/products")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []


# Test 6: Create and retrieve product
@pytest.mark.asyncio
async def test_create_and_retrieve_product(test_db, client):
    """Test creating and retrieving a product"""
    # First, we need to add a product to the database
    async with test_db() as session:
        product = Product(
            url="https://example.com/product1",
            name="Test Product",
            brand="Test Brand",
            category="Electronics",
            source="grailed",
            price=99.99,
            description="A test product"
        )
        session.add(product)
        await session.commit()
        product_id = product.id
    
    # Now retrieve it via API
    response = await client.get(f"/api/products/{product_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 99.99
    assert data["brand"] == "Test Brand"


# Test 7: Filter products by price range
@pytest.mark.asyncio
async def test_filter_products_by_price(test_db, client):
    """Test filtering products by price range"""
    # Add test products
    async with test_db() as session:
        products_data = [
            {"url": "https://example.com/p1", "name": "Cheap Product", "price": 10.0},
            {"url": "https://example.com/p2", "name": "Medium Product", "price": 50.0},
            {"url": "https://example.com/p3", "name": "Expensive Product", "price": 200.0},
        ]
        
        for data in products_data:
            product = Product(
                url=data["url"],
                name=data["name"],
                source="test",
                price=data["price"]
            )
            session.add(product)
        await session.commit()
    
    # Test filter
    response = await client.get("/api/products?min_price=30&max_price=100")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["name"] == "Medium Product"


# Test 8: Price history tracking
@pytest.mark.asyncio
async def test_price_history_tracking(test_db):
    """Test price history tracking for products"""
    async with test_db() as session:
        # Create a product
        product = Product(
            url="https://example.com/product",
            name="Test Product",
            source="test",
            price=100.0
        )
        session.add(product)
        await session.flush()
        
        # Add price history entries
        history1 = PriceHistory(
            product_id=product.id,
            old_price=None,
            new_price=100.0,
            change_reason="initial_import"
        )
        history2 = PriceHistory(
            product_id=product.id,
            old_price=100.0,
            new_price=85.0,
            change_percentage=-15.0,
            change_reason="price_drop"
        )
        session.add(history1)
        session.add(history2)
        await session.commit()
        
        # Verify price history
        from sqlalchemy import select
        history_stmt = select(PriceHistory).where(PriceHistory.product_id == product.id)
        result = await session.execute(history_stmt)
        histories = result.scalars().all()
        
        assert len(histories) == 2
        assert histories[1].new_price == 85.0
        assert histories[1].change_percentage == -15.0


# Test 9: Analytics endpoint
@pytest.mark.asyncio
async def test_analytics_endpoint(test_db, client):
    """Test analytics endpoint"""
    # Add test products
    async with test_db() as session:
        for i in range(3):
            product = Product(
                url=f"https://example.com/p{i}",
                name=f"Product {i}",
                brand="Brand A" if i < 2 else "Brand B",
                category="Category 1",
                source="grailed" if i < 2 else "fashionphile",
                price=50.0 + (i * 10)
            )
            session.add(product)
        await session.commit()
    
    # Test analytics
    response = await client.get("/api/analytics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] == 3
    assert "products_by_source" in data
    assert "price_statistics" in data


# Test 10: Notification events (Bonus test)
@pytest.mark.asyncio
async def test_notification_events(test_db):
    """Test notification event creation"""
    async with test_db() as session:
        # Create a product
        product = Product(
            url="https://example.com/product",
            name="Test Product",
            source="test",
            price=100.0
        )
        session.add(product)
        await session.flush()
        
        # Create a notification event
        event = NotificationEvent(
            product_id=product.id,
            event_type="price_drop",
            old_price=100.0,
            new_price=80.0,
            change_percentage=-20.0
        )
        session.add(event)
        await session.commit()
        
        # Verify event
        from sqlalchemy import select
        event_stmt = select(NotificationEvent).where(NotificationEvent.product_id == product.id)
        result = await session.execute(event_stmt)
        retrieved_event = result.scalar_one()
        
        assert retrieved_event.event_type == "price_drop"
        assert retrieved_event.change_percentage == -20.0
        assert retrieved_event.is_processed == False

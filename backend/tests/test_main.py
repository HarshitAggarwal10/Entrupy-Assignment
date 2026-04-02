import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base, Product, PriceHistory, NotificationEvent, NotificationDeliveryLog
from app.import_products import normalize_product_data
from app.notifications import NotificationManager
from datetime import datetime


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_db():
    """Isolated in-memory SQLite DB per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestSessionLocal
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """HTTPX async test client wired to in-memory DB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Test 1: Normalize 1stdibs
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_normalize_product_1stdibs():
    """Product normalization extracts all fields for 1stdibs source."""
    raw = {
        "product_url": "https://www.1stdibs.com/product123",
        "model": "Chanel Flap Bag",
        "price": 4500.0,
        "brand": "Chanel",
        "size": "Medium",
        "full_description": "Authentic Chanel bag",
        "main_images": [{"url": "https://example.com/img.jpg"}],
    }
    normalized = normalize_product_data("1stdibs", raw)

    assert normalized is not None
    assert normalized["url"] == "https://www.1stdibs.com/product123"
    assert normalized["name"] == "Chanel Flap Bag"
    assert normalized["price"] == 4500.0
    assert normalized["brand"] == "Chanel"
    assert normalized["source"] == "1stdibs"
    assert normalized["main_image_url"] == "https://example.com/img.jpg"


# ---------------------------------------------------------------------------
# Test 2: Normalize fashionphile
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_normalize_product_fashionphile():
    """Product normalization extracts condition and brand for fashionphile."""
    raw = {
        "product_url": "https://www.fashionphile.com/product123",
        "product_id": "fph-123",
        "brand_id": "louis-vuitton",
        "price": 1200.0,
        "condition": "Excellent",
        "image_url": "https://example.com/img.jpg",
        "metadata": {"description": "LV Neverfull MM"},
    }
    normalized = normalize_product_data("fashionphile", raw)

    assert normalized is not None
    assert normalized["price"] == 1200.0
    assert normalized["source"] == "fashionphile"
    assert normalized["condition"] == "Excellent"
    assert normalized["brand"] == "louis-vuitton"


# ---------------------------------------------------------------------------
# Test 3: Normalize grailed
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_normalize_product_grailed():
    """Product normalization works for grailed source."""
    raw = {
        "product_url": "https://www.grailed.com/listings/123",
        "model": "Washed Tee",
        "brand": "Amiri",
        "price": 350.0,
        "image_url": "https://example.com/img.jpg",
        "metadata": {"condition": "Used"},
    }
    normalized = normalize_product_data("grailed", raw)

    assert normalized is not None
    assert normalized["source"] == "grailed"
    assert normalized["price"] == 350.0
    assert normalized["brand"] == "Amiri"


# ---------------------------------------------------------------------------
# Test 4: Normalize — missing price returns None gracefully
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_normalize_missing_price_returns_none():
    """normalize_product_data returns None when price is absent (bad input)."""
    raw = {"product_url": "https://www.grailed.com/listings/999", "model": "No Price Item"}
    assert normalize_product_data("grailed", raw) is None


# ---------------------------------------------------------------------------
# Test 5: Health check
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# Test 6: Products list — empty DB
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_products_empty(client):
    """Product list endpoint returns empty result on fresh DB."""
    response = await client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []


# ---------------------------------------------------------------------------
# Test 7: Create product, retrieve by ID
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_and_retrieve_product(test_db, client):
    """Product created in DB is retrievable via GET /api/products/{id}."""
    async with test_db() as session:
        product = Product(
            url="https://example.com/bag-001",
            name="Hermès Birkin 30",
            brand="Hermès",
            category="Bags",
            source="1stdibs",
            price=18000.0,
        )
        session.add(product)
        await session.commit()
        product_id = product.id

    response = await client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hermès Birkin 30"
    assert data["price"] == 18000.0
    assert data["brand"] == "Hermès"


# ---------------------------------------------------------------------------
# Test 8: Filter products by price range
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_filter_products_by_price(test_db, client):
    """Price range filter returns only matching products."""
    async with test_db() as session:
        for url, name, price in [
            ("https://ex.com/p1", "Budget Tee", 20.0),
            ("https://ex.com/p2", "Mid Jacket", 300.0),
            ("https://ex.com/p3", "Luxury Watch", 5000.0),
        ]:
            session.add(Product(url=url, name=name, source="grailed", price=price))
        await session.commit()

    response = await client.get("/api/products?min_price=100&max_price=999")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["name"] == "Mid Jacket"


# ---------------------------------------------------------------------------
# Test 9: Price history tracking
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_price_history_tracking(test_db):
    """PriceHistory rows are written and retrievable for a product."""
    from sqlalchemy import select

    async with test_db() as session:
        product = Product(
            url="https://ex.com/watch-001",
            name="Rolex Submariner",
            source="fashionphile",
            price=12000.0,
        )
        session.add(product)
        await session.flush()

        session.add(PriceHistory(product_id=product.id, old_price=None, new_price=12000.0, change_reason="initial_import"))
        session.add(PriceHistory(product_id=product.id, old_price=12000.0, new_price=10500.0, change_percentage=-12.5, change_reason="price_drop"))
        await session.commit()

        result = await session.execute(select(PriceHistory).where(PriceHistory.product_id == product.id))
        rows = result.scalars().all()

    assert len(rows) == 2
    drop = next(r for r in rows if r.change_percentage is not None)
    assert drop.new_price == 10500.0
    assert drop.change_percentage == -12.5


# ---------------------------------------------------------------------------
# Test 10: Analytics endpoint
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics_endpoint(test_db, client):
    """Analytics endpoint aggregates totals by source correctly."""
    async with test_db() as session:
        session.add(Product(url="https://ex.com/a1", name="A1", brand="BrandA", category="Bags", source="grailed", price=100.0))
        session.add(Product(url="https://ex.com/a2", name="A2", brand="BrandA", category="Bags", source="grailed", price=200.0))
        session.add(Product(url="https://ex.com/a3", name="A3", brand="BrandB", category="Watches", source="1stdibs", price=500.0))
        await session.commit()

    response = await client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] == 3
    assert data["products_by_source"]["grailed"] == 2
    assert data["products_by_source"]["1stdibs"] == 1
    assert "price_statistics" in data
    assert "average_prices_by_category" in data


# ---------------------------------------------------------------------------
# Test 11: Notification event created on price change
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notification_event_created(test_db):
    """NotificationEvent row is written and starts as unprocessed."""
    from sqlalchemy import select

    async with test_db() as session:
        product = Product(url="https://ex.com/n1", name="Test Bag", source="grailed", price=500.0)
        session.add(product)
        await session.flush()

        event = NotificationEvent(
            product_id=product.id,
            event_type="price_drop",
            old_price=500.0,
            new_price=400.0,
            change_percentage=-20.0,
        )
        session.add(event)
        await session.commit()

        result = await session.execute(select(NotificationEvent).where(NotificationEvent.product_id == product.id))
        retrieved = result.scalar_one()

    assert retrieved.event_type == "price_drop"
    assert retrieved.change_percentage == -20.0
    assert retrieved.is_processed is False


# ---------------------------------------------------------------------------
# Test 12: Notification retry — delivery log persisted, event stays unprocessed
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notification_retry_and_delivery_log(test_db):
    """
    When a handler fails all retries:
    - NotificationDeliveryLog rows are written for every attempt
    - The event stays unprocessed (is_processed stays False)
    """
    from sqlalchemy import select
    import app.notifications as notif_module

    # Speed up retries for test
    original_delays = notif_module.RETRY_DELAYS
    notif_module.RETRY_DELAYS = [0, 0, 0]

    class AlwaysFailHandler:
        async def __call__(self, payload):
            raise RuntimeError("Simulated failure")

    async with test_db() as session:
        product = Product(url="https://ex.com/retry1", name="Retry Test", source="grailed", price=200.0)
        session.add(product)
        await session.flush()

        event = NotificationEvent(
            product_id=product.id,
            event_type="price_drop",
            old_price=200.0,
            new_price=150.0,
            change_percentage=-25.0,
        )
        session.add(event)
        await session.commit()

        mgr = NotificationManager()
        mgr.register_handler(AlwaysFailHandler())
        await mgr.send_notifications(session)

        await session.refresh(event)
        logs_result = await session.execute(
            select(NotificationDeliveryLog).where(NotificationDeliveryLog.event_id == event.id)
        )
        logs = logs_result.scalars().all()

    notif_module.RETRY_DELAYS = original_delays

    assert event.is_processed is False, "Event must stay unprocessed when handler fails"
    assert len(logs) == 3, f"Expected 3 delivery log rows (one per retry), got {len(logs)}"
    assert all(not log.success for log in logs), "All attempts should be marked as failures"


# ---------------------------------------------------------------------------
# Test 13: Product not found returns 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_product_not_found(client):
    """Invalid product ID returns 404 with proper error message."""
    response = await client.get("/api/products/nonexistent-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

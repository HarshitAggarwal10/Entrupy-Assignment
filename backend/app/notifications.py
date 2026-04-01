import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import NotificationEvent, Product

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages price change notifications"""

    def __init__(self):
        self.handlers: List[callable] = []

    def register_handler(self, handler: callable):
        """Register a notification handler"""
        self.handlers.append(handler)
        handler_name = handler.__class__.__name__ if hasattr(handler, '__class__') else str(handler)
        logger.info(f"Registered notification handler: {handler_name}")

    async def send_notifications(self, db: AsyncSession):
        """Send all unprocessed notifications"""
        try:
            # Get unprocessed events
            stmt = select(NotificationEvent).where(
                NotificationEvent.is_processed == False
            ).order_by(NotificationEvent.created_at)
            result = await db.execute(stmt)
            events = result.scalars().all()

            logger.info(f"Found {len(events)} unprocessed notification events")

            for event in events:
                # Get product details
                product_stmt = select(Product).where(Product.id == event.product_id)
                product_result = await db.execute(product_stmt)
                product = product_result.scalar_one_or_none()

                if not product:
                    continue

                # Build notification payload
                payload = {
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_brand": product.brand,
                    "product_source": product.source,
                    "old_price": event.old_price,
                    "new_price": event.new_price,
                    "change_percentage": event.change_percentage,
                    "product_url": product.url,
                    "created_at": event.created_at.isoformat(),
                }

                # Send through all registered handlers
                for handler in self.handlers:
                    try:
                        await handler(payload)
                    except Exception as e:
                        logger.error(f"Error in notification handler {handler.__name__}: {e}")

                # Mark as processed
                event.is_processed = True
                event.processed_at = datetime.utcnow()

            await db.commit()
            logger.info(f"Processed {len(events)} notification events")
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            await db.rollback()


class EventLogNotificationHandler:
    """Logs notifications to event log"""

    async def __call__(self, payload: Dict[str, Any]):
        """Handle notification by logging to event log"""
        logger.info(f"Price Change Event: {payload['event_type']} - {payload['product_name']} "
                   f"[{payload['old_price']} → {payload['new_price']}] "
                   f"({payload['change_percentage']:.2f}%)")
        # In a real system, this would write to a persistent event log


class WebhookNotificationHandler:
    """Sends notifications via webhooks"""

    def __init__(self, webhook_urls: List[str]):
        self.webhook_urls = webhook_urls

    async def __call__(self, payload: Dict[str, Any]):
        """Handle notification by sending to webhooks"""
        import aiohttp
        payload_json = json.dumps(payload)
        
        async with aiohttp.ClientSession() as session:
            for url in self.webhook_urls:
                try:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status != 200:
                            logger.warning(f"Webhook request failed: {url} - Status: {resp.status}")
                        else:
                            logger.info(f"Webhook sent to {url}")
                except Exception as e:
                    logger.error(f"Error sending webhook to {url}: {e}")


class QueueNotificationHandler:
    """Sends notifications to a queue (e.g., RabbitMQ, Redis)"""

    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.queue = []  # In-memory queue for demo

    async def __call__(self, payload: Dict[str, Any]):
        """Add notification to queue"""
        self.queue.append(payload)
        logger.info(f"Notification queued: {payload['event_type']} - Queue size: {len(self.queue)}")

    def get_queued_notifications(self) -> List[Dict[str, Any]]:
        """Get and clear queued notifications"""
        result = self.queue.copy()
        self.queue.clear()
        return result


# Global notification manager instance
notification_manager = NotificationManager()

# Register event log handler by default
notification_manager.register_handler(EventLogNotificationHandler())

# Queue handler for demo
queue_handler = QueueNotificationHandler("price_changes")
notification_manager.register_handler(queue_handler)

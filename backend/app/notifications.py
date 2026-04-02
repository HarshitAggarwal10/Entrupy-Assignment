"""
Notification system for price change events.

Design:
- NotificationEvent rows are written to DB *before* dispatch (don't lose events)
- Delivery runs in background tasks (don't block the fetch process)
- Each handler runs with exponential-backoff retry (handle delivery failures)
- Events are only marked is_processed=True when ALL handlers succeed
- Every attempt (success or failure) is persisted to NotificationDeliveryLog (DB-backed audit trail)
- Webhook handler raises on failure so the retry mechanism can intervene
"""

import logging
import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import NotificationEvent, NotificationDeliveryLog, Product

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds — exponential backoff


class NotificationManager:
    """
    Central dispatcher for price-change notification events.

    Guarantees:
    1. Events persisted to DB before dispatch → no event loss on crash
    2. Background execution → never blocks the HTTP response
    3. Per-handler retry with backoff → handles transient delivery failures
    4. Event only marked processed when all handlers succeed → safe for retry
    5. Every attempt logged to notification_delivery_logs table → DB-backed audit trail
    """

    def __init__(self):
        self.handlers: List[callable] = []

    def register_handler(self, handler: callable):
        """Register a notification handler."""
        self.handlers.append(handler)
        handler_name = handler.__class__.__name__
        logger.info(f"Registered notification handler: {handler_name}")

    async def send_notifications(self, db: AsyncSession):
        """
        Dispatch all unprocessed notification events through registered handlers.

        Only marks an event as processed when ALL handlers succeed (after retries).
        Failed events remain unprocessed and will be retried on the next refresh.
        """
        try:
            stmt = (
                select(NotificationEvent)
                .where(NotificationEvent.is_processed == False)
                .order_by(NotificationEvent.created_at)
            )
            result = await db.execute(stmt)
            events = result.scalars().all()

            logger.info(f"Processing {len(events)} unprocessed notification events")

            for event in events:
                # Fetch product details for the payload
                product_stmt = select(Product).where(Product.id == event.product_id)
                product_result = await db.execute(product_stmt)
                product = product_result.scalar_one_or_none()

                if not product:
                    # Product was deleted — mark as processed to prevent infinite retry loop
                    event.is_processed = True
                    event.processed_at = datetime.utcnow()
                    logger.warning(f"Event {event.id[:8]}... has no product (deleted?); skipping.")
                    continue

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

                # Run every handler; collect results
                all_succeeded = True
                for handler in self.handlers:
                    success = await self._run_with_retry(handler, payload, event.id, db)
                    if not success:
                        all_succeeded = False
                        logger.warning(
                            f"Handler {handler.__class__.__name__} failed all retries "
                            f"for event {event.id[:8]}... — event stays unprocessed."
                        )

                # Only promote to processed when every handler delivered successfully
                if all_succeeded:
                    event.is_processed = True
                    event.processed_at = datetime.utcnow()
                    logger.info(f"Event {event.id[:8]}... fully delivered and marked processed.")

            await db.commit()
            logger.info("Notification dispatch complete.")

        except Exception as e:
            logger.error(f"Error in send_notifications: {e}")
            await db.rollback()

    async def _run_with_retry(
        self,
        handler: callable,
        payload: Dict[str, Any],
        event_id: str,
        db: AsyncSession,
    ) -> bool:
        """
        Run one handler with exponential-backoff retry.
        Logs every attempt (success or failure) to notification_delivery_logs.
        Returns True on success, False when all retries are exhausted.
        """
        handler_name = handler.__class__.__name__

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await handler(payload)
                await self._persist_delivery_log(db, event_id, handler_name, attempt, True, None)
                logger.info(f"[{handler_name}] delivered on attempt {attempt}")
                return True

            except Exception as exc:
                error_msg = str(exc)
                await self._persist_delivery_log(db, event_id, handler_name, attempt, False, error_msg)
                logger.warning(f"[{handler_name}] attempt {attempt}/{MAX_RETRIES} failed: {error_msg}")

                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[attempt - 1]
                    logger.info(f"[{handler_name}] retrying in {delay}s…")
                    await asyncio.sleep(delay)

        logger.error(f"[{handler_name}] exhausted {MAX_RETRIES} retries for event {event_id[:8]}...")
        return False

    @staticmethod
    async def _persist_delivery_log(
        db: AsyncSession,
        event_id: str,
        handler_name: str,
        attempt: int,
        success: bool,
        error_message: Optional[str],
    ):
        """Write a delivery attempt row to notification_delivery_logs (DB-backed, survives restarts)."""
        try:
            log = NotificationDeliveryLog(
                event_id=event_id,
                handler_name=handler_name,
                attempt_number=attempt,
                success=success,
                error_message=error_message[:500] if error_message else None,
            )
            db.add(log)
            # Not committing here — the caller's commit covers this too
        except Exception as e:
            logger.error(f"Failed to persist delivery log: {e}")


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------

class EventLogNotificationHandler:
    """
    Writes a structured log line for every price-change event.
    This always succeeds (no network I/O) and acts as the guaranteed fallback.
    """

    async def __call__(self, payload: Dict[str, Any]):
        pct = payload.get("change_percentage") or 0
        direction = "↓" if pct < 0 else "↑"
        logger.info(
            f"[PRICE {payload['event_type'].upper()}] "
            f"{payload['product_name'][:60]} | "
            f"Source: {payload['product_source']} | "
            f"${payload['old_price']} → ${payload['new_price']} "
            f"({direction}{abs(pct):.2f}%) | "
            f"event_id={payload['event_id'][:8]}..."
        )


class WebhookNotificationHandler:
    """
    Delivers price-change notifications via HTTP POST to configured webhook URLs.

    - Raises an exception if ANY URL fails so that NotificationManager can retry.
    - Uses a 10-second timeout per request to avoid hanging.
    - Webhook URLs are read from WEBHOOK_URLS env var (comma-separated).
    """

    def __init__(self, webhook_urls: List[str]):
        self.webhook_urls = [url.strip() for url in webhook_urls if url.strip()]
        logger.info(
            f"WebhookNotificationHandler ready with {len(self.webhook_urls)} URL(s): "
            f"{self.webhook_urls}"
        )

    async def __call__(self, payload: Dict[str, Any]):
        """POST payload to every configured webhook URL. Raises if any delivery fails."""
        if not self.webhook_urls:
            return  # Nothing to do; not an error

        import aiohttp

        failed: List[str] = []

        async with aiohttp.ClientSession() as session:
            for url in self.webhook_urls:
                try:
                    async with session.post(
                        url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status >= 400:
                            failed.append(f"{url} (HTTP {resp.status})")
                            logger.warning(f"Webhook {url} returned HTTP {resp.status}")
                        else:
                            logger.info(f"Webhook delivered → {url} ({resp.status})")
                except aiohttp.ClientError as exc:
                    failed.append(f"{url} ({type(exc).__name__}: {exc})")
                except asyncio.TimeoutError:
                    failed.append(f"{url} (timeout after 10s)")

        if failed:
            # Raising causes NotificationManager to retry and log the failure
            raise RuntimeError(f"Webhook delivery failed for: {'; '.join(failed)}")


# ---------------------------------------------------------------------------
# Module-level singleton — configured at startup via main.py
# ---------------------------------------------------------------------------

# Global notification manager instance
notification_manager = NotificationManager()

# EventLogNotificationHandler is always registered as the guaranteed fallback
notification_manager.register_handler(EventLogNotificationHandler())

# WebhookNotificationHandler is registered at startup by main.py if WEBHOOK_URLS is set
# (see startup_event in main.py)

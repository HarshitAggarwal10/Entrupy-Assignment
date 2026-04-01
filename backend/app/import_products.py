import json
import os
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Product, PriceHistory, NotificationEvent

logger = logging.getLogger(__name__)


def extract_category_from_filename(filename: str) -> str:
    """Extract category from filename like 'grailed_amiri_apparel_01.json'"""
    parts = filename.replace('.json', '').split('_')
    if len(parts) >= 2:
        # Get everything after source and index
        category = '_'.join(parts[1:-1])
        return category.replace('_', ' ').title()
    return "Unknown"


def extract_source_from_filename(filename: str) -> str:
    """Extract source from filename"""
    source = filename.split('_')[0]
    return source.lower()


def normalize_product_data(source: str, raw_data: dict) -> Optional[dict]:
    """Normalize product data from different sources to a common format"""
    try:
        # Common fields
        url = raw_data.get("product_url", "")
        price = raw_data.get("price", 0)
        
        if not url or not price:
            return None

        # Source-specific extraction
        if source == "1stdibs":
            return {
                "url": url,
                "name": raw_data.get("model", ""),
                "brand": raw_data.get("brand", ""),
                "source": source,
                "price": float(price),
                "size": raw_data.get("size"),
                "condition": None,
                "description": raw_data.get("full_description", ""),
                "main_image_url": raw_data.get("main_images", [{}])[0].get("url") if raw_data.get("main_images") else None,
                "all_images": raw_data.get("main_images"),
                "product_metadata": raw_data.get("metadata"),
            }
        
        elif source == "fashionphile":
            return {
                "url": url,
                "name": raw_data.get("product_id", ""),
                "brand": raw_data.get("brand_id", ""),
                "source": source,
                "price": float(price),
                "size": raw_data.get("size"),
                "condition": raw_data.get("condition"),
                "description": raw_data.get("metadata", {}).get("description", ""),
                "main_image_url": raw_data.get("image_url"),
                "all_images": raw_data.get("main_images"),
                "product_metadata": raw_data.get("metadata"),
            }
        
        elif source == "grailed":
            return {
                "url": url,
                "name": raw_data.get("model", ""),
                "brand": raw_data.get("brand", ""),
                "source": source,
                "price": float(price),
                "size": raw_data.get("size"),
                "condition": raw_data.get("metadata", {}).get("condition"),
                "description": raw_data.get("metadata", {}).get("full_product_description", ""),
                "main_image_url": raw_data.get("image_url"),
                "all_images": raw_data.get("main_images"),
                "product_metadata": raw_data.get("metadata"),
            }
        
        return None
    except Exception as e:
        logger.error(f"Error normalizing product data: {e}")
        return None


async def load_products_from_json_files(
    sample_products_dir: str,
    db: AsyncSession,
    category: Optional[str] = None
) -> Tuple[int, int, int]:
    """
    Load products from JSON files in the sample_products directory.
    Returns (imported_count, updated_count, error_count)
    """
    imported_count = 0
    updated_count = 0
    error_count = 0
    
    sample_path = Path(sample_products_dir)
    if not sample_path.exists():
        logger.error(f"Sample products directory not found: {sample_products_dir}")
        return 0, 0, 1

    # Find all JSON files
    json_files = list(sample_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to process")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Extract source and category from filename
            source = extract_source_from_filename(json_file.name)
            file_category = extract_category_from_filename(json_file.name)

            # Normalize data
            normalized_data = normalize_product_data(source, raw_data)
            if not normalized_data:
                error_count += 1
                continue

            # Set category from file if not extracted
            normalized_data["category"] = category or file_category

            # Check if product already exists
            stmt = select(Product).where(Product.url == normalized_data["url"])
            result = await db.execute(stmt)
            existing_product = result.scalar_one_or_none()

            if existing_product:
                # Update existing product
                old_price = existing_product.price
                new_price = normalized_data["price"]
                
                # Update product
                for key, value in normalized_data.items():
                    setattr(existing_product, key, value)
                existing_product.updated_at = datetime.utcnow()

                # Record price change if price differs
                if old_price != new_price:
                    change_percentage = ((new_price - old_price) / old_price * 100) if old_price != 0 else 0
                    
                    price_history = PriceHistory(
                        product_id=existing_product.id,
                        old_price=old_price,
                        new_price=new_price,
                        change_percentage=change_percentage,
                        change_reason="data_refresh"
                    )
                    db.add(price_history)
                    
                    # Create notification event
                    event_type = "price_drop" if new_price < old_price else "price_increase"
                    notification = NotificationEvent(
                        product_id=existing_product.id,
                        event_type=event_type,
                        old_price=old_price,
                        new_price=new_price,
                        change_percentage=change_percentage
                    )
                    db.add(notification)

                updated_count += 1
            else:
                # Create new product
                new_product = Product(**normalized_data)
                db.add(new_product)
                await db.flush()  # Flush to get the ID
                
                # Record initial price
                price_history = PriceHistory(
                    product_id=new_product.id,
                    old_price=None,
                    new_price=new_product.price,
                    change_reason="initial_import"
                )
                db.add(price_history)
                
                imported_count += 1

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {json_file.name}: {e}")
            error_count += 1
        except Exception as e:
            logger.error(f"Error processing {json_file.name}: {e}")
            error_count += 1

    # Commit all changes
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Error committing products: {e}")
        await db.rollback()
        error_count += 1

    logger.info(f"Import complete - Imported: {imported_count}, Updated: {updated_count}, Errors: {error_count}")
    return imported_count, updated_count, error_count


async def get_product_stats(db: AsyncSession) -> dict:
    """Get product statistics"""
    try:
        # Total products
        total_stmt = select(func.count(Product.id))
        total_result = await db.execute(total_stmt)
        total_products = total_result.scalar() or 0

        # Products by source
        source_stmt = select(Product.source, func.count(Product.id)).group_by(Product.source)
        source_result = await db.execute(source_stmt)
        products_by_source = dict(source_result.all())

        # Products by brand
        brand_stmt = select(Product.brand, func.count(Product.id)).where(Product.brand != None).group_by(Product.brand)
        brand_result = await db.execute(brand_stmt)
        products_by_brand = dict(brand_result.all())

        # Products by category
        category_stmt = select(Product.category, func.count(Product.id)).where(Product.category != None).group_by(Product.category)
        category_result = await db.execute(category_stmt)
        products_by_category = dict(category_result.all())

        # Price statistics
        price_stats_stmt = select(
            func.min(Product.price).label("min_price"),
            func.max(Product.price).label("max_price"),
            func.avg(Product.price).label("avg_price"),
        )
        price_stats_result = await db.execute(price_stats_stmt)
        price_row = price_stats_result.one()
        price_statistics = {
            "min_price": float(price_row.min_price or 0),
            "max_price": float(price_row.max_price or 0),
            "avg_price": float(price_row.avg_price or 0),
        }

        # Average prices by source
        avg_source_stmt = select(Product.source, func.avg(Product.price).label("avg_price")).group_by(Product.source)
        avg_source_result = await db.execute(avg_source_stmt)
        average_prices_by_source = {source: float(price) for source, price in avg_source_result.all()}

        # Average prices by category
        avg_category_stmt = select(Product.category, func.avg(Product.price).label("avg_price")).where(Product.category != None).group_by(Product.category)
        avg_category_result = await db.execute(avg_category_stmt)
        average_prices_by_category = {category: float(price) for category, price in avg_category_result.all()}

        return {
            "total_products": total_products,
            "products_by_source": products_by_source,
            "products_by_brand": products_by_brand,
            "products_by_category": products_by_category,
            "price_statistics": price_statistics,
            "average_prices_by_source": average_prices_by_source,
            "average_prices_by_category": average_prices_by_category,
        }
    except Exception as e:
        logger.error(f"Error getting product stats: {e}")
        return {}

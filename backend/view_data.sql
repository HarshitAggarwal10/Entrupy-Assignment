-- View PostgreSQL Database Data
-- Run this in psql terminal: psql -U postgres -d entrupy_products -f view_data.sql

-- 1. Total Products Count
SELECT COUNT(*) as "Total Products" FROM products;

-- 2. Products by Source
SELECT source, COUNT(*) as count FROM products GROUP BY source ORDER BY source;

-- 3. Sample Products (First 5)
SELECT id, title, brand, price, source FROM products LIMIT 5;

-- 4. Price Statistics
SELECT 
    MIN(price) as "Min Price",
    MAX(price) as "Max Price",
    AVG(price) as "Avg Price"
FROM products;

-- 5. Products by Category
SELECT category, COUNT(*) as count FROM products WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC LIMIT 10;

-- 6. All Products (Full List)
SELECT id, title, brand, category, price, source, created_at FROM products ORDER BY source, created_at DESC;

-- 7. Price History Data
SELECT COUNT(*) as "Total Price History Records" FROM price_history;

-- 8. Notification Events
SELECT COUNT(*) as "Total Notifications" FROM notification_events;

#!/usr/bin/env python3
"""
PostgreSQL Setup Script
Sets up database and initializes schema
"""

import asyncio
import os
from getpass import getpass
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def setup_database():
    """Create PostgreSQL database and user if needed"""
    
    print("=" * 60)
    print("PostgreSQL Setup for Entrupy Assignment")
    print("=" * 60)
    
    # Get credentials
    postgres_user = input("PostgreSQL username (default: postgres): ").strip() or "postgres"
    postgres_password = getpass(f"PostgreSQL password for {postgres_user}: ")
    postgres_host = input("PostgreSQL host (default: localhost): ").strip() or "localhost"
    postgres_port = input("PostgreSQL port (default: 5432): ").strip() or "5432"
    
    try:
        # Connect to default postgres database
        print(f"\n✓ Connecting to PostgreSQL at {postgres_host}:{postgres_port}...")
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if not exists
        print("✓ Creating database 'entrupy_products'...")
        try:
            cursor.execute("CREATE DATABASE entrupy_products;")
            print("  ✓ Database created successfully")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("  ℹ Database already exists, continuing...")
            else:
                raise
        
        cursor.close()
        conn.close()
        
        # Now connect to the new database and create tables
        print(f"\n✓ Connecting to entrupy_products database...")
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database="entrupy_products"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables
        print("✓ Creating database schema...")
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                brand VARCHAR(100),
                source VARCHAR(50) NOT NULL,
                category VARCHAR(100),
                condition VARCHAR(50),
                size VARCHAR(50),
                price DECIMAL(10, 2),
                currency VARCHAR(10) DEFAULT 'USD',
                original_price DECIMAL(10, 2),
                product_url TEXT,
                image_url TEXT,
                product_metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, source)
            );
        """)
        print("  ✓ Created products table")
        
        # Price history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price DECIMAL(10, 2),
                currency VARCHAR(10) DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        print("  ✓ Created price_history table")
        
        # Notification events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                old_price DECIMAL(10, 2),
                new_price DECIMAL(10, 2),
                percentage_change DECIMAL(5, 2),
                event_type VARCHAR(50),
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        print("  ✓ Created notification_events table")
        
        # API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key_name VARCHAR(100) NOT NULL,
                key_value VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            );
        """)
        print("  ✓ Created api_keys table")
        
        # Request logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                endpoint VARCHAR(255),
                method VARCHAR(10),
                status_code INTEGER,
                response_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  ✓ Created request_logs table")
        
        # Create indexes
        print("✓ Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_source ON products(source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_created_at ON price_history(created_at);")
        print("  ✓ Indexes created")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ PostgreSQL Setup Completed Successfully!")
        print("=" * 60)
        
        # Save connection string to .env
        db_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/entrupy_products"
        
        print(f"\n📝 Update your backend/.env file with:")
        print(f"DATABASE_URL={db_url}")
        
        # Try to update .env automatically
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Replace or add DATABASE_URL
            import re
            new_content = re.sub(
                r'DATABASE_URL=.*',
                f'DATABASE_URL={db_url}',
                content
            )
            
            if 'DATABASE_URL' not in new_content:
                new_content += f"\nDATABASE_URL={db_url}"
            
            with open(env_file, 'w') as f:
                f.write(new_content)
            
            print(f"✓ Updated backend/.env file")
        else:
            print(f"⚠ Could not find .env file at {os.path.abspath(env_file)}")
        
        print("\n📖 Next steps:")
        print("1. Ensure the DATABASE_URL is correctly set in backend/.env")
        print("2. Run: python import_data.py (to load 90 products from sample_products/)")
        print("3. Run: python -m pytest tests/ (to run tests)")
        print("4. Run: python -m uvicorn app.main:app --reload")
        
    except psycopg2.Error as e:
        print(f"\n❌ PostgreSQL Error: {e}")
        print("\nMake sure:")
        print("  • PostgreSQL service is running")
        print("  • Username and password are correct")
        print("  • Host and port are correct")
        return False
    
    return True


if __name__ == "__main__":
    success = setup_database()
    if not success:
        exit(1)

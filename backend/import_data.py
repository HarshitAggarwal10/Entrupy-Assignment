import asyncio
from app.database import AsyncSessionLocal, init_db
from app.import_products import load_products_from_json_files

async def main():
    # Initialize database
    await init_db()
    
    # Create session
    async with AsyncSessionLocal() as db:
        # Import products
        imported, updated, errors = await load_products_from_json_files(
            '../sample_products', 
            db
        )
        
        print(f"\n✅ Import Complete!")
        print(f"   Imported: {imported}")
        print(f"   Updated:  {updated}")
        print(f"   Errors:   {errors}")

if __name__ == "__main__":
    asyncio.run(main())
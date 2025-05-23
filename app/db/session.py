import asyncpg

from app.core.config import settings

# Global variable to hold the pool
db_pool: asyncpg.Pool | None = None


async def create_db_pool():
    """Creates a PostgreSQL connection pool."""
    global db_pool
    if settings.DATABASE_DSN:
        print("Attempting to create PostgreSQL connection pool...")
        try:
            db_pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_DSN,
                min_size=5,  # จำนวน connection ขั้นต่ำใน pool
                max_size=20,  # จำนวน connection สูงสุดใน pool
            )
            print("PostgreSQL connection pool created successfully.")
        except Exception as e:
            print(f"Error creating PostgreSQL connection pool: {e}")
            # อาจจะ raise exception หรือจัดการ error ตามความเหมาะสม
    else:
        print("DATABASE_DSN not configured. Cannot create pool.")


async def close_db_pool():
    """Closes the PostgreSQL connection pool."""
    global db_pool
    if db_pool:
        print("Attempting to close PostgreSQL connection pool...")
        await db_pool.close()
        print("PostgreSQL connection pool closed.")


async def get_db_connection():
    if not db_pool:
        raise RuntimeError(
            "Database pool is not initialized. Ensure lifespan context manager is setup correctly."
        )
    async with db_pool.acquire() as connection:
        yield connection

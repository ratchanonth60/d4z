from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from app.core.config import settings
from app.db.sqlmodel_setup import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing resources...")

    # Initialize SQLModel tables
    await create_db_and_tables()

    # Keep direct asyncpg pool if still needed for other parts of the app
    # Otherwise, this can be removed if all DB access goes via SQLModel
    if settings.DATABASE_DSN:  #
        try:
            app.state.direct_db_pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_DSN,
                min_size=5,
                max_size=20,  #
            )
            print(
                "Direct PostgreSQL connection pool (asyncpg) created and stored in app.state.direct_db_pool"
            )
        except Exception as e:
            app.state.direct_db_pool = None
            print(f"Failed to create direct asyncpg pool: {e}")
    else:
        app.state.direct_db_pool = None
        print("DATABASE_DSN not configured for direct pool. Pool not created.")

    yield

    print("Application shutdown: Cleaning up resources...")
    if hasattr(app.state, "direct_db_pool") and app.state.direct_db_pool:
        await app.state.direct_db_pool.close()
        print("Direct PostgreSQL connection pool (asyncpg) closed.")

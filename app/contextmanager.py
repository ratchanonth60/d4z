from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing resources...")
    # สร้าง pool และเก็บไว้ใน app.state
    if settings.DATABASE_DSN:
        app.state.db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_DSN, min_size=5, max_size=20
        )
        print("PostgreSQL connection pool created and stored")
    else:
        app.state.db_pool = None
        print("DATABASE_DSN not configured. Pool not created.")

    yield

    print("Application shutdown: Cleaning up resources...")
    if app.state.db_pool:
        await app.state.db_pool.close()
        print("PostgreSQL connection pool closed.")

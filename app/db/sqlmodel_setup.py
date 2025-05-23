from sqlalchemy.ext.asyncio import (
    create_async_engine,
)  # SQLModel uses SQLAlchemy's engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

print(f"DATABASE_URL for SQLModel engine: {settings.DATABASE_URL}")
async_engine = create_async_engine(settings.DATABASE_URL, echo=True)


async def get_sqlmodel_session() -> AsyncSession:
    async with AsyncSession(async_engine) as session:
        yield session


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Use with caution
        await conn.run_sync(SQLModel.metadata.create_all)
    print("SQLModel tables created (if they didn't exist).")

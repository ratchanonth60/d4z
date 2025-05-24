from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from app.db.tortoise_config import TORTOISE_ORM_CONFIG  # Import config ของ Tortoise


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing resources...")

    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    # await Tortoise.generate_schemas() # สร้าง schema ครั้งแรก (คล้าย create_all)
    # หลังจากนั้นจะใช้ Aerich สำหรับ migrations
    print("Tortoise-ORM initialized.")

    yield

    print("Application shutdown: Cleaning up resources...")
    await Tortoise.close_connections()
    print("Tortoise-ORM connections closed.")

from app.core.config import settings  #

# DATABASE_URL ควรเป็นแบบที่ Tortoise ORM รองรับ เช่น "asyncpg://user:pass@host:port/db"
# settings.DATABASE_URL จาก SQLModel อาจจะต้องปรับ format เล็กน้อย (เอา +asyncpg ออก)
# หรือสร้าง DSN ใหม่สำหรับ Tortoise
TORTOISE_ORM_CONFIG = {
    "connections": {
        # settings.DATABASE_DSN น่าจะใกล้เคียงกว่า
        # "default": settings.DATABASE_URL_FOR_TORTOISE or "asyncpg://user:password@db:5432/mydatabase"
        "default": settings.DATABASE_DSN  #
    },
    "apps": {
        "models": {  # 'models' คือชื่อ app ที่ Tortoise ใช้, คุณสามารถตั้งชื่ออื่นได้
            "models": [
                "app.models.users",
                "app.models.session",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,  # หรือ True ถ้าคุณใช้ timezone-aware datetimes
    "timezone": "UTC",  # หรือ timezone ที่คุณต้องการ
}

import asyncio
from typing import AsyncGenerator, Generator
import asyncpg  # ต้องมี asyncpg ติดตั้ง

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise, connections
from tortoise.exceptions import DBConnectionError

from app.main import app
from app.core.config import settings
from app.models.users import User
from app.models.session import Session
from app.core.security import get_password_hash

# --- Database Configuration for Test ---
# User ที่จะใช้ต้องมีสิทธิ์ CREATEDB และ DROPDB
# DSN สำหรับเชื่อมต่อกับ default DB (เช่น 'postgres') เพื่อสร้าง/ลบ test DB
ADMIN_DB_USER = settings.POSTGRES_USER  # หรือ user อื่นที่มีสิทธิ์
ADMIN_DB_PASSWORD = settings.POSTGRES_PASSWORD
ADMIN_DB_HOST = settings.POSTGRES_SERVER
ADMIN_DB_PORT = settings.POSTGRES_PORT
ADMIN_TASK_DB_NAME = "postgres"  # หรือ template1

TEST_DB_NAME = settings.TEST_POSTGRES_DB  # เช่น "mydatabase_test"
TEST_DB_DSN_FOR_APP = f"asyncpg://{ADMIN_DB_USER}:{ADMIN_DB_PASSWORD}@{ADMIN_DB_HOST}:{ADMIN_DB_PORT}/{TEST_DB_NAME}"

TORTOISE_ORM_CONFIG_TEST = {
    "connections": {"default": TEST_DB_DSN_FOR_APP},
    "apps": {
        "models": {
            "models": [
                "app.models.users",
                "app.models.session",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}


@pytest_asyncio.fixture(scope="session", autouse=True)
async def manage_postgres_database_instance():
    """
    Session-scoped fixture to CREATE and DROP the PostgreSQL database instance.
    Relies on pytest-asyncio to provide the event loop for its execution.
    """
    conn_admin = None
    try:
        print(
            f"SessionSetup: Connecting to '{ADMIN_TASK_DB_NAME}' to manage test database '{TEST_DB_NAME}'..."
        )
        # asyncpg.connect will use the currently running event loop.
        conn_admin = await asyncpg.connect(
            user=ADMIN_DB_USER,
            password=ADMIN_DB_PASSWORD,
            database=ADMIN_TASK_DB_NAME,
            host=ADMIN_DB_HOST,
            port=ADMIN_DB_PORT,
        )
        db_exists = await conn_admin.fetchval(
            f"SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not db_exists:
            print(f"SessionSetup: Creating test database: {TEST_DB_NAME}")
            await conn_admin.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
        else:
            print(f"SessionSetup: Test database {TEST_DB_NAME} already exists.")
        await conn_admin.close()
        conn_admin = None  # Ensure it's not reused if an error occurs before yield
    except Exception as e:
        if conn_admin:
            await conn_admin.close()
        print(
            f"SessionSetup: CRITICAL - Failed to create/ensure test database '{TEST_DB_NAME}': {e}"
        )
        pytest.exit(
            f"Failed to prepare test database: {e}"
        )  # Exit pytest if DB setup fails

    yield  # Tests run here

    # Teardown: Drop the database
    conn_admin_drop = None
    try:
        print(
            f"SessionTeardown: Connecting to '{ADMIN_TASK_DB_NAME}' to drop test database '{TEST_DB_NAME}'..."
        )
        conn_admin_drop = await asyncpg.connect(
            user=ADMIN_DB_USER,
            password=ADMIN_DB_PASSWORD,
            database=ADMIN_TASK_DB_NAME,
            host=ADMIN_DB_HOST,
            port=ADMIN_DB_PORT,
        )
        # Terminate connections BEFORE dropping database
        print(f"SessionTeardown: Terminating active connections to '{TEST_DB_NAME}'...")
        await conn_admin_drop.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
              AND pid <> pg_backend_pid();
        """)
        print(f"SessionTeardown: Dropping test database: {TEST_DB_NAME}")
        await conn_admin_drop.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
        await conn_admin_drop.close()
        conn_admin_drop = None
    except Exception as e:
        if conn_admin_drop:
            await conn_admin_drop.close()
        print(
            f"SessionTeardown: ERROR - Failed to drop test database '{TEST_DB_NAME}': {e}"
        )


@pytest_asyncio.fixture(scope="function", autouse=True)
async def tortoise_db_per_function():
    """
    Function-scoped fixture to initialize Tortoise, generate schemas for each test,
    and ensure tables are clean and connections are closed.
    """
    # Clear Tortoise's app registry to allow re-initialization. This is crucial.
    Tortoise.apps = {}
    _tortoise_initialized = False
    try:
        # Tortoise.init will use the event loop provided by pytest-asyncio for this function.
        await Tortoise.init(config=TORTOISE_ORM_CONFIG_TEST)
        _tortoise_initialized = True
        await Tortoise.generate_schemas()  # Create tables if they don't exist
        yield  # Test runs here
    except Exception as e:
        print(f"FunctionScope Tortoise ERROR during setup: {e}")
        if _tortoise_initialized:
            await (
                connections.close_all()
            )  # Attempt to close if init was partially successful
        raise  # Re-raise to fail the test
    finally:
        if _tortoise_initialized:
            # Clean data from tables after each test
            try:
                await Session.all().delete()
                await User.all().delete()
            except Exception as e:
                print(f"FunctionScope Tortoise ERROR during table cleanup: {e}")
            await connections.close_all()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def test_user_data() -> dict:
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "full_name": "Test User",
    }


@pytest_asyncio.fixture
async def created_test_user(test_user_data: dict) -> User:
    # Pre-cleanup for this specific user, relying on tortoise_db_per_function having set up Tortoise
    await User.filter(username=test_user_data["username"]).delete()
    await User.filter(email=test_user_data["email"]).delete()

    user = await User.create(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),  #
        full_name=test_user_data["full_name"],
        is_active=False,
        is_email_verified=False,
    )
    return user


@pytest_asyncio.fixture
async def active_user_token_headers(client: AsyncClient, test_user_data: dict) -> dict:
    # Clean up sessions related to the test user more carefully
    # First, try to find the user if they exist from a previous (possibly failed) run
    user_to_clean = await User.get_or_none(username=test_user_data["username"])
    if user_to_clean:
        # If user exists, delete their sessions by user_id
        await Session.filter(user_id=user_to_clean.id).delete()

    # Now, delete the user record itself to ensure a clean state for creation
    await User.filter(username=test_user_data["username"]).delete()
    # --- MODIFICATION END ---

    # Create the user
    user = await User.create(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),  #
        full_name=test_user_data["full_name"],
        is_active=True,
        is_email_verified=True,
    )

    # Login to get tokens
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
    }
    response = await client.post("/api/v1/auth/login", data=login_data)  #
    response.raise_for_status()  # Ensure login is successful
    tokens = response.json()["data"]
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

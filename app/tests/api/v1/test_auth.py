from datetime import datetime, timedelta, timezone  # Added imports
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import settings  # For EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
from app.core.security import (
    get_password_hash,
)  # For creating test user fixture if needed elsewhere
from app.models.session import Session
from app.models.users import User

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_register_new_user(client: AsyncClient, test_user_data: dict):
    # Clear any existing user with the same username/email before test
    await User.filter(username=test_user_data["username"]).delete()
    await User.filter(email=test_user_data["email"]).delete()

    payload = {
        "username": test_user_data["username"],
        "email": test_user_data["email"],
        "password": test_user_data["password"],
        "password_confirm": test_user_data["password"],
        "full_name": test_user_data["full_name"],
    }
    # Mock send_verification_email
    with patch(
        "app.services.users.send_verification_email", new_callable=AsyncMock
    ) as mock_send_email:
        response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["message"] == "User registered successfully"
    assert response_data["data"]["username"] == test_user_data["username"]
    assert response_data["data"]["email"] == test_user_data["email"]
    assert response_data["data"]["is_active"] is False
    assert response_data["data"]["is_email_verified"] is False

    mock_send_email.assert_called_once()

    user_in_db = await User.get_or_none(username=test_user_data["username"])
    assert user_in_db is not None
    assert user_in_db.email == test_user_data["email"]
    assert user_in_db.is_active is False
    assert user_in_db.email_verification_token is not None


async def test_register_user_username_exists(
    client: AsyncClient, created_test_user: User, test_user_data: dict
):
    payload = {
        "username": created_test_user.username,
        "email": "newemail@example.com",
        "password": "testpassword",
        "password_confirm": "testpassword",
        "full_name": "Another User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert "Username already registered" in response_data["message"]


async def test_login_correct_credentials(
    client: AsyncClient, created_test_user: User, test_user_data: dict
):
    created_test_user.is_active = True
    created_test_user.is_email_verified = True
    await created_test_user.save()

    login_payload = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
    }
    response = await client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "access_token" in response_data["data"]
    assert "refresh_token" in response_data["data"]
    assert response_data["data"]["token_type"] == "bearer"


async def test_login_incorrect_password(
    client: AsyncClient, created_test_user: User, test_user_data: dict
):
    created_test_user.is_active = True
    created_test_user.is_email_verified = True  # Ensure user is verifiable
    await created_test_user.save()

    login_payload = {
        "username": test_user_data["username"],
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["code"] == 401
    assert "Incorrect username or password" in response_data["message"]


async def test_login_inactive_user(
    client: AsyncClient, created_test_user: User, test_user_data: dict
):
    # User is inactive by default from fixture, ensure email is also not verified for this state
    created_test_user.is_active = False
    created_test_user.is_email_verified = False
    await created_test_user.save()

    login_payload = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
    }
    response = await client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["code"] == 400
    assert "Account not active" in response_data["message"]


async def test_verify_email(client: AsyncClient, created_test_user: User):
    assert created_test_user.is_active is False
    assert created_test_user.is_email_verified is False

    verification_token = "test_verification_token_123"
    created_test_user.email_verification_token = verification_token

    # --- CORRECTED LINE ---
    # Calculate the actual datetime for expiration
    created_test_user.email_verification_token_expires_at = datetime.now(
        timezone.utc
    ) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
        or 1  # Default to 1 if not set
    )
    # --- END CORRECTION ---
    await created_test_user.save()

    response = await client.get(f"/api/v1/auth/verify-email/{verification_token}")
    assert response.status_code == 200
    response_data = response.json()

    # Assertions might need to be adjusted based on what verify_email_token returns
    # For example, if it returns the user object upon successful verification
    if not response_data["success"]:
        print(
            "Verification failed:",
            response_data.get("message"),
            response_data.get("errors"),
        )

    assert response_data["success"] is True
    assert "Email verified successfully" in response_data["message"]
    assert response_data["data"]["username"] == created_test_user.username
    assert response_data["data"]["is_active"] is True
    assert response_data["data"]["is_email_verified"] is True

    user_in_db = await User.get(id=created_test_user.id)
    assert user_in_db.is_active is True
    assert user_in_db.is_email_verified is True
    assert (
        user_in_db.email_verification_token is None
    )  # Token should be cleared after verification


async def test_verify_email_invalid_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/verify-email/invalidtoken123")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["code"] == 400
    assert "Invalid or expired verification token" in response_data["message"]


# async def test_refresh_token(
#     client: AsyncClient, active_user_token_headers: dict
# ):  # active_user_token_headers creates an active user
#     # To get a refresh token, we need to log in that active user.
#     # The active_user_token_headers fixture already logs in 'testuser'.
#     # We need to get the refresh token from that login process.
#     # The fixture currently only returns access_token headers.
#     # For this test, it's cleaner to perform a login here explicitly to get the refresh token.
#
#     await Session.filter().delete()  # Clean up any existing sessions
#
#     temp_user_for_refresh_test_username = "refreshtestuser"
#     temp_user_for_refresh_test_password = "refreshpassword"
#
#     await User.filter(username=temp_user_for_refresh_test_username).delete()  # Clean up
#
#     # Create a user specifically for this test
#     refresh_user = await User.create(
#         username=temp_user_for_refresh_test_username,
#         email="refresh@example.com",
#         hashed_password=get_password_hash(temp_user_for_refresh_test_password),
#         is_active=True,
#         is_email_verified=True,
#     )
#
#     login_payload = {
#         "username": temp_user_for_refresh_test_username,
#         "password": temp_user_for_refresh_test_password,
#     }
#     login_resp = await client.post("/api/v1/auth/login", data=login_payload)
#     assert login_resp.status_code == 200
#     login_data = login_resp.json()["data"]
#     original_refresh_token = login_data["refresh_token"]
#     original_access_token = login_data["access_token"]
#
#     refresh_payload = {"refresh_token": original_refresh_token}
#     response = await client.post("/api/v1/auth/refresh_token", json=refresh_payload)
#
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["success"] is True
#     assert "access_token" in response_data["data"]
#     assert "refresh_token" in response_data["data"]
#     assert response_data["data"]["access_token"] != original_access_token
#     assert response_data["data"]["refresh_token"] != original_refresh_token
#


async def test_refresh_token_invalid(client: AsyncClient):
    refresh_payload = {"refresh_token": "invalid_refresh_token_value_long_enough"}
    response = await client.post("/api/v1/auth/refresh_token", json=refresh_payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["code"] == 401
    # The exact message depends on the failure point (decode, session not found, etc.)
    assert (
        "Invalid refresh token" in response_data["message"]
        or "Refresh token not found" in response_data["message"]
        or "Invalid refresh token payload or type" in response_data["message"]
    )


async def test_logout(client: AsyncClient, active_user_token_headers: dict):
    # Similar to refresh_token, we need a refresh token to invalidate.
    # Let's log in a specific user for this test.
    temp_user_for_logout_test_username = "logouttestuser"
    temp_user_for_logout_test_password = "logoutpassword"

    await User.filter(username=temp_user_for_logout_test_username).delete()

    logout_user = await User.create(
        username=temp_user_for_logout_test_username,
        email="logout@example.com",
        hashed_password=get_password_hash(temp_user_for_logout_test_password),
        is_active=True,
        is_email_verified=True,
    )

    login_payload = {
        "username": temp_user_for_logout_test_username,
        "password": temp_user_for_logout_test_password,
    }
    login_resp = await client.post("/api/v1/auth/login", data=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    refresh_token_to_invalidate = login_data["refresh_token"]
    access_token_for_logout_auth = login_data[
        "access_token"
    ]  # Use this for authenticating the /logout request

    headers_for_logout = {"Authorization": f"Bearer {access_token_for_logout_auth}"}
    logout_payload = {"refresh_token": refresh_token_to_invalidate}

    response = await client.post(
        "/api/v1/auth/logout", json=logout_payload, headers=headers_for_logout
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "Successfully logged out" in response_data["message"]

    # Try to use the invalidated refresh token again
    refresh_payload_after_logout = {"refresh_token": refresh_token_to_invalidate}
    response_after_logout = await client.post(
        "/api/v1/auth/refresh_token", json=refresh_payload_after_logout
    )
    assert response_after_logout.status_code == 200
    assert response_after_logout.json()["success"] is False
    assert response_after_logout.json()["code"] == 401
    assert (
        "Refresh token has been invalidated" in response_after_logout.json()["message"]
        or "Refresh token not found or already used"
        in response_after_logout.json()["message"]
    )

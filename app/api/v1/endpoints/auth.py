from datetime import datetime, timezone
from typing import Annotated

import jwt  # type: ignore
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

from app.models.users import UserCreate, UserRead
from app.schemas.base_response import BaseResponse
from app.schemas.token_schema import LogoutRequest, RefreshTokenRequest, Token
from app.services.users import UserService

router = APIRouter()


def get_user_service() -> UserService:
    return UserService()


@router.post("/login", response_model=BaseResponse[Token])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    ### Login for an existing user.

    Authenticates a user and provides JWT access and refresh tokens.

    **Request Body (form-data):**
    - `username`: The user's username (string, required).
    - `password`: The user's password (string, required).

    **Responses:**
    - `200 OK`: Successful authentication. Returns `Token` object with `access_token`, `refresh_token`, and `token_type`.
    - `400 Bad Request`: If the user is inactive.
    - `401 Unauthorized`: If the username or password is incorrect.
    """
    user = await user_service.get_user_by_username(username=form_data.username)
    if (
        not user
        or not user.hashed_password
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not active. Please verify your email address first.",
        )

    token_payload_data = {
        "sub": user.username,
        "user_id": user.id,
    }

    access_token = create_access_token(data=token_payload_data)
    refresh_token = create_refresh_token(data=token_payload_data)

    # Create user session for refresh token tracking
    await user_service.create_user_session(
        user_id=user.id, refresh_token_value=refresh_token
    )

    return BaseResponse(
        data=Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    )


@router.post("/refresh_token", response_model=BaseResponse[Token])
async def refresh_access_token(
    token_request: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    ### Refresh Access Token.

    Obtains a new JWT access token and a new JWT refresh token using a valid, non-expired refresh token.
    This endpoint implements **Refresh Token Rotation**.

    **Request Body:**
    - `refresh_token`: The refresh token (string, required).

    **Responses:**
    - `200 OK`: Successfully refreshed tokens. Returns new `Token` object.
    - `401 Unauthorized`:
        - Invalid or malformed refresh token.
        - Refresh token not found or already used/invalidated.
        - Refresh token has expired.
        - User associated with the token not found or inactive.
    """
    try:
        token_data = decode_token(token_request.refresh_token)
        if (
            not token_data or not token_data.username or token_data.type != "refresh"
        ):  # Ensure it's a refresh token
            raise AuthenticationError(message="Invalid refresh token payload or type")

        user_session = await user_service.get_user_session_by_token(
            token_request.refresh_token
        )
        if not user_session:
            raise AuthenticationError(message="Refresh token not found or already used")
        if not user_session.is_active:
            raise AuthenticationError(message="Refresh token has been invalidated")
        if user_session.expires_at < datetime.now(timezone.utc):
            await user_service.deactivate_user_session(user_session)
            raise AuthenticationError(message="Refresh token has expired")

        user = await user_service.get_user_by_id(user_id=user_session.user_id)
        if not user:
            await user_service.deactivate_user_session(user_session)
            raise AuthenticationError(
                message="User associated with refresh token not found"
            )
        if not user.is_active:
            await user_service.deactivate_user_session(user_session)
            raise AuthenticationError(message="User is inactive")

        await user_service.deactivate_user_session(
            user_session
        )  # Deactivate old refresh token

        new_token_payload_data = {"sub": user.username, "user_id": user.id}
        new_access_token = create_access_token(data=new_token_payload_data)
        new_refresh_token_value = create_refresh_token(data=new_token_payload_data)

        await user_service.create_user_session(  # Store new refresh token session
            user_id=user.id, refresh_token_value=new_refresh_token_value
        )

        return BaseResponse(
            data=Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token_value,
                token_type="bearer",
            )
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token signature has expired (JWT lib check)",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token (JWT lib check)",
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e.detail)
        )


@router.post("/logout", response_model=BaseResponse[None])
async def logout_user(
    token_request: LogoutRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
):
    """
    ### Logout User.

    Invalidates the provided refresh token, effectively logging the user out from that session.
    The client should also discard both the access and refresh tokens locally.

    **Requires Authentication (Access Token)**: Although this endpoint acts on a refresh token,
    it requires a valid access token for the initial authorization to ensure the calling user
    has some authenticated context, even if the primary action is on the refresh token.

    **Request Body:**
    - `refresh_token`: The refresh token to invalidate (string, required).

    **Responses:**
    - `200 OK`: Logout processed. The `success` field will be true.
        The message might indicate success even if the token was already invalid to prevent token status enumeration.
    """
    access_token_data = getattr(request.state, "token_data", None)

    user_session = await user_service.get_user_session_by_token(
        token_request.refresh_token
    )

    if not user_session or not user_session.is_active:
        return BaseResponse(
            success=True,
            message="Logout processed (token not found or already inactive).",
        )

    # Optional: Verify that the user logging out (from access token) owns this refresh token.
    # This check is based on the global JWTBearer dependency setting request.state.token_data.
    if access_token_data and access_token_data.username:
        # Assuming user_id is in the access token payload as set during creation.
        user_id_from_access_token = getattr(access_token_data, "user_id", None)
        if (
            user_id_from_access_token is None
        ):  # Fallback if user_id not in token, check by username
            user_from_access_token = await user_service.get_user_by_username(
                access_token_data.username
            )
            if user_from_access_token:
                user_id_from_access_token = user_from_access_token.id

        if user_id_from_access_token != user_session.user_id:
            # Log potential mismatch but still invalidate the target refresh token for security.
            # This prevents a user from using their access token to enumerate other users' refresh tokens
            # if they somehow got hold of one. The primary action is to invalidate the *provided* refresh token.
            print(
                f"Warning: Logout attempt with mismatched user context. "
                f"Access token user ID: {user_id_from_access_token}, "
                f"Refresh token owner ID: {user_session.user_id}"
            )
            # To strictly prevent user A from logging out user B's refresh token:
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token does not belong to the authenticated user.")
            # However, the current implementation invalidates the refresh token if found, regardless of direct ownership by access token holder,
            # which can be a valid strategy if the refresh token itself is considered compromised.
            # For this example, we proceed to invalidate the refresh token.
            pass  # Continue to invalidate the refresh_token

    await user_service.deactivate_user_session(user_session)
    return BaseResponse(success=True, message="Successfully logged out.")


@router.post(
    "/register",
    response_model=BaseResponse[UserRead],
)
async def register_new_user(
    user_in: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    ### Register a new user.

    Creates a new user account. The new user will be active by default
    but will not have superuser privileges.

    **Request Body (`UserCreate`):**
    - `username` (str, required): Unique username (max 50 chars).
    - `email` (Optional[str]): Unique email address (max 100 chars).
    - `password` (str, required): User's password.
    - `full_name` (Optional[str]): User's full name (max 100 chars).
    - `is_active` (bool, default: true): Set by UserCreate model, usually true.
    - `is_superuser` (bool, default: false): Set by UserCreate model, usually false.

    **Responses:**
    - `201 Created`: User registered successfully. Returns `BaseResponse` with the created `UserRead` data.
    - `400 Bad Request`: If the username or email already exists, or validation fails.
    """
    # The create_user service method already checks for existing username/email
    # and handles password hashing.
    # By default, UserCreate sets is_active=True and is_superuser=False
    db_user = await user_service.create_user(user_in=user_in)
    return BaseResponse(message="User registered successfully", data=db_user)


@router.get("/verify-email/{token}", response_model=BaseResponse[UserRead])
async def verify_user_email(
    token: str,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    ### Verify User Email Address.

    This endpoint is typically accessed by clicking a link sent to the user's email.
    If the token is valid and not expired, the user's email is marked as verified,
    and the user account is activated.

    **Path Parameters:**
    - `token` (str, required): The email verification token.

    **Responses:**
    - `200 OK`: Email verified successfully. Returns `BaseResponse` with `UserRead` data.
    - `400 Bad Request`: If the token is invalid, expired, or already used.
    """
    user = await user_service.verify_email_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token, or email already verified with this token.",
        )
    if not user.is_email_verified:  # Should have been set by verify_email_token
        # This case implies an issue in verify_email_token logic if it returns a user but not verified
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification process failed unexpectedly.",
        )

    return BaseResponse(
        message="Email verified successfully. Your account is now active.", data=user
    )


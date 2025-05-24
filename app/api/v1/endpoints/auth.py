from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
import jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.sqlmodel_setup import (
    get_sqlmodel_session,
)
from app.schemas.base_response import BaseResponse
from app.schemas.token_schema import LogoutRequest, RefreshTokenRequest, Token
from app.services.users import UserService


router = APIRouter()


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_sqlmodel_session)],
) -> UserService:
    return UserService(session=session)


@router.post("/login", response_model=BaseResponse[Token])
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm, Depends()
    ],  # รับ username และ password
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await user_service.get_user_by_username(username=form_data.username)
    if (
        not user
        or not user.hashed_password
        or not verify_password(form_data.password, user.hashed_password)
    ):  #
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    token_payload_data = {
        "sub": user.username,
        "user_id": user.id,
    }  # ใส่ user_id เข้าไปด้วยเผื่อใช้

    access_token = create_access_token(data=token_payload_data)  #
    refresh_token = create_refresh_token(data=token_payload_data)  #
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
    try:
        # 1. Decode the provided refresh token to get user info
        token_data = decode_token(token_request.refresh_token)  #
        if not token_data or not token_data.username:
            raise AuthenticationError(detail="Invalid refresh token payload")

        # 2. Verify the refresh token against the database (UserSession table)
        user_session = await user_service.get_user_session_by_token(
            token_request.refresh_token
        )
        if not user_session:
            raise AuthenticationError(detail="Refresh token not found or already used")
        if not user_session.is_active:
            raise AuthenticationError(detail="Refresh token has been invalidated")
        if user_session.expires_at < datetime.now(timezone.utc):
            # Deactivate expired token
            await user_service.deactivate_user_session(user_session)
            raise AuthenticationError(detail="Refresh token has expired")

        # 3. Get the user associated with the token
        user = await user_service.get_user_by_id(user_id=user_session.user_id)
        if not user:
            # This case should ideally not happen if foreign keys are set up
            await user_service.deactivate_user_session(
                user_session
            )  # Deactivate orphan session
            raise AuthenticationError(
                detail="User associated with refresh token not found"
            )
        if not user.is_active:
            await user_service.deactivate_user_session(
                user_session
            )  # Deactivate session for inactive user
            raise AuthenticationError(detail="User is inactive")

        # 4. (Refresh Token Rotation) Deactivate the old refresh token
        await user_service.deactivate_user_session(user_session)

        # 5. Create new access and refresh tokens
        new_token_payload_data = {"sub": user.username, "user_id": user.id}
        new_access_token = create_access_token(data=new_token_payload_data)  #
        new_refresh_token_value = create_refresh_token(data=new_token_payload_data)  #

        # 6. Store the new refresh token session
        await user_service.create_user_session(
            user_id=user.id, refresh_token_value=new_refresh_token_value
        )

        return BaseResponse(
            data=Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token_value,
                token_type="bearer",
            )
        )

    except (
        jwt.ExpiredSignatureError
    ):  # This is for JWT library's own expiry check on decode_token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token signature has expired (JWT lib check)",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token (JWT lib check)",
        )
    except AuthenticationError as e:  #
        # Log the original error e if needed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e.detail)
        )


@router.post("/logout", response_model=BaseResponse[None])
async def logout_user(
    # To ensure only authenticated users can logout their own refresh token
    # current_user: Annotated[User, Depends(get_current_active_user)], # User object from access token
    token_request: LogoutRequest,  # Refresh token to be invalidated
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,  # To get access token if needed for user context
):
    """
    Logout user by invalidating the provided refresh token.
    Client should also delete access and refresh tokens from its storage.
    """
    # Option 1: Get user context from access token (if required to match refresh token owner)
    # This requires the /logout endpoint to be protected by JWTBearer for access token
    access_token_credentials = await JWTBearer(auto_error=False)(
        request
    )  # Try to get access token

    user_session = await user_service.get_user_session_by_token(
        token_request.refresh_token
    )

    if not user_session or not user_session.is_active:
        # Even if not found or not active, return success to not reveal token status
        return BaseResponse(success=True, message="Logout processed.")

    # Optional: Verify that the user logging out owns this refresh token
    # This is important if /logout is protected and you want to prevent
    # user A from logging out user B's refresh token if they somehow got it.
    if access_token_credentials and access_token_credentials.username:
        user_from_access_token = await user_service.get_user_by_username(
            access_token_credentials.username
        )
        if (
            not user_from_access_token
            or user_from_access_token.id != user_session.user_id
        ):
            # Potentially malicious attempt or mismatch, log it
            # For security, still proceed as if logout was for the given refresh token
            # or return a generic success. Avoid giving away too much info.
            print(
                f"Warning: Logout attempt with mismatched user context. Access token user: {access_token_credentials.username}, Refresh token owner ID: {user_session.user_id}"
            )
            # We can choose to still invalidate the refresh token or return error
            # For simplicity here, we'll invalidate if found
            await user_service.deactivate_user_session(user_session)
            return BaseResponse(
                success=True, message="Logout processed (context mismatch noted)."
            )

    await user_service.deactivate_user_session(user_session)
    return BaseResponse(success=True, message="Successfully logged out.")

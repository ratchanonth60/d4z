from typing import Annotated, List, Optional

import jwt  # PyJWT
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token  # ใช้ decode_token
from app.db.sqlmodel_setup import get_sqlmodel_session
from app.models.users import User
from app.schemas.token_schema import TokenData
from app.services.users import UserService


class JWTBearer(HTTPBearer):
    def __init__(
        self, auto_error: bool = True, excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(auto_error=auto_error)
        self.excluded_paths = (
            excluded_paths if excluded_paths is not None else []
        )  # Ensure it's a list

    async def __call__(self, request: Request) -> Optional[TokenData]:  # type: ignore
        current_path = request.url.path

        # Path exclusion logic (เหมือนที่คุณเคยให้มา)
        for excluded_pattern in self.excluded_paths:
            # 1. Exact match for root path "/"
            if excluded_pattern == "/" and current_path == "/":
                return None
            # 2. Prefix match for patterns ending with "/" (and not just "/")
            elif (
                excluded_pattern.endswith("/")
                and excluded_pattern != "/"
                and current_path.startswith(excluded_pattern)
            ):
                return None
            # 3. Exact match for other patterns
            elif (
                not excluded_pattern.endswith("/")
                and excluded_pattern != "/"
                and current_path == excluded_pattern
            ):
                return None

        # If not excluded, proceed with token validation
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(
            request
        )

        if credentials:
            if credentials.scheme.lower() != "bearer":
                if self.auto_error:
                    raise AuthenticationError(message="Invalid authentication scheme.")
                else:
                    return None

            token = credentials.credentials
            try:
                token_data = decode_token(token)  #
                if not token_data or not token_data.username:
                    raise AuthenticationError(
                        message="Invalid token: Username missing."
                    )

                # Store TokenData in request.state so other dependencies can use it
                request.state.token_data = token_data
                return token_data  # Return TokenData, or you could return the user object itself if desired
            # แต่การ return TokenData และให้ get_current_user ดึง user จะแยกส่วนดีกว่า

            except (
                jwt.ExpiredSignatureError,
                jwt.InvalidTokenError,
                AuthenticationError,
            ) as e:
                if isinstance(e, AuthenticationError):
                    raise e
                if isinstance(e, jwt.ExpiredSignatureError):
                    raise AuthenticationError(message="Access token has expired.")
                raise AuthenticationError(message="Invalid access token.")
            except Exception as e:
                print(f"Unexpected error in JWTBearer: {e}")  # Log the error
                raise AuthenticationError(
                    message="Could not validate credentials (unexpected)."
                )
        else:  # No credentials provided
            if self.auto_error:
                raise AuthenticationError(message="Not authenticated.")
            return AuthenticationError(message="Not authenticated.")


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_sqlmodel_session)],
) -> UserService:
    return UserService(session=session)


async def get_optional_token_data(request: Request) -> Optional[TokenData]:
    # This dependency tries to get token_data if JWTBearer (global) has set it.
    # It doesn't raise an error if not found, allowing truly public endpoints.
    # However, JWTBearer with auto_error=True will raise before this if no valid token.
    # This is more for if JWTBearer had auto_error=False for some paths.
    # For global JWTBearer(auto_error=True), request.state.token_data should exist if not excluded.
    return getattr(request.state, "token_data", None)


async def get_current_user(
    # Option 1: JWTBearer (global) sets request.state.token_data
    # token_data: Annotated[Optional[TokenData], Depends(get_optional_token_data)],
    # Option 2: If JWTBearer (global) returns TokenData, FastAPI can inject it.
    #           However, global dependencies usually don't return values directly to path operations.
    #           They modify the request or raise exceptions.
    # The most robust way is for JWTBearer to set request.state.token_data,
    # and then this dependency reads from it.
    request: Request,  # Get the request object
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:  # This should always return a User or raise an error
    token_data: Optional[TokenData] = getattr(request.state, "token_data", None)

    if token_data is None or token_data.username is None:
        # This should ideally be caught by JWTBearer(auto_error=True) already
        # if the path is not in excluded_paths.
        raise AuthenticationError(
            message="Credentials not provided or invalid (get_current_user)."
        )

    user = await user_service.get_user_by_username(username=token_data.username)
    if user is None:
        raise AuthenticationError(message="User not found based on token.")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

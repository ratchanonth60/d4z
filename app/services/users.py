import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import get_password_hash  #

# Import models and security functions
from app.models.session import Session
from app.models.users import User, UserCreate, UserUpdate
from app.schemas.users import UserFilterParams
from app.services.utils import task_send_verification_email


class UserService:
    async def create_user(self, *, user_in: UserCreate) -> User:  #
        if not user_in.email:  #
            raise HTTPException(  #
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required.",  #
            )

        if await User.filter(username=user_in.username).exists():  #
            raise HTTPException(  #
                status_code=status.HTTP_400_BAD_REQUEST,  #
                detail="Username already registered.",  #
            )
        if await User.filter(email=user_in.email).exists():  #
            raise HTTPException(  #
                status_code=status.HTTP_400_BAD_REQUEST,  #
                detail="Email already registered.",  #
            )

        hashed_password = get_password_hash(user_in.password)  #
        verification_token = secrets.token_urlsafe(32)  #
        token_expires_at = datetime.now(timezone.utc) + timedelta(  #
            hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS or 1  #
        )

        db_user = await User.create(  #
            username=user_in.username,  #
            email=user_in.email,  #
            full_name=user_in.full_name,  #
            hashed_password=hashed_password,  #
            is_active=False,  #
            is_email_verified=False,  #
            email_verification_token=verification_token,  #
            email_verification_token_expires_at=token_expires_at,  #
        )

        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")  #
        verification_link = (
            f"{base_url}/api/v1/auth/verify-email/{verification_token}"  #
        )
        task_send_verification_email(  #
            db_user.email,
            db_user.username,
            verification_link,  #
        )

        return db_user  #

    async def get_user_by_id(self, user_id: int) -> Optional[User]:  #
        return await User.get_or_none(id=user_id)  #

    async def get_user_by_username(self, username: str) -> Optional[User]:  #
        return await User.get_or_none(username=username)  #

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:  #
        return await User.get_or_none(email=email)  #

    async def get_users_paginated(  #
        self,  #
        filters: UserFilterParams,  #
        page: int = 1,  #
        page_size: int = 10,  #
        sort_by: Optional[str] = None,  #
        sort_order: str = "asc",  #
    ) -> Tuple[List[User], int]:  #
        offset = (page - 1) * page_size  #
        query = User.all()  #

        if filters.username_contains:  #
            query = query.filter(username__icontains=filters.username_contains)  #
        if filters.email_equals:  #
            query = query.filter(email=filters.email_equals)  #
        if filters.is_active is not None:  #
            query = query.filter(is_active=filters.is_active)  #

        total_count = await query.count()  #

        if sort_by:  #
            if sort_order.lower() == "desc":  #
                sort_by = f"-{sort_by}"  #
            query = query.order_by(sort_by)  #

        users = await query.offset(offset).limit(page_size)  #
        return users, total_count  #

    async def verify_email_token(self, token: str) -> Optional[User]:  #
        user = await User.get_or_none(email_verification_token=token)  #

        if not user:  #
            return None  #

        if user.is_email_verified:  #
            return user  #

        if (  #
            not user.email_verification_token_expires_at  #
            or user.email_verification_token_expires_at < datetime.now(timezone.utc)  #
        ):
            user.email_verification_token = None  #
            user.email_verification_token_expires_at = None  #
            await user.save()  #
            return None  #

        user.is_active = True  #
        user.is_email_verified = True  #
        user.email_verification_token = None  #
        user.email_verification_token_expires_at = None  #
        await user.save()  #
        return user  #

    async def request_password_reset(self, email: EmailStr) -> bool:  #
        user = await self.get_user_by_email(email)  #
        if user and user.is_active:  #
            reset_token = secrets.token_urlsafe(32)  #
            expires_at = datetime.now(timezone.utc) + timedelta(  #
                hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS or 1  #
            )
            user.password_reset_token = reset_token  #
            user.password_reset_token_expires_at = expires_at  #
            await user.save()  #

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")  #
            reset_link = f"{base_url}/reset-password-page?token={reset_token}"  #

            await task_send_password_reset_email(  #
                user.email,
                user.username,
                reset_link,  # type: ignore #
            )
            return True  #
        return False  #

    async def resend_verification_email(self, email: EmailStr) -> bool:
        user = await self.get_user_by_email(email)
        if user and not user.is_email_verified:
            # Potentially rate limit this to prevent abuse
            if (
                user.email_verification_token
                and user.email_verification_token_expires_at
                and user.email_verification_token_expires_at
                > datetime.now(timezone.utc)
                - timedelta(
                    minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS * 60 - 5
                )
            ):  # Check if token was generated recently (e.g. within last 5 mins)
                # To prevent spamming, you might want to disallow resending too quickly
                # For now, we allow it but this is a place for future rate limiting logic
                pass

            new_verification_token = secrets.token_urlsafe(32)
            new_token_expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS or 1
            )
            user.email_verification_token = new_verification_token
            user.email_verification_token_expires_at = new_token_expires_at
            # User remains inactive until new token is used
            user.is_active = False
            await user.save()

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
            new_verification_link = (
                f"{base_url}/api/v1/auth/verify-email/{new_verification_token}"
            )

            task_send_verification_email(
                user.email,
                user.username,
                new_verification_link,  # type: ignore
            )
            return True
        return False

    async def reset_password(self, token: str, new_password: str) -> Optional[User]:  #
        user = await User.get_or_none(password_reset_token=token)  #

        if not user:  #
            return None  #

        if (  #
            not user.password_reset_token_expires_at  #
            or user.password_reset_token_expires_at < datetime.now(timezone.utc)  #
        ):
            user.password_reset_token = None  #
            user.password_reset_token_expires_at = None  #
            await user.save()  #
            return None  #

        user.hashed_password = get_password_hash(new_password)  #
        user.password_reset_token = None  #
        user.password_reset_token_expires_at = None  #
        user.is_active = True  #
        await user.save()  #
        return user  #

    async def update_user(  #
        self,
        *,
        user_id: int,
        user_in: UserUpdate,  #
    ) -> Optional[User]:  #
        db_user = await self.get_user_by_id(user_id)  #
        if not db_user:  #
            raise HTTPException(  #
                status_code=status.HTTP_404_NOT_FOUND,  #
                detail="User not found for update",  #
            )

        user_data = user_in.model_dump(exclude_unset=True)  #
        if "password" in user_data and user_data["password"]:  #
            hashed_password = get_password_hash(user_data["password"])  #
            db_user.hashed_password = hashed_password  #
            del user_data["password"]  #

        if "email" in user_data and user_data["email"] != db_user.email:  #
            if await User.filter(email=user_data["email"]).exists():  #
                raise HTTPException(  #
                    status_code=status.HTTP_400_BAD_REQUEST,  #
                    detail="Email already registered by another user.",  #
                )
        if "username" in user_data and user_data["username"] != db_user.username:  #
            if await User.filter(username=user_data["username"]).exists():  #
                raise HTTPException(  #
                    status_code=status.HTTP_400_BAD_REQUEST,  #
                    detail="Username already taken.",  #
                )

        for field, value in user_data.items():  #
            setattr(db_user, field, value)  #

        await db_user.save()  #
        return db_user  #

    async def delete_user(  #
        self,
        user_id: int,  #
    ) -> Optional[User]:  #
        db_user = await self.get_user_by_id(user_id)  #
        if not db_user:  #
            raise HTTPException(  #
                status_code=status.HTTP_404_NOT_FOUND,  #
                detail="User not found for deletion",  #
            )

        from app.models.users import (
            UserRead,
        )  # Avoid circular import if UserRead is used within the model file itself often

        deleted_user_data = UserRead.model_validate(db_user)  #

        await db_user.delete()  #
        return deleted_user_data  # type: ignore #

    async def create_user_session(  #
        self,
        user_id: int,
        refresh_token_value: str,  #
    ) -> Session:  #
        user = await User.get_or_none(id=user_id)  #
        if not user:  #
            raise HTTPException(  #
                status_code=status.HTTP_404_NOT_FOUND,  #
                detail="User not found for session creation",  #
            )

        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)  #
        expires_at_dt = datetime.now(timezone.utc) + expires_delta  #

        user_session = await Session.create(  #
            user_id=user.id,  #
            refresh_token=refresh_token_value,  #
            expires_at=expires_at_dt,  #
            is_active=True,  #
        )
        return user_session  #

    async def get_user_session_by_token(  #
        self,
        refresh_token_value: str,  #
    ) -> Optional[Session]:  #
        return await Session.get_or_none(refresh_token=refresh_token_value)  #

    async def deactivate_user_session(self, user_session: Session) -> Session:  #
        user_session.is_active = False  #
        await user_session.save()  #
        return user_session  #

    async def deactivate_all_user_sessions(self, user_id: int) -> int:  #
        active_sessions = await Session.filter(user_id=user_id, is_active=True).all()  #
        count = len(active_sessions)  #

        if count > 0:  #
            for session_to_deactivate in active_sessions:  #
                session_to_deactivate.is_active = False  #
                await session_to_deactivate.save()  #
        return count  #

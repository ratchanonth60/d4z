import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import get_password_hash  #

# Import models and security functions
from app.models.session import Session
from app.models.users import User, UserCreate, UserUpdate
from app.schemas.users import UserFilterParams
from app.services.utils import send_verification_email


class UserService:
    async def create_user(self, *, user_in: UserCreate) -> User:
        if not user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required."
            )

        if await User.filter(username=user_in.username).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered.",
            )
        if await User.filter(email=user_in.email).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        verification_token = secrets.token_urlsafe(32)
        token_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS or 1
        )

        db_user = await User.create(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            is_active=False,
            is_email_verified=False,
            email_verification_token=verification_token,
            email_verification_token_expires_at=token_expires_at,
            # is_superuser จะเป็น default False จาก model
        )

        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        verification_link = f"{base_url}/api/v1/auth/verify-email/{verification_token}"
        await send_verification_email(
            db_user.email, db_user.username, verification_link
        )  #

        return db_user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await User.get_or_none(id=user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await User.get_or_none(username=username)

    async def get_users_paginated(
        self,
        filters: UserFilterParams,
        page: int = 1,
        page_size: int = 10,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[User], int]:
        offset = (page - 1) * page_size
        query = User.all()

        if filters.username_contains:
            query = query.filter(username__icontains=filters.username_contains)
        if filters.email_equals:
            query = query.filter(email=filters.email_equals)
        if filters.is_active is not None:
            query = query.filter(is_active=filters.is_active)

        total_count = await query.count()

        if sort_by:
            if sort_order.lower() == "desc":
                sort_by = f"-{sort_by}"
            query = query.order_by(sort_by)

        users = await query.offset(offset).limit(page_size)
        return users, total_count

    async def verify_email_token(self, token: str) -> Optional[User]:
        # ค้นหาผู้ใช้ด้วย verification token ที่ระบุ
        user = await User.get_or_none(email_verification_token=token)

        if not user:
            # ไม่พบผู้ใช้ หรือ token ไม่ถูกต้อง
            return None

        if user.is_email_verified:
            # อีเมลนี้ถูกยืนยันแล้ว
            # คุณอาจจะต้องการให้ user ทราบ หรือจะ return user ไปเลยก็ได้
            return user

        # ตรวจสอบว่า token หมดอายุหรือไม่
        if (
            not user.email_verification_token_expires_at
            or user.email_verification_token_expires_at < datetime.now(timezone.utc)
        ):
            # Token หมดอายุแล้ว, ล้าง token และเวลาหมดอายุ
            user.email_verification_token = None
            user.email_verification_token_expires_at = None
            await user.save()  # บันทึกการเปลี่ยนแปลง
            return None  # คืนค่า None เพื่อบ่งบอกว่า token หมดอายุ

        # ถ้า token ถูกต้องและยังไม่หมดอายุ:
        user.is_active = True  # ตั้งค่าให้ user active
        user.is_email_verified = True  # ตั้งค่าว่าอีเมลถูกยืนยันแล้ว
        user.email_verification_token = None  # ล้าง token หลังจากใช้งานแล้ว
        user.email_verification_token_expires_at = None  # ล้างเวลาหมดอายุของ token
        await user.save()  # บันทึกการเปลี่ยนแปลงทั้งหมด

        return user

    async def update_user(
        self, *, user_id: int, user_in: UserUpdate
    ) -> Optional[User]:  # Return ORM model
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            # The get_user_by_id doesn't raise 404, so we check here
            # Or you can modify get_user_by_id to raise if not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for update",
            )

        user_data = user_in.model_dump(exclude_unset=True)
        if (
            "password" in user_data and user_data["password"]
        ):  # Check if password is not None or empty
            hashed_password = get_password_hash(user_data["password"])
            db_user.hashed_password = hashed_password
            del user_data["password"]  # Don't try to set plain password on model

        for field, value in user_data.items():
            setattr(db_user, field, value)

        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        return db_user

    async def delete_user(
        self, user_id: int
    ) -> Optional[User]:  # Return ORM model of deleted user
        db_user = await self.get_user_by_id(user_id)  # Get existing user ORM model
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for deletion",
            )

        await self.db_session.delete(db_user)
        await self.db_session.commit()
        # The db_user object is now expired, but contains the data of the deleted user.
        # You might choose to return a confirmation message or the object as it was.
        return db_user

    # --- UserSession (Refresh Token) Methods ---
    async def create_user_session(
        self, user_id: int, refresh_token_value: str
    ) -> Session:
        user = await User.get_or_none(id=user_id)
        if not user:
            # This should ideally not happen if user_id is valid
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for session creation",
            )

        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        expires_at_dt = datetime.now(timezone.utc) + expires_delta

        user_session = await Session.create(
            user=user,  # Pass the User object directly
            refresh_token=refresh_token_value,
            expires_at=expires_at_dt,
            is_active=True,
        )
        return user_session

    async def get_user_session_by_token(
        self, refresh_token_value: str
    ) -> Optional[Session]:
        return await Session.get_or_none(refresh_token=refresh_token_value)

    async def deactivate_user_session(self, user_session: Session) -> Session:
        user_session.is_active = False
        await user_session.save()  # Call .save() on the instance to persist changes
        return user_session

    async def deactivate_all_user_sessions(self, user_id: int) -> int:
        """Deactivates all active sessions for a given user_id and returns the count."""
        # First, fetch the sessions to be deactivated
        active_sessions = await Session.filter(user_id=user_id, is_active=True).all()
        count = len(active_sessions)

        if count > 0:
            # Update them in a loop or use a batch update if Tortoise supports it easily for this case.
            # For simplicity, a loop:
            for session_to_deactivate in active_sessions:
                session_to_deactivate.is_active = False
                await session_to_deactivate.save()
            # Alternative using .update() if you don't need the objects themselves
            # updated_rows = await Session.filter(user_id=user_id, is_active=True).update(is_active=False)
            # return updated_rows # This would return the number of updated rows

        return count

from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlmodel import asc, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash  #

# Import models and security functions
from app.models.users import User, UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):  # Constructor injection
        self.db_session = session

    async def create_user(
        self, *, user_in: UserCreate
    ) -> User:  # Return the ORM model User
        # Check if user already exists by username
        statement_username = select(User).where(User.username == user_in.username)
        existing_user_username_result = await self.db_session.exec(statement_username)
        existing_user_username = existing_user_username_result.first()
        if existing_user_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered.",
            )
        # Check if user already exists by email (if provided)
        if user_in.email:
            statement_email = select(User).where(User.email == user_in.email)
            existing_user_email_result = await self.db_session.exec(statement_email)
            existing_user_email = existing_user_email_result.first()
            if existing_user_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered.",
                )

        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump(
            exclude={"password"}
        )  # Use model_dump for Pydantic v2+

        # Create User ORM model instance
        db_user = User(**user_data, hashed_password=hashed_password)

        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        return db_user  # Return the User ORM model instance

    async def get_user_by_id(self, user_id: int) -> Optional[User]:  # Return ORM model
        user = await self.db_session.get(User, user_id)  # SQLModel's get method
        return user

    async def get_user_by_username(
        self, username: str
    ) -> Optional[User]:  # Return ORM model
        statement = select(User).where(User.username == username)
        result = await self.db_session.exec(statement)
        user = result.first()
        return user

    async def get_users_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        # Filter parameters
        username_contains: Optional[str] = None,
        email_equals: Optional[str] = None,
        is_active_status: Optional[bool] = None,
        # Sort parameters
        sort_by: Optional[str] = None,  # e.g., "username", "id"
        sort_order: str = "asc",  # "asc" or "desc"
    ) -> Tuple[List[User], int]:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        offset = (page - 1) * page_size

        # Base statements for data and count
        data_query = select(User)
        count_query = select(func.count()).select_from(User)

        # Apply filters
        conditions = []
        if username_contains:
            conditions.append(
                User.username.ilike(f"%{username_contains}%")
            )  # Case-insensitive like
        if email_equals:
            conditions.append(User.email == email_equals)
        if (
            is_active_status is not None
        ):  # Check for None explicitly because False is a valid value
            conditions.append(User.is_active == is_active_status)

        if conditions:
            for condition in conditions:
                data_query = data_query.where(condition)
                count_query = count_query.where(
                    condition
                )  # Apply same conditions to count query

        # Apply sorting (only to data query)
        if sort_by:
            column_to_sort = getattr(User, sort_by, None)
            if column_to_sort:  # Check if the sort_by field exists in User model
                if sort_order.lower() == "desc":
                    data_query = data_query.order_by(desc(column_to_sort))
                else:
                    data_query = data_query.order_by(asc(column_to_sort))
            else:
                # Optional: raise error or log if sort_by field is invalid
                print(f"Warning: Invalid sort_by field: {sort_by}")

        # Add pagination to data query
        data_query = data_query.offset(offset).limit(page_size)

        # Execute queries
        result_data = await self.db_session.exec(data_query)
        users = result_data.all()

        total_count_result = await self.db_session.exec(count_query)
        total_count = (
            total_count_result.one_or_none() or 0
        )  # Using one_or_none() as corrected

        return users, total_count  # type: ignore

    async def update_user(
        self, *, user_id: int, user_in: UserUpdate
    ) -> Optional[User]:  # Return ORM model
        db_user = await self.get_user_by_id(user_id)  # Get existing user ORM model
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

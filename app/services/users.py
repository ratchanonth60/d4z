import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import get_password_hash  #

# Import models and security functions
from app.models.session import Session
from app.models.users import User, UserCreate, UserRead, UserUpdate
from app.schemas.users import UserFilterParams
from app.services.utils import (
    task_send_password_reset_email,
    task_send_verification_email,
)

logger = logging.getLogger(__name__)


class UserService:
    async def create_user(self, *, user_in: UserCreate) -> User:
        """
        Creates a new user in the database.

        Validates input, checks for existing username/email, hashes the password,
        generates an email verification token, and queues an email verification task.
        The user is initially inactive and not email-verified.

        Args:
            user_in: UserCreate schema containing new user details (username, email, password, etc.).

        Raises:
            HTTPException: If email is not provided, or if username/email already exists,
                           or if a server error occurs during user creation.

        Returns:
            The created User ORM object.
        """
        if not user_in.email:
            # This check might be redundant if UserCreate model enforces email,
            # but good for service layer robustness.
            logger.warning("User creation attempt without an email address.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required.",
            )

        if await User.filter(username=user_in.username).exists():
            logger.warning(
                f"Registration attempt with existing username: {user_in.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered.",
            )
        if await User.filter(email=user_in.email).exists():
            logger.warning(f"Registration attempt with existing email: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        hashed_password = get_password_hash(user_in.password)
        verification_token = secrets.token_urlsafe(32)
        token_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
        )

        try:
            db_user = await User.create(
                username=user_in.username,
                email=user_in.email,
                full_name=user_in.full_name,
                hashed_password=hashed_password,
                is_active=False,  # User starts inactive
                is_email_verified=False,  # Email is not verified initially
                email_verification_token=verification_token,
                email_verification_token_expires_at=token_expires_at,
            )

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
            verification_link = (
                f"{base_url}/api/v1/auth/verify-email/{verification_token}"
            )

            task_send_verification_email.delay(
                email_to=str(db_user.email),
                username=db_user.username,
                verification_link=verification_link,
            )
            logger.info(
                f"User '{db_user.username}' created. Verification email task queued for '{db_user.email}'."
            )
            return db_user
        except Exception as e:
            logger.error(
                f"Database error during user creation for username '{user_in.username}': {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create user due to a server error.",
            )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by their unique ID.

        Args:
            user_id: The integer ID of the user.

        Returns:
            The User ORM object if found, otherwise None.
        """
        logger.debug(f"Fetching user by ID: {user_id}")
        return await User.get_or_none(id=user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by their unique username.

        Args:
            username: The username string.

        Returns:
            The User ORM object if found, otherwise None.
        """
        logger.debug(f"Fetching user by username: {username}")
        return await User.get_or_none(username=username)

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        """
        Retrieves a user by their unique email address.

        Args:
            email: The email address (validated by Pydantic's EmailStr).

        Returns:
            The User ORM object if found, otherwise None.
        """
        logger.debug(f"Fetching user by email: {email}")
        return await User.get_or_none(email=email)

    async def get_users_paginated(
        self,
        filters: UserFilterParams,
        page: int = 1,
        page_size: int = 10,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[User], int]:
        """
        Retrieves a paginated, filtered, and sorted list of users.

        Args:
            filters: UserFilterParams schema containing filter criteria.
            page: The page number to retrieve (1-indexed).
            page_size: The number of users per page.
            sort_by: Optional field name to sort users by (e.g., "username", "email").
            sort_order: Sort direction, "asc" or "desc".

        Returns:
            A tuple containing:
                - A list of User ORM objects for the current page.
                - The total count of users matching the filters.
        """
        logger.debug(
            f"Fetching paginated users: page={page}, size={page_size}, sort_by={sort_by}, order={sort_order}, filters={filters.model_dump()}"
        )
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
                sort_by = (
                    f"-{sort_by}"  # Tortoise ORM uses '-' prefix for descending order
                )
            query = query.order_by(sort_by)

        users = await query.offset(offset).limit(page_size)
        return users, total_count

    async def verify_email_token(self, token: str) -> Optional[User]:
        """
        Verifies an email verification token.

        If the token is valid and not expired, it marks the user's email as verified,
        activates the user account, and clears the token from the database.

        Args:
            token: The email verification token string.

        Returns:
            The updated User ORM object if verification is successful, otherwise None.
        """
        user = await User.get_or_none(email_verification_token=token)

        if not user:
            logger.warning(
                f"Email verification attempt with invalid or non-existent token: '{token[:10]}...'"
            )
            return None

        if user.is_email_verified:
            # User's email is already verified.
            logger.info(
                f"Email for user '{user.username}' already verified. Token: '{token[:10]}...'"
            )
            return user

        if (
            not user.email_verification_token_expires_at
            or user.email_verification_token_expires_at < datetime.now(timezone.utc)
        ):
            logger.warning(
                f"Email verification token expired for user '{user.username}'. Token: '{token[:10]}...'"
            )
            # Clear the expired token
            user.email_verification_token = None
            user.email_verification_token_expires_at = None
            await user.save(
                update_fields=[
                    "email_verification_token",
                    "email_verification_token_expires_at",
                ]
            )
            return None  # Token is invalid (expired)

        # Token is valid, verify email and activate user
        user.is_active = True
        user.is_email_verified = True
        user.email_verification_token = None  # Clear the token after use
        user.email_verification_token_expires_at = None
        await user.save(
            update_fields=[
                "is_active",
                "is_email_verified",
                "email_verification_token",
                "email_verification_token_expires_at",
            ]
        )
        logger.info(
            f"Email verified and user '{user.username}' activated successfully. Token: '{token[:10]}...'"
        )
        return user

    async def request_password_reset(self, email: EmailStr) -> bool:
        """
        Initiates a password reset process for a user.

        If an active user with the given email exists, a password reset token is generated,
        saved to the user, and a password reset email task is queued.

        Args:
            email: The email address of the user requesting a password reset.

        Returns:
            True if a password reset email was initiated (user found and active),
            False otherwise (user not found, inactive, or other reason).
            The API layer typically normalizes this to always return a generic success
            message to prevent email enumeration.
        """
        user = await self.get_user_by_email(email)
        if user and user.is_active:
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
            )
            user.password_reset_token = reset_token
            user.password_reset_token_expires_at = expires_at
            await user.save(
                update_fields=[
                    "password_reset_token",
                    "password_reset_token_expires_at",
                ]
            )

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
            # Note: "/reset-password-page" is likely a frontend route that will use the token
            reset_link = f"{base_url}/reset-password-page?token={reset_token}"

            task_send_password_reset_email.delay(
                email_to=str(user.email), username=user.username, reset_link=reset_link
            )
            logger.info(
                f"Password reset task queued for user '{user.username}' (email: '{user.email}')."
            )
            return True
        elif user and not user.is_active:
            logger.warning(f"Password reset request for inactive user: '{email}'.")
        else:  # User not found
            logger.info(f"Password reset request for non-existent email: '{email}'.")
        return False

    async def resend_verification_email(self, email: EmailStr) -> bool:
        """
        Resends an email verification link to a user whose email is not yet verified.

        Generates a new verification token and queues a new verification email task.
        The user's `is_active` status is set to False to ensure the new token is used.

        Args:
            email: The email address of the user.

        Returns:
            True if a new verification email was initiated (user found and not verified),
            False otherwise (user not found, already verified, or other reason).
        """
        user = await self.get_user_by_email(email)
        if user and not user.is_email_verified:
            # Consider adding rate limiting here to prevent abuse
            if (
                user.email_verification_token
                and user.email_verification_token_expires_at
                and user.email_verification_token_expires_at
                > datetime.now(timezone.utc)
            ):
                logger.info(
                    f"Resending verification email for '{email}'; existing token for user '{user.username}' is still technically valid but a new one will be issued."
                )

            new_verification_token = secrets.token_urlsafe(32)
            new_token_expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
            )
            user.email_verification_token = new_verification_token
            user.email_verification_token_expires_at = new_token_expires_at
            user.is_active = False  # Ensure user must verify with the new token
            await user.save(
                update_fields=[
                    "email_verification_token",
                    "email_verification_token_expires_at",
                    "is_active",
                ]
            )

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
            new_verification_link = (
                f"{base_url}/api/v1/auth/verify-email/{new_verification_token}"
            )

            send_verification_email_task.delay(
                email_to=str(user.email),
                username=user.username,
                verification_link=new_verification_link,
            )
            logger.info(
                f"New verification email task queued for '{email}' (user: '{user.username}')."
            )
            return True
        elif user and user.is_email_verified:
            logger.info(
                f"Verification email resend request for already verified user: '{email}'."
            )
        else:  # User not found
            logger.info(
                f"Verification email resend request for non-existent email: '{email}'."
            )
        return False

    async def reset_password(self, token: str, new_password: str) -> Optional[User]:
        """
        Resets a user's password using a valid password reset token.

        If the token is valid and not expired, the user's password is updated,
        the reset token is cleared, and the user is marked as active.

        Args:
            token: The password reset token string.
            new_password: The new password to set for the user.

        Returns:
            The updated User ORM object if password reset is successful, otherwise None.
        """
        user = await User.get_or_none(password_reset_token=token)

        if not user:
            logger.warning(
                f"Password reset attempt with invalid or non-existent token: '{token[:10]}...'"
            )
            return None

        if (
            not user.password_reset_token_expires_at
            or user.password_reset_token_expires_at < datetime.now(timezone.utc)
        ):
            logger.warning(
                f"Password reset token expired for user '{user.username}'. Token: '{token[:10]}...'"
            )
            # Clear the expired token
            user.password_reset_token = None
            user.password_reset_token_expires_at = None
            await user.save(
                update_fields=[
                    "password_reset_token",
                    "password_reset_token_expires_at",
                ]
            )
            return None  # Token is invalid (expired)

        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None  # Clear the token after use
        user.password_reset_token_expires_at = None
        user.is_active = True  # Ensure user is active after password reset
        await user.save(
            update_fields=[
                "hashed_password",
                "password_reset_token",
                "password_reset_token_expires_at",
                "is_active",
            ]
        )
        logger.info(f"Password reset successfully for user '{user.username}'.")
        return user

    async def update_user(
        self,
        *,
        user_id: int,
        user_in: UserUpdate,
    ) -> Optional[User]:
        """
        Updates a user's details in the database.

        Allows partial updates. If 'password' is provided, it will be hashed.
        Checks for username/email conflicts if these fields are being changed.

        Args:
            user_id: The ID of the user to update.
            user_in: UserUpdate schema containing fields to update.

        Raises:
            HTTPException: If user is not found, or if new username/email conflicts.

        Returns:
            The updated User ORM object, or None if user not found (though it raises HTTP 404).
        """
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            logger.warning(f"Attempt to update non-existent user with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for update",
            )

        user_data = user_in.model_dump(
            exclude_unset=True
        )  # Get only fields that were provided
        update_fields_list = []  # Keep track of fields that will be saved

        if not user_data:  # No fields provided to update
            logger.info(f"Update attempt for user ID {user_id} with no data provided.")
            return db_user  # Return user as is

        if "password" in user_data and user_data["password"]:
            db_user.hashed_password = get_password_hash(user_data["password"])
            update_fields_list.append("hashed_password")
            del user_data[
                "password"
            ]  # Remove from dict as 'password' is not a direct model field

        # Check for conflicts only if email/username is actually changing
        if "email" in user_data and user_data["email"] != db_user.email:
            if await User.filter(email=user_data["email"], id__not=db_user.id).exists():
                logger.warning(
                    f"Update conflict: Email '{user_data['email']}' already in use by another user. User ID: {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered by another user.",
                )
        if "username" in user_data and user_data["username"] != db_user.username:
            if await User.filter(
                username=user_data["username"], id__not=db_user.id
            ).exists():
                logger.warning(
                    f"Update conflict: Username '{user_data['username']}' already taken. User ID: {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken.",
                )

        # Apply other updates
        for field, value in user_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
                if (
                    field not in update_fields_list
                ):  # Add to list if not already (e.g. from password)
                    update_fields_list.append(field)

        if update_fields_list:
            # Filter update_fields_list to ensure only actual model fields are passed to save()
            valid_model_fields_to_update = [
                f for f in update_fields_list if hasattr(User, f)
            ]
            if valid_model_fields_to_update:
                await db_user.save(update_fields=valid_model_fields_to_update)
                logger.info(
                    f"User '{db_user.username}' (ID: {user_id}) updated successfully. Fields: {valid_model_fields_to_update}"
                )
            else:
                logger.info(
                    f"No valid model fields to update for user ID {user_id} after processing input."
                )
        else:
            logger.info(
                f"No fields were updated for user '{db_user.username}' (ID: {user_id})."
            )

        return db_user

    async def delete_user(
        self,
        user_id: int,
    ) -> Optional[UserRead]:
        """
        Deletes a user from the database.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            HTTPException: If the user with the given ID is not found.

        Returns:
            A UserRead Pydantic model of the deleted user's data if successful.
        """
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            logger.warning(f"Attempt to delete non-existent user with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for deletion",
            )

        # Create a Pydantic model from the ORM object before deleting
        deleted_user_data = UserRead.model_validate(db_user)

        await db_user.delete()
        logger.info(
            f"User '{deleted_user_data.username}' (ID: {user_id}) deleted successfully."
        )
        return deleted_user_data

    # --- Session Management Methods ---

    async def create_user_session(
        self,
        user_id: int,
        refresh_token_value: str,
    ) -> Session:
        """
        Creates a new session for a user, typically for refresh token management.

        Args:
            user_id: The ID of the user for whom the session is created.
            refresh_token_value: The string value of the refresh token.

        Raises:
            HTTPException: If the user with user_id is not found.

        Returns:
            The created Session ORM object.
        """
        user = await self.get_user_by_id(user_id)  # Re-fetch user to ensure exists
        if not user:
            logger.error(
                f"Attempt to create session for non-existent user ID: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # Should be rare if user_id is from a valid source
                detail="User not found for session creation",
            )

        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        expires_at_dt = datetime.now(timezone.utc) + expires_delta

        user_session = await Session.create(
            user_id=user.id,  # Use user.id to ensure it's the correct foreign key
            refresh_token=refresh_token_value,
            expires_at=expires_at_dt,
            is_active=True,  # New sessions are active
        )
        logger.info(
            f"Session created for user '{user.username}' (ID: {user_id}). Token hint: {refresh_token_value[:10]}..."
        )
        return user_session

    async def get_user_session_by_token(
        self,
        refresh_token_value: str,
    ) -> Optional[Session]:
        """
        Retrieves a user session by its refresh token value.

        Args:
            refresh_token_value: The refresh token string.

        Returns:
            The Session ORM object if found, otherwise None.
        """
        logger.debug(f"Fetching session by token hint: {refresh_token_value[:10]}...")
        return await Session.get_or_none(refresh_token=refresh_token_value)

    async def deactivate_user_session(self, user_session: Session) -> Session:
        """
        Deactivates a specific user session.

        Sets the `is_active` flag of the session to False.

        Args:
            user_session: The Session ORM object to deactivate.

        Returns:
            The updated (deactivated) Session ORM object.
        """
        if user_session.is_active:
            user_session.is_active = False
            await user_session.save(update_fields=["is_active"])
            logger.info(
                f"Session ID '{user_session.id}' for user_id '{user_session.user_id}' deactivated."
            )
        else:
            logger.info(
                f"Session ID '{user_session.id}' for user_id '{user_session.user_id}' was already inactive."
            )
        return user_session

    async def deactivate_all_user_sessions(self, user_id: int) -> int:
        """
        Deactivates all active sessions for a given user ID using a bulk update.

        Args:
            user_id: The ID of the user whose sessions are to be deactivated.

        Returns:
            The number of sessions that were deactivated.
        """
        # Optimized: Perform a bulk update. Tortoise's .update() returns the count of affected rows.
        count = await Session.filter(user_id=user_id, is_active=True).update(
            is_active=False
        )
        if count > 0:
            logger.info(
                f"Deactivated {count} active session(s) for user ID '{user_id}'."
            )
        else:
            logger.info(
                f"No active sessions found to deactivate for user ID '{user_id}'."
            )
        return count

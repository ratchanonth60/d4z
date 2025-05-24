import math
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_active_user, get_user_service

# Import ORM model and Pydantic schemas
from app.models.users import User, UserCreate, UserRead, UserUpdate
from app.schemas.base_response import (
    BaseResponse,
    PaginationInfo,
)
from app.schemas.users import SortOrder, UserFilterParams, UserSortByField
from app.services.users import UserService

router = APIRouter()


@router.get("/", response_model=BaseResponse[List[UserRead]])
async def read_users_paginated_filtered_sorted_api(
    user_service: Annotated[UserService, Depends(get_user_service)],
    filters: Annotated[UserFilterParams, Depends()],
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of items per page (max 100)"
    ),
    sort_by: Optional[UserSortByField] = Query(
        None, description="Field to sort by (e.g., 'username', 'id', 'email')."
    ),
    sort_order: SortOrder = Query(
        SortOrder.ASC, description="Sort order ('asc' or 'desc')."
    ),
    # current_user: Annotated[User, Depends(get_current_active_user)] # Covered by global dependency
):
    """
    ### Retrieve a list of users with pagination, filtering, and sorting.

    **Requires Authentication.**

    **Query Parameters:**
    - **Filtering (`UserFilterParams`):**
        - `username_contains` (Optional[str]): Filter by username containing this string (case-insensitive).
        - `email_equals` (Optional[str]): Filter by an exact email match.
        - `is_active` (Optional[bool]): Filter by user active status (`true` or `false`).
    - **Pagination:**
        - `page` (int, default: 1): Page number to retrieve.
        - `page_size` (int, default: 10, max: 100): Number of users per page.
    - **Sorting:**
        - `sort_by` (Optional[str], enum: "username", "id", "email"): Field to sort the results by.
        - `sort_order` (str, enum: "asc", "desc", default: "asc"): Direction of sorting.

    **Responses:**
    - `200 OK`: A list of users matching the criteria.
        Returns `BaseResponse` containing a list of `UserRead` objects and `PaginationInfo`.
    - `404 Not Found`: If the requested `page` is beyond the total number of pages for the given filters.
    """
    users_orm, total_items = await user_service.get_users_paginated(
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by.value if sort_by else None,  # Pass the string value of the enum
        sort_order=sort_order.value,  # Pass the string value of the enum
    )

    if not users_orm and page > 1 and total_items > 0:
        raise HTTPException(
            status_code=404, detail="Page not found for the given filters"
        )

    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    pagination_info = PaginationInfo(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    return BaseResponse(data=users_orm, pagination=pagination_info)


@router.post(
    "/", response_model=BaseResponse[UserRead], status_code=status.HTTP_201_CREATED
)
async def create_user_api(
    *,
    user_in: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_superuser)] # Example: if only superusers can create users
):
    """
    ### Create a new user.

    **Requires Authentication.** (Permissions might vary, e.g., superuser only)

    **Request Body (`UserCreate`):**
    - `username` (str, required): Unique username (max 50 chars).
    - `email` (Optional[str]): Unique email address (max 100 chars).
    - `password` (str, required): User's password.
    - `full_name` (Optional[str]): User's full name (max 100 chars).
    - `is_active` (bool, default: true): Whether the user is active.
    - `is_superuser` (bool, default: false): Whether the user has superuser privileges.

    **Responses:**
    - `201 Created`: User created successfully. Returns `BaseResponse` with the created `UserRead` data.
    - `400 Bad Request`: If the username or email already exists, or validation fails.
    """
    db_user = await user_service.create_user(user_in=user_in)
    return BaseResponse(message="User created successfully", data=db_user)


@router.get("/me", response_model=BaseResponse[UserRead])
async def read_current_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    ### Get current authenticated user's details.

    **Requires Authentication.**

    Provides information about the user whose JWT access token is currently being used.

    **Responses:**
    - `200 OK`: Details of the current user. Returns `BaseResponse` with `UserRead` data.
    - `400 Bad Request`: If the user associated with the token is inactive.
    - `401 Unauthorized`: If authentication fails.
    """
    return BaseResponse(data=current_user)


@router.get("/{user_id}", response_model=BaseResponse[UserRead])
async def read_user_by_id_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_user)] # Covered by global
):
    """
    ### Get a specific user by their ID.

    **Requires Authentication.**

    **Path Parameters:**
    - `user_id` (int, required): The ID of the user to retrieve.

    **Responses:**
    - `200 OK`: Details of the specified user. Returns `BaseResponse` with `UserRead` data.
    - `404 Not Found`: If no user exists with the given `user_id`.
    """
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return BaseResponse(data=db_user)


@router.patch("/{user_id}", response_model=BaseResponse[UserRead])
async def update_user_api(
    user_id: int,
    user_in: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_user)] # Ensure user can only update self or is superuser
):
    """
    ### Update a user's details.

    **Requires Authentication.** (Permissions might vary, e.g., user can update self, or superuser can update any)

    Allows partial updates to a user's information. Only include fields that need to be changed.

    **Path Parameters:**
    - `user_id` (int, required): The ID of the user to update.

    **Request Body (`UserUpdate` - all fields optional):**
    - `username` (Optional[str]): New username (max 50 chars).
    - `email` (Optional[str]): New email address (max 100 chars).
    - `full_name` (Optional[str]): New full name (max 100 chars).
    - `password` (Optional[str]): New password.
    - `is_active` (Optional[bool]): New active status.
    - `is_superuser` (Optional[bool]): New superuser status.

    **Responses:**
    - `200 OK`: User updated successfully. Returns `BaseResponse` with the updated `UserRead` data.
    - `404 Not Found`: If the user with the specified `user_id` does not exist.
    - `400 Bad Request`: If update data leads to a conflict (e.g., duplicate username/email if changed).
    """
    # Add permission checks here if necessary, e.g.:
    # if user_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    updated_user_orm = await user_service.update_user(user_id=user_id, user_in=user_in)
    return BaseResponse(message="User updated successfully", data=updated_user_orm)


@router.delete("/{user_id}", response_model=BaseResponse[UserRead])
async def delete_user_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_superuser)] # Example: if only superusers can delete
):
    """
    ### Delete a user.

    **Requires Authentication.** (Typically restricted to superusers or users deleting their own account)

    Permanently deletes a user from the system.

    **Path Parameters:**
    - `user_id` (int, required): The ID of the user to delete.

    **Responses:**
    - `200 OK`: User deleted successfully. Returns `BaseResponse` with the data of the `UserRead` that was deleted.
    - `404 Not Found`: If the user with the specified `user_id` does not exist.
    """
    # Add permission checks here if necessary, e.g.:
    # if user_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    deleted_user_orm = await user_service.delete_user(user_id=user_id)
    return BaseResponse(message="User deleted successfully", data=deleted_user_orm)

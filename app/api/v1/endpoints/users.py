import math
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.sqlmodel_setup import get_sqlmodel_session

# Import ORM model and Pydantic schemas
from app.models.users import UserCreate, UserRead, UserUpdate
from app.schemas.base_response import (
    BaseResponse,
    PaginationInfo,
)  # Import BaseResponse
from app.services.users import UserService

router = APIRouter()


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_sqlmodel_session)],
) -> UserService:
    return UserService(session=session)


@router.get("/", response_model=BaseResponse[List[UserRead]])
async def read_users_paginated_filtered_sorted_api(
    user_service: Annotated[UserService, Depends(get_user_service)],
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    # Filter parameters
    username_contains: Optional[str] = Query(
        None, description="Filter by username (case-insensitive, partial match)"
    ),
    email_equals: Optional[str] = Query(
        None, description="Filter by email (exact match)"
    ),
    is_active_status: Optional[bool] = Query(
        None, description="Filter by active status (true or false)"
    ),
    # Sort parameters
    sort_by: Optional[str] = Query(
        None, description="Field to sort by (e.g., 'username', 'id')"
    ),
    sort_order: str = Query(
        "asc", description="Sort order: 'asc' or 'desc'", pattern="^(asc|desc)$"
    ),
    # current_user: Annotated[User, Depends(get_current_active_user)] # TODO: Add auth
):
    """
    Retrieve users with pagination, filtering, and sorting.
    """
    users_orm, total_items = await user_service.get_users_paginated(
        page=page,
        page_size=page_size,
        username_contains=username_contains,
        email_equals=email_equals,
        is_active_status=is_active_status,
        sort_by=sort_by,
        sort_order=sort_order,
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
):
    db_user = await user_service.create_user(user_in=user_in)
    return BaseResponse(message="User created successfully", data=db_user)


@router.get("/{user_id}", response_model=BaseResponse[UserRead])  # response_model เปลี่ยน
async def read_user_by_id_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return BaseResponse(data=db_user)  # FastAPI จะแปลงเป็น UserRead


@router.patch("/{user_id}", response_model=BaseResponse[UserRead])
async def update_user_api(
    user_id: int,
    user_in: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    updated_user_orm = await user_service.update_user(user_id=user_id, user_in=user_in)
    return BaseResponse(message="User updated successfully", data=updated_user_orm)


@router.delete("/{user_id}", response_model=BaseResponse[UserRead])
async def delete_user_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    deleted_user_orm = await user_service.delete_user(user_id=user_id)
    return BaseResponse(
        message="User deleted successfully", data=deleted_user_orm
    )  # FastAPI จะแปลงเป็น UserRead


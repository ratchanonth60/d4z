import math
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_active_user, get_user_service

# Import ORM model and Pydantic schemas
from app.models.users import User, UserCreate, UserRead, UserUpdate
from app.schemas.base_response import (
    BaseResponse,
    PaginationInfo,
)  # Import BaseResponse
from app.schemas.users import SortOrder, UserFilterParams, UserSortByField
from app.services.users import UserService

router = APIRouter()


@router.get("/", response_model=BaseResponse[List[UserRead]])
async def read_users_paginated_filtered_sorted_api(
    user_service: Annotated[UserService, Depends(get_user_service)],
    # Filter parameters
    filters: Annotated[UserFilterParams, Depends()],
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    # Sort parameters
    sort_by: Optional[UserSortByField] = Query(None),
    sort_order: SortOrder = Query(SortOrder.ASC),
    # current_user: Annotated[User, Depends(get_current_active_user)] # TODO: Add auth
):
    """
    Retrieve users with pagination, filtering, and sorting.
    """
    users_orm, total_items = await user_service.get_users_paginated(
        filters=filters,
        page=page,
        page_size=page_size,
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


@router.get("/me", response_model=BaseResponse[UserRead])
async def read_current_user_me(
    # JWTBearer (global) ได้ทำงานไปแล้ว และตั้ง request.state.token_data
    # get_current_active_user จะใช้ token_data นั้นเพื่อดึง User object
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return BaseResponse(data=current_user)


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

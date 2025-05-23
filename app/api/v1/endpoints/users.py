from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.sqlmodel_setup import get_sqlmodel_session

# Import ORM model and Pydantic schemas
from app.models.users import UserCreate, UserRead, UserUpdate
from app.services.users import UserService  # Import the service class

router = APIRouter()


# Dependency to create UserService instance with a session for each request
def get_user_service(
    session: Annotated[AsyncSession, Depends(get_sqlmodel_session)],
) -> UserService:
    return UserService(session=session)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_api(  # Renamed to avoid conflict if you had user_service instance directly
    *,
    user_in: UserCreate,
    user_service: Annotated[
        UserService, Depends(get_user_service)
    ],  # Inject UserService
    # current_user: Annotated[User, Depends(get_current_active_superuser)] # TODO: Add auth
):
    """
    Create new user. The service will return the User ORM model.
    FastAPI will automatically convert it to UserRead based on response_model.
    """
    db_user = await user_service.create_user(user_in=user_in)
    # No need to manually convert to UserRead here if service returns ORM User model
    # and response_model=UserRead is set. FastAPI handles it.
    return db_user


@router.get("/", response_model=List[UserRead])
async def read_users_api(
    user_service: Annotated[UserService, Depends(get_user_service)],
    skip: int = 0,
    limit: int = 100,
    # current_user: Annotated[User, Depends(get_current_active_user)] # TODO: Add auth
):
    """
    Retrieve users. Service returns a list of User ORM models.
    FastAPI converts them to UserRead.
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_id_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_user)] # TODO: Add auth
):
    """
    Get a specific user by id.
    """
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    # Add permission checks here if needed
    return db_user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_api(
    user_id: int,
    user_in: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_user)] # TODO: Add auth
):
    """
    Update a user.
    """
    # The service method get_user_by_id called within update_user will handle not found
    updated_user = await user_service.update_user(user_id=user_id, user_in=user_in)
    # No need to check if updated_user is None if service raises HTTPException for not found
    return updated_user


@router.delete(
    "/{user_id}", response_model=UserRead
)  # Or return a different model/status
async def delete_user_api(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    # current_user: Annotated[User, Depends(get_current_active_superuser)] # TODO: Add auth
):
    """
    Delete a user.
    """
    # The service method get_user_by_id called within delete_user will handle not found
    deleted_user = await user_service.delete_user(user_id=user_id)
    # No need to check if deleted_user is None if service raises HTTPException for not found
    return deleted_user


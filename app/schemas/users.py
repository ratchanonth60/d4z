from typing import Optional

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=50)
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)


class UserCreate(UserBase):
    password: str  # Receive plain password


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

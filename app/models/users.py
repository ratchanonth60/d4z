# app/models/user_model.py
from typing import Optional

from sqlmodel import Field, SQLModel


# For database table
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


# For API input when creating a user
class UserCreate(SQLModel):
    username: str = Field(max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    password: str
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True
    is_superuser: bool = False


# For API output when reading a user
class UserRead(SQLModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool


# For API input when updating a user (all fields optional)
class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    password: Optional[str] = None  # For changing password
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

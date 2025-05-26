from typing import Optional

from pydantic import BaseModel, Field, model_validator
from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, index=True)
    email = fields.CharField(max_length=100, unique=True, index=True, null=True)
    full_name = fields.CharField(max_length=100, null=True)
    hashed_password = fields.CharField(
        max_length=255
    )  # Tortoise ไม่มี CharField ไม่จำกัดความยาวโดยตรง
    is_active = fields.BooleanField(default=False, index=True)
    is_superuser = fields.BooleanField(default=False)

    # Fields สำหรับ email verification
    email_verification_token = fields.CharField(
        max_length=128, null=True, unique=True, index=True
    )
    email_verification_token_expires_at = fields.DatetimeField(null=True)
    is_email_verified = fields.BooleanField(default=False)

    # Fields for password reset
    password_reset_token = fields.CharField(
        max_length=128, null=True, unique=True, index=True
    )
    password_reset_token_expires_at = fields.DatetimeField(null=True)

    sessions: fields.ReverseRelation["app.models.session.Session"]  # type: ignore
    # Relationships (จะนิยามใน Session model ด้วย)
    # sessions: fields.ReverseRelation["Session"] # หรือ fields.OneToManyRelation

    def __str__(self):
        return self.username


# For API input when creating a user
class UserCreate(BaseModel):
    username: str = Field(max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    password: str
    password_confirm: str
    full_name: Optional[str] = Field(default=None, max_length=100)

    # is_active: bool = True
    # is_superuser: bool = False
    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        pw1 = self.password
        pw2 = self.password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords do not match")
        return self


# For API output when reading a user
class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_email_verified: bool


# For API input when updating a user (all fields optional)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    password: Optional[str] = None  # For changing password
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str]


class TokenData(BaseModel):
    username: Optional[str] = None
    type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class PasswordResetRequestForm(BaseModel):
    email: EmailStr


class PasswordResetForm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
    new_password_confirm: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> "PasswordResetForm":
        pw1 = self.new_password
        pw2 = self.new_password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords do not match")
        return self


class ResendVerificationEmailRequestForm(BaseModel):  # New Schema
    email: EmailStr

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    phone: str | None = Field(None, min_length=10, max_length=15)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="customer", pattern=r"^(customer|manufacturer|corporate_admin|superadmin)$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().replace(" ", "")
            if not v.isdigit():
                raise ValueError("Phone must contain only digits")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserUpdateRole(BaseModel):
    role: str = Field(pattern=r"^(customer|manufacturer|corporate_admin|superadmin)$")


class UserUpdateStatus(BaseModel):
    is_active: bool
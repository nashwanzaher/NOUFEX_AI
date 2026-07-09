from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from noufex_ai.modules.tenants.schemas import TenantCreate


class SignupRequest(TenantCreate):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class UserRead(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(min_length=8, max_length=128)


class ValidateResetTokenRequest(BaseModel):
    token: str = Field(..., description="Password reset token to validate")

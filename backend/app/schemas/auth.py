"""
RouteIQ 2.0 - Authentication & User Schemas (Phase 2)
"""
from datetime import datetime
from enum import Enum
from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_email_format(email: str) -> str:
    cleaned = email.strip().lower()
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(pattern, cleaned):
        raise ValueError("Invalid email format. Expected example@domain.com")
    return cleaned


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"


class UserBase(BaseModel):
    email: str = Field(..., description="User login email")
    full_name: str = Field(..., min_length=2, max_length=128)
    role: UserRole = Field(default=UserRole.OPERATOR)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User login email")
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=128)
    organization_name: str = Field(..., min_length=2, max_length=128, description="New or existing org name")
    role: Optional[UserRole] = Field(default=UserRole.ADMIN, description="Initial registrant role")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_id: str
    organization_id: str
    role: str
    email: str
    full_name: str


class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=128)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

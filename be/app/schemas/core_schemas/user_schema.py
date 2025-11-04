"""
User Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.enums import UserRole as UserRoleEnum


class UserResponse(BaseModel):
    """User response model for API responses"""
    id: str
    username: str
    email: str
    full_name: str
    role: UserRoleEnum
    is_active: bool
    skill_points: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr


class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"


class MagicLinkToken(BaseModel):
    """Magic link token for authentication"""
    token: str


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    email: Optional[str] = None
    user_id: Optional[str] = None


class UserCreate:
    """User creation request"""
    username: str
    email: EmailStr
    full_name: str
    role: UserRoleEnum = UserRoleEnum.USER  # Default role is USER

    class Config:
        from_attributes = True
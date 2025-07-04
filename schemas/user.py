from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from models.user import UserTier, SubscriptionStatus
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: str
    tier: UserTier
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Dict[str, Any]

    class Config:
        from_attributes = True


# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Subscription schemas
class SubscriptionBase(BaseModel):
    tier: UserTier
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    payment_method_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    auto_renew: Optional[bool] = None
    payment_method_id: Optional[str] = None


class SubscriptionResponse(SubscriptionBase):
    id: str
    user_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

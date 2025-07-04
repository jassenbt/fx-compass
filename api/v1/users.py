from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from api.dependencies import get_current_active_user
from services.user_service import UserService
from schemas.user import (
    UserResponse, UserUpdate, SubscriptionCreate,
    SubscriptionResponse, SubscriptionUpdate
)
from models.user import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """Update current user information."""
    user_service = UserService(db)
    updated_user = await user_service.update_user(str(current_user.id), user_update)
    return updated_user


@router.post("/me/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
        subscription_data: SubscriptionCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """Create a new subscription for current user."""
    user_service = UserService(db)
    subscription = await user_service.create_subscription(str(current_user.id), subscription_data)
    return subscription


@router.get("/me/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """Get all subscriptions for current user."""
    user_service = UserService(db)
    subscriptions = await user_service.get_user_subscriptions(str(current_user.id))
    return subscriptions


@router.get("/me/subscription/active", response_model=SubscriptionResponse)
async def get_active_subscription(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """Get active subscription for current user."""
    user_service = UserService(db)
    subscription = await user_service.get_active_subscription(str(current_user.id))

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    return subscription

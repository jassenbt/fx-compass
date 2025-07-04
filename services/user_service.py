from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models.user import User, UserSubscription, UserTier, SubscriptionStatus
from schemas.user import UserCreate, UserUpdate, SubscriptionCreate, SubscriptionUpdate
from core.security import get_password_hash, verify_password
from datetime import datetime, timedelta
import uuid


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        stmt = select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
        result = await self.db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            timezone=user_data.timezone
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user information."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def create_subscription(self, user_id: str, subscription_data: SubscriptionCreate) -> UserSubscription:
        """Create a new subscription for user."""
        # Check if user exists
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Cancel existing active subscriptions
        stmt = update(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).values(status=SubscriptionStatus.CANCELLED)
        await self.db.execute(stmt)

        # Create new subscription
        end_date = datetime.utcnow() + timedelta(days=30)  # 30 days from now

        subscription = UserSubscription(
            user_id=user_id,
            tier=subscription_data.tier,
            status=SubscriptionStatus.ACTIVE,
            end_date=end_date,
            auto_renew=subscription_data.auto_renew,
            payment_method_id=subscription_data.payment_method_id
        )

        # Update user tier
        user.tier = subscription_data.tier

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def get_user_subscriptions(self, user_id: str) -> List[UserSubscription]:
        """Get all subscriptions for a user."""
        stmt = select(UserSubscription).where(UserSubscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_active_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """Get active subscription for a user."""
        stmt = select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
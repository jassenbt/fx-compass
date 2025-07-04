from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import create_access_token, create_refresh_token, verify_token
from services.user_service import UserService
from schemas.user import (
    UserCreate, UserResponse, LoginRequest, LoginResponse,
    RefreshTokenRequest, TokenResponse
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
        login_data: LoginRequest,
        db: AsyncSession = Depends(get_db)
):
    """Login user and return tokens."""
    user_service = UserService(db)
    user = await user_service.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
        refresh_data: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db)
):
    """Refresh access token."""
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, "refresh")
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)

"""
Authentication Endpoints
This module provides FastAPI endpoints for user authentication, including
magic link authentication, token verification, user information retrieval,
and token refresh functionality. It integrates with the AuthService for
handling authentication logic and user management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.schemas.core_schemas.user_schema import UserResponse, UserLogin, Token, MagicLinkToken
from app.services.auth_services.auth_service import AuthService
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/send-magic-link", status_code=status.HTTP_200_OK)
async def send_magic_link(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db_session)
):
    """Send magic link for passwordless authentication"""
    auth_service = AuthService(db)
    return await auth_service.send_magic_link(login_data.email)


@router.post("/verify-magic-link", response_model=Token)
async def verify_magic_link(
    token_data: MagicLinkToken,
    db: AsyncSession = Depends(get_db_session)
):
    """Verify magic link token and return access token"""
    auth_service = AuthService(db)
    return await auth_service.verify_magic_link(token_data.token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh access token"""
    from app.core.auth import create_access_token
    from datetime import timedelta
    
    # Update last login
    auth_service = AuthService(db)
    await auth_service.update_user_last_login(current_user.id)
    
    # Create new access token
    access_token_expires = timedelta(minutes=1000)  # Same as in auth.py
    access_token = create_access_token(
        data={"sub": current_user.email, "user_id": current_user.id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Logout user (marks user as logged out)"""
    auth_service = AuthService(db)
    await auth_service.logout_user(current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_active_user)
):
    """Validate if token is still valid"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

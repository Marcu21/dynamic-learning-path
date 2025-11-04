from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.core_schemas.user_schema import UserCreate, UserResponse, Token
from app.core.auth import create_access_token, generate_magic_link_token, verify_magic_link_token
from app.services.auth_services.email_service import email_service
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for handling authentication and user management"""

    def __init__(self, db: AsyncSession):
        self.db = db


    async def _generate_unique_username(self, base_username: str) -> str:
        """Generate a unique username by checking database"""
        username = base_username
        counter = 1

        while True:
            result = await self.db.execute(select(User).filter(User.username == username))
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}_{counter}"
            counter += 1

        return username

    async def send_magic_link(self, email: str) -> dict:
        """Send magic link for passwordless authentication"""
        try:
            # Check if user exists, create if not
            result = await self.db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                # Auto-create user for valid emails
                base_username = email.split('@')[0].replace('.', '_').replace('-', '_')
                username = await self._generate_unique_username(base_username)
                full_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=UserRole.USER
                )

                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                logger.info(f"Auto-created new user: {email} with username: {username}")

            # Generate magic link token
            token = generate_magic_link_token(email)

            # Send email
            email_sent = await email_service.send_magic_link(email, token)

            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send magic link email. Please try again."
                )

            return {
                "message": "Magic link sent successfully",
                "email": email,
                "user_exists": True
            }

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in send_magic_link: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in send_magic_link: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again."
            )

    async def verify_magic_link(self, token: str) -> Token:
        """Verify magic link token and return access token"""
        try:
            # Verify token and get email
            email = verify_magic_link_token(token)
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired magic link"
                )

            # Get user from database
            result = await self.db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Update user login info
            user.is_active = True
            user.last_login = datetime.now()
            await self.db.commit()

            # Create access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = create_access_token(
                data={"sub": user.email, "user_id": user.id},
                expires_delta=access_token_expires
            )

            logger.info(f"User {email} successfully authenticated via magic link")

            return Token(access_token=access_token, token_type="bearer")

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in verify_magic_link: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in verify_magic_link: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again."
            )

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        try:

            # Check if user already exists
            result = await self.db.execute(select(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ))
            existing_user = result.scalar_one_or_none()

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
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Successfully registered new user: {user_data.email}")
            return UserResponse.model_validate(user)

        except HTTPException:
            raise
        except IntegrityError as e:
            logger.error(f"Integrity error in register_user: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error in register_user: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in register_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again."
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await self.db.execute(select(User).filter(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_by_email: {str(e)}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = await self.db.execute(select(User).filter(User.username == username))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_by_username: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_by_id: {str(e)}")
            return None

    async def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.last_login = datetime.now()
                user.is_active = True
                await self.db.commit()
                logger.debug(f"Updated last login for user {user_id}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_user_last_login: {str(e)}")
            await self.db.rollback()
            return False

    async def logout_user(self, user_id: str) -> bool:
        """Mark user as logged out"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_active = False
                await self.db.commit()
                logger.info(f"User {user_id} logged out successfully")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error in logout_user: {str(e)}")
            await self.db.rollback()
            return False

    async def activate_user(self, user_id: str) -> bool:
        """Activate a user account (deprecated - kept for backward compatibility)"""
        logger.warning("activate_user method is deprecated")
        return await self.update_user_last_login(user_id)

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_active = False
                await self.db.commit()
                logger.info(f"User {user_id} deactivated successfully")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error in deactivate_user: {str(e)}")
            await self.db.rollback()
            return False

    async def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                old_role = user.role
                user.role = new_role
                await self.db.commit()
                logger.info(f"User {user_id} role updated from {old_role} to {new_role}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_user_role: {str(e)}")
            await self.db.rollback()
            return False

    async def is_user_active(self, user_id: str) -> bool:
        """Check if user is active"""
        try:
            result = await self.db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            return user.is_active if user else False
        except SQLAlchemyError as e:
            logger.error(f"Database error in is_user_active: {str(e)}")
            return False

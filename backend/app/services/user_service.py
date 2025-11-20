"""
User service layer for business logic.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email.

    Args:
        db: Database session
        email: User email

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user_data: User creation data

    Returns:
        Created user object

    Raises:
        ValueError: If email already exists
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError("Email already registered")

    # Create user with hashed password
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_created", user_id=user.id, email=user.email)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """
    Authenticate user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User object if authenticated, None otherwise
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    logger.info("user_authenticated", user_id=user.id, email=user.email)
    return user


async def update_user(
    db: AsyncSession, user: User, user_data: UserUpdate
) -> User:
    """
    Update user profile.

    Args:
        db: Database session
        user: User object to update
        user_data: Update data

    Returns:
        Updated user object
    """
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "preferences" and value:
            # Merge preferences
            current_prefs = user.preferences or {}
            current_prefs.update(value.model_dump() if hasattr(value, 'model_dump') else value)
            setattr(user, field, current_prefs)
        else:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info("user_updated", user_id=user.id)
    return user


async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> bool:
    """
    Change user password.

    Args:
        db: Database session
        user: User object
        current_password: Current password
        new_password: New password

    Returns:
        True if password changed successfully

    Raises:
        ValueError: If current password is incorrect
    """
    if not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")

    user.password_hash = hash_password(new_password)
    await db.commit()

    logger.info("password_changed", user_id=user.id)
    return True


async def delete_user(db: AsyncSession, user: User) -> bool:
    """
    Delete a user account.

    Args:
        db: Database session
        user: User object to delete

    Returns:
        True if deleted successfully
    """
    await db.delete(user)
    await db.commit()

    logger.info("user_deleted", user_id=user.id)
    return True

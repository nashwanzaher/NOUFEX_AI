from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import ValidationError, NotFoundError
from noufex_ai.modules.users.models import EmailVerification, PasswordReset, User

logger = logging.getLogger(__name__)


def _generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(48)


def _hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EmailService:
    """Service for email verification and password reset."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Email Verification ──────────────────────────────────────────

    async def create_verification(self, user_id: UUID) -> str:
        """Create an email verification token.

        Args:
            user_id: The user ID to create verification for

        Returns:
            The raw token (to be sent in email)
        """
        token = _generate_token()
        token_hash = _hash_token(token)

        verification = EmailVerification(
            user_id=user_id,
            token=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.session.add(verification)
        await self.session.flush()

        logger.info("Created email verification for user %s", user_id)
        return token

    async def verify_email(self, token: str) -> User:
        """Verify an email address using a token.

        Args:
            token: The verification token

        Returns:
            The verified user

        Raises:
            ValidationError: If token is invalid or expired
        """
        token_hash = _hash_token(token)

        result = await self.session.execute(
            select(EmailVerification).where(
                EmailVerification.token == token_hash,
                EmailVerification.used_at.is_(None),
            )
        )
        verification = result.scalar_one_or_none()

        if verification is None:
            raise ValidationError("Invalid or already used verification token")

        if verification.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Verification token has expired")

        # Mark as used
        verification.used_at = datetime.now(timezone.utc)
        self.session.add(verification)

        # Update user
        user = await self.session.get(User, verification.user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.is_verified = True
        self.session.add(user)
        await self.session.flush()

        logger.info("Email verified for user %s", user.id)
        return user

    async def resend_verification(self, email: str) -> str | None:
        """Resend verification email.

        Args:
            email: The user's email address

        Returns:
            The token if user needs verification, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Don't reveal if email exists
            return None

        if user.is_verified:
            return None

        return await self.create_verification(user.id)

    # ── Password Reset ──────────────────────────────────────────────

    async def create_password_reset(self, email: str) -> str | None:
        """Create a password reset token.

        Args:
            email: The user's email address

        Returns:
            The raw token if user exists, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Don't reveal if email exists
            return None

        token = _generate_token()
        token_hash = _hash_token(token)

        reset = PasswordReset(
            user_id=user.id,
            token=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.session.add(reset)
        await self.session.flush()

        logger.info("Created password reset for user %s", user.id)
        return token

    async def reset_password(self, token: str, new_password: str) -> User:
        """Reset a password using a token.

        Args:
            token: The reset token
            new_password: The new password

        Returns:
            The user with updated password

        Raises:
            ValidationError: If token is invalid or expired
        """
        from noufex_ai.modules.users.security import hash_password

        token_hash = _hash_token(token)

        result = await self.session.execute(
            select(PasswordReset).where(
                PasswordReset.token == token_hash,
                PasswordReset.used_at.is_(None),
            )
        )
        reset = result.scalar_one_or_none()

        if reset is None:
            raise ValidationError("Invalid or already used reset token")

        if reset.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Reset token has expired")

        # Mark as used
        reset.used_at = datetime.now(timezone.utc)
        self.session.add(reset)

        # Update user password
        user = await self.session.get(User, reset.user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.password_hash = hash_password(new_password)
        self.session.add(user)
        await self.session.flush()

        logger.info("Password reset for user %s", user.id)
        return user

    async def validate_reset_token(self, token: str) -> bool:
        """Validate a password reset token without using it.

        Args:
            token: The reset token

        Returns:
            True if token is valid
        """
        token_hash = _hash_token(token)

        result = await self.session.execute(
            select(PasswordReset).where(
                PasswordReset.token == token_hash,
                PasswordReset.used_at.is_(None),
            )
        )
        reset = result.scalar_one_or_none()

        if reset is None:
            return False

        return reset.expires_at >= datetime.now(timezone.utc)

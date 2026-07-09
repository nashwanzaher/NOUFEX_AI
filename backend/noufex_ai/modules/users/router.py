from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request, status
from sqlalchemy import select

from noufex_ai.deps import CurrentUserDep, SessionDep
from noufex_ai.exceptions import UnauthorizedError
from noufex_ai.modules.users.models import RefreshToken, User
from noufex_ai.modules.users.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserRead,
    ValidateResetTokenRequest,
    VerifyEmailRequest,
)
from noufex_ai.modules.users.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from noufex_ai.modules.users.service import UserService
from noufex_ai.modules.users.email_service import EmailService

router = APIRouter()


def _default_scopes(role: str) -> list[str]:
    base = ["chat:read", "chat:write", "agents:read"]
    if role in {"owner", "admin"}:
        base += [
            "agents:write",
            "rag:write",
            "billing:read",
            "billing:write",
            "admin:read",
            "admin:write",
            "computer:read",
            "computer:write",
            "computer:execute",
            "browser:read",
            "browser:write",
            "browser:execute",
            "design:generate",
        ]
    return base


async def _issue_tokens(
    user: User, *, user_agent: str | None, ip: str | None, session
) -> TokenResponse:
    scopes = _default_scopes(user.role)
    access, expires_in = create_access_token(
        sub=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role,
        scopes=scopes,
    )
    refresh, expires_at = create_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            user_agent=user_agent,
            ip_address=ip,
            expires_at=expires_at,
        )
    )
    await session.flush()
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest, request: Request, session: SessionDep
) -> TokenResponse:
    service = UserService(session)
    _, user = await service.signup(payload)

    # Send verification email
    email_service = EmailService(session)
    verification_token = await email_service.create_verification(user.id)
    # TODO: Send email with verification_token
    # For now, log it
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Email verification token for %s: %s", user.email, verification_token)

    return await _issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        session=session,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, session: SessionDep
) -> TokenResponse:
    service = UserService(session)
    user = await service.authenticate(email=str(payload.email), password=payload.password)
    return await _issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        session=session,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest, request: Request, session: SessionDep
) -> TokenResponse:
    hashed = hash_refresh_token(payload.refresh_token)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )
    record = result.scalar_one_or_none()
    if record is None or record.revoked_at is not None:
        raise UnauthorizedError("Invalid refresh token")
    if record.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expired")

    record.revoked_at = datetime.now(timezone.utc)
    session.add(record)

    user = await session.get(User, record.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not active")

    return await _issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        session=session,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, session: SessionDep) -> None:
    if not payload.refresh_token:
        return
    hashed = hash_refresh_token(payload.refresh_token)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )
    record = result.scalar_one_or_none()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        session.add(record)
        await session.flush()


@router.get("/me", response_model=UserRead)
async def get_me(session: SessionDep, user: CurrentUserDep) -> UserRead:
    db_user = await session.get(User, user.id)
    if db_user is None:
        raise UnauthorizedError("User not found")
    return UserRead.model_validate(db_user)


# ── Email Verification ─────────────────────────────────────────────

@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest, session: SessionDep
) -> dict:
    email_service = EmailService(session)
    user = await email_service.verify_email(payload.token)
    return {"message": "Email verified successfully", "user_id": str(user.id)}


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    payload: ResendVerificationRequest, session: SessionDep
) -> dict:
    email_service = EmailService(session)
    token = await email_service.resend_verification(str(payload.email))
    if token:
        # TODO: Send email with token
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Resent verification token for %s: %s", payload.email, token)
    # Always return success to prevent email enumeration
    return {"message": "If the email exists and is unverified, a verification link has been sent"}


# ── Password Reset ─────────────────────────────────────────────────

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest, session: SessionDep
) -> dict:
    email_service = EmailService(session)
    token = await email_service.create_password_reset(str(payload.email))
    if token:
        # TODO: Send email with token
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Password reset token for %s: %s", payload.email, token)
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/validate-reset-token")
async def validate_reset_token(
    payload: ValidateResetTokenRequest, session: SessionDep
) -> dict:
    email_service = EmailService(session)
    is_valid = await email_service.validate_reset_token(payload.token)
    return {"valid": is_valid}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest, session: SessionDep
) -> dict:
    email_service = EmailService(session)
    user = await email_service.reset_password(payload.token, payload.new_password)
    return {"message": "Password reset successfully", "user_id": str(user.id)}

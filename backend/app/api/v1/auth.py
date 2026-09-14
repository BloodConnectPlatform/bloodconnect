from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.security import create_verification_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    SendOTPRequest,
    SendOTPResponse,
    TokenResponse,
    UserResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.services.auth_service import auth_service
from app.services.otp_service import otp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP to mobile number",
    description="Generates, hashes, and dispatches an OTP to the given mobile number. Enforces cooldown and rate limits.",
    status_code=status.HTTP_200_OK
)
async def send_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await otp_service.send_otp(
        db=db,
        mobile=request.mobile,
        purpose=request.purpose or "LOGIN"
    )
    return result


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Verify OTP",
    description="Validates a submitted OTP for a mobile number and issues a verification token for registration.",
    status_code=status.HTTP_200_OK
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    success, message, _ = await otp_service.verify_otp(
        db=db,
        mobile=request.mobile,
        otp=request.otp
    )

    # Check if this mobile is already registered
    stmt = select(User).where(User.mobile == request.mobile)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    verification_token = create_verification_token(request.mobile)

    return VerifyOTPResponse(
        success=True,
        message=message,
        verification_token=verification_token,
        is_registered=existing_user is not None,
        role=existing_user.role if existing_user else None
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with mobile OTP",
    description="Authenticates an existing user using their verified mobile number and OTP, returning JWT tokens.",
    status_code=status.HTTP_200_OK
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.login_with_otp(
        db=db,
        mobile=request.mobile,
        otp=request.otp
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generates a new access token and refresh token using a valid refresh token.",
    status_code=status.HTTP_200_OK
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh_tokens(
        db=db,
        refresh_token_str=request.refresh_token
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns identity and role information for the currently authenticated user.",
    status_code=status.HTTP_200_OK
)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        mobile=current_user.mobile,
        role=current_user.role,
        is_active=current_user.is_active,
        has_donor_profile=current_user.donor_profile is not None,
        created_at=current_user.created_at
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Logs out the currently authenticated user session.",
    status_code=status.HTTP_200_OK
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    return LogoutResponse(
        success=True,
        message="User logged out successfully."
    )

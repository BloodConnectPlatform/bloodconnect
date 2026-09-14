import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse
from app.services.otp_service import otp_service


class AuthService:
    async def login_with_otp(
        self, db: AsyncSession, mobile: str, otp: str
    ) -> TokenResponse:
        """Authenticate an existing user via verified mobile OTP."""
        # 1. Verify OTP
        await otp_service.verify_otp(db, mobile, otp)

        # 2. Look up user by mobile
        stmt = select(User).where(User.mobile == mobile)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found for this mobile number. Please register first."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support."
            )

        # 3. Create tokens
        token_payload = {
            "sub": str(user.id),
            "mobile": user.mobile,
            "role": user.role.value
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        has_donor = user.donor_profile is not None

        user_response = UserResponse(
            id=user.id,
            name=user.name,
            mobile=user.mobile,
            role=user.role,
            is_active=user.is_active,
            has_donor_profile=has_donor,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response
        )

    async def refresh_tokens(
        self, db: AsyncSession, refresh_token_str: str
    ) -> TokenResponse:
        """Issue a new access token and refresh token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token_str)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Provided token is not a refresh token."
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )

        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed user ID in token."
            )

        stmt = select(User).where(User.id == user_uuid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or no longer exists."
            )

        token_payload = {
            "sub": str(user.id),
            "mobile": user.mobile,
            "role": user.role.value
        }
        new_access_token = create_access_token(token_payload)
        new_refresh_token = create_refresh_token(token_payload)

        has_donor = user.donor_profile is not None

        user_response = UserResponse(
            id=user.id,
            name=user.name,
            mobile=user.mobile,
            role=user.role,
            is_active=user.is_active,
            has_donor_profile=has_donor,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=user_response
        )


auth_service = AuthService()

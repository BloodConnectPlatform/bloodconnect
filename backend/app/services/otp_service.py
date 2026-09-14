from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_otp, hash_otp, verify_otp_hash, create_verification_token
from app.models.otp import OtpVerification
from app.services.sms import get_sms_provider


class OTPService:
    def __init__(self):
        self.sms_provider = get_sms_provider()

    async def send_otp(self, db: AsyncSession, mobile: str, purpose: str = "LOGIN") -> dict:
        """Generate, hash, store, and dispatch an OTP to a mobile number with rate limiting."""
        now = datetime.now(timezone.utc)

        # 1. Cooldown check (e.g. 60 seconds)
        stmt_latest = (
            select(OtpVerification)
            .where(OtpVerification.mobile == mobile)
            .order_by(OtpVerification.created_at.desc())
            .limit(1)
        )
        result_latest = await db.execute(stmt_latest)
        latest_otp = result_latest.scalar_one_or_none()

        if latest_otp:
            # Ensure timezone awareness comparison
            latest_created = latest_otp.created_at
            if latest_created.tzinfo is None:
                latest_created = latest_created.replace(tzinfo=timezone.utc)
            
            elapsed = (now - latest_created).total_seconds()
            if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {remaining} second(s) before requesting another OTP."
                )

        # 2. Hourly rate limit check (e.g. max 5 OTPs per hour)
        one_hour_ago = now - timedelta(hours=1)
        stmt_count = (
            select(func.count(OtpVerification.id))
            .where(
                OtpVerification.mobile == mobile,
                OtpVerification.created_at >= one_hour_ago
            )
        )
        result_count = await db.execute(stmt_count)
        hourly_count = result_count.scalar() or 0
        if hourly_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests for this mobile number. Please try again in an hour."
            )

        # 3. Generate & Hash OTP
        otp_code = generate_otp(6)
        otp_hashed = hash_otp(mobile, otp_code)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        otp_record = OtpVerification(
            mobile=mobile,
            otp_hash=otp_hashed,
            expires_at=expires_at,
            attempts=0,
            created_at=now
        )
        db.add(otp_record)
        await db.commit()
        await db.refresh(otp_record)

        # 4. Dispatch SMS
        sms_message = (
            f"Your Blood Connect verification code is {otp_code}. "
            f"Valid for {settings.OTP_EXPIRE_MINUTES} minutes. Do not share this code with anyone."
        )
        await self.sms_provider.send_sms(mobile, sms_message)

        return {
            "success": True,
            "message": "OTP sent successfully.",
            "expires_in_seconds": settings.OTP_EXPIRE_MINUTES * 60,
            "cooldown_seconds": settings.OTP_RESEND_COOLDOWN_SECONDS,
            "debug_otp": otp_code if settings.DEBUG else None
        }

    async def verify_otp(
        self, db: AsyncSession, mobile: str, otp: str
    ) -> Tuple[bool, str, OtpVerification]:
        """Verify the user-provided OTP against the latest active hash."""
        now = datetime.now(timezone.utc)

        stmt = (
            select(OtpVerification)
            .where(
                OtpVerification.mobile == mobile,
                OtpVerification.verified_at.is_(None)
            )
            .order_by(OtpVerification.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending OTP request found for this mobile number. Please request a new OTP."
            )

        # Check maximum attempts
        if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new OTP."
            )

        # Check expiration
        record_expires = otp_record.expires_at
        if record_expires.tzinfo is None:
            record_expires = record_expires.replace(tzinfo=timezone.utc)
        if now > record_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new OTP."
            )

        # Verify hash
        is_valid = verify_otp_hash(mobile, otp, otp_record.otp_hash)
        if not is_valid:
            otp_record.attempts += 1
            await db.commit()
            remaining = settings.OTP_MAX_ATTEMPTS - otp_record.attempts
            if remaining > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid OTP. {remaining} attempt(s) remaining."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP. Maximum attempts reached. Please request a new OTP."
                )

        # Mark as verified
        otp_record.verified_at = now
        await db.commit()
        await db.refresh(otp_record)

        return True, "OTP verified successfully.", otp_record


otp_service = OTPService()

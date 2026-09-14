from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, UUIDPrimaryKeyMixin


class OtpVerification(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "otp_verifications"

    mobile: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("ix_otp_mobile_created_at", "mobile", "created_at"),
    )

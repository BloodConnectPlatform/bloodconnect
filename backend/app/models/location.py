from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.donor import DonorProfile
    from app.models.blood_request import BloodRequest


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), default="Coimbatore", nullable=False)
    state: Mapped[str] = mapped_column(String(100), default="Tamil Nadu", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    donors: Mapped[List["DonorProfile"]] = relationship("DonorProfile", back_populates="location")
    blood_requests: Mapped[List["BloodRequest"]] = relationship("BloodRequest", back_populates="location")

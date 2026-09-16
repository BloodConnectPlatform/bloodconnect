import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import BloodGroup, RequestStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.donor import DonorProfile
    from app.models.location import Location


class BloodRequest(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "blood_requests"

    requester_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    blood_group: Mapped[BloodGroup] = mapped_column(
        Enum(BloodGroup, name="blood_group_enum", native_enum=False),
        nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False
    )
    patient_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    hospital_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status_enum", native_enum=False),
        default=RequestStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="sent_requests",
        lazy="selectin"
    )
    donor: Mapped["DonorProfile"] = relationship(
        "DonorProfile",
        foreign_keys=[donor_id],
        back_populates="received_requests",
        lazy="selectin"
    )
    location: Mapped["Location"] = relationship("Location", back_populates="blood_requests", lazy="selectin")

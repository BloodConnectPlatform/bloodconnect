import uuid
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BloodGroup

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.location import Location
    from app.models.blood_request import BloodRequest
    from app.models.report import Report


class DonorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "donor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[BloodGroup] = mapped_column(
        Enum(BloodGroup, name="blood_group_enum", native_enum=False),
        nullable=False,
        index=True
    )
    location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    is_otp_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    contact_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="donor_profile", lazy="selectin")
    location: Mapped["Location"] = relationship("Location", back_populates="donors", lazy="selectin")
    received_requests: Mapped[List["BloodRequest"]] = relationship(
        "BloodRequest",
        foreign_keys="[BloodRequest.donor_id]",
        back_populates="donor",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="[Report.donor_id]",
        back_populates="donor",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "ix_donors_search_composite",
            "blood_group",
            "location_id",
            "is_available",
            "is_active",
            "is_otp_verified"
        ),
    )

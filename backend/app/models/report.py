import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import ReportReason, ReportStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.donor import DonorProfile


class Report(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reports"

    donor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reason: Mapped[ReportReason] = mapped_column(
        Enum(ReportReason, name="report_reason_enum", native_enum=False),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", native_enum=False),
        default=ReportStatus.OPEN,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    donor: Mapped["DonorProfile"] = relationship(
        "DonorProfile",
        foreign_keys=[donor_id],
        back_populates="reports",
        lazy="selectin"
    )
    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reports_filed",
        lazy="selectin"
    )

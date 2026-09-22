from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.donor import DonorProfile
    from app.models.blood_request import BloodRequest
    from app.models.report import Report
    from app.models.notification import Notification
    from app.models.admin_action import AdminAction
    from app.models.whatsapp_login_token import WhatsAppLoginToken


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.REQUESTER,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    donor_profile: Mapped[Optional["DonorProfile"]] = relationship(
        "DonorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    sent_requests: Mapped[List["BloodRequest"]] = relationship(
        "BloodRequest",
        foreign_keys="[BloodRequest.requester_id]",
        back_populates="requester",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reports_filed: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="[Report.reporter_id]",
        back_populates="reporter",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    admin_actions: Mapped[List["AdminAction"]] = relationship(
        "AdminAction",
        foreign_keys="[AdminAction.admin_id]",
        back_populates="admin",
        lazy="selectin"
    )
    whatsapp_login_tokens: Mapped[List["WhatsAppLoginToken"]] = relationship(
        "WhatsAppLoginToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

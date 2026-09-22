from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class WhatsAppLoginToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whatsapp_login_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    whatsapp_phone: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    request_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    request_user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    redeemed_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    redeemed_user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="whatsapp_login_tokens", lazy="selectin")

    __table_args__ = (
        Index("ix_wa_token_phone_created_at", "whatsapp_phone", "created_at"),
        Index("ix_wa_token_hash_used_at", "token_hash", "used_at"),
    )

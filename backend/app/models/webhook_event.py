from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import WebhookEventStatus


class WebhookEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "webhook_events"

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus, name="webhook_event_status_enum", native_enum=False),
        default=WebhookEventStatus.PROCESSED,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

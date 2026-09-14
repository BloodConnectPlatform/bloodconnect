import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    """Base declarative class for all models."""
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Generate default tablename from class name in lowercase plural style
        name = cls.__name__
        # Convert CamelCase to snake_case
        snake = "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
        return snake if snake.endswith("s") else f"{snake}s"


class TimestampMixin:
    """Mixin for models requiring created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class UUIDPrimaryKeyMixin:
    """Mixin for models using UUID as primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

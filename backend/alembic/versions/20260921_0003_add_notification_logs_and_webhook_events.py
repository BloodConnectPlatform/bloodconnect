"""Add notification_logs and webhook_events tables

Revision ID: 20260921_0003
Revises: 20260917_0002
Create Date: 2026-09-21 10:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260921_0003"
down_revision: Union[str, None] = "20260917_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. notification_logs table
    if "notification_logs" not in existing_tables:
        op.create_table(
            "notification_logs",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
            sa.Column("mobile", sa.String(length=15), nullable=False),
            sa.Column("channel", sa.String(length=20), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("provider_message_id", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_notification_logs_user_id", "notification_logs", ["user_id"])
        op.create_index("ix_notification_logs_mobile", "notification_logs", ["mobile"])
        op.create_index("ix_notification_logs_channel", "notification_logs", ["channel"])
        op.create_index("ix_notification_logs_event_type", "notification_logs", ["event_type"])
        op.create_index("ix_notification_logs_provider_message_id", "notification_logs", ["provider_message_id"])
        op.create_index("ix_notification_logs_status", "notification_logs", ["status"])
        op.create_index("ix_notification_logs_created_at", "notification_logs", ["created_at"])

    # 2. webhook_events table
    if "webhook_events" not in existing_tables:
        op.create_table(
            "webhook_events",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("event_id", sa.String(length=255), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PROCESSED"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id"),
        )
        op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"])
        op.create_index("ix_webhook_events_event_type", "webhook_events", ["event_type"])
        op.create_index("ix_webhook_events_status", "webhook_events", ["status"])
        op.create_index("ix_webhook_events_created_at", "webhook_events", ["created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "webhook_events" in existing_tables:
        op.drop_table("webhook_events")
    if "notification_logs" in existing_tables:
        op.drop_table("notification_logs")

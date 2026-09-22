"""Add whatsapp_login_tokens table

Revision ID: 20260922_0004
Revises: 20260921_0003
Create Date: 2026-09-22 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260922_0004"
down_revision: Union[str, None] = "20260921_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "whatsapp_login_tokens" not in existing_tables:
        op.create_table(
            "whatsapp_login_tokens",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("whatsapp_phone", sa.String(length=15), nullable=False),
            sa.Column("token_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("request_ip", sa.String(length=50), nullable=True),
            sa.Column("request_user_agent", sa.String(length=255), nullable=True),
            sa.Column("redeemed_ip", sa.String(length=50), nullable=True),
            sa.Column("redeemed_user_agent", sa.String(length=255), nullable=True),
            sa.Column("request_metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index("ix_whatsapp_login_tokens_user_id", "whatsapp_login_tokens", ["user_id"])
        op.create_index("ix_whatsapp_login_tokens_whatsapp_phone", "whatsapp_login_tokens", ["whatsapp_phone"])
        op.create_index("ix_whatsapp_login_tokens_token_hash", "whatsapp_login_tokens", ["token_hash"])
        op.create_index("ix_whatsapp_login_tokens_created_at", "whatsapp_login_tokens", ["created_at"])
        op.create_index("ix_whatsapp_login_tokens_expires_at", "whatsapp_login_tokens", ["expires_at"])
        op.create_index("ix_whatsapp_login_tokens_used_at", "whatsapp_login_tokens", ["used_at"])
        op.create_index("ix_wa_token_phone_created_at", "whatsapp_login_tokens", ["whatsapp_phone", "created_at"])
        op.create_index("ix_wa_token_hash_used_at", "whatsapp_login_tokens", ["token_hash", "used_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "whatsapp_login_tokens" in existing_tables:
        op.drop_table("whatsapp_login_tokens")

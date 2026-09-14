"""Initial database schema for Blood Connect

Revision ID: 20260914_0001
Revises: 
Create Date: 2026-09-14 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260914_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_locations_name", "locations", ["name"])

    # 2. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("mobile", sa.String(length=15), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="REQUESTER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mobile"),
    )
    op.create_index("ix_users_mobile", "users", ["mobile"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # 3. donor_profiles table
    op.create_table(
        "donor_profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("blood_group", sa.String(length=10), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("is_otp_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("contact_consent", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_donor_profiles_user_id", "donor_profiles", ["user_id"])
    op.create_index("ix_donor_profiles_blood_group", "donor_profiles", ["blood_group"])
    op.create_index("ix_donor_profiles_location_id", "donor_profiles", ["location_id"])
    op.create_index("ix_donor_profiles_is_otp_verified", "donor_profiles", ["is_otp_verified"])
    op.create_index("ix_donor_profiles_is_available", "donor_profiles", ["is_available"])
    op.create_index("ix_donor_profiles_is_active", "donor_profiles", ["is_active"])
    op.create_index(
        "ix_donors_search_composite",
        "donor_profiles",
        ["blood_group", "location_id", "is_available", "is_active", "is_otp_verified"]
    )

    # 4. otp_verifications table
    op.create_table(
        "otp_verifications",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("mobile", sa.String(length=15), nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_verifications_mobile", "otp_verifications", ["mobile"])
    op.create_index("ix_otp_verifications_expires_at", "otp_verifications", ["expires_at"])
    op.create_index("ix_otp_verifications_created_at", "otp_verifications", ["created_at"])
    op.create_index("ix_otp_mobile_created_at", "otp_verifications", ["mobile", "created_at"])

    # 5. blood_requests table
    op.create_table(
        "blood_requests",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("requester_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("donor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("blood_group", sa.String(length=10), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["donor_id"], ["donor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_blood_requests_requester_id", "blood_requests", ["requester_id"])
    op.create_index("ix_blood_requests_donor_id", "blood_requests", ["donor_id"])
    op.create_index("ix_blood_requests_status", "blood_requests", ["status"])
    op.create_index("ix_blood_requests_created_at", "blood_requests", ["created_at"])

    # 6. reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("donor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reporter_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["donor_id"], ["donor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_donor_id", "reports", ["donor_id"])
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_created_at", "reports", ["created_at"])

    # 7. admin_actions table
    op.create_table(
        "admin_actions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("admin_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_actions_admin_id", "admin_actions", ["admin_id"])
    op.create_index("ix_admin_actions_action", "admin_actions", ["action"])
    op.create_index("ix_admin_actions_target_type", "admin_actions", ["target_type"])
    op.create_index("ix_admin_actions_target_id", "admin_actions", ["target_id"])
    op.create_index("ix_admin_actions_created_at", "admin_actions", ["created_at"])

    # 8. notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("admin_actions")
    op.drop_table("reports")
    op.drop_table("blood_requests")
    op.drop_table("otp_verifications")
    op.drop_table("donor_profiles")
    op.drop_table("users")
    op.drop_table("locations")

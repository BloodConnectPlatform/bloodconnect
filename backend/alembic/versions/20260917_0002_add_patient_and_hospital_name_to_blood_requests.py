"""Add patient_name and hospital_name to blood_requests

Revision ID: 20260917_0002
Revises: 20260914_0001
Create Date: 2026-09-17 00:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260917_0002"
down_revision: Union[str, None] = "20260914_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "blood_requests",
        sa.Column("patient_name", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "blood_requests",
        sa.Column("hospital_name", sa.String(length=200), nullable=True)
    )
    op.create_index("ix_blood_requests_patient_name", "blood_requests", ["patient_name"])


def downgrade() -> None:
    op.drop_index("ix_blood_requests_patient_name", table_name="blood_requests")
    op.drop_column("blood_requests", "hospital_name")
    op.drop_column("blood_requests", "patient_name")

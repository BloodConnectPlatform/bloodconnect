"""Seed and activate predefined locations in production PostgreSQL database

Revision ID: 20260922_0005
Revises: 20260922_0004
Create Date: 2026-09-22 19:10:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260922_0005"
down_revision: Union[str, None] = "20260922_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PREDEFINED_LOCATIONS = [
    {"name": "Coimbatore", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Sulur", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Tiruppur", "district": "Tiruppur", "state": "Tamil Nadu"},
    {"name": "Pollachi", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Mettupalayam", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Avinashi", "district": "Tiruppur", "state": "Tamil Nadu"},
    {"name": "Palladam", "district": "Tiruppur", "state": "Tamil Nadu"},
    {"name": "Udumalpet", "district": "Tiruppur", "state": "Tamil Nadu"},
    {"name": "Annur", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Madukkarai", "district": "Coimbatore", "state": "Tamil Nadu"},
    {"name": "Perur", "district": "Coimbatore", "state": "Tamil Nadu"},
]


def upgrade() -> None:
    conn = op.get_bind()
    locations_table = sa.table(
        "locations",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("district", sa.String),
        sa.column("state", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)

    # 1. Fetch existing location names
    result = conn.execute(sa.select(locations_table.c.name))
    existing_names = {row[0].strip().lower() for row in result.fetchall() if row[0]}

    # 2. Insert missing predefined locations
    for loc in PREDEFINED_LOCATIONS:
        if loc["name"].lower() not in existing_names:
            conn.execute(
                locations_table.insert().values(
                    name=loc["name"],
                    district=loc["district"],
                    state=loc["state"],
                    is_active=True,
                    created_at=now,
                )
            )

    # 3. Ensure all existing locations have is_active = True and valid district/state
    conn.execute(
        locations_table.update()
        .where(
            sa.or_(
                locations_table.c.is_active.is_(None),
                locations_table.c.is_active.is_(False),
                locations_table.c.district.is_(None),
                locations_table.c.state.is_(None),
            )
        )
        .values(
            is_active=True,
            district=sa.case(
                (locations_table.c.district.is_(None), "Coimbatore"),
                else_=locations_table.c.district,
            ),
            state=sa.case(
                (locations_table.c.state.is_(None), "Tamil Nadu"),
                else_=locations_table.c.state,
            ),
        )
    )


def downgrade() -> None:
    pass

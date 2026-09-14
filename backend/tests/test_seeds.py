import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import DonorProfile
from app.models.enums import UserRole
from app.models.location import Location
from app.models.user import User
from app.seeds.users import seed_users


@pytest.mark.asyncio
async def test_seed_users_creates_expected_data(db_session: AsyncSession):
    """Verify that seed_users correctly populates admins, requesters, and donors."""
    stats = await seed_users(db_session)

    assert stats["admins"] >= 1
    assert stats["requesters"] >= 4
    assert stats["donors"] >= 20

    # Verify admin user exists
    admin_stmt = select(User).where(User.role == UserRole.ADMIN)
    admin_user = (await db_session.execute(admin_stmt)).scalar_one_or_none()
    assert admin_user is not None
    assert admin_user.mobile == "9876543210"

    # Verify donors exist and are linked to valid locations
    donor_count = (await db_session.execute(select(func.count(DonorProfile.id)))).scalar()
    assert donor_count >= 20

    # Verify idempotency on second run
    second_stats = await seed_users(db_session)
    assert second_stats["admins"] == 0
    assert second_stats["donors"] == 0

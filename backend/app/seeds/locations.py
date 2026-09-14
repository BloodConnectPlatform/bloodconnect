import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.location import Location

logger = logging.getLogger(__name__)

INITIAL_LOCATIONS = [
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


async def seed_locations(session: AsyncSession) -> int:
    """Seed predefined locations if they do not already exist."""
    count = 0
    for loc_data in INITIAL_LOCATIONS:
        stmt = select(Location).where(Location.name == loc_data["name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            location = Location(
                name=loc_data["name"],
                district=loc_data["district"],
                state=loc_data["state"],
                is_active=True
            )
            session.add(location)
            count += 1
    if count > 0:
        await session.commit()
        logger.info(f"Successfully seeded {count} new locations.")
    else:
        logger.info("All predefined locations are already seeded.")
    return count


async def main():
    logging.basicConfig(level=logging.INFO)
    async with AsyncSessionLocal() as session:
        await seed_locations(session)


if __name__ == "__main__":
    asyncio.run(main())

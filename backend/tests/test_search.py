from datetime import date
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, UserRole
from app.models.location import Location
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def seeded_donors(db_session: AsyncSession):
    """Seed various donors across blood groups, locations, and availability statuses."""
    loc_cbe = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()
    loc_sul = (await db_session.execute(select(Location).where(Location.name == "Sulur"))).scalar_one()
    loc_pol = (await db_session.execute(select(Location).where(Location.name == "Pollachi"))).scalar_one()

    # 1. Eligible O+ in Coimbatore
    u1 = User(name="Donor One", mobile="9876543250", role=UserRole.DONOR, is_active=True)
    d1 = DonorProfile(
        user=u1,
        date_of_birth=date(1992, 1, 1),
        blood_group=BloodGroup.O_POS,
        location_id=loc_cbe.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )

    # 2. Eligible O+ in Sulur
    u2 = User(name="Donor Two", mobile="9876543251", role=UserRole.DONOR, is_active=True)
    d2 = DonorProfile(
        user=u2,
        date_of_birth=date(1993, 2, 2),
        blood_group=BloodGroup.O_POS,
        location_id=loc_sul.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )

    # 3. Eligible A+ in Coimbatore
    u3 = User(name="Donor Three", mobile="9876543252", role=UserRole.DONOR, is_active=True)
    d3 = DonorProfile(
        user=u3,
        date_of_birth=date(1994, 3, 3),
        blood_group=BloodGroup.A_POS,
        location_id=loc_cbe.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )

    # 4. Unavailable O+ in Coimbatore (is_available=False) -> SHOULD BE EXCLUDED
    u4 = User(name="Donor Four", mobile="9876543253", role=UserRole.DONOR, is_active=True)
    d4 = DonorProfile(
        user=u4,
        date_of_birth=date(1995, 4, 4),
        blood_group=BloodGroup.O_POS,
        location_id=loc_cbe.id,
        is_otp_verified=True,
        is_available=False,
        is_active=True,
        contact_consent=True
    )

    # 5. Unverified O+ in Coimbatore (is_otp_verified=False) -> SHOULD BE EXCLUDED
    u5 = User(name="Donor Five", mobile="9876543254", role=UserRole.DONOR, is_active=True)
    d5 = DonorProfile(
        user=u5,
        date_of_birth=date(1996, 5, 5),
        blood_group=BloodGroup.O_POS,
        location_id=loc_cbe.id,
        is_otp_verified=False,
        is_available=True,
        is_active=True,
        contact_consent=True
    )

    # 6. Deactivated Profile O+ (is_active=False) -> SHOULD BE EXCLUDED
    u6 = User(name="Donor Six", mobile="9876543255", role=UserRole.DONOR, is_active=True)
    d6 = DonorProfile(
        user=u6,
        date_of_birth=date(1997, 6, 6),
        blood_group=BloodGroup.O_POS,
        location_id=loc_cbe.id,
        is_otp_verified=True,
        is_available=True,
        is_active=False,
        contact_consent=True
    )

    # 7. Deactivated User O+ (user.is_active=False) -> SHOULD BE EXCLUDED
    u7 = User(name="Donor Seven", mobile="9876543256", role=UserRole.DONOR, is_active=False)
    d7 = DonorProfile(
        user=u7,
        date_of_birth=date(1998, 7, 7),
        blood_group=BloodGroup.O_POS,
        location_id=loc_cbe.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )

    db_session.add_all([u1, u2, u3, u4, u5, u6, u7, d1, d2, d3, d4, d5, d6, d7])
    await db_session.commit()

    return {
        "cbe": loc_cbe,
        "sul": loc_sul,
        "pol": loc_pol
    }


@pytest.mark.asyncio
async def test_list_locations_endpoint(client: AsyncClient):
    """Test GET /api/v1/locations returns all 11 active predefined locations."""
    response = await client.get("/api/v1/locations")
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) == 11
    names = [loc["name"] for loc in locations]
    assert "Coimbatore" in names
    assert "Sulur" in names
    assert "Tiruppur" in names
    assert "Pollachi" in names


@pytest.mark.asyncio
async def test_search_donors_by_blood_group(client: AsyncClient, seeded_donors):
    """Test searching by blood group returns only eligible donors with matching blood group."""
    response = await client.get("/api/v1/donors/search", params={"blood_group": "O+"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Donor One & Donor Two
    for item in data["items"]:
        assert item["blood_group"] == "O+"
        assert item["is_available"] is True


@pytest.mark.asyncio
async def test_search_donors_by_location(client: AsyncClient, seeded_donors):
    """Test searching by location_id returns only eligible donors in that location."""
    cbe_id = seeded_donors["cbe"].id
    response = await client.get("/api/v1/donors/search", params={"location_id": cbe_id})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Donor One (O+) and Donor Three (A+)
    names = [d["name"] for d in data["items"]]
    assert "Donor One" in names
    assert "Donor Three" in names


@pytest.mark.asyncio
async def test_search_donors_by_both_blood_group_and_location(client: AsyncClient, seeded_donors):
    """Test searching by both blood group and location returns intersection."""
    cbe_id = seeded_donors["cbe"].id
    response = await client.get(
        "/api/v1/donors/search",
        params={"blood_group": "A+", "location_id": cbe_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Donor Three"
    assert data["items"][0]["blood_group"] == "A+"
    assert data["items"][0]["location"]["name"] == "Coimbatore"


@pytest.mark.asyncio
async def test_search_excludes_ineligible_donors(client: AsyncClient, seeded_donors):
    """Verify unavailable, unverified, and deactivated donors are strictly excluded."""
    cbe_id = seeded_donors["cbe"].id
    response = await client.get(
        "/api/v1/donors/search",
        params={"blood_group": "O+", "location_id": cbe_id}
    )
    assert response.status_code == 200
    data = response.json()
    # In CBE for O+, there were 5 seeded donors (1 active/verified/available, 1 unavailable, 1 unverified, 1 inactive profile, 1 inactive user)
    # Only 1 (Donor One) should be returned!
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Donor One"


@pytest.mark.asyncio
async def test_search_response_privacy_protection(client: AsyncClient, seeded_donors):
    """Verify public search response does NOT expose mobile numbers, dates of birth, or internal fields."""
    response = await client.get("/api/v1/donors/search")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0

    for donor in data["items"]:
        # Verify allowed public fields
        assert "id" in donor
        assert "name" in donor
        assert "blood_group" in donor
        assert "location" in donor
        assert "is_available" in donor

        # Verify STRICT PRIVACY: Private fields must NOT exist in the JSON response
        assert "mobile" not in donor
        assert "phone" not in donor
        assert "date_of_birth" not in donor
        assert "otp" not in donor
        assert "user_id" not in donor


@pytest.mark.asyncio
async def test_search_pagination(client: AsyncClient, seeded_donors):
    """Test search pagination parameters."""
    response = await client.get("/api/v1/donors/search", params={"page": 1, "size": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # Donor One, Donor Two, Donor Three
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] == 2

    # Second page
    res2 = await client.get("/api/v1/donors/search", params={"page": 2, "size": 2})
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 1
    assert data2["page"] == 2

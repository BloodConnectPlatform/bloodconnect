from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User
from app.services.sms import default_sms_provider


@pytest.fixture(autouse=True)
def clear_sms():
    default_sms_provider.clear()
    yield
    default_sms_provider.clear()


@pytest.mark.asyncio
async def test_donor_registration_with_verification_token(
    client: AsyncClient, db_session: AsyncSession
):
    """Test full donor registration flow using a verification token from verify-otp."""
    # 1. Fetch Coimbatore location ID
    loc_stmt = select(Location).where(Location.name == "Coimbatore")
    loc_res = await db_session.execute(loc_stmt)
    location = loc_res.scalar_one()

    # 2. Send & Verify OTP
    mobile = "9876543230"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    assert send_res.status_code == 200
    debug_otp = send_res.json()["debug_otp"]

    verify_res = await client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": mobile, "otp": debug_otp}
    )
    assert verify_res.status_code == 200
    verification_token = verify_res.json()["verification_token"]

    # 3. Register as Donor
    reg_payload = {
        "name": "Ramesh Kumar",
        "mobile": mobile,
        "verification_token": verification_token,
        "date_of_birth": "1996-06-15",
        "blood_group": "O+",
        "location_id": location.id,
        "contact_consent": True
    }
    reg_res = await client.post("/api/v1/donors", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "DONOR"
    assert data["user"]["has_donor_profile"] is True

    # 4. Check Database
    user_stmt = select(User).where(User.mobile == mobile)
    user_res = await db_session.execute(user_stmt)
    user = user_res.scalar_one()
    assert user.donor_profile is not None
    assert user.donor_profile.blood_group == BloodGroup.O_POS
    assert user.donor_profile.is_otp_verified is True
    assert user.donor_profile.is_available is True


@pytest.mark.asyncio
async def test_donor_registration_with_direct_otp(
    client: AsyncClient, db_session: AsyncSession
):
    """Test donor registration providing OTP directly in registration body."""
    loc_stmt = select(Location).where(Location.name == "Sulur")
    loc_res = await db_session.execute(loc_stmt)
    location = loc_res.scalar_one()

    mobile = "9876543231"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_payload = {
        "name": "Suresh Raina",
        "mobile": mobile,
        "otp": debug_otp,
        "date_of_birth": "1994-03-20",
        "blood_group": "A+",
        "location_id": location.id,
        "contact_consent": True
    }
    reg_res = await client.post("/api/v1/donors", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["user"]["name"] == "Suresh Raina"


@pytest.mark.asyncio
async def test_donor_registration_underage_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    """Test donor registration fails if applicant is under 18 years old."""
    loc_stmt = select(Location).where(Location.name == "Pollachi")
    loc_res = await db_session.execute(loc_stmt)
    location = loc_res.scalar_one()

    mobile = "9876543232"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_payload = {
        "name": "Young Donor",
        "mobile": mobile,
        "otp": debug_otp,
        "date_of_birth": "2015-01-01",  # Underage (< 18)
        "blood_group": "B+",
        "location_id": location.id,
        "contact_consent": True
    }
    reg_res = await client.post("/api/v1/donors", json=reg_payload)
    assert reg_res.status_code == 422
    assert "at least 18 years" in str(reg_res.json())


@pytest.mark.asyncio
async def test_donor_registration_invalid_location_rejected(
    client: AsyncClient
):
    """Test donor registration with invalid location_id returns 400."""
    mobile = "9876543233"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_payload = {
        "name": "Test User",
        "mobile": mobile,
        "otp": debug_otp,
        "date_of_birth": "1990-01-01",
        "blood_group": "AB+",
        "location_id": 99999,  # Non-existent
        "contact_consent": True
    }
    reg_res = await client.post("/api/v1/donors", json=reg_payload)
    assert reg_res.status_code == 400
    assert "location" in reg_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_donor_registration_duplicate_mobile_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    """Test duplicate registration for already registered donor returns 409 Conflict."""
    loc_stmt = select(Location).where(Location.name == "Tiruppur")
    loc_res = await db_session.execute(loc_stmt)
    location = loc_res.scalar_one()

    mobile = "9876543234"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_payload = {
        "name": "Donor Once",
        "mobile": mobile,
        "otp": debug_otp,
        "date_of_birth": "1992-05-12",
        "blood_group": "O-",
        "location_id": location.id,
        "contact_consent": True
    }
    res1 = await client.post("/api/v1/donors", json=reg_payload)
    assert res1.status_code == 201

    # Try registering again with a new verification token for the same mobile
    from app.core.security import create_verification_token
    verification_token = create_verification_token(mobile)
    reg_payload.pop("otp", None)
    reg_payload["verification_token"] = verification_token
    res2 = await client.post("/api/v1/donors", json=reg_payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_and_update_donor_profile(
    client: AsyncClient, db_session: AsyncSession
):
    """Test GET /api/v1/donors/me and PATCH /api/v1/donors/me."""
    loc_cbe = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()
    loc_sul = (await db_session.execute(select(Location).where(Location.name == "Sulur"))).scalar_one()

    mobile = "9876543235"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_res = await client.post(
        "/api/v1/donors",
        json={
            "name": "Initial Name",
            "mobile": mobile,
            "otp": debug_otp,
            "date_of_birth": "1991-07-24",
            "blood_group": "A-",
            "location_id": loc_cbe.id,
            "contact_consent": True
        }
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get profile
    get_res = await client.get("/api/v1/donors/me", headers=headers)
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile["name"] == "Initial Name"
    assert profile["location"]["name"] == "Coimbatore"
    assert profile["is_available"] is True

    # 2. Update profile
    patch_res = await client.patch(
        "/api/v1/donors/me",
        headers=headers,
        json={"name": "Updated Name", "location_id": loc_sul.id}
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "Updated Name"
    assert updated["location"]["name"] == "Sulur"


@pytest.mark.asyncio
async def test_toggle_donor_availability(
    client: AsyncClient, db_session: AsyncSession
):
    """Test PATCH /api/v1/donors/availability toggles availability state."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Avinashi"))).scalar_one()

    mobile = "9876543236"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_res = await client.post(
        "/api/v1/donors",
        json={
            "name": "Toggle Donor",
            "mobile": mobile,
            "otp": debug_otp,
            "date_of_birth": "1993-11-05",
            "blood_group": "B-",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Toggle to unavailable
    toggle1 = await client.patch(
        "/api/v1/donors/availability",
        headers=headers,
        json={"is_available": False}
    )
    assert toggle1.status_code == 200
    assert toggle1.json()["is_available"] is False

    # Toggle back to available
    toggle2 = await client.patch(
        "/api/v1/donors/availability",
        headers=headers,
        json={"is_available": True}
    )
    assert toggle2.status_code == 200
    assert toggle2.json()["is_available"] is True


@pytest.mark.asyncio
async def test_donor_dashboard_with_requests_and_contact_privacy(
    client: AsyncClient, db_session: AsyncSession
):
    """Test donor dashboard stats and strict privacy enforcement on requester contacts."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Pollachi"))).scalar_one()

    # 1. Register Donor
    donor_mobile = "9876543237"
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_mobile})
    debug_otp = send_res.json()["debug_otp"]

    reg_res = await client.post(
        "/api/v1/donors",
        json={
            "name": "Dashboard Donor",
            "mobile": donor_mobile,
            "otp": debug_otp,
            "date_of_birth": "1990-09-10",
            "blood_group": "AB-",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch donor entity
    donor_user = (await db_session.execute(select(User).where(User.mobile == donor_mobile))).scalar_one()
    donor_profile = donor_user.donor_profile

    # 2. Create Requesters and Requests (1 PENDING, 1 ACCEPTED)
    requester1 = User(name="Pending Requester", mobile="9876543238", role=UserRole.REQUESTER)
    requester2 = User(name="Accepted Requester", mobile="9876543239", role=UserRole.REQUESTER)
    db_session.add_all([requester1, requester2])
    await db_session.flush()

    req_pending = BloodRequest(
        requester_id=requester1.id,
        donor_id=donor_profile.id,
        blood_group=BloodGroup.AB_NEG,
        location_id=loc.id,
        message="Urgent AB- needed",
        status=RequestStatus.PENDING
    )
    req_accepted = BloodRequest(
        requester_id=requester2.id,
        donor_id=donor_profile.id,
        blood_group=BloodGroup.AB_NEG,
        location_id=loc.id,
        message="Confirmed donation request",
        status=RequestStatus.ACCEPTED,
        responded_at=datetime.now(timezone.utc)
    )
    db_session.add_all([req_pending, req_accepted])
    await db_session.commit()

    # 3. Fetch Donor Dashboard
    dash_res = await client.get("/api/v1/donors/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()

    # Verify counts
    assert dash["stats"]["total_requests"] == 2
    assert dash["stats"]["pending_requests"] == 1
    assert dash["stats"]["accepted_requests"] == 1
    assert dash["stats"]["rejected_requests"] == 0

    # Verify requests list & contact privacy rules
    recent = dash["recent_requests"]
    assert len(recent) == 2

    for r in recent:
        if r["status"] == "PENDING":
            # STRICT PRIVACY: Requester mobile MUST be hidden when status is PENDING!
            assert r["requester_mobile"] is None
            assert r["requester_name"] == "Pending Requester"
        elif r["status"] == "ACCEPTED":
            # Requester mobile IS disclosed when donor accepted the request!
            assert r["requester_mobile"] == "9876543239"
            assert r["requester_name"] == "Accepted Requester"


@pytest.mark.asyncio
async def test_requester_cannot_access_donor_endpoints(
    client: AsyncClient, db_session: AsyncSession
):
    """Test regular REQUESTER user receives 403 Forbidden on donor-specific endpoints."""
    requester = User(name="Pure Requester", mobile="9876543240", role=UserRole.REQUESTER)
    db_session.add(requester)
    await db_session.commit()

    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543240"})
    debug_otp = send_res.json()["debug_otp"]
    login_res = await client.post("/api/v1/auth/login", json={"mobile": "9876543240", "otp": debug_otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /donors/me -> 403
    res_me = await client.get("/api/v1/donors/me", headers=headers)
    assert res_me.status_code == 403

    # /donors/dashboard -> 403
    res_dash = await client.get("/api/v1/donors/dashboard", headers=headers)
    assert res_dash.status_code == 403

    # /donors/availability -> 403
    res_avail = await client.patch("/api/v1/donors/availability", headers=headers, json={"is_available": True})
    assert res_avail.status_code == 403

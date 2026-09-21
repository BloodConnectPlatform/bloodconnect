from datetime import date, datetime, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def security_fixture(client: AsyncClient, db_session: AsyncSession):
    """Setup testing environment with multiple roles, donors, and requesters."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # 1. Admin
    admin_mobile = "9876543280"
    admin_user = User(name="Sec Admin", mobile=admin_mobile, role=UserRole.ADMIN, is_active=True)
    db_session.add(admin_user)
    await db_session.commit()
    s_admin = await client.post("/api/v1/auth/send-otp", json={"mobile": admin_mobile})
    l_admin = await client.post("/api/v1/auth/login", json={"mobile": admin_mobile, "otp": s_admin.json()["debug_otp"]})
    admin_token = l_admin.json()["access_token"]

    # 2. Donor A (Eligible)
    donor_a_mobile = "9876543281"
    s_da = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_a_mobile})
    r_da = await client.post(
        "/api/v1/donors",
        json={
            "name": "Donor Alpha",
            "mobile": donor_a_mobile,
            "otp": s_da.json()["debug_otp"],
            "date_of_birth": "1992-02-02",
            "blood_group": "O+",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    donor_a_token = r_da.json()["access_token"]
    donor_a_user = (await db_session.execute(select(User).where(User.mobile == donor_a_mobile))).scalar_one()
    donor_a_profile = donor_a_user.donor_profile

    # 3. Donor B (Eligible)
    donor_b_mobile = "9876543282"
    s_db = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_b_mobile})
    r_db = await client.post(
        "/api/v1/donors",
        json={
            "name": "Donor Beta",
            "mobile": donor_b_mobile,
            "otp": s_db.json()["debug_otp"],
            "date_of_birth": "1993-03-03",
            "blood_group": "A+",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    donor_b_token = r_db.json()["access_token"]
    donor_b_user = (await db_session.execute(select(User).where(User.mobile == donor_b_mobile))).scalar_one()
    donor_b_profile = donor_b_user.donor_profile

    # 4. Requester X
    req_x_mobile = "9876543283"
    req_x_user = User(name="Requester X", mobile=req_x_mobile, role=UserRole.REQUESTER, is_active=True)
    db_session.add(req_x_user)
    await db_session.commit()
    s_rx = await client.post("/api/v1/auth/send-otp", json={"mobile": req_x_mobile})
    l_rx = await client.post("/api/v1/auth/login", json={"mobile": req_x_mobile, "otp": s_rx.json()["debug_otp"]})
    req_x_token = l_rx.json()["access_token"]

    # 5. Requester Y
    req_y_mobile = "9876543284"
    req_y_user = User(name="Requester Y", mobile=req_y_mobile, role=UserRole.REQUESTER, is_active=True)
    db_session.add(req_y_user)
    await db_session.commit()
    s_ry = await client.post("/api/v1/auth/send-otp", json={"mobile": req_y_mobile})
    l_ry = await client.post("/api/v1/auth/login", json={"mobile": req_y_mobile, "otp": s_ry.json()["debug_otp"]})
    req_y_token = l_ry.json()["access_token"]

    return {
        "location": loc,
        "admin_user": admin_user,
        "admin_token": admin_token,
        "donor_a_user": donor_a_user,
        "donor_a_profile": donor_a_profile,
        "donor_a_token": donor_a_token,
        "donor_b_user": donor_b_user,
        "donor_b_profile": donor_b_profile,
        "donor_b_token": donor_b_token,
        "req_x_user": req_x_user,
        "req_x_token": req_x_token,
        "req_y_user": req_y_user,
        "req_y_token": req_y_token
    }


@pytest.mark.asyncio
async def test_invariant_1_unauthenticated_user_blocked(client: AsyncClient):
    """Invariant 1: Unauthenticated requests to protected endpoints MUST return 401."""
    protected_endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("POST", "/api/v1/auth/logout"),
        ("GET", "/api/v1/donors/me"),
        ("GET", "/api/v1/donors/dashboard"),
        ("PATCH", "/api/v1/donors/availability"),
        ("GET", "/api/v1/requests/sent"),
        ("GET", "/api/v1/requests/received"),
        ("POST", "/api/v1/requests"),
        ("GET", "/api/v1/notifications"),
        ("GET", "/api/v1/admin/statistics"),
        ("GET", "/api/v1/admin/donors"),
        ("GET", "/api/v1/admin/reports"),
        ("GET", "/api/v1/admin/audit-logs"),
    ]
    for method, path in protected_endpoints:
        if method == "GET":
            res = await client.get(path)
        elif method == "POST":
            res = await client.post(path, json={})
        elif method == "PATCH":
            res = await client.patch(path, json={})
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


@pytest.mark.asyncio
async def test_invariant_2_requester_cannot_retrieve_donor_phone_before_acceptance(
    client: AsyncClient, security_fixture
):
    """Invariant 2: Requester cannot view donor phone number before acceptance (PENDING / REJECTED)."""
    data = security_fixture
    req_headers = {"Authorization": f"Bearer {data['req_x_token']}"}

    # Create request
    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_a_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id,
            "message": "Urgent request"
        }
    )
    assert create_res.status_code == 201
    req_id = create_res.json()["id"]

    # 1. Inspect direct POST response
    assert create_res.json()["donor_mobile"] is None

    # 2. Inspect GET /requests/{id} in PENDING state
    get_res = await client.get(f"/api/v1/requests/{req_id}", headers=req_headers)
    assert get_res.status_code == 200
    assert get_res.json()["donor_mobile"] is None

    # 3. Inspect GET /requests/sent
    sent_res = await client.get("/api/v1/requests/sent", headers=req_headers)
    assert sent_res.status_code == 200
    assert sent_res.json()[0]["donor_mobile"] is None


@pytest.mark.asyncio
async def test_invariant_3_cross_requester_privacy_isolation(
    client: AsyncClient, security_fixture
):
    """Invariant 3: Requester X cannot view or access Requester Y's sent requests."""
    data = security_fixture
    req_x_headers = {"Authorization": f"Bearer {data['req_x_token']}"}
    req_y_headers = {"Authorization": f"Bearer {data['req_y_token']}"}

    # Requester X creates request
    create_res = await client.post(
        "/api/v1/requests",
        headers=req_x_headers,
        json={
            "donor_id": str(data["donor_a_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    req_x_id = create_res.json()["id"]

    # Requester Y tries to fetch Requester X's request -> 403 Forbidden
    cross_res = await client.get(f"/api/v1/requests/{req_x_id}", headers=req_y_headers)
    assert cross_res.status_code == 403

    # Requester Y's sent requests list MUST NOT contain Requester X's request
    sent_y_res = await client.get("/api/v1/requests/sent", headers=req_y_headers)
    sent_y_ids = [r["id"] for r in sent_y_res.json()]
    assert req_x_id not in sent_y_ids


@pytest.mark.asyncio
async def test_invariant_4_cross_donor_privacy_isolation(
    client: AsyncClient, security_fixture
):
    """Invariant 4: Donor B cannot access Donor A's dashboard, received requests, or accept Donor A's requests."""
    data = security_fixture
    req_x_headers = {"Authorization": f"Bearer {data['req_x_token']}"}
    donor_a_headers = {"Authorization": f"Bearer {data['donor_a_token']}"}
    donor_b_headers = {"Authorization": f"Bearer {data['donor_b_token']}"}

    # Create request targeting Donor A
    create_res = await client.post(
        "/api/v1/requests",
        headers=req_x_headers,
        json={
            "donor_id": str(data["donor_a_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    req_id = create_res.json()["id"]

    # Donor B tries to view request targeting Donor A -> 403 Forbidden
    res_b_view = await client.get(f"/api/v1/requests/{req_id}", headers=donor_b_headers)
    assert res_b_view.status_code == 403

    # Donor B tries to accept request targeting Donor A -> 403 Forbidden
    res_b_accept = await client.patch(f"/api/v1/requests/{req_id}/accept", headers=donor_b_headers)
    assert res_b_accept.status_code == 403

    # Donor B's received requests list MUST NOT contain Donor A's request
    res_b_rec = await client.get("/api/v1/requests/received", headers=donor_b_headers)
    rec_b_ids = [r["id"] for r in res_b_rec.json()]
    assert req_id not in rec_b_ids


@pytest.mark.asyncio
async def test_invariant_5_non_admin_cannot_access_admin_endpoints(
    client: AsyncClient, security_fixture
):
    """Invariant 5: Normal users (requesters & donors) CANNOT access any admin endpoints."""
    data = security_fixture
    tokens = [data["req_x_token"], data["donor_a_token"]]

    admin_endpoints = [
        ("GET", "/api/v1/admin/donors"),
        ("GET", "/api/v1/admin/requests"),
        ("GET", "/api/v1/admin/reports"),
        ("GET", "/api/v1/admin/statistics"),
        ("GET", "/api/v1/admin/audit-logs"),
        ("PATCH", f"/api/v1/admin/donors/{data['donor_a_profile'].id}/activate"),
        ("PATCH", f"/api/v1/admin/donors/{data['donor_a_profile'].id}/deactivate"),
        ("DELETE", f"/api/v1/admin/donors/{data['donor_a_profile'].id}"),
    ]

    for token in tokens:
        headers = {"Authorization": f"Bearer {token}"}
        for method, path in admin_endpoints:
            if method == "GET":
                res = await client.get(path, headers=headers)
            elif method == "PATCH":
                res = await client.patch(path, headers=headers, json={"is_available": True})
            elif method == "DELETE":
                res = await client.delete(path, headers=headers)
            assert res.status_code == 403, f"Expected 403 for {method} {path} with non-admin token, got {res.status_code}"


@pytest.mark.asyncio
async def test_invariant_6_7_8_search_excludes_unverified_inactive_unavailable(
    client: AsyncClient, security_fixture, db_session: AsyncSession
):
    """Invariants 6, 7, 8: Unverified, inactive, or unavailable donors MUST NOT appear in search."""
    loc = security_fixture["location"]

    # 1. Unverified donor
    u_unv = User(name="Unverified User", mobile="9876543290", role=UserRole.DONOR, is_active=True)
    d_unv = DonorProfile(
        user=u_unv, date_of_birth=date(1990, 1, 1), blood_group=BloodGroup.AB_POS,
        location_id=loc.id, is_otp_verified=False, is_available=True, is_active=True, contact_consent=True
    )

    # 2. Inactive profile donor
    u_inact = User(name="Inactive User", mobile="9876543291", role=UserRole.DONOR, is_active=True)
    d_inact = DonorProfile(
        user=u_inact, date_of_birth=date(1990, 1, 1), blood_group=BloodGroup.AB_POS,
        location_id=loc.id, is_otp_verified=True, is_available=True, is_active=False, contact_consent=True
    )

    # 3. Unavailable donor
    u_unavail = User(name="Unavailable User", mobile="9876543292", role=UserRole.DONOR, is_active=True)
    d_unavail = DonorProfile(
        user=u_unavail, date_of_birth=date(1990, 1, 1), blood_group=BloodGroup.AB_POS,
        location_id=loc.id, is_otp_verified=True, is_available=False, is_active=True, contact_consent=True
    )

    # 4. Eligible AB+ donor
    u_elig = User(name="Eligible AB User", mobile="9876543293", role=UserRole.DONOR, is_active=True)
    d_elig = DonorProfile(
        user=u_elig, date_of_birth=date(1990, 1, 1), blood_group=BloodGroup.AB_POS,
        location_id=loc.id, is_otp_verified=True, is_available=True, is_active=True, contact_consent=True
    )

    db_session.add_all([u_unv, d_unv, u_inact, d_inact, u_unavail, d_unavail, u_elig, d_elig])
    await db_session.commit()

    # Search for AB+ in location
    search_res = await client.get(
        "/api/v1/donors/search",
        params={"blood_group": "AB+", "location_id": loc.id}
    )
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Eligible AB User"


@pytest.mark.asyncio
async def test_invariant_9_rejected_request_permanently_conceals_contact(
    client: AsyncClient, security_fixture
):
    """Invariant 9: Rejected requests MUST NEVER disclose contact numbers to either party."""
    data = security_fixture
    req_headers = {"Authorization": f"Bearer {data['req_x_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_a_token']}"}

    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_a_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    req_id = create_res.json()["id"]

    # Donor declines
    reject_res = await client.patch(f"/api/v1/requests/{req_id}/reject", headers=donor_headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"
    assert reject_res.json()["donor_mobile"] is None
    assert reject_res.json()["requester_mobile"] is None

    # Requester checks detail view -> Numbers remain hidden
    req_view = await client.get(f"/api/v1/requests/{req_id}", headers=req_headers)
    assert req_view.json()["donor_mobile"] is None
    assert req_view.json()["requester_mobile"] is None


@pytest.mark.asyncio
async def test_invariant_10_immutable_request_states(
    client: AsyncClient, security_fixture
):
    """Invariant 10: Closed requests cannot be transitioned again (ACCEPTED -> ACCEPTED/REJECTED, REJECTED -> ACCEPTED)."""
    data = security_fixture
    req_headers = {"Authorization": f"Bearer {data['req_x_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_a_token']}"}

    # Request 1: Accept
    r1 = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={"donor_id": str(data["donor_a_profile"].id), "blood_group": "O+", "location_id": data["location"].id}
    )
    r1_id = r1.json()["id"]
    await client.patch(f"/api/v1/requests/{r1_id}/accept", headers=donor_headers)

    # Re-accepting fails
    res_dup_acc = await client.patch(f"/api/v1/requests/{r1_id}/accept", headers=donor_headers)
    assert res_dup_acc.status_code == 400

    # Rejecting accepted request fails
    res_acc_to_rej = await client.patch(f"/api/v1/requests/{r1_id}/reject", headers=donor_headers)
    assert res_acc_to_rej.status_code == 400

    # Request 2: Reject
    r2 = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={"donor_id": str(data["donor_a_profile"].id), "blood_group": "O+", "location_id": data["location"].id}
    )
    r2_id = r2.json()["id"]
    await client.patch(f"/api/v1/requests/{r2_id}/reject", headers=donor_headers)

    # Accepting rejected request fails
    res_rej_to_acc = await client.patch(f"/api/v1/requests/{r2_id}/accept", headers=donor_headers)
    assert res_rej_to_acc.status_code == 400


@pytest.mark.asyncio
async def test_production_environment_security_enforcement(db_session: AsyncSession, monkeypatch):
    """Verify that in production mode, DEBUG is forced to False and debug_otp is strictly omitted."""
    from app.core.config import Settings, settings
    from app.services.otp_service import otp_service

    # 1. Test Settings model validator forces DEBUG=False when ENVIRONMENT=production
    prod_settings = Settings(ENVIRONMENT="production", DEBUG=True)
    assert prod_settings.DEBUG is False
    assert prod_settings.is_production is True
    assert prod_settings.is_development is False

    # 2. Test send_otp strictly suppresses debug_otp when ENVIRONMENT=production
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEBUG", False)

    otp_res = await otp_service.send_otp(db_session, mobile="9876543299", purpose="LOGIN")
    assert otp_res["success"] is True
    assert otp_res["debug_otp"] is None


@pytest.mark.asyncio
async def test_production_health_check_masks_internal_errors(client: AsyncClient, monkeypatch):
    """Verify that in production mode, health check endpoint masks internal errors."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["error"] is None
    assert "status" in res.json()


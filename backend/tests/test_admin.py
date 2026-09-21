from datetime import date
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, ReportReason, ReportStatus, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def setup_admin_and_data(client: AsyncClient, db_session: AsyncSession):
    """Setup Admin user, Donor user, and Requester user with auth tokens."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # 1. Admin User
    admin_mobile = "9876543270"
    admin_user = User(name="Master Admin", mobile=admin_mobile, role=UserRole.ADMIN, is_active=True)
    db_session.add(admin_user)
    await db_session.commit()

    s1 = await client.post("/api/v1/auth/send-otp", json={"mobile": admin_mobile})
    l1 = await client.post("/api/v1/auth/login", json={"mobile": admin_mobile, "otp": s1.json()["debug_otp"]})
    admin_token = l1.json()["access_token"]

    # 2. Donor User
    donor_mobile = "9876543271"
    s2 = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_mobile})
    r2 = await client.post(
        "/api/v1/donors",
        json={
            "name": "Reportable Donor",
            "mobile": donor_mobile,
            "otp": s2.json()["debug_otp"],
            "date_of_birth": "1991-08-12",
            "blood_group": "B+",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    donor_token = r2.json()["access_token"]
    donor_user = (await db_session.execute(select(User).where(User.mobile == donor_mobile))).scalar_one()
    donor_profile = donor_user.donor_profile

    # 3. Requester User
    req_mobile = "9876543272"
    req_user = User(name="Reporter User", mobile=req_mobile, role=UserRole.REQUESTER, is_active=True)
    db_session.add(req_user)
    await db_session.commit()

    s3 = await client.post("/api/v1/auth/send-otp", json={"mobile": req_mobile})
    l3 = await client.post("/api/v1/auth/login", json={"mobile": req_mobile, "otp": s3.json()["debug_otp"]})
    req_token = l3.json()["access_token"]

    return {
        "location": loc,
        "admin_user": admin_user,
        "admin_token": admin_token,
        "donor_user": donor_user,
        "donor_profile": donor_profile,
        "donor_token": donor_token,
        "req_user": req_user,
        "req_token": req_token
    }


@pytest.mark.asyncio
async def test_create_report_success(client: AsyncClient, setup_admin_and_data):
    """Test user submitting a report against a donor profile."""
    data = setup_admin_and_data
    headers = {"Authorization": f"Bearer {data['req_token']}"}

    payload = {
        "donor_id": str(data["donor_profile"].id),
        "reason": "WRONG_BLOOD_GROUP",
        "description": "Donor reported they are actually O- not B+"
    }
    response = await client.post("/api/v1/reports", headers=headers, json=payload)
    assert response.status_code == 201
    rep = response.json()
    assert rep["reason"] == "WRONG_BLOOD_GROUP"
    assert rep["status"] == "OPEN"
    assert rep["donor_name"] == "Reportable Donor"
    assert rep["reporter_name"] == "Reporter User"


@pytest.mark.asyncio
async def test_admin_authorization_blocks_non_admin(client: AsyncClient, setup_admin_and_data):
    """Test regular users cannot access administrative endpoints."""
    data = setup_admin_and_data
    req_headers = {"Authorization": f"Bearer {data['req_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}

    # Requester access -> 403
    r1 = await client.get("/api/v1/admin/statistics", headers=req_headers)
    assert r1.status_code == 403

    # Donor access -> 403
    r2 = await client.get("/api/v1/admin/donors", headers=donor_headers)
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_donors_and_filtering(client: AsyncClient, setup_admin_and_data):
    """Test admin donor list, search, and blood group filters."""
    data = setup_admin_and_data
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}

    response = await client.get(
        "/api/v1/admin/donors",
        headers=admin_headers,
        params={"search": "Reportable", "blood_group": "B+"}
    )
    assert response.status_code == 200
    donors_data = response.json()
    assert donors_data["total"] >= 1
    assert donors_data["items"][0]["name"] == "Reportable Donor"
    assert donors_data["items"][0]["mobile"] == "9876543271"


@pytest.mark.asyncio
async def test_admin_activate_deactivate_and_availability(
    client: AsyncClient, setup_admin_and_data
):
    """Test admin deactivating, activating, and updating availability of a donor."""
    data = setup_admin_and_data
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}
    donor_id = data["donor_profile"].id

    # 1. Deactivate Donor
    deact_res = await client.patch(f"/api/v1/admin/donors/{donor_id}/deactivate", headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # 2. Activate Donor
    act_res = await client.patch(f"/api/v1/admin/donors/{donor_id}/activate", headers=admin_headers)
    assert act_res.status_code == 200
    assert act_res.json()["is_active"] is True

    # 3. Update Availability
    avail_res = await client.patch(
        f"/api/v1/admin/donors/{donor_id}/availability",
        headers=admin_headers,
        json={"is_available": False}
    )
    assert avail_res.status_code == 200
    assert avail_res.json()["is_available"] is False


@pytest.mark.asyncio
async def test_admin_handle_reports_and_audit_log(client: AsyncClient, setup_admin_and_data):
    """Test admin viewing, resolving reports, and verifying audit logging."""
    data = setup_admin_and_data
    req_headers = {"Authorization": f"Bearer {data['req_token']}"}
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}

    # 1. Submit report
    rep_res = await client.post(
        "/api/v1/reports",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "reason": "SPAM",
            "description": "Spam profile"
        }
    )
    report_id = rep_res.json()["id"]

    # 2. Admin lists open reports
    reports_list = await client.get("/api/v1/admin/reports", headers=admin_headers, params={"status": "OPEN"})
    assert reports_list.status_code == 200
    assert reports_list.json()["total"] >= 1

    # 3. Admin resolves report
    resolve_res = await client.patch(
        f"/api/v1/admin/reports/{report_id}",
        headers=admin_headers,
        json={"status": "RESOLVED", "notes": "Verified and resolved"}
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolved_at"] is not None

    # 4. Check audit logs
    audit_res = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["items"]
    assert any(log["action"] == "RESOLVE_REPORT" and log["target_id"] == report_id for log in logs)


@pytest.mark.asyncio
async def test_admin_statistics(client: AsyncClient, setup_admin_and_data):
    """Test GET /api/v1/admin/statistics computes correct aggregations."""
    data = setup_admin_and_data
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}

    stats_res = await client.get("/api/v1/admin/statistics", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()

    assert stats["total_registered_donors"] >= 1
    assert "B+" in stats["donors_by_blood_group"]
    assert "Coimbatore" in stats["donors_by_location"]
    assert "requests" in stats
    assert "reports" in stats


@pytest.mark.asyncio
async def test_admin_delete_donor(client: AsyncClient, setup_admin_and_data, db_session: AsyncSession):
    """Test admin deleting an inappropriate donor profile."""
    data = setup_admin_and_data
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}

    # Register temporary fake donor
    loc = data["location"]
    fake_mobile = "9876543279"
    s = await client.post("/api/v1/auth/send-otp", json={"mobile": fake_mobile})
    r = await client.post(
        "/api/v1/donors",
        json={
            "name": "Fake Profile",
            "mobile": fake_mobile,
            "otp": s.json()["debug_otp"],
            "date_of_birth": "1990-01-01",
            "blood_group": "AB+",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    fake_user = (await db_session.execute(select(User).where(User.mobile == fake_mobile))).scalar_one()
    fake_donor_id = fake_user.donor_profile.id

    # Admin deletes donor
    del_res = await client.delete(f"/api/v1/admin/donors/{fake_donor_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify donor profile is gone
    check_stmt = select(DonorProfile).where(DonorProfile.id == fake_donor_id)
    check_res = await db_session.execute(check_stmt)
    assert check_res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_admin_test_whatsapp_with_jwt(client: AsyncClient, setup_admin_and_data):
    """Test admin invoking the WhatsApp diagnostic test endpoint with JWT."""
    data = setup_admin_and_data
    admin_headers = {"Authorization": f"Bearer {data['admin_token']}"}

    payload = {
        "recipient_mobile": "9876543201",
        "template_name": "hello_world",
        "language_code": "en_US"
    }
    res = await client.post("/api/v1/admin/test-whatsapp", headers=admin_headers, json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["template_used"] == "hello_world"
    assert "provider" in res_data
    assert "provider_message_id" in res_data
    assert "recipient" in res_data


@pytest.mark.asyncio
async def test_admin_test_whatsapp_with_secret(client: AsyncClient, monkeypatch):
    """Test invoking WhatsApp diagnostic test with X-Admin-Secret header."""
    from app.core.config import settings
    test_secret = "test_bootstrap_secret_123456789012"
    monkeypatch.setattr(settings, "ADMIN_BOOTSTRAP_SECRET", test_secret)

    headers = {"X-Admin-Secret": test_secret}
    payload = {
        "recipient_mobile": "9876543220",
        "template_name": "hello_world"
    }
    res = await client.post("/api/v1/admin/test-whatsapp", headers=headers, json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True


@pytest.mark.asyncio
async def test_admin_test_whatsapp_unauthenticated_blocked(client: AsyncClient):
    """Test unauthenticated requests to WhatsApp test endpoint are rejected."""
    payload = {"recipient_mobile": "9876543220"}
    res = await client.post("/api/v1/admin/test-whatsapp", json=payload)
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_test_whatsapp_non_admin_blocked(client: AsyncClient, setup_admin_and_data):
    """Test non-admin user cannot access WhatsApp diagnostic test endpoint."""
    data = setup_admin_and_data
    req_headers = {"Authorization": f"Bearer {data['req_token']}"}
    payload = {"recipient_mobile": "9876543220"}
    res = await client.post("/api/v1/admin/test-whatsapp", headers=req_headers, json=payload)
    assert res.status_code == 403

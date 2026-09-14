from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.location import Location
from app.models.user import User


@pytest.mark.asyncio
async def test_complete_end_to_end_platform_lifecycle(
    client: AsyncClient, db_session: AsyncSession
):
    """Test full end-to-end user journey across all roles and system components."""
    # 0. Setup Location
    loc_stmt = select(Location).where(Location.name == "Coimbatore")
    loc_res = await db_session.execute(loc_stmt)
    location = loc_res.scalar_one()

    # Step 1: Donor Registration
    donor_mobile = "9876543295"
    s1 = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_mobile})
    assert s1.status_code == 200
    v1 = await client.post("/api/v1/auth/verify-otp", json={"mobile": donor_mobile, "otp": s1.json()["debug_otp"]})
    assert v1.status_code == 200
    verification_token = v1.json()["verification_token"]

    r_donor = await client.post(
        "/api/v1/donors",
        json={
            "name": "E2E Donor",
            "mobile": donor_mobile,
            "verification_token": verification_token,
            "date_of_birth": "1995-10-10",
            "blood_group": "O+",
            "location_id": location.id,
            "contact_consent": True
        }
    )
    assert r_donor.status_code == 201
    donor_token = r_donor.json()["access_token"]
    donor_headers = {"Authorization": f"Bearer {donor_token}"}
    donor_id = r_donor.json()["user"]["id"]

    # Step 2: Requester Discovery Search
    search_res = await client.get(
        "/api/v1/donors/search",
        params={"blood_group": "O+", "location_id": location.id}
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    found_donor = next(d for d in search_data["items"] if d["name"] == "E2E Donor")
    donor_profile_id = found_donor["id"]
    assert "mobile" not in found_donor

    # Step 3: Requester Registration / Login
    req_mobile = "9876543296"
    u_req = User(name="E2E Requester", mobile=req_mobile, role=UserRole.REQUESTER)
    db_session.add(u_req)
    await db_session.commit()

    s2 = await client.post("/api/v1/auth/send-otp", json={"mobile": req_mobile})
    l2 = await client.post("/api/v1/auth/login", json={"mobile": req_mobile, "otp": s2.json()["debug_otp"]})
    req_token = l2.json()["access_token"]
    req_headers = {"Authorization": f"Bearer {req_token}"}

    # Step 4: Requester Submits Blood Request
    req_create = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": donor_profile_id,
            "blood_group": "O+",
            "location_id": location.id,
            "message": "Urgent need for surgery"
        }
    )
    assert req_create.status_code == 201
    request_id = req_create.json()["id"]
    assert req_create.json()["status"] == "PENDING"
    assert req_create.json()["donor_mobile"] is None

    # Step 5: Donor receives notification & views dashboard
    notifs = await client.get("/api/v1/notifications", headers=donor_headers)
    assert notifs.status_code == 200
    assert notifs.json()["unread_count"] >= 1

    dash = await client.get("/api/v1/donors/dashboard", headers=donor_headers)
    assert dash.status_code == 200
    assert dash.json()["stats"]["pending_requests"] >= 1

    # Step 6: Donor Accepts Request (Unlocking Contacts)
    accept_res = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=donor_headers)
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"
    assert accept_res.json()["requester_mobile"] == req_mobile
    assert accept_res.json()["donor_mobile"] == donor_mobile

    # Step 7: Requester views sent requests -> Donor phone is now visible!
    sent_res = await client.get("/api/v1/requests/sent", headers=req_headers)
    assert sent_res.status_code == 200
    assert sent_res.json()[0]["donor_mobile"] == donor_mobile

    # Step 8: User files a report against donor
    rep_res = await client.post(
        "/api/v1/reports",
        headers=req_headers,
        json={
            "donor_id": donor_profile_id,
            "reason": "OTHER",
            "description": "Verification follow up"
        }
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]

    # Step 9: Admin reviews statistics & resolves report
    admin_user = User(name="Admin E2E", mobile="9876543297", role=UserRole.ADMIN)
    db_session.add(admin_user)
    await db_session.commit()

    s3 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543297"})
    l3 = await client.post("/api/v1/auth/login", json={"mobile": "9876543297", "otp": s3.json()["debug_otp"]})
    admin_token = l3.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin checks statistics
    stats_res = await client.get("/api/v1/admin/statistics", headers=admin_headers)
    assert stats_res.status_code == 200
    assert stats_res.json()["requests"]["accepted"] >= 1

    # Admin resolves report
    res_rep = await client.patch(
        f"/api/v1/admin/reports/{report_id}",
        headers=admin_headers,
        json={"status": "RESOLVED", "notes": "E2E test verified"}
    )
    assert res_rep.status_code == 200
    assert res_rep.json()["status"] == "RESOLVED"

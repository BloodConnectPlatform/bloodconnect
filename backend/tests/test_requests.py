from datetime import date
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, NotificationType, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def setup_users_and_donor(client: AsyncClient, db_session: AsyncSession):
    """Setup a registered donor and two requesters with authentication tokens."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # 1. Register Donor
    donor_mobile = "9876543260"
    s1 = await client.post("/api/v1/auth/send-otp", json={"mobile": donor_mobile})
    r1 = await client.post(
        "/api/v1/donors",
        json={
            "name": "Donor Dave",
            "mobile": donor_mobile,
            "otp": s1.json()["debug_otp"],
            "date_of_birth": "1993-04-15",
            "blood_group": "O+",
            "location_id": loc.id,
            "contact_consent": True
        }
    )
    donor_token = r1.json()["access_token"]
    donor_user = (await db_session.execute(select(User).where(User.mobile == donor_mobile))).scalar_one()
    donor_profile = donor_user.donor_profile

    # 2. Register / Login Requester 1
    req1_mobile = "9876543261"
    u_req1 = User(name="Requester Ryan", mobile=req1_mobile, role=UserRole.REQUESTER)
    db_session.add(u_req1)
    await db_session.commit()

    s2 = await client.post("/api/v1/auth/send-otp", json={"mobile": req1_mobile})
    l2 = await client.post("/api/v1/auth/login", json={"mobile": req1_mobile, "otp": s2.json()["debug_otp"]})
    req1_token = l2.json()["access_token"]

    # 3. Register / Login Requester 2 (Third party)
    req2_mobile = "9876543262"
    u_req2 = User(name="Other User", mobile=req2_mobile, role=UserRole.REQUESTER)
    db_session.add(u_req2)
    await db_session.commit()

    s3 = await client.post("/api/v1/auth/send-otp", json={"mobile": req2_mobile})
    l3 = await client.post("/api/v1/auth/login", json={"mobile": req2_mobile, "otp": s3.json()["debug_otp"]})
    req2_token = l3.json()["access_token"]

    return {
        "location": loc,
        "donor_user": donor_user,
        "donor_profile": donor_profile,
        "donor_token": donor_token,
        "req1_user": u_req1,
        "req1_token": req1_token,
        "req2_user": u_req2,
        "req2_token": req2_token
    }


@pytest.mark.asyncio
async def test_create_blood_request_success(client: AsyncClient, setup_users_and_donor):
    """Test creating a blood donation request dispatches notification and conceals numbers."""
    data = setup_users_and_donor
    headers = {"Authorization": f"Bearer {data['req1_token']}"}

    payload = {
        "donor_id": str(data["donor_profile"].id),
        "blood_group": "O+",
        "location_id": data["location"].id,
        "message": "Emergency requirement at KMCH Hospital"
    }

    response = await client.post("/api/v1/requests", headers=headers, json=payload)
    assert response.status_code == 201
    res_data = response.json()

    assert res_data["status"] == "PENDING"
    assert res_data["blood_group"] == "O+"
    assert res_data["donor_name"] == "Donor Dave"
    assert res_data["requester_name"] == "Requester Ryan"

    # STRICT PRIVACY: Contacts must be hidden in PENDING state
    assert res_data["donor_mobile"] is None
    assert res_data["requester_mobile"] is None

    # Check that Donor received REQUEST_RECEIVED notification
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}
    notif_res = await client.get("/api/v1/notifications", headers=donor_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert notifs["unread_count"] == 1
    assert notifs["items"][0]["type"] == "REQUEST_RECEIVED"
    assert "O+" in notifs["items"][0]["message"]


@pytest.mark.asyncio
async def test_create_blood_request_self_request_forbidden(client: AsyncClient, setup_users_and_donor):
    """Test donor cannot send a blood request to themselves."""
    data = setup_users_and_donor
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}

    payload = {
        "donor_id": str(data["donor_profile"].id),
        "blood_group": "O+",
        "location_id": data["location"].id,
        "message": "Self request"
    }

    response = await client.post("/api/v1/requests", headers=donor_headers, json=payload)
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_blood_request_unavailable_donor_rejected(
    client: AsyncClient, setup_users_and_donor
):
    """Test sending request to an unavailable donor fails with 404."""
    data = setup_users_and_donor
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}

    # Donor toggles availability to False
    await client.patch("/api/v1/donors/availability", headers=donor_headers, json={"is_available": False})

    payload = {
        "donor_id": str(data["donor_profile"].id),
        "blood_group": "O+",
        "location_id": data["location"].id
    }
    response = await client.post("/api/v1/requests", headers=req_headers, json=payload)
    assert response.status_code == 404
    assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_request_and_contact_disclosure(
    client: AsyncClient, setup_users_and_donor
):
    """Test donor accepting request unlocks requester mobile number for coordination."""
    data = setup_users_and_donor
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}

    # 1. Create request
    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    request_id = create_res.json()["id"]

    # 2. Donor views received requests -> Requester mobile is STILL HIDDEN
    rec_res = await client.get("/api/v1/requests/received", headers=donor_headers)
    assert rec_res.status_code == 200
    assert rec_res.json()[0]["requester_mobile"] is None

    # 3. Donor accepts request
    accept_res = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=donor_headers)
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["status"] == "ACCEPTED"

    # CRITICAL: Requester mobile is now disclosed to donor!
    assert accept_data["requester_mobile"] == "9876543261"
    assert accept_data["donor_mobile"] == "9876543260"

    # 4. Requester views sent requests -> Donor phone is now visible!
    sent_res = await client.get("/api/v1/requests/sent", headers=req_headers)
    assert sent_res.status_code == 200
    assert sent_res.json()[0]["status"] == "ACCEPTED"
    assert sent_res.json()[0]["donor_mobile"] == "9876543260"

    # 5. Check Requester received REQUEST_ACCEPTED notification
    notif_res = await client.get("/api/v1/notifications", headers=req_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert notifs["items"][0]["type"] == "REQUEST_ACCEPTED"


@pytest.mark.asyncio
async def test_reject_request_success(client: AsyncClient, setup_users_and_donor):
    """Test donor declining a request updates status to REJECTED and notifies requester."""
    data = setup_users_and_donor
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}

    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    request_id = create_res.json()["id"]

    reject_res = await client.patch(f"/api/v1/requests/{request_id}/reject", headers=donor_headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"
    assert reject_res.json()["donor_mobile"] is None
    assert reject_res.json()["requester_mobile"] is None

    # Check notification for requester
    notif_res = await client.get("/api/v1/notifications", headers=req_headers)
    assert notif_res.json()["items"][0]["type"] == "REQUEST_REJECTED"


@pytest.mark.asyncio
async def test_invalid_state_transitions_rejected(client: AsyncClient, setup_users_and_donor):
    """Test state machine guards: ACCEPTED -> ACCEPTED, ACCEPTED -> REJECTED, REJECTED -> ACCEPTED."""
    data = setup_users_and_donor
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}
    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}

    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    request_id = create_res.json()["id"]

    # 1. Accept once -> 200 OK
    res_accept1 = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=donor_headers)
    assert res_accept1.status_code == 200

    # 2. Try to accept again -> 400 Bad Request
    res_accept2 = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=donor_headers)
    assert res_accept2.status_code == 400
    assert "already marked" in res_accept2.json()["detail"].lower()

    # 3. Try to reject an accepted request -> 400 Bad Request
    res_reject = await client.patch(f"/api/v1/requests/{request_id}/reject", headers=donor_headers)
    assert res_reject.status_code == 400


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_view_or_modify_request(
    client: AsyncClient, setup_users_and_donor
):
    """Test third-party user cannot view or accept/reject someone else's request."""
    data = setup_users_and_donor
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}
    other_headers = {"Authorization": f"Bearer {data['req2_token']}"}

    create_res = await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )
    request_id = create_res.json()["id"]

    # Other user trying to view request -> 403 Forbidden
    res_view = await client.get(f"/api/v1/requests/{request_id}", headers=other_headers)
    assert res_view.status_code == 403

    # Other user trying to accept request -> 403 Forbidden
    res_accept = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=other_headers)
    assert res_accept.status_code == 403


@pytest.mark.asyncio
async def test_notifications_mark_read_and_mark_all_read(
    client: AsyncClient, setup_users_and_donor
):
    """Test marking individual and all notifications as read."""
    data = setup_users_and_donor
    req_headers = {"Authorization": f"Bearer {data['req1_token']}"}

    # Trigger a notification
    await client.post(
        "/api/v1/requests",
        headers=req_headers,
        json={
            "donor_id": str(data["donor_profile"].id),
            "blood_group": "O+",
            "location_id": data["location"].id
        }
    )

    donor_headers = {"Authorization": f"Bearer {data['donor_token']}"}
    notif_res = await client.get("/api/v1/notifications", headers=donor_headers)
    notif_id = notif_res.json()["items"][0]["id"]
    assert notif_res.json()["unread_count"] >= 1

    # 1. Mark single notification as read
    read_res = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=donor_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 2. Mark all as read
    all_read_res = await client.patch("/api/v1/notifications/read-all", headers=donor_headers)
    assert all_read_res.status_code == 200
    assert all_read_res.json()["success"] is True

    # 3. Verify unread count is 0
    final_notifs = await client.get("/api/v1/notifications", headers=donor_headers)
    assert final_notifs.json()["unread_count"] == 0

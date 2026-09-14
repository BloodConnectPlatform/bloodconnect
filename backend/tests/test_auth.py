from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, hash_otp
from app.models.enums import UserRole
from app.models.otp import OtpVerification
from app.models.user import User
from app.services.sms import default_sms_provider


@pytest.fixture(autouse=True)
def clear_sms_provider():
    default_sms_provider.clear()
    yield
    default_sms_provider.clear()


@pytest.mark.asyncio
async def test_send_otp_success(client: AsyncClient, db_session: AsyncSession):
    """Test sending OTP generates a record, hashes it, and sends SMS."""
    response = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543210"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "expires_in_seconds" in data
    assert data["cooldown_seconds"] == 60

    # Verify SMS was dispatched
    assert len(default_sms_provider.sent_messages) == 1
    assert default_sms_provider.sent_messages[0]["mobile"] == "9876543210"

    # Verify DB record exists and is hashed
    stmt = select(OtpVerification).where(OtpVerification.mobile == "9876543210")
    result = await db_session.execute(stmt)
    otp_record = result.scalar_one()
    assert otp_record.attempts == 0
    assert otp_record.verified_at is None
    # Ensure plaintext OTP is NOT in database
    assert len(otp_record.otp_hash) == 64  # SHA-256 hex string


@pytest.mark.asyncio
async def test_send_otp_cooldown_rate_limit(client: AsyncClient):
    """Test 60-second cooldown rate limiting on OTP requests."""
    # First request
    res1 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543211"})
    assert res1.status_code == 200

    # Immediate second request should trigger 429
    res2 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543211"})
    assert res2.status_code == 429
    assert "wait" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_otp_valid(client: AsyncClient, db_session: AsyncSession):
    """Test verifying a valid OTP returns verification token."""
    # Send OTP
    res_send = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543212"})
    assert res_send.status_code == 200
    debug_otp = res_send.json()["debug_otp"]

    # Verify OTP
    res_verify = await client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": "9876543212", "otp": debug_otp}
    )
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["success"] is True
    assert verify_data["is_registered"] is False
    assert verify_data["verification_token"] is not None

    # Check decoded verification token
    token_payload = decode_token(verify_data["verification_token"])
    assert token_payload["sub"] == "9876543212"
    assert token_payload["purpose"] == "otp_verified"


@pytest.mark.asyncio
async def test_verify_otp_invalid_and_attempt_limit(client: AsyncClient):
    """Test incorrect OTP increments attempt counter and blocks after 3 failures."""
    res_send = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543213"})
    assert res_send.status_code == 200

    # Attempt 1: wrong OTP
    res1 = await client.post("/api/v1/auth/verify-otp", json={"mobile": "9876543213", "otp": "000000"})
    assert res1.status_code == 400
    assert "2 attempt(s) remaining" in res1.json()["detail"]

    # Attempt 2: wrong OTP
    res2 = await client.post("/api/v1/auth/verify-otp", json={"mobile": "9876543213", "otp": "000000"})
    assert res2.status_code == 400
    assert "1 attempt(s) remaining" in res2.json()["detail"]

    # Attempt 3: wrong OTP
    res3 = await client.post("/api/v1/auth/verify-otp", json={"mobile": "9876543213", "otp": "000000"})
    assert res3.status_code == 400
    assert "maximum attempts reached" in res3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_with_otp_success(client: AsyncClient, db_session: AsyncSession):
    """Test login flow for registered user issuing valid JWT access and refresh tokens."""
    # Create existing user
    user = User(name="Registered User", mobile="9876543214", role=UserRole.DONOR)
    db_session.add(user)
    await db_session.commit()

    # Send OTP
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543214"})
    assert send_res.status_code == 200
    debug_otp = send_res.json()["debug_otp"]

    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"mobile": "9876543214", "otp": debug_otp}
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Registered User"
    assert data["user"]["role"] == "DONOR"

    # Validate access token claims
    payload = decode_token(data["access_token"])
    assert payload["sub"] == str(user.id)
    assert payload["role"] == "DONOR"
    assert payload["token_type"] == "access"


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient):
    """Test login fails with 404 if mobile number is not registered."""
    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543215"})
    assert send_res.status_code == 200
    debug_otp = send_res.json()["debug_otp"]

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"mobile": "9876543215", "otp": debug_otp}
    )
    assert login_res.status_code == 404
    assert "not found" in login_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_deactivated_user(client: AsyncClient, db_session: AsyncSession):
    """Test login fails with 403 if user account is deactivated."""
    user = User(name="Deactivated User", mobile="9876543216", role=UserRole.REQUESTER, is_active=False)
    db_session.add(user)
    await db_session.commit()

    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543216"})
    debug_otp = send_res.json()["debug_otp"]

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"mobile": "9876543216", "otp": debug_otp}
    )
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db_session: AsyncSession):
    """Test exchanging refresh token for a new access token."""
    user = User(name="Token User", mobile="9876543217", role=UserRole.REQUESTER)
    db_session.add(user)
    await db_session.commit()

    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543217"})
    debug_otp = send_res.json()["debug_otp"]

    login_res = await client.post("/api/v1/auth/login", json={"mobile": "9876543217", "otp": debug_otp})
    refresh_token = login_res.json()["refresh_token"]

    # Use refresh token
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/auth/me returns profile for valid Bearer token."""
    user = User(name="Me User", mobile="9876543218", role=UserRole.ADMIN)
    db_session.add(user)
    await db_session.commit()

    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543218"})
    debug_otp = send_res.json()["debug_otp"]

    login_res = await client.post("/api/v1/auth/login", json={"mobile": "9876543218", "otp": debug_otp})
    access_token = login_res.json()["access_token"]

    # Call /me with Bearer token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["name"] == "Me User"
    assert me_data["role"] == "ADMIN"
    assert me_data["mobile"] == "9876543218"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test GET /api/v1/auth/me returns 401 without Bearer token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test POST /api/v1/auth/logout with authenticated session."""
    user = User(name="Logout User", mobile="9876543219", role=UserRole.REQUESTER)
    db_session.add(user)
    await db_session.commit()

    send_res = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543219"})
    debug_otp = send_res.json()["debug_otp"]
    login_res = await client.post("/api/v1/auth/login", json={"mobile": "9876543219", "otp": debug_otp})
    access_token = login_res.json()["access_token"]

    logout_res = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True


@pytest.mark.asyncio
async def test_role_authorization_enforcement(client: AsyncClient, db_session: AsyncSession):
    """Test role checker dependency correctly allows authorized role and rejects unauthorized role."""
    from app.core.dependencies import require_admin, require_donor
    from fastapi import APIRouter, Depends

    test_router = APIRouter()

    @test_router.get("/admin-only")
    async def admin_only_endpoint(admin: User = Depends(require_admin)):
        return {"authorized": True, "admin": admin.name}

    @test_router.get("/donor-only")
    async def donor_only_endpoint(donor: User = Depends(require_donor)):
        return {"authorized": True, "donor": donor.name}

    from app.main import app
    app.include_router(test_router, prefix="/api/v1/test-roles")

    # Create a requester user and an admin user
    requester = User(name="Regular Requester", mobile="9876543220", role=UserRole.REQUESTER)
    admin = User(name="Master Admin", mobile="9876543221", role=UserRole.ADMIN)
    donor = User(name="Registered Donor", mobile="9876543222", role=UserRole.DONOR)
    db_session.add_all([requester, admin, donor])
    await db_session.commit()

    # Login Requester
    send1 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543220"})
    log1 = await client.post("/api/v1/auth/login", json={"mobile": "9876543220", "otp": send1.json()["debug_otp"]})
    req_token = log1.json()["access_token"]

    # Login Admin
    send2 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543221"})
    log2 = await client.post("/api/v1/auth/login", json={"mobile": "9876543221", "otp": send2.json()["debug_otp"]})
    admin_token = log2.json()["access_token"]

    # Login Donor
    send3 = await client.post("/api/v1/auth/send-otp", json={"mobile": "9876543222"})
    log3 = await client.post("/api/v1/auth/login", json={"mobile": "9876543222", "otp": send3.json()["debug_otp"]})
    donor_token = log3.json()["access_token"]

    # 1. Requester accessing admin-only endpoint -> 403 Forbidden
    res = await client.get("/api/v1/test-roles/admin-only", headers={"Authorization": f"Bearer {req_token}"})
    assert res.status_code == 403
    assert "ADMIN" in res.json()["detail"]

    # 2. Admin accessing admin-only endpoint -> 200 OK
    res = await client.get("/api/v1/test-roles/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["authorized"] is True

    # 3. Requester accessing donor-only endpoint -> 403 Forbidden
    res = await client.get("/api/v1/test-roles/donor-only", headers={"Authorization": f"Bearer {req_token}"})
    assert res.status_code == 403

    # 4. Donor accessing donor-only endpoint -> 200 OK
    res = await client.get("/api/v1/test-roles/donor-only", headers={"Authorization": f"Bearer {donor_token}"})
    assert res.status_code == 200
    assert res.json()["authorized"] is True


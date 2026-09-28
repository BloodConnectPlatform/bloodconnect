import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_whatsapp_token
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, UserRole
from app.models.location import Location
from app.models.user import User
from app.models.whatsapp_login_token import WhatsAppLoginToken
from app.services.whatsapp_auth_service import whatsapp_auth_service
from app.services.whatsapp_service import default_mock_whatsapp_provider


@pytest_asyncio.fixture(autouse=True)
async def reset_mock_provider_and_rate_limits():
    """Clear in-memory mock messages and rate limiters before and after each test."""
    default_mock_whatsapp_provider.clear()
    whatsapp_auth_service.clear_ip_rate_limits()
    yield
    default_mock_whatsapp_provider.clear()
    whatsapp_auth_service.clear_ip_rate_limits()


@pytest_asyncio.fixture(scope="function")
async def setup_auth_users(db_session: AsyncSession):
    """Seed test users for WhatsApp authentication testing."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # Active Donor User
    donor_user = User(
        name="Arun Donor",
        mobile="9876543201",
        role=UserRole.DONOR,
        is_active=True
    )
    db_session.add(donor_user)
    await db_session.flush()

    donor_profile = DonorProfile(
        user_id=donor_user.id,
        date_of_birth=datetime(1992, 4, 15).date(),
        blood_group=BloodGroup.O_POS,
        location_id=loc.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )
    db_session.add(donor_profile)

    # Active Requester User
    requester_user = User(
        name="Priya Requester",
        mobile="9876543220",
        role=UserRole.REQUESTER,
        is_active=True
    )
    db_session.add(requester_user)

    # Active Admin User
    admin_user = User(
        name="Admin User",
        mobile="9876543299",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)

    # Deactivated User
    deactivated_user = User(
        name="Deactivated Dave",
        mobile="9876543228",
        role=UserRole.DONOR,
        is_active=False
    )
    db_session.add(deactivated_user)

    await db_session.commit()
    await db_session.refresh(donor_user)
    await db_session.refresh(requester_user)
    await db_session.refresh(admin_user)
    await db_session.refresh(deactivated_user)

    return {
        "donor": donor_user,
        "requester": requester_user,
        "admin": admin_user,
        "deactivated": deactivated_user
    }


def create_whatsapp_webhook_payload(mobile: str, text: str, msg_id: str = "wamid.test.001") -> dict:
    """Helper to generate a Meta WhatsApp webhook payload for a text message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_TEST_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": f"91{mobile}" if not mobile.startswith("91") else mobile,
                                    "id": msg_id,
                                    "timestamp": "1726960000",
                                    "text": {"body": text},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }


# -----------------------------------------------------------------------------
# 1. LOGIN from Registered WhatsApp Number
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_login_registered_user(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test sending 'LOGIN' from a registered number dispatches a magic link with hashed token in DB."""
    donor: User = setup_auth_users["donor"]
    payload = create_whatsapp_webhook_payload(mobile=donor.mobile, text="LOGIN", msg_id="wamid.login.reg.001")

    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "EVENT_RECEIVED"

    # Verify message was dispatched via WhatsApp mock provider
    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    msg_body = sent[0]["text"]
    assert "Blood Connect Login" in msg_body
    assert "This link expires in 5 minutes" in msg_body

    # Extract token from magic link URL in message
    match = re.search(r"token=([A-Za-z0-9_-]+)", msg_body)
    assert match is not None
    raw_token = match.group(1)
    assert len(raw_token) >= 32

    # Verify DB token record
    token_hash = hash_whatsapp_token(raw_token)
    stmt = select(WhatsAppLoginToken).where(WhatsAppLoginToken.token_hash == token_hash)
    db_token = (await db_session.execute(stmt)).scalar_one_or_none()

    assert db_token is not None
    assert db_token.user_id == donor.id
    assert db_token.whatsapp_phone == donor.mobile
    assert db_token.used_at is None
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc) if db_token.expires_at.tzinfo is None else db_token.expires_at
    assert expires_at_aware > datetime.now(timezone.utc)
    # Ensure raw token is NEVER stored in database
    assert db_token.token_hash != raw_token


# -----------------------------------------------------------------------------
# 2. LOGIN with Capitalization & Surrounding Whitespace Variants
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("text_variant", ["login", "Login", "LoGiN", "  LOGIN  ", "\n\tLOGIN\t\n "])
@pytest.mark.asyncio
async def test_whatsapp_login_case_and_whitespace_insensitivity(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict,
    text_variant: str
):
    """Test that 'login', 'Login', 'LoGiN' and whitespace surrounding variants trigger successfully."""
    requester: User = setup_auth_users["requester"]
    payload = create_whatsapp_webhook_payload(
        mobile=requester.mobile,
        text=text_variant,
        msg_id=f"wamid.variant.{hash(text_variant)}"
    )

    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200

    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    assert "Blood Connect Login" in sent[0]["text"]


# -----------------------------------------------------------------------------
# 3. Non-Command Messages Containing LOGIN As Substring
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("non_command", [
    "I want to login",
    "How do I login to blood connect?",
    "LOGIN please help",
    "my login is broken"
])
@pytest.mark.asyncio
async def test_whatsapp_non_command_sentences_ignored(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict,
    non_command: str
):
    """Test that messages containing LOGIN as part of a sentence do NOT trigger the login flow."""
    donor: User = setup_auth_users["donor"]
    payload = create_whatsapp_webhook_payload(
        mobile=donor.mobile,
        text=non_command,
        msg_id=f"wamid.noncmd.{hash(non_command)}"
    )

    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200

    # No WhatsApp message sent & no tokens generated
    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 0

    tokens_stmt = select(WhatsAppLoginToken)
    tokens = (await db_session.execute(tokens_stmt)).scalars().all()
    assert len(tokens) == 0


# -----------------------------------------------------------------------------
# 4. LOGIN from Unregistered WhatsApp Number
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_login_unregistered_number(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Test that unregistered phone number receives registration prompt and no token is created."""
    unregistered_phone = "9999888877"
    payload = create_whatsapp_webhook_payload(mobile=unregistered_phone, text="LOGIN", msg_id="wamid.unreg.001")

    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200

    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    assert "We couldn't find a Blood Connect account linked to this WhatsApp number. Please register first." in sent[0]["text"]

    # Verify NO token created in DB
    stmt = select(WhatsAppLoginToken)
    tokens = (await db_session.execute(stmt)).scalars().all()
    assert len(tokens) == 0


# -----------------------------------------------------------------------------
# 5. LOGIN from Deactivated User
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_login_deactivated_user(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test that deactivated account receives contact support reply and no token is generated."""
    deactivated: User = setup_auth_users["deactivated"]
    payload = create_whatsapp_webhook_payload(mobile=deactivated.mobile, text="LOGIN", msg_id="wamid.deact.001")

    response = await client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200

    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    assert "Your Blood Connect account has been deactivated" in sent[0]["text"]

    stmt = select(WhatsAppLoginToken)
    tokens = (await db_session.execute(stmt)).scalars().all()
    assert len(tokens) == 0


# -----------------------------------------------------------------------------
# 6. Magic Link Redemption Flow (GET & POST)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_magic_link_redemption_success_json_and_browser(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test successful magic link redemption returns valid JWT session and marks token used."""
    donor: User = setup_auth_users["donor"]
    raw_token, token_obj = await whatsapp_auth_service.create_whatsapp_login_token(
        db=db_session,
        user=donor,
        whatsapp_phone=donor.mobile
    )

    # 1. Test programmatic JSON redemption via POST /api/v1/auth/whatsapp/redeem
    res_post = await client.post(
        "/api/v1/auth/whatsapp/redeem",
        json={"token": raw_token}
    )
    assert res_post.status_code == 200
    data = res_post.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["mobile"] == donor.mobile
    assert data["user"]["role"] == "DONOR"

    # 2. Verify token atomically marked used in DB
    await db_session.refresh(token_obj)
    assert token_obj.used_at is not None


@pytest.mark.asyncio
async def test_magic_link_redemption_browser_html_redirect(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test GET /auth/whatsapp returns auto-login HTML page redirecting to dashboard."""
    requester: User = setup_auth_users["requester"]
    raw_token, _ = await whatsapp_auth_service.create_whatsapp_login_token(
        db=db_session,
        user=requester,
        whatsapp_phone=requester.mobile
    )

    res = await client.get(
        "/auth/whatsapp",
        params={"token": raw_token},
        headers={"Accept": "text/html,application/xhtml+xml"}
    )
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Signing in to Blood Connect..." in res.text
    # Response is either same-origin (localStorage) or cross-origin (callback redirect)
    has_localstorage = "localStorage.setItem('access_token'" in res.text
    has_callback_redirect = "/auth/whatsapp/callback#" in res.text
    assert has_localstorage or has_callback_redirect, "Expected either localStorage or callback redirect in HTML"
    if has_localstorage:
        assert "/requester/dashboard" in res.text
    elif has_callback_redirect:
        import base64
        import json
        hash_b64 = res.text.split("/auth/whatsapp/callback#")[1].split('"')[0]
        hash_b64 += "=" * ((4 - len(hash_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(hash_b64.encode()).decode())
        assert payload["redirect"] == "/requester/dashboard"


# -----------------------------------------------------------------------------
# 7. Expired Token Redemption
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_expired_token_redemption(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test that redeeming an expired token returns a generic error."""
    donor: User = setup_auth_users["donor"]
    raw_token, token_obj = await whatsapp_auth_service.create_whatsapp_login_token(
        db=db_session,
        user=donor,
        whatsapp_phone=donor.mobile
    )

    # Manually expire the token in DB
    token_obj.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    # Attempt redemption via GET
    res_get = await client.get(
        "/auth/whatsapp",
        params={"token": raw_token},
        headers={"Accept": "application/json"}
    )
    assert res_get.status_code == 400
    assert "This login link is invalid or has expired" in res_get.json()["detail"]


# -----------------------------------------------------------------------------
# 8. Token Reuse & Already-Used Token
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_token_reuse_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test that a token cannot be reused once redeemed."""
    donor: User = setup_auth_users["donor"]
    raw_token, _ = await whatsapp_auth_service.create_whatsapp_login_token(
        db=db_session,
        user=donor,
        whatsapp_phone=donor.mobile
    )

    # First redemption -> Success
    res1 = await client.post(
        "/api/v1/auth/whatsapp/redeem",
        json={"token": raw_token}
    )
    assert res1.status_code == 200

    # Second redemption attempt -> Fails
    res2 = await client.post(
        "/api/v1/auth/whatsapp/redeem",
        json={"token": raw_token}
    )
    assert res2.status_code == 400
    assert "This login link is invalid or has expired" in res2.json()["detail"]


# -----------------------------------------------------------------------------
# 9. Malformed Token Redemption
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_malformed_token_redemption(client: AsyncClient):
    """Test that malformed, short, or invalid tokens are safely rejected."""
    # Empty token
    res_empty = await client.get("/auth/whatsapp?token=", headers={"Accept": "application/json"})
    assert res_empty.status_code == 400

    # Non-existent token
    res_fake = await client.post(
        "/api/v1/auth/whatsapp/redeem",
        json={"token": "invalid_non_existent_token_string_123456"}
    )
    assert res_fake.status_code == 400
    assert "This login link is invalid or has expired" in res_fake.json()["detail"]


# -----------------------------------------------------------------------------
# 10. Atomic Concurrency / Simultaneous Token Redemption Race Condition
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_simultaneous_token_redemption_race_condition(
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test that multiple concurrent requests to redeem the same token results in exactly ONE success."""
    from fastapi import HTTPException
    from tests.conftest import TestSessionLocal

    donor: User = setup_auth_users["donor"]
    raw_token, _ = await whatsapp_auth_service.create_whatsapp_login_token(
        db=db_session,
        user=donor,
        whatsapp_phone=donor.mobile
    )

    # Concurrently attempt 5 simultaneous redemptions with isolated DB sessions
    async def attempt_redeem(task_id: int):
        async with TestSessionLocal() as session:
            try:
                res, user = await whatsapp_auth_service.redeem_whatsapp_login_token(
                    db=session,
                    raw_token=raw_token,
                    client_ip=f"10.0.0.{task_id + 1}"
                )
                return 200
            except HTTPException as e:
                return e.status_code

    status_codes = await asyncio.gather(*[attempt_redeem(i) for i in range(5)])
    assert status_codes.count(200) == 1, f"Expected exactly 1 success, got status codes: {status_codes}"
    assert status_codes.count(400) == 4, f"Expected 4 rejections, got status codes: {status_codes}"


# -----------------------------------------------------------------------------
# 11. Rate Limiting & Cooldown Protection
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_login_cooldown_rate_limit(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict
):
    """Test that requesting LOGIN repeatedly within cooldown triggers rate limit notice."""
    donor: User = setup_auth_users["donor"]

    # 1. First LOGIN -> Success
    res1 = await client.post(
        "/webhooks/whatsapp",
        json=create_whatsapp_webhook_payload(mobile=donor.mobile, text="LOGIN", msg_id="wamid.rate.001")
    )
    assert res1.status_code == 200
    assert len(default_mock_whatsapp_provider.sent_messages) == 1

    # 2. Second immediate LOGIN -> Cooldown triggered
    res2 = await client.post(
        "/webhooks/whatsapp",
        json=create_whatsapp_webhook_payload(mobile=donor.mobile, text="LOGIN", msg_id="wamid.rate.002")
    )
    assert res2.status_code == 200
    assert len(default_mock_whatsapp_provider.sent_messages) == 2
    assert "A login link was recently sent" in default_mock_whatsapp_provider.sent_messages[1]["text"]

    # Only 1 token created in DB
    tokens_stmt = select(WhatsAppLoginToken)
    tokens = (await db_session.execute(tokens_stmt)).scalars().all()
    assert len(tokens) == 1


# -----------------------------------------------------------------------------
# 12. Security & Privacy Log Check (No Raw Token in Logs)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_raw_token_not_in_logs(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_auth_users: dict,
    caplog
):
    """Verify raw magic login token does not appear in application logs."""
    caplog.set_level(logging.DEBUG)
    donor: User = setup_auth_users["donor"]

    # Trigger LOGIN via webhook
    await client.post(
        "/webhooks/whatsapp",
        json=create_whatsapp_webhook_payload(mobile=donor.mobile, text="LOGIN", msg_id="wamid.log.001")
    )

    # Extract the raw token
    sent_msg = default_mock_whatsapp_provider.sent_messages[0]["text"]
    raw_token = re.search(r"token=([A-Za-z0-9_-]+)", sent_msg).group(1)

    # Redeem token
    await client.post(
        "/api/v1/auth/whatsapp/redeem",
        json={"token": raw_token}
    )

    # Check all captured log output
    full_log_text = caplog.text
    assert raw_token not in full_log_text, "Security violation: raw token appeared in logs!"


# -----------------------------------------------------------------------------
# 13. WhatsApp Config Endpoint
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_config_endpoints(client: AsyncClient):
    """Verify both /auth/whatsapp/config and /api/v1/auth/whatsapp/config return valid wa.me link."""
    # Test v1 endpoint
    res1 = await client.get("/api/v1/auth/whatsapp/config")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "whatsapp_phone_number" in data1
    assert "login_url" in data1
    assert "wa.me" in data1["login_url"]
    assert "text=LOGIN" in data1["login_url"]

    # Test top-level alias
    res2 = await client.get("/auth/whatsapp/config")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["login_url"] == data1["login_url"]


# -----------------------------------------------------------------------------
# 14. Unregistered Number In INITIAL_ADMIN_PHONE_NUMBERS Auto-Provisions as Admin
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_login_initial_admin_auto_provisioned(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch
):
    """Test that an unseeded number listed in INITIAL_ADMIN_PHONE_NUMBERS is auto-provisioned as ADMIN on WhatsApp LOGIN."""
    admin_test_phone = "9876599999"
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PHONE_NUMBERS", [admin_test_phone])

    # Send LOGIN from this unseeded admin phone
    payload = create_whatsapp_webhook_payload(
        mobile=admin_test_phone,
        text="LOGIN",
        msg_id="wamid.admin.auto.001"
    )
    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200

    # Verify WhatsApp message is a LOGIN link, NOT a registration link
    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    assert "Blood Connect Login" in sent[0]["text"]
    assert "/register" not in sent[0]["text"]

    # Verify user exists in database with UserRole.ADMIN
    stmt = select(User).where(User.mobile == admin_test_phone)
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None
    assert user.role == UserRole.ADMIN
    assert user.is_active is True


# -----------------------------------------------------------------------------
# 15. Production URL Normalization (api.bloodconnect.online -> www.bloodconnect.online)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_whatsapp_register_normalizes_api_subdomain_to_frontend(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch
):
    """Test that even if WHATSAPP_MAGIC_LINK_BASE_URL or PUBLIC_API_URL is set to api.bloodconnect.online,
    the registration magic link points to www.bloodconnect.online/register."""
    monkeypatch.setattr(settings, "WHATSAPP_MAGIC_LINK_BASE_URL", "https://api.bloodconnect.online")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")

    unregistered_phone = "9888777666"
    payload = create_whatsapp_webhook_payload(
        mobile=unregistered_phone,
        text="REGISTER",
        msg_id="wamid.reg.norm.001"
    )
    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200

    sent = default_mock_whatsapp_provider.sent_messages
    assert len(sent) == 1
    msg_text = sent[0]["text"]
    assert "https://www.bloodconnect.online/register?mobile=9888777666&token=" in msg_text
    assert "https://api.bloodconnect.online/register" not in msg_text


# -----------------------------------------------------------------------------
# 16. Backend GET /register and GET /login Redirects to Frontend
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_backend_register_and_login_routes_redirect_to_frontend(
    client: AsyncClient,
    monkeypatch
):
    """Test that hitting GET /register or GET /login on the API domain redirects to the frontend web app."""
    monkeypatch.setattr(settings, "WHATSAPP_MAGIC_LINK_BASE_URL", "https://api.bloodconnect.online")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")

    res_reg = await client.get(
        "/register?mobile=9843883304&token=sample_jwt_token",
        follow_redirects=False
    )
    assert res_reg.status_code == 307
    assert res_reg.headers["location"] == "https://www.bloodconnect.online/register?mobile=9843883304&token=sample_jwt_token"

    res_login = await client.get(
        "/login",
        follow_redirects=False
    )
    assert res_login.status_code == 307
    assert res_login.headers["location"] == "https://www.bloodconnect.online/login"




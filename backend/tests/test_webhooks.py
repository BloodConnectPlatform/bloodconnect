from datetime import datetime, timezone
import hashlib
import hmac
import json
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, NotificationChannel, NotificationDeliveryStatus, RequestStatus, UserRole
from app.models.location import Location
from app.models.notification_log import NotificationLog
from app.models.user import User
from app.models.webhook_event import WebhookEvent


@pytest_asyncio.fixture(scope="function")
async def setup_webhook_entities(db_session: AsyncSession):
    """Set up test donor, requester, location, and a pending blood request."""
    loc = (await db_session.execute(select(Location).where(Location.name == "Coimbatore"))).scalar_one()

    # Donor User & Profile
    donor_user = User(
        name="Donor Dave",
        mobile="9876543250",
        role=UserRole.DONOR,
        is_active=True
    )
    db_session.add(donor_user)
    await db_session.flush()

    donor_profile = DonorProfile(
        user_id=donor_user.id,
        date_of_birth=datetime(1995, 1, 1).date(),
        blood_group="O+",
        location_id=loc.id,
        is_otp_verified=True,
        is_available=True,
        is_active=True,
        contact_consent=True
    )
    db_session.add(donor_profile)
    await db_session.flush()

    # Requester User
    requester_user = User(
        name="Requester Ryan",
        mobile="9876543251",
        role=UserRole.REQUESTER,
        is_active=True
    )
    db_session.add(requester_user)
    await db_session.flush()

    # Pending Blood Request
    blood_req = BloodRequest(
        requester_id=requester_user.id,
        donor_id=donor_profile.id,
        blood_group=BloodGroup.O_POS,
        location_id=loc.id,
        patient_name="Patient Peter",
        hospital_name="Apex Hospital",
        status=RequestStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(blood_req)
    await db_session.commit()
    await db_session.refresh(blood_req)

    return {
        "donor_user": donor_user,
        "donor_profile": donor_profile,
        "requester_user": requester_user,
        "blood_request": blood_req,
        "location": loc
    }


# -----------------------------------------------------------------------------
# GET /webhooks/whatsapp Verification Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_webhook_get_verification_success(client: AsyncClient):
    """Test GET webhook verification with valid token returns challenge string."""
    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 200
    assert response.text == "1158201444"


@pytest.mark.asyncio
async def test_webhook_get_verification_invalid_token(client: AsyncClient):
    """Test GET webhook verification with incorrect token returns 403 Forbidden."""
    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token_value",
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 403
    assert "Invalid verification token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_get_verification_missing_params(client: AsyncClient):
    """Test GET webhook verification with missing params returns 400 Bad Request."""
    response = await client.get("/webhooks/whatsapp")
    assert response.status_code == 400


# -----------------------------------------------------------------------------
# POST /webhooks/whatsapp Signature Validation Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_webhook_post_signature_validation(client: AsyncClient):
    """Test HMAC-SHA256 signature verification on incoming webhook payloads."""
    orig_sig_setting = settings.WEBHOOK_VERIFY_SIGNATURE
    orig_secret = settings.META_APP_SECRET
    settings.WEBHOOK_VERIFY_SIGNATURE = True
    settings.META_APP_SECRET = "test_meta_app_secret_12345"

    try:
        payload = {"entry": []}
        body_bytes = json.dumps(payload).encode("utf-8")

        # Valid signature
        valid_hmac = hmac.new(b"test_meta_app_secret_12345", body_bytes, hashlib.sha256).hexdigest()
        valid_header = f"sha256={valid_hmac}"

        res_valid = await client.post(
            "/webhooks/whatsapp",
            content=body_bytes,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": valid_header}
        )
        assert res_valid.status_code == 200

        # Invalid signature
        res_invalid = await client.post(
            "/webhooks/whatsapp",
            content=body_bytes,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalid_hex"}
        )
        assert res_invalid.status_code == 401
    finally:
        settings.WEBHOOK_VERIFY_SIGNATURE = orig_sig_setting
        settings.META_APP_SECRET = orig_secret


# -----------------------------------------------------------------------------
# POST /webhooks/whatsapp Interactive Button Replies
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_webhook_interactive_accept_request(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_webhook_entities: dict
):
    """Test donor clicking ACCEPT button transitions request to ACCEPTED."""
    data = setup_webhook_entities
    req: BloodRequest = data["blood_request"]
    donor_user: User = data["donor_user"]

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": f"91{donor_user.mobile}",
                                    "id": "wamid.accept.001",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": f"ACCEPT:{req.id}",
                                            "title": "Accept"
                                        }
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "EVENT_RECEIVED"

    # Verify Database state
    stmt = select(BloodRequest).where(BloodRequest.id == req.id)
    updated_req = (await db_session.execute(stmt)).scalar_one()
    assert updated_req.status == RequestStatus.ACCEPTED
    assert updated_req.responded_at is not None

    # Verify idempotency event recorded
    evt_stmt = select(WebhookEvent).where(WebhookEvent.event_id == "wamid.accept.001")
    evt = (await db_session.execute(evt_stmt)).scalar_one_or_none()
    assert evt is not None


@pytest.mark.asyncio
async def test_webhook_interactive_reject_request(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_webhook_entities: dict
):
    """Test donor clicking REJECT/Not Available button transitions request to REJECTED."""
    data = setup_webhook_entities
    req: BloodRequest = data["blood_request"]
    donor_user: User = data["donor_user"]

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": f"91{donor_user.mobile}",
                                    "id": "wamid.reject.001",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": f"REJECT:{req.id}",
                                            "title": "Not Available"
                                        }
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200

    stmt = select(BloodRequest).where(BloodRequest.id == req.id)
    updated_req = (await db_session.execute(stmt)).scalar_one()
    assert updated_req.status == RequestStatus.REJECTED
    assert updated_req.responded_at is not None


@pytest.mark.asyncio
async def test_webhook_idempotency_duplicate_events(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_webhook_entities: dict
):
    """Test duplicate webhook delivery is safely ignored without re-executing."""
    data = setup_webhook_entities
    req: BloodRequest = data["blood_request"]
    donor_user: User = data["donor_user"]

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": f"91{donor_user.mobile}",
                                    "id": "wamid.idempotent.001",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": f"ACCEPT:{req.id}",
                                            "title": "Accept"
                                        }
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    # 1. First delivery
    res1 = await client.post("/webhooks/whatsapp", json=payload)
    assert res1.status_code == 200

    # 2. Duplicate delivery with same event id
    res2 = await client.post("/webhooks/whatsapp", json=payload)
    assert res2.status_code == 200
    details = res2.json()["details"]
    assert details["processed"][0]["action"] == "duplicate_skipped"


@pytest.mark.asyncio
async def test_webhook_unauthorized_sender_phone(
    client: AsyncClient,
    db_session: AsyncSession,
    setup_webhook_entities: dict
):
    """Test spoofed / unauthorized sender cannot modify other donors' requests."""
    data = setup_webhook_entities
    req: BloodRequest = data["blood_request"]

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919999999999",  # Unrelated phone
                                    "id": "wamid.unauth.001",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": f"ACCEPT:{req.id}",
                                            "title": "Accept"
                                        }
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200

    # Request MUST remain PENDING
    stmt = select(BloodRequest).where(BloodRequest.id == req.id)
    req_db = (await db_session.execute(stmt)).scalar_one()
    assert req_db.status == RequestStatus.PENDING


@pytest.mark.asyncio
async def test_webhook_status_update_delivered(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Test message status updates (sent -> delivered) update notification_logs."""
    # 1. Insert a mock NotificationLog record
    msg_id = "wamid.status.test.001"
    log = NotificationLog(
        mobile="9876543250",
        channel=NotificationChannel.WHATSAPP,
        event_type="AUTH_OTP",
        provider="meta",
        provider_message_id=msg_id,
        status=NotificationDeliveryStatus.SENT,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(log)
    await db_session.commit()

    # 2. Post delivery status update
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": msg_id,
                                    "status": "delivered",
                                    "timestamp": "1600000000",
                                    "recipient_id": "919876543250"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res = await client.post("/webhooks/whatsapp", json=payload)
    assert res.status_code == 200

    # 3. Verify status updated in DB
    stmt = select(NotificationLog).where(NotificationLog.provider_message_id == msg_id)
    updated_log = (await db_session.execute(stmt)).scalar_one()
    assert updated_log.status == NotificationDeliveryStatus.DELIVERED
    assert updated_log.delivered_at is not None

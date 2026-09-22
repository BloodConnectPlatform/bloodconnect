import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import NotificationChannel, NotificationDeliveryStatus
from app.models.notification_log import NotificationLog
from app.services.notification_service import notification_service
from app.services.sms_service import default_mock_sms_provider
from app.services.whatsapp_service import default_mock_whatsapp_provider


@pytest.fixture(autouse=True)
def reset_providers():
    default_mock_whatsapp_provider.clear()
    default_mock_sms_provider.clear()
    notification_service.clear_recorded_logs()
    orig_primary = settings.NOTIFICATION_PRIMARY_CHANNEL
    orig_fallback = settings.NOTIFICATION_SMS_FALLBACK
    orig_provider = settings.NOTIFICATION_PROVIDER
    settings.NOTIFICATION_PRIMARY_CHANNEL = "whatsapp"
    settings.NOTIFICATION_SMS_FALLBACK = True
    settings.NOTIFICATION_PROVIDER = "mock"
    yield
    default_mock_whatsapp_provider.clear()
    default_mock_sms_provider.clear()
    notification_service.clear_recorded_logs()
    settings.NOTIFICATION_PRIMARY_CHANNEL = orig_primary
    settings.NOTIFICATION_SMS_FALLBACK = orig_fallback
    settings.NOTIFICATION_PROVIDER = orig_provider


@pytest.mark.asyncio
async def test_send_otp_via_whatsapp_primary(db_session: AsyncSession):
    """Test OTP notification sent via WhatsApp primary channel when WhatsApp succeeds."""
    result = await notification_service.send_otp(
        mobile="9876543210",
        otp_code="123456",
        expires_minutes=5,
        db=db_session
    )

    assert result.success is True
    assert result.channel_used == "WHATSAPP"
    assert result.fallback_used is False
    assert len(default_mock_whatsapp_provider.sent_messages) == 1
    assert len(default_mock_sms_provider.sent_messages) == 0

    # Verify audit log in database
    stmt = select(NotificationLog).where(NotificationLog.mobile == "9876543210")
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    assert len(logs) == 1
    assert logs[0].channel == NotificationChannel.WHATSAPP
    assert logs[0].event_type == "AUTH_OTP"
    assert logs[0].status == NotificationDeliveryStatus.SENT


@pytest.mark.asyncio
async def test_send_otp_whatsapp_failure_sms_fallback(db_session: AsyncSession):
    """Test fallback to SMS when WhatsApp dispatch fails and fallback is enabled."""
    default_mock_whatsapp_provider.simulate_failure = True

    result = await notification_service.send_otp(
        mobile="9876543211",
        otp_code="654321",
        expires_minutes=5,
        db=db_session
    )

    assert result.success is True
    assert result.channel_used == "SMS"
    assert result.fallback_used is True
    assert len(default_mock_sms_provider.sent_messages) == 1
    assert "654321" in default_mock_sms_provider.sent_messages[0]["message"]

    # Verify audit logs in database (one FAILED for WA, one SENT for SMS)
    stmt = select(NotificationLog).where(NotificationLog.mobile == "9876543211").order_by(NotificationLog.created_at.asc())
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    assert len(logs) == 2
    assert logs[0].channel == NotificationChannel.WHATSAPP
    assert logs[0].status == NotificationDeliveryStatus.FAILED
    assert logs[1].channel == NotificationChannel.SMS
    assert logs[1].status == NotificationDeliveryStatus.SENT


@pytest.mark.asyncio
async def test_send_otp_whatsapp_failure_no_fallback(db_session: AsyncSession):
    """Test failure when WhatsApp fails and SMS fallback is disabled."""
    default_mock_whatsapp_provider.simulate_failure = True
    settings.NOTIFICATION_SMS_FALLBACK = False

    result = await notification_service.send_otp(
        mobile="9876543212",
        otp_code="111222",
        expires_minutes=5,
        db=db_session
    )

    assert result.success is False
    assert result.channel_used == "WHATSAPP"
    assert result.fallback_used is False
    assert len(default_mock_sms_provider.sent_messages) == 0


@pytest.mark.asyncio
async def test_send_blood_request_notification(db_session: AsyncSession):
    """Test blood request notification formatted with interactive buttons."""
    req_id = uuid.uuid4()
    result = await notification_service.send_blood_request(
        donor_mobile="9876543213",
        blood_group="O+",
        location_name="Coimbatore",
        patient_name="John Doe",
        hospital_name="City Hospital",
        request_id=req_id,
        db=db_session
    )

    assert result.success is True
    assert result.channel_used == "WHATSAPP"
    assert len(default_mock_whatsapp_provider.sent_messages) == 1
    wa_msg = default_mock_whatsapp_provider.sent_messages[0]
    assert wa_msg["type"] == "interactive"
    assert "O+" in wa_msg["body_text"]
    assert "Coimbatore" in wa_msg["body_text"]
    assert f"ACCEPT:{req_id}" == wa_msg["buttons"][0]["reply"]["id"]
    assert f"REJECT:{req_id}" == wa_msg["buttons"][1]["reply"]["id"]


@pytest.mark.asyncio
async def test_send_request_lifecycle_notifications(db_session: AsyncSession):
    """Test accepted, rejected, cancelled, and reminder notifications."""
    req_id = uuid.uuid4()

    # 1. Accepted
    r1 = await notification_service.send_request_accepted(
        requester_mobile="9876543214",
        donor_name="Donor Dave",
        donor_mobile="9876543215",
        blood_group="A+",
        request_id=req_id,
        db=db_session
    )
    assert r1.success is True
    assert "Donor Dave" in default_mock_whatsapp_provider.sent_messages[-1]["text"]

    # 2. Rejected
    r2 = await notification_service.send_request_rejected(
        requester_mobile="9876543214",
        blood_group="A+",
        donor_name="Donor Dave",
        request_id=req_id,
        db=db_session
    )
    assert r2.success is True
    assert "Donor Dave" in default_mock_whatsapp_provider.sent_messages[-1]["text"]

    # 3. Cancelled
    r3 = await notification_service.send_request_cancelled(
        donor_mobile="9876543215",
        requester_name="Requester Ryan",
        blood_group="A+",
        request_id=req_id,
        db=db_session
    )
    assert r3.success is True

    # 4. Reminder
    r4 = await notification_service.send_request_reminder(
        donor_mobile="9876543215",
        blood_group="A+",
        location_name="Chennai",
        request_id=req_id,
        db=db_session
    )
    assert r4.success is True

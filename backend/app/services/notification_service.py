from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.models.notification import Notification
from app.models.notification_log import NotificationLog
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.sms_service import BaseSMSProvider, get_sms_provider
from app.services.whatsapp_service import (
    BaseWhatsAppProvider,
    MetaWhatsAppProvider,
    ProviderSendResult,
    get_whatsapp_provider,
)

logger = logging.getLogger("notification_service")


@dataclass
class NotificationResult:
    success: bool
    channel_used: str
    primary_channel: str
    fallback_used: bool = False
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)


class NotificationService:
    def __init__(
        self,
        whatsapp_provider: Optional[BaseWhatsAppProvider] = None,
        sms_provider: Optional[BaseSMSProvider] = None
    ):
        self._whatsapp_provider = whatsapp_provider
        self._sms_provider = sms_provider
        self.recorded_logs: List[Dict[str, Any]] = []

    @property
    def whatsapp_provider(self) -> BaseWhatsAppProvider:
        return self._whatsapp_provider or get_whatsapp_provider()

    @property
    def sms_provider(self) -> BaseSMSProvider:
        return self._sms_provider or get_sms_provider()

    # -------------------------------------------------------------------------
    # In-App Notification Methods (Preserved & Enhanced)
    # -------------------------------------------------------------------------
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str
    ) -> Notification:
        """Create a new in-app database notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            is_read=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> NotificationListResponse:
        """Retrieve user's notifications along with total unread count."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        result = await db.execute(query)
        notifications = result.scalars().all()

        unread_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        unread_res = await db.execute(unread_stmt)
        unread_count = unread_res.scalar() or 0

        total_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
        )
        total_res = await db.execute(total_stmt)
        total_count = total_res.scalar() or 0

        items = [NotificationResponse.model_validate(n) for n in notifications]

        return NotificationListResponse(
            items=items,
            unread_count=unread_count,
            total=total_count
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> NotificationResponse:
        """Mark an individual notification as read."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found."
            )

        notification.is_read = True
        await db.commit()
        await db.refresh(notification)
        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> int:
        """Mark all unread notifications for a user as read."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    # -------------------------------------------------------------------------
    # Notification Audit Logging Helper
    # -------------------------------------------------------------------------
    async def _record_audit_log(
        self,
        mobile: str,
        channel: NotificationChannel,
        event_type: str,
        provider: str,
        status_val: NotificationDeliveryStatus,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[dict] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """Record notification dispatch attempt in memory and database."""
        now = datetime.now(timezone.utc)
        log_entry = {
            "mobile": mobile,
            "channel": channel.value,
            "event_type": event_type,
            "provider": provider,
            "status": status_val.value,
            "provider_message_id": provider_message_id,
            "error_message": error_message,
            "user_id": str(user_id) if user_id else None,
            "created_at": now
        }
        self.recorded_logs.append(log_entry)

        if db is not None:
            try:
                db_log = NotificationLog(
                    user_id=user_id,
                    mobile=mobile,
                    channel=channel,
                    event_type=event_type,
                    provider=provider,
                    provider_message_id=provider_message_id,
                    status=status_val,
                    error_message=error_message,
                    details=details,
                    created_at=now
                )
                db.add(db_log)
                await db.commit()
            except Exception as e:
                logger.warning(f"[NotificationService] Failed to persist audit log to DB: {e}")

    # -------------------------------------------------------------------------
    # Multi-Channel Dispatch Strategy (WhatsApp Primary -> SMS Fallback)
    # -------------------------------------------------------------------------
    async def _dispatch_with_fallback(
        self,
        mobile: str,
        event_type: str,
        wa_dispatch_func,
        sms_text: str,
        sms_template_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Execute channel strategy: Try primary channel (WhatsApp); fallback to SMS if failed."""
        primary_channel = (settings.NOTIFICATION_PRIMARY_CHANNEL or "whatsapp").lower()

        if primary_channel == "whatsapp":
            # 1. Attempt WhatsApp Primary
            wa_result: ProviderSendResult = await wa_dispatch_func(self.whatsapp_provider)
            
            if wa_result.success:
                await self._record_audit_log(
                    mobile=mobile,
                    channel=NotificationChannel.WHATSAPP,
                    event_type=event_type,
                    provider=wa_result.provider,
                    status_val=NotificationDeliveryStatus.SENT,
                    provider_message_id=wa_result.provider_message_id,
                    details=wa_result.details,
                    user_id=user_id,
                    db=db
                )
                return NotificationResult(
                    success=True,
                    channel_used="WHATSAPP",
                    primary_channel="whatsapp",
                    fallback_used=False,
                    provider_message_id=wa_result.provider_message_id,
                    details=wa_result.details
                )

            # Log WhatsApp Failure
            await self._record_audit_log(
                mobile=mobile,
                channel=NotificationChannel.WHATSAPP,
                event_type=event_type,
                provider=wa_result.provider,
                status_val=NotificationDeliveryStatus.FAILED,
                error_message=wa_result.error_message,
                details=wa_result.details,
                user_id=user_id,
                db=db
            )

            # 2. Check SMS Fallback
            if settings.NOTIFICATION_SMS_FALLBACK:
                logger.info(f"[NotificationService] WhatsApp delivery failed for {mobile}. Falling back to SMS.")
                sms_result: ProviderSendResult = await self.sms_provider.send_sms(
                    mobile=mobile,
                    message=sms_text,
                    template_id=sms_template_id
                )

                if sms_result.success:
                    await self._record_audit_log(
                        mobile=mobile,
                        channel=NotificationChannel.SMS,
                        event_type=event_type,
                        provider=sms_result.provider,
                        status_val=NotificationDeliveryStatus.SENT,
                        provider_message_id=sms_result.provider_message_id,
                        details=sms_result.details,
                        user_id=user_id,
                        db=db
                    )
                    return NotificationResult(
                        success=True,
                        channel_used="SMS",
                        primary_channel="whatsapp",
                        fallback_used=True,
                        provider_message_id=sms_result.provider_message_id,
                        details=sms_result.details
                    )
                else:
                    await self._record_audit_log(
                        mobile=mobile,
                        channel=NotificationChannel.SMS,
                        event_type=event_type,
                        provider=sms_result.provider,
                        status_val=NotificationDeliveryStatus.FAILED,
                        error_message=sms_result.error_message,
                        details=sms_result.details,
                        user_id=user_id,
                        db=db
                    )
                    return NotificationResult(
                        success=False,
                        channel_used="SMS",
                        primary_channel="whatsapp",
                        fallback_used=True,
                        error_message=f"WhatsApp failed: {wa_result.error_message}; SMS fallback failed: {sms_result.error_message}"
                    )
            else:
                return NotificationResult(
                    success=False,
                    channel_used="WHATSAPP",
                    primary_channel="whatsapp",
                    fallback_used=False,
                    error_message=wa_result.error_message
                )

        else:
            # Primary channel is SMS
            sms_result = await self.sms_provider.send_sms(
                mobile=mobile,
                message=sms_text,
                template_id=sms_template_id
            )
            status_val = NotificationDeliveryStatus.SENT if sms_result.success else NotificationDeliveryStatus.FAILED
            await self._record_audit_log(
                mobile=mobile,
                channel=NotificationChannel.SMS,
                event_type=event_type,
                provider=sms_result.provider,
                status_val=status_val,
                provider_message_id=sms_result.provider_message_id,
                error_message=sms_result.error_message,
                details=sms_result.details,
                user_id=user_id,
                db=db
            )
            return NotificationResult(
                success=sms_result.success,
                channel_used="SMS",
                primary_channel="sms",
                fallback_used=False,
                provider_message_id=sms_result.provider_message_id,
                error_message=sms_result.error_message,
                details=sms_result.details
            )

    # -------------------------------------------------------------------------
    # High-Level Operations for Business Services
    # -------------------------------------------------------------------------
    async def send_otp(
        self,
        mobile: str,
        otp_code: str,
        expires_minutes: int,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Send verification OTP code via WhatsApp primary or SMS fallback."""
        sms_text = (
            f"Your Blood Connect verification code is {otp_code}. "
            f"Valid for {expires_minutes} minutes. Do not share this code with anyone."
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            template_name = settings.WHATSAPP_TEMPLATE_AUTH_OTP
            if template_name and template_name.lower() == "hello_world":
                return await provider.send_template(
                    to_mobile=mobile,
                    template_name="hello_world",
                    language_code="en_US",
                    components=[]
                )
            elif template_name and template_name != "none":
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": otp_code}
                        ]
                    }
                ]
                lang_code = settings.WHATSAPP_TEMPLATE_LANGUAGE or "en_US"
                return await provider.send_template(
                    to_mobile=mobile,
                    template_name=template_name,
                    language_code=lang_code,
                    components=components
                )
            else:
                return await provider.send_text(
                    to_mobile=mobile,
                    text=sms_text
                )

        return await self._dispatch_with_fallback(
            mobile=mobile,
            event_type="AUTH_OTP",
            wa_dispatch_func=_wa_send,
            sms_text=sms_text,
            sms_template_id=settings.MSG91_OTP_TEMPLATE_ID,
            user_id=user_id,
            db=db
        )

    async def send_blood_request(
        self,
        donor_mobile: str,
        blood_group: str,
        location_name: str,
        patient_name: Optional[str] = None,
        hospital_name: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Dispatch urgent blood donation request notification to a prospective donor."""
        patient_info = f" for patient '{patient_name}'" if patient_name else ""
        hospital_info = f" at {hospital_name}" if hospital_name else ""
        
        sms_text = (
            f"BloodConnect: Urgent {blood_group} blood request{patient_info} in {location_name}{hospital_info}. "
            f"Please check your BloodConnect dashboard to accept or decline."
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            req_id_str = str(request_id) if request_id else "unknown"
            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": f"ACCEPT:{req_id_str}",
                        "title": "Accept"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": f"REJECT:{req_id_str}",
                        "title": "Not Available"
                    }
                }
            ]
            body_text = (
                f"BloodConnect Urgent Blood Request\n\n"
                f"Blood group: {blood_group}\n"
                f"Location: {location_name}\n"
                f"Patient: {patient_name or 'Urgent requirement'}\n"
                f"Hospital: {hospital_name or 'Not specified'}\n\n"
                f"A patient needs your help. Please click Accept or Not Available below:"
            )
            return await provider.send_interactive_buttons(
                to_mobile=donor_mobile,
                body_text=body_text,
                buttons=buttons,
                header_text="Urgent Blood Donation Request",
                footer_text="BloodConnect Donor Platform"
            )

        return await self._dispatch_with_fallback(
            mobile=donor_mobile,
            event_type="BLOOD_REQUEST",
            wa_dispatch_func=_wa_send,
            sms_text=sms_text,
            user_id=user_id,
            db=db
        )

    async def send_request_accepted(
        self,
        requester_mobile: str,
        donor_name: str,
        donor_mobile: str,
        blood_group: str,
        request_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Notify requester that a donor has accepted their blood request and share contact details."""
        message = (
            f"BloodConnect Update: Great news! Donor {donor_name} has ACCEPTED your {blood_group} blood request. "
            f"Donor Contact: {donor_mobile}. Please connect with the donor to coordinate donation."
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            template_name = settings.WHATSAPP_TEMPLATE_REQUEST_ACCEPTED
            if template_name and template_name.lower() == "hello_world":
                return await provider.send_template(
                    to_mobile=requester_mobile,
                    template_name="hello_world",
                    language_code="en_US",
                    components=[]
                )
            elif template_name and template_name != "none" and isinstance(provider, MetaWhatsAppProvider):
                # Meta Cloud API Template: Great news! Donor {{1}} has ACCEPTED your {{2}} blood request. Donor Contact: {{3}}...
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": donor_name},
                            {"type": "text", "text": blood_group},
                            {"type": "text", "text": donor_mobile}
                        ]
                    }
                ]
                lang_code = settings.WHATSAPP_TEMPLATE_LANGUAGE or "en_US"
                return await provider.send_template(
                    to_mobile=requester_mobile,
                    template_name=template_name,
                    language_code=lang_code,
                    components=components
                )
            return await provider.send_text(to_mobile=requester_mobile, text=message)

        return await self._dispatch_with_fallback(
            mobile=requester_mobile,
            event_type="REQUEST_ACCEPTED",
            wa_dispatch_func=_wa_send,
            sms_text=message,
            user_id=user_id,
            db=db
        )

    async def send_request_rejected(
        self,
        requester_mobile: str,
        blood_group: str,
        donor_name: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Notify requester that donor is unable to donate at this time."""
        donor_display = f"Donor {donor_name}" if donor_name else "The donor"
        message = (
            f"BloodConnect Update: {donor_display} was unable to accept your {blood_group} blood request at this time. "
            f"Please browse other available matching donors on BloodConnect."
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            template_name = settings.WHATSAPP_TEMPLATE_REQUEST_REJECTED
            if template_name and template_name.lower() == "hello_world":
                return await provider.send_template(
                    to_mobile=requester_mobile,
                    template_name="hello_world",
                    language_code="en_US",
                    components=[]
                )
            elif template_name and template_name != "none" and isinstance(provider, MetaWhatsAppProvider):
                # Meta Cloud API Template: Donor {{1}} was unable to accept your {{2}} blood request at this time...
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": donor_name or "The requested donor"},
                            {"type": "text", "text": blood_group}
                        ]
                    }
                ]
                lang_code = settings.WHATSAPP_TEMPLATE_LANGUAGE or "en_US"
                return await provider.send_template(
                    to_mobile=requester_mobile,
                    template_name=template_name,
                    language_code=lang_code,
                    components=components
                )
            return await provider.send_text(to_mobile=requester_mobile, text=message)

        return await self._dispatch_with_fallback(
            mobile=requester_mobile,
            event_type="REQUEST_REJECTED",
            wa_dispatch_func=_wa_send,
            sms_text=message,
            user_id=user_id,
            db=db
        )

    async def send_request_cancelled(
        self,
        donor_mobile: str,
        requester_name: str,
        blood_group: str,
        patient_name: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Notify donor that a previously sent request has been cancelled or fulfilled."""
        patient_info = f" for patient '{patient_name}'" if patient_name else ""
        message = (
            f"BloodConnect Update: The {blood_group} blood request{patient_info} from {requester_name} "
            f"has been cancelled as the requirement is fulfilled or no longer needed. Thank you!"
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            return await provider.send_text(to_mobile=donor_mobile, text=message)

        return await self._dispatch_with_fallback(
            mobile=donor_mobile,
            event_type="REQUEST_CANCELLED",
            wa_dispatch_func=_wa_send,
            sms_text=message,
            user_id=user_id,
            db=db
        )

    async def send_request_reminder(
        self,
        donor_mobile: str,
        blood_group: str,
        location_name: str,
        patient_name: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> NotificationResult:
        """Send reminder notification to prospective donor."""
        patient_info = f" for patient '{patient_name}'" if patient_name else ""
        message = (
            f"BloodConnect Reminder: You have an active pending {blood_group} blood request{patient_info} "
            f"in {location_name}. Please respond when possible."
        )

        async def _wa_send(provider: BaseWhatsAppProvider) -> ProviderSendResult:
            return await provider.send_text(to_mobile=donor_mobile, text=message)

        return await self._dispatch_with_fallback(
            mobile=donor_mobile,
            event_type="REQUEST_REMINDER",
            wa_dispatch_func=_wa_send,
            sms_text=message,
            user_id=user_id,
            db=db
        )

    def clear_recorded_logs(self):
        """Clear recorded in-memory logs (for test isolation)."""
        self.recorded_logs.clear()


# Default singleton instance
notification_service = NotificationService()

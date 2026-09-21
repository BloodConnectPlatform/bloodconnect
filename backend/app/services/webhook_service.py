import hashlib
import hmac
import json
import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.user import User
from app.models.enums import NotificationDeliveryStatus, RequestStatus, WebhookEventStatus
from app.models.notification_log import NotificationLog
from app.models.webhook_event import WebhookEvent
from app.services.request_service import request_service

logger = logging.getLogger("webhook_service")


def normalize_incoming_mobile(mobile: str) -> str:
    """Normalize incoming international phone format (e.g. '919876543210' -> '9876543210')."""
    cleaned = mobile.strip().replace(" ", "").replace("-", "").replace("+", "")
    if len(cleaned) == 12 and cleaned.startswith("91") and cleaned[2] in "6789":
        return cleaned[2:]
    return cleaned


class WhatsAppWebhookService:
    def verify_challenge(
        self,
        mode: Optional[str],
        verify_token: Optional[str],
        challenge: Optional[str]
    ) -> str:
        """Validate Meta webhook registration challenge."""
        if not mode or not verify_token:
            logger.warning("[WebhookService] Verification failed: missing mode or token.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing hub.mode or hub.verify_token query parameter."
            )

        if mode != "subscribe":
            logger.warning(f"[WebhookService] Unexpected mode: {mode}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid hub.mode (expected 'subscribe')."
            )

        configured_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        if not configured_token or not secrets.compare_digest(verify_token, configured_token):
            logger.warning("[WebhookService] Token mismatch in verification challenge.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification token."
            )

        if challenge is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing hub.challenge query parameter."
            )

        logger.info("[WebhookService] Webhook verified successfully by Meta.")
        return challenge

    def verify_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        """Verify HMAC-SHA256 signature from Meta webhook."""
        if not settings.WEBHOOK_VERIFY_SIGNATURE or not settings.META_APP_SECRET:
            # If verification is disabled or secret is not set, allow in development
            return True

        if not signature_header:
            logger.warning("[WebhookService] Missing X-Hub-Signature-256 header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Hub-Signature-256 header."
            )

        prefix = "sha256="
        if not signature_header.startswith(prefix):
            logger.warning("[WebhookService] Malformed signature header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature header format."
            )

        expected_sig = signature_header[len(prefix):]
        secret_bytes = settings.META_APP_SECRET.encode("utf-8")
        computed_sig = hmac.new(secret_bytes, raw_body, hashlib.sha256).hexdigest()

        if not secrets.compare_digest(computed_sig, expected_sig):
            logger.warning("[WebhookService] Webhook signature mismatch.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature."
            )

        return True

    async def process_event_payload(
        self,
        db: AsyncSession,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process incoming Meta WhatsApp webhook payload with idempotency."""
        entries = payload.get("entry", [])
        if not entries:
            return {"status": "ignored", "reason": "No entries found in payload"}

        processed_actions = []

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # 1. Process Message Status Updates (sent, delivered, read, failed)
                statuses = value.get("statuses", [])
                for status_item in statuses:
                    msg_id = status_item.get("id")
                    status_str = (status_item.get("status") or "").upper()
                    if msg_id:
                        await self._update_message_status(db, msg_id, status_str, status_item)

                # 2. Process Incoming Messages (Interactive replies, Buttons, Text)
                messages = value.get("messages", [])
                for message in messages:
                    msg_id = message.get("id")
                    sender_raw = message.get("from", "")
                    sender_mobile = normalize_incoming_mobile(sender_raw)

                    # Check Idempotency Guard
                    if msg_id:
                        is_duplicate = await self._check_and_record_event(
                            db=db,
                            event_id=msg_id,
                            event_type="incoming_message",
                            payload=message
                        )
                        if is_duplicate:
                            logger.info(f"[WebhookService] Skipping duplicate event {msg_id}")
                            processed_actions.append({"msg_id": msg_id, "action": "duplicate_skipped"})
                            continue

                    # Extract interactive response / payload
                    action, request_id = self._extract_button_action(message)
                    if action and request_id:
                        result = await self._handle_interactive_response(
                            db=db,
                            sender_mobile=sender_mobile,
                            action=action,
                            request_id=request_id
                        )
                        processed_actions.append({"msg_id": msg_id, "result": result})

        return {"status": "success", "processed": processed_actions}

    async def _check_and_record_event(
        self,
        db: AsyncSession,
        event_id: str,
        event_type: str,
        payload: dict
    ) -> bool:
        """Check if event was already recorded. If not, record it. Returns True if duplicate."""
        stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return True

        now = datetime.now(timezone.utc)
        record = WebhookEvent(
            provider="meta_whatsapp",
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=WebhookEventStatus.PROCESSED,
            created_at=now,
            processed_at=now
        )
        db.add(record)
        await db.commit()
        return False

    async def _update_message_status(
        self,
        db: AsyncSession,
        provider_message_id: str,
        status_str: str,
        status_payload: dict
    ) -> None:
        """Update notification_logs delivery status based on WhatsApp status receipt."""
        status_map = {
            "SENT": NotificationDeliveryStatus.SENT,
            "DELIVERED": NotificationDeliveryStatus.DELIVERED,
            "READ": NotificationDeliveryStatus.READ,
            "FAILED": NotificationDeliveryStatus.FAILED,
        }
        mapped_status = status_map.get(status_str)
        if not mapped_status:
            return

        now = datetime.now(timezone.utc)
        update_vals: Dict[str, Any] = {"status": mapped_status}
        if mapped_status == NotificationDeliveryStatus.DELIVERED:
            update_vals["delivered_at"] = now

        stmt = (
            update(NotificationLog)
            .where(NotificationLog.provider_message_id == provider_message_id)
            .values(**update_vals)
        )
        await db.execute(stmt)
        await db.commit()
        logger.info(f"[WebhookService] Updated message {provider_message_id} status to {mapped_status.value}")

    def _extract_button_action(self, message: dict) -> Tuple[Optional[str], Optional[uuid.UUID]]:
        """Parse action and request_id from interactive button replies or quick replies."""
        msg_type = message.get("type")
        raw_payload = ""

        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                raw_payload = interactive.get("button_reply", {}).get("id", "")
        elif msg_type == "button":
            raw_payload = message.get("button", {}).get("payload", "")
        elif msg_type == "text":
            text = message.get("text", {}).get("body", "").strip().upper()
            if text in ["ACCEPT", "1", "YES"]:
                raw_payload = "ACCEPT"
            elif text in ["REJECT", "2", "NO", "NOT AVAILABLE", "UNAVAILABLE"]:
                raw_payload = "REJECT"

        if not raw_payload:
            return None, None

        if ":" in raw_payload:
            parts = raw_payload.split(":", 1)
            action = parts[0].strip().upper()
            req_id_str = parts[1].strip()
            try:
                req_uuid = uuid.UUID(req_id_str)
                return action, req_uuid
            except ValueError:
                logger.warning(f"[WebhookService] Malformed UUID in button payload: {req_id_str}")
                return None, None
        
        return None, None

    async def _handle_interactive_response(
        self,
        db: AsyncSession,
        sender_mobile: str,
        action: str,
        request_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Validate sender identity and transition blood request status based on interactive response."""
        # 1. Fetch Blood Request with Eager Loaded Relationships
        stmt = (
            select(BloodRequest)
            .options(
                selectinload(BloodRequest.donor).selectinload(DonorProfile.user).selectinload(User.donor_profile),
                selectinload(BloodRequest.requester),
                selectinload(BloodRequest.location)
            )
            .where(BloodRequest.id == request_id)
        )
        result = await db.execute(stmt)
        blood_req = result.scalar_one_or_none()

        if not blood_req:
            logger.warning(f"[WebhookService] Blood request {request_id} not found.")
            return {"status": "error", "message": f"Blood request {request_id} not found."}

        # 2. Fetch Donor Profile & User
        donor = blood_req.donor
        if not donor or not donor.user:
            donor_prof_stmt = (
                select(DonorProfile)
                .options(selectinload(DonorProfile.user).selectinload(User.donor_profile))
                .where(DonorProfile.id == blood_req.donor_id)
            )
            res_prof = await db.execute(donor_prof_stmt)
            donor = res_prof.scalar_one_or_none()

        if not donor or not donor.user:
            logger.warning(f"[WebhookService] Donor profile for request {request_id} not found.")
            return {"status": "error", "message": "Donor profile not found."}

        donor_user = donor.user
        donor_user.donor_profile = donor

        # 3. Security Validation: Verify Sender Mobile matches Donor Mobile
        donor_mobile = donor.user.mobile
        if donor_mobile != sender_mobile:
            logger.warning(
                f"[WebhookService] Sender mobile {sender_mobile} does not match request donor mobile {donor_mobile}."
            )
            return {"status": "unauthorized", "message": "Sender phone number does not match request donor."}

        # 4. Idempotency / Status check
        if blood_req.status == RequestStatus.ACCEPTED:
            logger.info(f"[WebhookService] Request {request_id} is already ACCEPTED.")
            return {"status": "already_accepted", "message": "Request is already accepted."}
        elif blood_req.status == RequestStatus.REJECTED:
            logger.info(f"[WebhookService] Request {request_id} is already REJECTED.")
            return {"status": "already_rejected", "message": "Request is already declined."}

        # 5. Execute Action
        if action == "ACCEPT":
            try:
                await request_service.accept_request(db=db, donor_user=donor.user, request_id=request_id)
                logger.info(f"[WebhookService] Request {request_id} marked as ACCEPTED via WhatsApp webhook.")
                return {"status": "accepted", "request_id": str(request_id)}
            except Exception as e:
                logger.exception(f"[WebhookService] Error accepting request: {e}")
                return {"status": "error", "message": str(e)}

        elif action in ["REJECT", "NOT_AVAILABLE"]:
            try:
                await request_service.reject_request(db=db, donor_user=donor.user, request_id=request_id)
                logger.info(f"[WebhookService] Request {request_id} marked as REJECTED via WhatsApp webhook.")
                return {"status": "rejected", "request_id": str(request_id)}
            except Exception as e:
                logger.exception(f"[WebhookService] Error rejecting request: {e}")
                return {"status": "error", "message": str(e)}

        return {"status": "unknown_action", "action": action}


webhook_service = WhatsAppWebhookService()

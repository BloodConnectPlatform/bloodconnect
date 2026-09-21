from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.whatsapp_service import ProviderSendResult

logger = logging.getLogger("sms_service")


class BaseSMSProvider(ABC):
    """Abstract SMS provider interface."""

    @abstractmethod
    async def send_sms(
        self,
        mobile: str,
        message: str,
        template_id: Optional[str] = None
    ) -> ProviderSendResult:
        """Send an SMS to the specified mobile number."""
        pass


class MSG91SMSProvider(BaseSMSProvider):
    """MSG91 SMS Provider implementation."""

    def __init__(
        self,
        auth_key: Optional[str] = None,
        sender_id: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.auth_key = auth_key or settings.MSG91_AUTH_KEY
        self.sender_id = sender_id or settings.MSG91_SENDER_ID
        self.timeout = timeout

    async def send_sms(
        self,
        mobile: str,
        message: str,
        template_id: Optional[str] = None
    ) -> ProviderSendResult:
        if not self.auth_key:
            logger.warning("[MSG91SMSProvider] Missing MSG91 auth key.")
            return ProviderSendResult(
                success=False,
                provider="msg91",
                error_message="MSG91 auth key not configured."
            )

        cleaned_mobile = mobile.strip().replace(" ", "").replace("-", "").replace("+", "")
        if len(cleaned_mobile) == 10:
            cleaned_mobile = f"91{cleaned_mobile}"

        url = "https://control.msg91.com/api/v5/flow/"
        headers = {
            "authkey": self.auth_key,
            "content-type": "application/json"
        }
        payload = {
            "template_id": template_id or settings.MSG91_OTP_TEMPLATE_ID,
            "sender": self.sender_id,
            "short_url": "0",
            "mobiles": cleaned_mobile,
            "message": message
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                data = response.json() if response.content else {}

                if response.is_success and data.get("type") == "success":
                    msg_id = data.get("message") or f"msg91_{cleaned_mobile}"
                    return ProviderSendResult(
                        success=True,
                        provider="msg91",
                        provider_message_id=str(msg_id),
                        details=data
                    )
                else:
                    err_msg = data.get("message") or f"MSG91 error ({response.status_code})"
                    logger.error(f"[MSG91SMSProvider] Failed to send SMS: {err_msg}")
                    return ProviderSendResult(
                        success=False,
                        provider="msg91",
                        error_message=err_msg,
                        details=data
                    )
        except Exception as e:
            logger.exception(f"[MSG91SMSProvider] Exception sending SMS: {e}")
            return ProviderSendResult(
                success=False,
                provider="msg91",
                error_message=str(e)
            )


class MockSMSProvider(BaseSMSProvider):
    """Development and test SMS provider storing sent messages in memory."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.simulate_failure: bool = False

    async def send_sms(
        self,
        mobile: str,
        message: str,
        template_id: Optional[str] = None
    ) -> ProviderSendResult:
        if self.simulate_failure:
            return ProviderSendResult(
                success=False,
                provider="mock_sms",
                error_message="Simulated mock SMS failure"
            )
        msg_id = f"sms.mock.{len(self.sent_messages) + 1}"
        record = {
            "mobile": mobile,
            "message": message,
            "template_id": template_id,
            "provider_message_id": msg_id
        }
        self.sent_messages.append(record)
        logger.info(f"[MockSMSProvider] Sending SMS to {mobile}: {message}")
        return ProviderSendResult(
            success=True,
            provider="mock_sms",
            provider_message_id=msg_id,
            details=record
        )

    def clear(self):
        """Clear recorded in-memory messages."""
        self.sent_messages.clear()
        self.simulate_failure = False


# Singleton instances
default_mock_sms_provider = MockSMSProvider()
default_msg91_sms_provider = MSG91SMSProvider()


def get_sms_provider() -> BaseSMSProvider:
    """Return configured SMS provider instance."""
    provider_name = (settings.SMS_PROVIDER or "mock").lower()
    if provider_name == "msg91" and settings.NOTIFICATION_PROVIDER != "mock":
        return default_msg91_sms_provider
    return default_mock_sms_provider

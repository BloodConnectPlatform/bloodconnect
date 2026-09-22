from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("whatsapp_service")


@dataclass
class ProviderSendResult:
    success: bool
    provider: str
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)


def normalize_recipient_mobile(mobile: str) -> str:
    """Normalize Indian mobile number to international format without plus sign for WhatsApp API (e.g. 919876543210)."""
    cleaned = mobile.strip().replace(" ", "").replace("-", "").replace("+", "")
    if len(cleaned) == 10 and cleaned[0] in "6789":
        return f"91{cleaned}"
    elif len(cleaned) == 12 and cleaned.startswith("91"):
        return cleaned
    return cleaned


class BaseWhatsAppProvider(ABC):
    """Abstract WhatsApp provider interface."""

    @abstractmethod
    async def send_template(
        self,
        to_mobile: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[dict]] = None
    ) -> ProviderSendResult:
        """Send a pre-approved template message via WhatsApp."""
        pass

    @abstractmethod
    async def send_interactive_buttons(
        self,
        to_mobile: str,
        body_text: str,
        buttons: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> ProviderSendResult:
        """Send an interactive button message via WhatsApp."""
        pass

    @abstractmethod
    async def send_text(self, to_mobile: str, text: str) -> ProviderSendResult:
        """Send a standard text message via WhatsApp."""
        pass


class MetaWhatsAppProvider(BaseWhatsAppProvider):
    """Meta WhatsApp Cloud API provider implementation."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.access_token = access_token or settings.META_WA_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.META_WA_PHONE_NUMBER_ID
        self.api_version = api_version or settings.META_GRAPH_API_VERSION
        self.timeout = timeout

    @property
    def api_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _post_payload(self, payload: dict) -> ProviderSendResult:
        if not self.access_token or not self.phone_number_id:
            logger.warning("[MetaWhatsAppProvider] Missing access token or phone number ID.")
            return ProviderSendResult(
                success=False,
                provider="meta",
                error_message="Meta WhatsApp Cloud API credentials not configured."
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=self._headers()
                )

                data = response.json() if response.content else {}

                if response.is_success and "messages" in data and len(data["messages"]) > 0:
                    msg_id = data["messages"][0].get("id")
                    return ProviderSendResult(
                        success=True,
                        provider="meta",
                        provider_message_id=msg_id,
                        details=data
                    )
                else:
                    err_msg = "Unknown Meta API error"
                    if "error" in data:
                        err_msg = data["error"].get("message", str(data["error"]))
                    elif response.text:
                        err_msg = response.text

                    logger.error(f"[MetaWhatsAppProvider] API call failed ({response.status_code}): {err_msg}")
                    return ProviderSendResult(
                        success=False,
                        provider="meta",
                        error_message=err_msg,
                        details=data
                    )
        except Exception as e:
            logger.exception(f"[MetaWhatsAppProvider] Exception sending message: {e}")
            return ProviderSendResult(
                success=False,
                provider="meta",
                error_message=str(e)
            )

    async def send_template(
        self,
        to_mobile: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[dict]] = None
    ) -> ProviderSendResult:
        recipient = normalize_recipient_mobile(to_mobile)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }
        res = await self._post_payload(payload)
        # Automatic language fallback if translation does not exist in requested language code
        if not res.success and res.details and "error" in res.details:
            err_code = res.details["error"].get("code")
            if err_code == 132001:  # Template name does not exist in the translation
                alt_lang = "en" if language_code in ("en_US", "en_GB") else "en_US"
                logger.info(f"[MetaWhatsAppProvider] Retrying template '{template_name}' with alternative language code '{alt_lang}'")
                payload["template"]["language"]["code"] = alt_lang
                retry_res = await self._post_payload(payload)
                if retry_res.success:
                    return retry_res
        return res

    async def send_interactive_buttons(
        self,
        to_mobile: str,
        body_text: str,
        buttons: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> ProviderSendResult:
        recipient = normalize_recipient_mobile(to_mobile)
        
        interactive_payload: Dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": buttons}
        }
        if header_text:
            interactive_payload["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_payload["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": interactive_payload
        }
        return await self._post_payload(payload)

    async def send_text(self, to_mobile: str, text: str) -> ProviderSendResult:
        recipient = normalize_recipient_mobile(to_mobile)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        }
        return await self._post_payload(payload)


class MockWhatsAppProvider(BaseWhatsAppProvider):
    """Development and test WhatsApp provider storing sent messages in memory."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.simulate_failure: bool = False

    async def send_template(
        self,
        to_mobile: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[dict]] = None
    ) -> ProviderSendResult:
        if self.simulate_failure:
            return ProviderSendResult(
                success=False,
                provider="mock_whatsapp",
                error_message="Simulated mock WhatsApp failure"
            )
        msg_id = f"wamid.mock.{len(self.sent_messages) + 1}"
        record = {
            "type": "template",
            "to_mobile": to_mobile,
            "template_name": template_name,
            "language_code": language_code,
            "components": components,
            "provider_message_id": msg_id
        }
        self.sent_messages.append(record)
        logger.info(f"[MockWhatsAppProvider] Sent template '{template_name}' to {to_mobile}")
        return ProviderSendResult(
            success=True,
            provider="mock_whatsapp",
            provider_message_id=msg_id,
            details=record
        )

    async def send_interactive_buttons(
        self,
        to_mobile: str,
        body_text: str,
        buttons: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> ProviderSendResult:
        if self.simulate_failure:
            return ProviderSendResult(
                success=False,
                provider="mock_whatsapp",
                error_message="Simulated mock WhatsApp failure"
            )
        msg_id = f"wamid.mock.{len(self.sent_messages) + 1}"
        record = {
            "type": "interactive",
            "to_mobile": to_mobile,
            "body_text": body_text,
            "buttons": buttons,
            "header_text": header_text,
            "footer_text": footer_text,
            "provider_message_id": msg_id
        }
        self.sent_messages.append(record)
        logger.info(f"[MockWhatsAppProvider] Sent interactive buttons to {to_mobile}")
        return ProviderSendResult(
            success=True,
            provider="mock_whatsapp",
            provider_message_id=msg_id,
            details=record
        )

    async def send_text(self, to_mobile: str, text: str) -> ProviderSendResult:
        if self.simulate_failure:
            return ProviderSendResult(
                success=False,
                provider="mock_whatsapp",
                error_message="Simulated mock WhatsApp failure"
            )
        msg_id = f"wamid.mock.{len(self.sent_messages) + 1}"
        record = {
            "type": "text",
            "to_mobile": to_mobile,
            "text": text,
            "provider_message_id": msg_id
        }
        self.sent_messages.append(record)
        logger.info(f"[MockWhatsAppProvider] Sent text to {to_mobile}")
        return ProviderSendResult(
            success=True,
            provider="mock_whatsapp",
            provider_message_id=msg_id,
            details=record
        )

    def clear(self):
        """Clear recorded in-memory messages."""
        self.sent_messages.clear()
        self.simulate_failure = False


# Singleton instances
default_mock_whatsapp_provider = MockWhatsAppProvider()
default_meta_whatsapp_provider = MetaWhatsAppProvider()


def get_whatsapp_provider() -> BaseWhatsAppProvider:
    """Return configured WhatsApp provider instance."""
    provider_name = (settings.WHATSAPP_PROVIDER or "mock").lower()
    if provider_name == "meta" and settings.NOTIFICATION_PROVIDER != "mock":
        return default_meta_whatsapp_provider
    return default_mock_whatsapp_provider

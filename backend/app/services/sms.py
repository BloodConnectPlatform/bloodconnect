from abc import ABC, abstractmethod
import logging
from typing import Dict, List

logger = logging.getLogger("sms_service")


class BaseSMSProvider(ABC):
    """Abstract SMS provider interface."""

    @abstractmethod
    async def send_sms(self, mobile: str, message: str) -> bool:
        """Send an SMS to the specified mobile number."""
        pass


class MockSMSProvider(BaseSMSProvider):
    """Development and testing SMS provider that records sent messages in memory."""

    def __init__(self):
        self.sent_messages: List[Dict[str, str]] = []

    async def send_sms(self, mobile: str, message: str) -> bool:
        self.sent_messages.append({"mobile": mobile, "message": message})
        logger.info(f"[MockSMSProvider] Sending SMS to {mobile}: {message}")
        return True

    def clear(self):
        """Clear recorded messages (useful in test teardown)."""
        self.sent_messages.clear()


# Default singleton instance
default_sms_provider = MockSMSProvider()


def get_sms_provider() -> BaseSMSProvider:
    return default_sms_provider

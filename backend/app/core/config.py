from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import json


class Settings(BaseSettings):
    APP_NAME: str = "Blood Connect API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    @property
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return str(self.ENVIRONMENT).strip().lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if current environment is development."""
        return str(self.ENVIRONMENT).strip().lower() in ("development", "dev", "local")

    @property
    def is_testing(self) -> bool:
        """Check if current environment is testing."""
        return str(self.ENVIRONMENT).strip().lower() in ("test", "testing")

    @model_validator(mode="after")
    def enforce_production_security(self) -> "Settings":
        """Strictly force DEBUG = False in production to guarantee no debug OTP or stack trace leaks."""
        if self.is_production:
            self.DEBUG = False
        return self

    @model_validator(mode="after")
    def sync_whatsapp_numbers(self) -> "Settings":
        """Ensure WHATSAPP_NUMBER and WHATSAPP_BUSINESS_PHONE_NUMBER are synchronized."""
        if hasattr(self, "WHATSAPP_NUMBER") and self.WHATSAPP_NUMBER:
            clean = str(self.WHATSAPP_NUMBER).strip().replace(" ", "").replace("-", "").replace("+", "")
            self.WHATSAPP_NUMBER = clean
            if not self.WHATSAPP_BUSINESS_PHONE_NUMBER or self.WHATSAPP_BUSINESS_PHONE_NUMBER == "919843883304":
                self.WHATSAPP_BUSINESS_PHONE_NUMBER = clean
        elif hasattr(self, "WHATSAPP_BUSINESS_PHONE_NUMBER") and self.WHATSAPP_BUSINESS_PHONE_NUMBER:
            clean = str(self.WHATSAPP_BUSINESS_PHONE_NUMBER).strip().replace(" ", "").replace("-", "").replace("+", "")
            self.WHATSAPP_NUMBER = clean
            self.WHATSAPP_BUSINESS_PHONE_NUMBER = clean
        return self

    # Security & Authentication
    SECRET_KEY: str = "dev_blood_connect_super_secret_jwt_key_change_in_production_32bytes!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bloodconnect_dev.db"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OTP configuration
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # Admin Bootstrap & Secret Configuration
    ADMIN_BOOTSTRAP_SECRET: str = ""
    INITIAL_ADMIN_PHONE_NUMBERS: Union[List[str], str] = []

    # Communication & Public URLs
    PUBLIC_API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    WHATSAPP_MAGIC_LINK_BASE_URL: Optional[str] = None  # Falls back to PUBLIC_API_URL if not specified
    WHATSAPP_NUMBER: str = "910000000000"
    WHATSAPP_BUSINESS_PHONE_NUMBER: str = "910000000000"
    WHATSAPP_LOGIN_TOKEN_EXPIRE_MINUTES: int = 5
    WHATSAPP_LOGIN_COOLDOWN_SECONDS: int = 60
    WHATSAPP_LOGIN_MAX_REQUESTS_WINDOW: int = 5
    NOTIFICATION_PROVIDER: str = "mock"  # "mock", "meta", "msg91", "live"
    NOTIFICATION_PRIMARY_CHANNEL: str = "whatsapp"  # "whatsapp", "sms"
    NOTIFICATION_SMS_FALLBACK: bool = True

    # WhatsApp / Meta Cloud API
    WHATSAPP_PROVIDER: str = "mock"  # "mock", "meta"
    META_WA_ACCESS_TOKEN: str = ""
    META_WA_PHONE_NUMBER_ID: str = ""
    META_WA_BUSINESS_ACCOUNT_ID: str = ""
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_GRAPH_API_VERSION: str = "v21.0"
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "dev_wa_verify_token_change_in_production!"
    WEBHOOK_VERIFY_SIGNATURE: bool = True

    # WhatsApp Templates (Configurable)
    WHATSAPP_TEMPLATE_LANGUAGE: str = "en_US"
    WHATSAPP_TEMPLATE_AUTH_OTP: str = "bloodconnect_auth_otp"
    WHATSAPP_TEMPLATE_BLOOD_REQUEST: str = "bloodconnect_blood_request"
    WHATSAPP_TEMPLATE_REQUEST_ACCEPTED: str = "bloodconnect_request_accepted"
    WHATSAPP_TEMPLATE_REQUEST_REJECTED: str = "bloodconnect_request_rejected"
    WHATSAPP_TEMPLATE_REQUEST_CANCELLED: str = "bloodconnect_request_cancelled"
    WHATSAPP_TEMPLATE_REQUEST_REMINDER: str = "bloodconnect_request_reminder"

    # SMS Configuration (MSG91 / Configurable)
    SMS_PROVIDER: str = "mock"  # "mock", "msg91"
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = "BLDCON"
    MSG91_OTP_TEMPLATE_ID: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    @field_validator("INITIAL_ADMIN_PHONE_NUMBERS", mode="before")
    @classmethod
    def assemble_initial_admin_phones(cls, v: Any) -> List[str]:
        if v is None:
            return []
        raw_items: List[str] = []
        if isinstance(v, (str, int)):
            v_str = str(v).strip()
            if not v_str:
                return []
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        raw_items = [str(item) for item in parsed]
                except Exception:
                    pass
            if not raw_items:
                raw_items = [i.strip() for i in v_str.split(",") if i.strip()]
        elif isinstance(v, (list, tuple, set)):
            raw_items = [str(item) for item in v]

        seen = set()
        normalized_list: List[str] = []
        for item in raw_items:
            cleaned = item.strip().replace(" ", "").replace("-", "")
            if cleaned.startswith("+91"):
                cleaned = cleaned[3:]
            elif cleaned.startswith("91") and len(cleaned) == 12:
                cleaned = cleaned[2:]
            elif cleaned.startswith("0") and len(cleaned) == 11:
                cleaned = cleaned[1:]

            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized_list.append(cleaned)
        return normalized_list

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()

from typing import Any, List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import json


class Settings(BaseSettings):
    APP_NAME: str = "Blood Connect API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

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

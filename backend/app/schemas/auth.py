import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.enums import UserRole


MOBILE_REGEX = r"^[6-9]\d{9}$"


def validate_indian_mobile(v: str) -> str:
    cleaned = v.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
        
    if not re.match(MOBILE_REGEX, cleaned):
        raise ValueError("Mobile number must be a valid 10-digit Indian mobile number (e.g. 9876543210)")
    return cleaned


class SendOTPRequest(BaseModel):
    mobile: str = Field(..., description="10-digit mobile number")
    purpose: Optional[str] = Field("LOGIN", description="Purpose: LOGIN or REGISTRATION")

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v: str) -> str:
        return validate_indian_mobile(v)


class SendOTPResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int
    cooldown_seconds: int
    debug_otp: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    mobile: str = Field(..., description="10-digit mobile number")
    otp: str = Field(..., min_length=4, max_length=8, description="Numeric OTP")

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v: str) -> str:
        return validate_indian_mobile(v)


class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    verification_token: Optional[str] = None
    is_registered: bool = False
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    mobile: str = Field(..., description="10-digit mobile number")
    otp: str = Field(..., min_length=4, max_length=8, description="6-digit OTP")

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v: str) -> str:
        return validate_indian_mobile(v)


class RequesterAuthRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Requester full name")
    mobile: str = Field(..., description="10-digit mobile number")
    otp: str = Field(..., min_length=4, max_length=8, description="6-digit OTP")

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v: str) -> str:
        return validate_indian_mobile(v)


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    mobile: str
    mobile_number: Optional[str] = None
    role: UserRole
    is_active: bool
    has_donor_profile: bool = False
    created_at: datetime

    @model_validator(mode="after")
    def populate_mobile_number(self):
        if not self.mobile_number:
            self.mobile_number = self.mobile
        return self

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    success: bool
    message: str

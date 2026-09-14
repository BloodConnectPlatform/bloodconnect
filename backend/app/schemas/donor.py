from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator
from app.models.enums import BloodGroup, RequestStatus
from app.schemas.auth import validate_indian_mobile, TokenResponse


class LocationResponse(BaseModel):
    id: int
    name: str
    district: str
    state: str

    model_config = {"from_attributes": True}


class DonorRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of donor")
    mobile: str = Field(..., description="10-digit mobile number")
    otp: Optional[str] = Field(None, min_length=4, max_length=8, description="6-digit OTP code")
    verification_token: Optional[str] = Field(None, description="Signed verification token from /verify-otp")
    date_of_birth: date = Field(..., description="Date of birth (must be 18+ years old)")
    blood_group: BloodGroup = Field(..., description="Donor blood group")
    location_id: int = Field(..., description="Predefined location ID")
    contact_consent: bool = Field(True, description="Consent to be contacted for blood donation")

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v: str) -> str:
        return validate_indian_mobile(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, dob: date) -> date:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise ValueError("Donor must be at least 18 years of age to register.")
        if age > 65:
            raise ValueError("Donor age exceeds the eligible donation limit (65 years).")
        return dob

    @field_validator("contact_consent")
    @classmethod
    def require_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must provide contact consent to register as a donor.")
        return v


class PublicDonorResponse(BaseModel):
    """Safe public donor projection: strictly conceals mobile, exact DOB, and private data."""
    id: uuid.UUID
    name: str
    blood_group: BloodGroup
    location: LocationResponse
    is_available: bool
    age: Optional[int] = None

    model_config = {"from_attributes": True}


class DonorProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    mobile: str
    date_of_birth: date
    blood_group: BloodGroup
    location: LocationResponse
    is_available: bool
    is_active: bool
    is_otp_verified: bool
    contact_consent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DonorProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    location_id: Optional[int] = None
    is_available: Optional[bool] = None
    contact_consent: Optional[bool] = None


class DonorAvailabilityUpdateRequest(BaseModel):
    is_available: bool = Field(..., description="Toggle donor availability for blood donation")


class DonorRequestSummary(BaseModel):
    id: uuid.UUID
    blood_group: BloodGroup
    location_name: str
    status: RequestStatus
    message: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    requester_name: str
    requester_mobile: Optional[str] = Field(
        None,
        description="Requester phone number (strictly revealed only if status == ACCEPTED)"
    )

    model_config = {"from_attributes": True}


class DonorDashboardStats(BaseModel):
    pending_requests: int = 0
    accepted_requests: int = 0
    rejected_requests: int = 0
    total_requests: int = 0


class DonorDashboardResponse(BaseModel):
    profile: DonorProfileResponse
    stats: DonorDashboardStats
    recent_requests: List[DonorRequestSummary]

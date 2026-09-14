from datetime import date, datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field
from app.models.enums import BloodGroup, ReportStatus
from app.schemas.donor import LocationResponse


class AdminDonorResponse(BaseModel):
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
    reports_count: int = 0

    model_config = {"from_attributes": True}


class AdminUpdateReportRequest(BaseModel):
    status: ReportStatus = Field(..., description="Target status: RESOLVED, DISMISSED, or REVIEWING")
    notes: Optional[str] = Field(None, max_length=500, description="Administrative audit notes")


class AdminAuditLogResponse(BaseModel):
    id: uuid.UUID
    admin_id: Optional[uuid.UUID] = None
    admin_name: Optional[str] = None
    action: str
    target_type: str
    target_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestStats(BaseModel):
    pending: int = 0
    accepted: int = 0
    rejected: int = 0
    total: int = 0


class ReportStats(BaseModel):
    open: int = 0
    reviewing: int = 0
    resolved: int = 0
    dismissed: int = 0
    total: int = 0


class AdminStatisticsResponse(BaseModel):
    total_registered_donors: int
    available_donors: int
    active_donors: int
    verified_donors: int
    donors_by_blood_group: Dict[str, int]
    donors_by_location: Dict[str, int]
    requests: RequestStats
    reports: ReportStats

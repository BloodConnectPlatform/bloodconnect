from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.enums import BloodGroup, ReportStatus, UserRole
from app.schemas.auth import validate_indian_mobile
from app.schemas.donor import LocationResponse


class AdminManagementAction(str, Enum):
    PROMOTE = "PROMOTE"
    DEMOTE = "DEMOTE"
    LIST = "LIST"


class AdminUserSummary(BaseModel):
    id: uuid.UUID
    name: str
    mobile: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminManagementRequest(BaseModel):
    action: AdminManagementAction = Field(..., description="Action to perform: PROMOTE, DEMOTE, or LIST")
    mobile: Optional[str] = Field(None, description="10-digit Indian mobile number for PROMOTE or DEMOTE")

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        return validate_indian_mobile(v)

    @model_validator(mode="after")
    def validate_action_payload(self) -> "AdminManagementRequest":
        if self.action in (AdminManagementAction.PROMOTE, AdminManagementAction.DEMOTE):
            if not self.mobile:
                raise ValueError(f"Field 'mobile' is required when action is '{self.action.value}'.")
        return self


class AdminManagementResponse(BaseModel):
    success: bool = True
    message: str
    action: AdminManagementAction
    user: Optional[AdminUserSummary] = None
    admins: Optional[list[AdminUserSummary]] = None



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

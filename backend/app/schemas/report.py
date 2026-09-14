from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field
from app.models.enums import ReportReason, ReportStatus


class CreateReportRequest(BaseModel):
    donor_id: uuid.UUID = Field(..., description="Target donor profile ID being reported")
    reason: ReportReason = Field(..., description="Categorical reason for reporting")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed explanation of the issue")


class ReportResponse(BaseModel):
    id: uuid.UUID
    donor_id: uuid.UUID
    donor_name: str
    donor_mobile: str
    reporter_id: uuid.UUID
    reporter_name: str
    reason: ReportReason
    description: Optional[str] = None
    status: ReportStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

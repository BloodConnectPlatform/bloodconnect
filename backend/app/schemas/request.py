from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field
from app.models.enums import BloodGroup, RequestStatus
from app.schemas.donor import LocationResponse


class CreateBloodRequest(BaseModel):
    donor_id: uuid.UUID = Field(..., description="Target donor profile ID")
    blood_group: Optional[BloodGroup] = Field(None, description="Required blood group (defaults to donor's blood group if omitted)")
    location_id: Optional[int] = Field(None, description="Donation hospital / clinic location ID (defaults to donor's location if omitted)")
    patient_name: Optional[str] = Field(None, description="Patient full name")
    hospital_name: Optional[str] = Field(None, description="Hospital name & city")
    required_units: Optional[int] = Field(1, description="Required units")
    urgency: Optional[str] = Field("HIGH", description="Urgency level")
    message: Optional[str] = Field(None, max_length=500, description="Optional note for the donor (e.g. hospital name, urgency)")


class BloodRequestResponse(BaseModel):
    id: uuid.UUID
    requester_id: uuid.UUID
    donor_id: uuid.UUID
    blood_group: BloodGroup
    location: LocationResponse
    patient_name: Optional[str] = None
    hospital_name: Optional[str] = None
    message: Optional[str] = None
    status: RequestStatus
    created_at: datetime
    responded_at: Optional[datetime] = None
    donor_name: str
    donor_mobile: Optional[str] = Field(
        None,
        description="Donor phone number (revealed ONLY when status == ACCEPTED)"
    )
    requester_name: str
    requester_mobile: Optional[str] = Field(
        None,
        description="Requester phone number (revealed ONLY when status == ACCEPTED)"
    )

    model_config = {"from_attributes": True}


class SentRequestSummary(BaseModel):
    id: uuid.UUID
    blood_group: BloodGroup
    location: LocationResponse
    patient_name: Optional[str] = None
    hospital_name: Optional[str] = None
    status: RequestStatus
    message: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    donor_name: str
    donor_mobile: Optional[str] = Field(
        None,
        description="Donor contact revealed to requester only upon acceptance"
    )

    model_config = {"from_attributes": True}


class ReceivedRequestSummary(BaseModel):
    id: uuid.UUID
    blood_group: BloodGroup
    location: LocationResponse
    patient_name: Optional[str] = None
    hospital_name: Optional[str] = None
    status: RequestStatus
    message: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    requester_name: str
    requester_mobile: Optional[str] = Field(
        None,
        description="Requester contact revealed to donor only upon acceptance"
    )

    model_config = {"from_attributes": True}

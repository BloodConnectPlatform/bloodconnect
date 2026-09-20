from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, require_donor
from app.database.session import get_db
from app.models.user import User
from app.schemas.request import (
    BloodRequestResponse,
    CreateBloodRequest,
    ReceivedRequestSummary,
    SentRequestSummary,
)
from app.services.request_service import request_service

router = APIRouter(prefix="/requests", tags=["Blood Requests"])


@router.post(
    "",
    response_model=BloodRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a blood donation request",
    description="Submits a blood donation request to a verified, available donor. Dispatches in-app notification to donor."
)
async def create_blood_request(
    request: CreateBloodRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.create_request(db, current_user, request)


@router.get(
    "/sent",
    response_model=List[SentRequestSummary],
    summary="Get blood requests sent by current user",
    description="Retrieves history and response statuses of all blood requests submitted by the logged in user."
)
async def get_sent_requests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.get_sent_requests(db, current_user)


@router.get(
    "/received",
    response_model=List[ReceivedRequestSummary],
    summary="Get blood requests received by current donor",
    description="Retrieves all incoming blood requests directed at the authenticated donor profile."
)
async def get_received_requests(
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.get_received_requests(db, current_user)


@router.get(
    "/{request_id}",
    response_model=BloodRequestResponse,
    summary="Get blood request details",
    description="Retrieves request details with strict role-appropriate contact privacy filtering."
)
async def get_request_by_id(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.get_request_by_id(db, current_user, request_id)


@router.patch(
    "/{request_id}/accept",
    response_model=BloodRequestResponse,
    summary="Accept a blood request",
    description="Donor accepts a pending blood request, unlocking requester contact information for coordination."
)
@router.post(
    "/{request_id}/accept",
    response_model=BloodRequestResponse,
    summary="Accept a blood request (POST alias)",
    include_in_schema=False
)
async def accept_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.accept_request(db, current_user, request_id)


@router.patch(
    "/{request_id}/reject",
    response_model=BloodRequestResponse,
    summary="Reject / Decline a blood request",
    description="Donor declines a pending blood request. State is updated to REJECTED."
)
@router.post(
    "/{request_id}/reject",
    response_model=BloodRequestResponse,
    summary="Reject / Decline a blood request (POST alias)",
    include_in_schema=False
)
async def reject_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.reject_request(db, current_user, request_id)


@router.delete(
    "/{request_id}",
    summary="Delete / Cancel a blood request",
    description="Allows a requester (or admin) to delete or cancel a blood request when their requirement has been fulfilled or is no longer needed."
)
async def delete_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await request_service.delete_request(db, current_user, request_id)

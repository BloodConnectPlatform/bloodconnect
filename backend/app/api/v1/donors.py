from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_donor
from app.database.session import get_db
from app.models.enums import BloodGroup
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.common import PaginatedResponse
from app.schemas.donor import (
    DonorAvailabilityUpdateRequest,
    DonorDashboardResponse,
    DonorProfileResponse,
    DonorProfileUpdateRequest,
    DonorRegisterRequest,
    PublicDonorResponse,
)
from app.services.donor_service import donor_service

router = APIRouter(prefix="/donors", tags=["Donors"])


@router.post(
    "",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new blood donor",
    description="Registers a new donor user after validating OTP/verification token, age, blood group, and location."
)
async def register_donor(
    request: DonorRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.register_donor(db, request)


@router.get(
    "/search",
    response_model=PaginatedResponse[PublicDonorResponse],
    summary="Search verified, available blood donors",
    description="Search active and verified blood donors filtered by blood group and location. Strictly returns safe public donor data (no contact numbers)."
)
async def search_donors(
    blood_group: Optional[BloodGroup] = Query(None, description="Filter by blood group (e.g. O+, A-)"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.search_donors(
        db=db,
        blood_group=blood_group,
        location_id=location_id,
        page=page,
        size=size
    )


@router.get(
    "/me",
    response_model=DonorProfileResponse,
    summary="Get authenticated donor's profile",
    description="Retrieves the full donor profile for the currently logged in donor."
)
async def get_my_donor_profile(
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.get_donor_profile(db, current_user)


@router.patch(
    "/me",
    response_model=DonorProfileResponse,
    summary="Update authenticated donor's profile",
    description="Allows a donor to update their name, location, availability, or contact consent."
)
async def update_my_donor_profile(
    request: DonorProfileUpdateRequest,
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.update_donor_profile(db, current_user, request)


@router.patch(
    "/availability",
    response_model=DonorProfileResponse,
    summary="Toggle blood donation availability",
    description="Quickly set donor status as available or unavailable for urgent blood requests."
)
async def toggle_availability(
    request: DonorAvailabilityUpdateRequest,
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.toggle_availability(db, current_user, request.is_available)


@router.get(
    "/dashboard",
    response_model=DonorDashboardResponse,
    summary="Get donor dashboard summary",
    description="Returns donor profile details, aggregate request statistics, and recent received requests."
)
async def get_donor_dashboard(
    current_user: User = Depends(require_donor),
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.get_donor_dashboard(db, current_user)

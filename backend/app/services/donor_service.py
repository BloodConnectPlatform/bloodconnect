from datetime import date, datetime
import math
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import BloodGroup, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.donor import (
    DonorDashboardResponse,
    DonorDashboardStats,
    DonorProfileResponse,
    DonorProfileUpdateRequest,
    DonorRegisterRequest,
    DonorRequestSummary,
    LocationResponse,
    PublicDonorResponse,
    PublicStatsResponse,
)
from app.services.otp_service import otp_service


class DonorService:
    async def list_locations(self, db: AsyncSession) -> List[LocationResponse]:
        """Retrieve all active predefined donation locations."""
        stmt = select(Location).where(Location.is_active.is_(True)).order_by(Location.name.asc())
        result = await db.execute(stmt)
        locations = result.scalars().all()
        return [LocationResponse.model_validate(loc) for loc in locations]

    async def register_donor(
        self, db: AsyncSession, data: DonorRegisterRequest
    ) -> TokenResponse:
        """Register a new donor profile with server-side OTP verification enforcement."""
        # 1. Verify OTP or verification token
        if data.verification_token:
            try:
                payload = decode_token(data.verification_token)
                if payload.get("sub") != data.mobile or payload.get("purpose") != "otp_verified":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid verification token for this mobile number."
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Verification token validation failed: {str(e)}"
                )
        elif data.otp:
            await otp_service.verify_otp(db, data.mobile, data.otp)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'otp' or 'verification_token' is required to complete donor registration."
            )

        # 2. Verify location exists and is active
        loc_stmt = select(Location).where(Location.id == data.location_id, Location.is_active.is_(True))
        loc_result = await db.execute(loc_stmt)
        location = loc_result.scalar_one_or_none()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected location does not exist or is inactive."
            )

        # 3. Check existing user
        user_stmt = select(User).where(User.mobile == data.mobile)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user:
            if user.donor_profile is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A donor profile is already registered with this mobile number. Please log in."
                )
            # Upgrade existing requester account to donor
            user.name = data.name
            user.role = UserRole.DONOR
            user.is_active = True
        else:
            user = User(
                name=data.name,
                mobile=data.mobile,
                role=UserRole.DONOR,
                is_active=True
            )
            db.add(user)
            await db.flush()

        # 4. Create DonorProfile
        donor_profile = DonorProfile(
            user_id=user.id,
            date_of_birth=data.date_of_birth,
            blood_group=data.blood_group,
            location_id=data.location_id,
            is_otp_verified=True,
            is_available=True,
            is_active=True,
            contact_consent=data.contact_consent
        )
        db.add(donor_profile)
        await db.commit()
        await db.refresh(user)

        # 5. Generate Auth Tokens
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        token_payload = {
            "sub": str(user.id),
            "mobile": user.mobile,
            "role": role_val
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        user_response = UserResponse(
            id=user.id,
            name=user.name,
            mobile=user.mobile,
            role=user.role if isinstance(user.role, UserRole) else UserRole(user.role),
            is_active=user.is_active,
            has_donor_profile=True,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response
        )

    async def search_donors(
        self,
        db: AsyncSession,
        blood_group: Optional[BloodGroup] = None,
        location_id: Optional[int] = None,
        location_name: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse[PublicDonorResponse]:
        """Search eligible active, OTP-verified, and available donors with safe public response projection."""
        page = max(1, page)
        size = max(1, min(size, 100))
        offset = (page - 1) * size

        # Query builder for eligible donors
        query = (
            select(DonorProfile)
            .join(DonorProfile.user)
            .where(
                DonorProfile.is_otp_verified.is_(True),
                DonorProfile.is_active.is_(True),
                DonorProfile.is_available.is_(True),
                User.is_active.is_(True)
            )
        )

        count_query = (
            select(func.count(DonorProfile.id))
            .join(DonorProfile.user)
            .where(
                DonorProfile.is_otp_verified.is_(True),
                DonorProfile.is_active.is_(True),
                DonorProfile.is_available.is_(True),
                User.is_active.is_(True)
            )
        )

        if blood_group:
            query = query.where(DonorProfile.blood_group == blood_group)
            count_query = count_query.where(DonorProfile.blood_group == blood_group)

        if location_id:
            query = query.where(DonorProfile.location_id == location_id)
            count_query = count_query.where(DonorProfile.location_id == location_id)
        elif location_name and location_name.strip():
            loc_term = f"%{location_name.strip()}%"
            query = query.join(DonorProfile.location).where(
                or_(Location.name.ilike(loc_term), Location.district.ilike(loc_term))
            )
            count_query = count_query.join(DonorProfile.location).where(
                or_(Location.name.ilike(loc_term), Location.district.ilike(loc_term))
            )

        # Count total matches
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        pages = math.ceil(total / size) if total > 0 else 1

        # Fetch paginated slice ordered by most recently updated
        query = query.order_by(DonorProfile.updated_at.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        donors = result.scalars().all()

        def _calculate_age(dob: Optional[date]) -> Optional[int]:
            if not dob:
                return None
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        items = [
            PublicDonorResponse(
                id=d.id,
                name=d.user.name,
                blood_group=d.blood_group,
                location=LocationResponse.model_validate(d.location),
                is_available=d.is_available,
                age=_calculate_age(d.date_of_birth)
            )
            for d in donors
        ]

        return PaginatedResponse[PublicDonorResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def get_donor_profile(
        self, db: AsyncSession, user: User
    ) -> DonorProfileResponse:
        """Retrieve the current donor's profile."""
        profile = user.donor_profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found for the current user."
            )

        return DonorProfileResponse(
            id=profile.id,
            user_id=user.id,
            name=user.name,
            mobile=user.mobile,
            date_of_birth=profile.date_of_birth,
            blood_group=profile.blood_group,
            location=LocationResponse.model_validate(profile.location),
            is_available=profile.is_available,
            is_active=profile.is_active,
            is_otp_verified=profile.is_otp_verified,
            contact_consent=profile.contact_consent,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    async def update_donor_profile(
        self, db: AsyncSession, user: User, data: DonorProfileUpdateRequest
    ) -> DonorProfileResponse:
        """Update donor profile details (name, location, availability, consent)."""
        profile = user.donor_profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found for the current user."
            )

        if data.name is not None:
            user.name = data.name.strip()

        if data.location_id is not None:
            loc_stmt = select(Location).where(
                Location.id == data.location_id,
                Location.is_active.is_(True)
            )
            loc_result = await db.execute(loc_stmt)
            location = loc_result.scalar_one_or_none()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected location does not exist or is inactive."
                )
            profile.location_id = data.location_id

        if data.is_available is not None:
            profile.is_available = data.is_available

        if data.contact_consent is not None:
            profile.contact_consent = data.contact_consent

        await db.commit()
        await db.refresh(user)
        return await self.get_donor_profile(db, user)

    async def toggle_availability(
        self, db: AsyncSession, user: User, is_available: bool
    ) -> DonorProfileResponse:
        """Quickly toggle donor's active blood donation availability."""
        profile = user.donor_profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found for the current user."
            )

        profile.is_available = is_available
        await db.commit()
        await db.refresh(user)
        return await self.get_donor_profile(db, user)

    async def get_donor_dashboard(
        self, db: AsyncSession, user: User
    ) -> DonorDashboardResponse:
        """Fetch donor dashboard profile, statistics, and received request history."""
        profile = user.donor_profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found for the current user."
            )

        # 1. Fetch Request Statistics
        donor_id = profile.id
        stmt_requests = (
            select(BloodRequest)
            .where(BloodRequest.donor_id == donor_id)
            .order_by(BloodRequest.created_at.desc())
        )
        result_requests = await db.execute(stmt_requests)
        all_requests = result_requests.scalars().all()

        pending_count = sum(1 for r in all_requests if r.status == RequestStatus.PENDING)
        accepted_count = sum(1 for r in all_requests if r.status == RequestStatus.ACCEPTED)
        rejected_count = sum(1 for r in all_requests if r.status == RequestStatus.REJECTED)
        total_count = len(all_requests)

        stats = DonorDashboardStats(
            pending_requests=pending_count,
            accepted_requests=accepted_count,
            rejected_requests=rejected_count,
            total_requests=total_count
        )

        # 2. Build Request Summaries with Contact Privacy Rules
        pending_list: List[DonorRequestSummary] = []
        accepted_list: List[DonorRequestSummary] = []
        recent_list: List[DonorRequestSummary] = []

        for req in all_requests:
            # STRICT PRIVACY RULE: Requester mobile is ONLY exposed if the donor accepted the request!
            requester_phone = (
                req.requester.mobile
                if req.status == RequestStatus.ACCEPTED
                else None
            )

            item = DonorRequestSummary(
                id=req.id,
                blood_group=req.blood_group,
                location=LocationResponse.model_validate(req.location) if req.location else None,
                location_name=req.location.name if req.location else "Unknown",
                patient_name=req.patient_name,
                hospital_name=req.hospital_name,
                status=req.status,
                message=req.message,
                created_at=req.created_at,
                responded_at=req.responded_at,
                requester_name=req.requester.name,
                requester_mobile=requester_phone
            )

            if req.status == RequestStatus.PENDING:
                pending_list.append(item)
            elif req.status == RequestStatus.ACCEPTED:
                accepted_list.append(item)

            if len(recent_list) < 20:
                recent_list.append(item)

        profile_response = await self.get_donor_profile(db, user)

        return DonorDashboardResponse(
            profile=profile_response,
            stats=stats,
            pending_requests=pending_list,
            accepted_requests=accepted_list,
            recent_requests=recent_list
        )

    async def get_public_stats(self, db: AsyncSession) -> PublicStatsResponse:
        """Retrieve aggregated live public platform counts: verified active donors, available donors, and active locations."""
        total_donors_stmt = (
            select(func.count(DonorProfile.id))
            .join(DonorProfile.user)
            .where(
                DonorProfile.is_active.is_(True),
                DonorProfile.is_otp_verified.is_(True),
                User.is_active.is_(True)
            )
        )
        available_donors_stmt = (
            select(func.count(DonorProfile.id))
            .join(DonorProfile.user)
            .where(
                DonorProfile.is_active.is_(True),
                DonorProfile.is_available.is_(True),
                DonorProfile.is_otp_verified.is_(True),
                User.is_active.is_(True)
            )
        )
        locations_stmt = select(func.count(Location.id)).where(Location.is_active.is_(True))

        total_donors_res = await db.execute(total_donors_stmt)
        available_donors_res = await db.execute(available_donors_stmt)
        locations_res = await db.execute(locations_stmt)

        return PublicStatsResponse(
            total_donors=total_donors_res.scalar() or 0,
            available_donors=available_donors_res.scalar() or 0,
            total_locations=locations_res.scalar() or 0
        )


donor_service = DonorService()


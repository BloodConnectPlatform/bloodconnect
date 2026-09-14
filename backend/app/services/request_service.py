from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import NotificationType, RequestStatus, UserRole
from app.models.location import Location
from app.models.user import User
from app.schemas.donor import LocationResponse
from app.schemas.request import (
    BloodRequestResponse,
    CreateBloodRequest,
    ReceivedRequestSummary,
    SentRequestSummary,
)
from app.services.notification_service import notification_service


class RequestService:
    async def create_request(
        self,
        db: AsyncSession,
        requester: User,
        data: CreateBloodRequest
    ) -> BloodRequestResponse:
        """Create a new blood donation request targeted at an eligible donor."""
        # 1. Fetch Target Donor Profile
        donor_stmt = (
            select(DonorProfile)
            .join(DonorProfile.user)
            .where(
                DonorProfile.id == data.donor_id,
                DonorProfile.is_active.is_(True),
                DonorProfile.is_otp_verified.is_(True),
                DonorProfile.is_available.is_(True),
                User.is_active.is_(True)
            )
        )
        donor_res = await db.execute(donor_stmt)
        donor = donor_res.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected donor is not found, inactive, or currently unavailable for blood donation."
            )

        # 2. Prevent self-request
        if donor.user_id == requester.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send a blood donation request to yourself."
            )

        # 3. Blood group verification
        if donor.blood_group != data.blood_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested blood group ({data.blood_group.value}) does not match donor's blood group ({donor.blood_group.value})."
            )

        # 4. Location verification
        loc_stmt = select(Location).where(Location.id == data.location_id, Location.is_active.is_(True))
        loc_res = await db.execute(loc_stmt)
        location = loc_res.scalar_one_or_none()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive donation location selected."
            )

        # 5. Create BloodRequest entity
        blood_request = BloodRequest(
            requester_id=requester.id,
            donor_id=donor.id,
            blood_group=data.blood_group,
            location_id=data.location_id,
            message=data.message.strip() if data.message else None,
            status=RequestStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        db.add(blood_request)
        await db.flush()

        # 6. Notify the Donor User
        await notification_service.create_notification(
            db=db,
            user_id=donor.user_id,
            type=NotificationType.REQUEST_RECEIVED,
            title="New Blood Donation Request",
            message=f"You have received an urgent {data.blood_group.value} blood request in {location.name}."
        )

        await db.commit()
        await db.refresh(blood_request)

        # Strict contact privacy: Phone numbers HIDDEN while PENDING
        return BloodRequestResponse(
            id=blood_request.id,
            requester_id=blood_request.requester_id,
            donor_id=blood_request.donor_id,
            blood_group=blood_request.blood_group,
            location=LocationResponse.model_validate(blood_request.location),
            message=blood_request.message,
            status=blood_request.status,
            created_at=blood_request.created_at,
            responded_at=blood_request.responded_at,
            donor_name=donor.user.name,
            donor_mobile=None,
            requester_name=requester.name,
            requester_mobile=None
        )

    async def get_sent_requests(
        self,
        db: AsyncSession,
        requester: User
    ) -> List[SentRequestSummary]:
        """Retrieve all blood requests sent by the current requester."""
        stmt = (
            select(BloodRequest)
            .where(BloodRequest.requester_id == requester.id)
            .order_by(BloodRequest.created_at.desc())
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        summaries: List[SentRequestSummary] = []
        for req in requests:
            # Privacy rule: Donor mobile only shown if ACCEPTED
            donor_phone = (
                req.donor.user.mobile
                if req.status == RequestStatus.ACCEPTED
                else None
            )

            summaries.append(
                SentRequestSummary(
                    id=req.id,
                    blood_group=req.blood_group,
                    location=LocationResponse.model_validate(req.location),
                    status=req.status,
                    message=req.message,
                    created_at=req.created_at,
                    responded_at=req.responded_at,
                    donor_name=req.donor.user.name,
                    donor_mobile=donor_phone
                )
            )

        return summaries

    async def get_received_requests(
        self,
        db: AsyncSession,
        donor_user: User
    ) -> List[ReceivedRequestSummary]:
        """Retrieve all blood requests received by the current donor."""
        donor_profile = donor_user.donor_profile
        if not donor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found for current user."
            )

        stmt = (
            select(BloodRequest)
            .where(BloodRequest.donor_id == donor_profile.id)
            .order_by(BloodRequest.created_at.desc())
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        summaries: List[ReceivedRequestSummary] = []
        for req in requests:
            # Privacy rule: Requester mobile only disclosed if donor ACCEPTED
            requester_phone = (
                req.requester.mobile
                if req.status == RequestStatus.ACCEPTED
                else None
            )

            summaries.append(
                ReceivedRequestSummary(
                    id=req.id,
                    blood_group=req.blood_group,
                    location=LocationResponse.model_validate(req.location),
                    status=req.status,
                    message=req.message,
                    created_at=req.created_at,
                    responded_at=req.responded_at,
                    requester_name=req.requester.name,
                    requester_mobile=requester_phone
                )
            )

        return summaries

    async def get_request_by_id(
        self,
        db: AsyncSession,
        user: User,
        request_id: uuid.UUID
    ) -> BloodRequestResponse:
        """Fetch request details enforcing participant authorization and privacy rules."""
        stmt = select(BloodRequest).where(BloodRequest.id == request_id)
        result = await db.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blood request not found."
            )

        # Authorization: Requester, Target Donor, or Admin
        is_requester = req.requester_id == user.id
        is_donor = user.donor_profile and req.donor_id == user.donor_profile.id
        is_admin = user.role == UserRole.ADMIN

        if not (is_requester or is_donor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this request."
            )

        # Contact disclosure logic
        if req.status == RequestStatus.ACCEPTED:
            donor_phone = req.donor.user.mobile
            requester_phone = req.requester.mobile
        else:
            donor_phone = None
            requester_phone = None

        return BloodRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            donor_id=req.donor_id,
            blood_group=req.blood_group,
            location=LocationResponse.model_validate(req.location),
            message=req.message,
            status=req.status,
            created_at=req.created_at,
            responded_at=req.responded_at,
            donor_name=req.donor.user.name,
            donor_mobile=donor_phone,
            requester_name=req.requester.name,
            requester_mobile=requester_phone
        )

    async def accept_request(
        self,
        db: AsyncSession,
        donor_user: User,
        request_id: uuid.UUID
    ) -> BloodRequestResponse:
        """Donor accepts a pending blood request, unlocking requester contact information."""
        donor_profile = donor_user.donor_profile
        if not donor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered donors can accept blood requests."
            )

        stmt = select(BloodRequest).where(BloodRequest.id == request_id)
        result = await db.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blood request not found."
            )

        if req.donor_id != donor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to accept this request."
            )

        if req.status != RequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: Request is already marked as {req.status.value}."
            )

        # Transition to ACCEPTED
        now = datetime.now(timezone.utc)
        req.status = RequestStatus.ACCEPTED
        req.responded_at = now

        # Send notification to requester
        await notification_service.create_notification(
            db=db,
            user_id=req.requester_id,
            type=NotificationType.REQUEST_ACCEPTED,
            title="Blood Request Accepted!",
            message=f"Donor {donor_user.name} has accepted your {req.blood_group.value} blood request."
        )

        await db.commit()
        await db.refresh(req)

        return BloodRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            donor_id=req.donor_id,
            blood_group=req.blood_group,
            location=LocationResponse.model_validate(req.location),
            message=req.message,
            status=req.status,
            created_at=req.created_at,
            responded_at=req.responded_at,
            donor_name=donor_user.name,
            donor_mobile=donor_user.mobile,
            requester_name=req.requester.name,
            requester_mobile=req.requester.mobile
        )

    async def reject_request(
        self,
        db: AsyncSession,
        donor_user: User,
        request_id: uuid.UUID
    ) -> BloodRequestResponse:
        """Donor declines or marks themselves unavailable for a pending blood request."""
        donor_profile = donor_user.donor_profile
        if not donor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered donors can respond to blood requests."
            )

        stmt = select(BloodRequest).where(BloodRequest.id == request_id)
        result = await db.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blood request not found."
            )

        if req.donor_id != donor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to reject this request."
            )

        if req.status != RequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: Request is already marked as {req.status.value}."
            )

        # Transition to REJECTED
        now = datetime.now(timezone.utc)
        req.status = RequestStatus.REJECTED
        req.responded_at = now

        # Send notification to requester
        await notification_service.create_notification(
            db=db,
            user_id=req.requester_id,
            type=NotificationType.REQUEST_REJECTED,
            title="Blood Request Declined",
            message=f"The donor was unable to accept your {req.blood_group.value} blood request at this time."
        )

        await db.commit()
        await db.refresh(req)

        return BloodRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            donor_id=req.donor_id,
            blood_group=req.blood_group,
            location=LocationResponse.model_validate(req.location),
            message=req.message,
            status=req.status,
            created_at=req.created_at,
            responded_at=req.responded_at,
            donor_name=donor_user.name,
            donor_mobile=None,
            requester_name=req.requester.name,
            requester_mobile=None
        )


request_service = RequestService()

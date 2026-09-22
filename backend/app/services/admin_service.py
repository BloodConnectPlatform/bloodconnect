import asyncio
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminAuthContext
from app.models.admin_action import AdminAction
from app.models.blood_request import BloodRequest
from app.models.donor import DonorProfile
from app.models.enums import (
    AdminActionType,
    BloodGroup,
    ReportStatus,
    RequestStatus,
    UserRole,
)
from app.models.location import Location
from app.models.report import Report
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminDonorResponse,
    AdminManagementAction,
    AdminManagementRequest,
    AdminManagementResponse,
    AdminStatisticsResponse,
    AdminUserSummary,
    AdminWhatsAppTestRequest,
    AdminWhatsAppTestResponse,
    ReportStats,
    RequestStats,
)
from app.schemas.common import PaginatedResponse
from app.schemas.donor import LocationResponse
from app.schemas.request import BloodRequestResponse


class AdminService:
    def __init__(self):
        self._mutation_lock = asyncio.Lock()

    async def list_donors(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        blood_group: Optional[BloodGroup] = None,
        location_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_available: Optional[bool] = None,
        is_otp_verified: Optional[bool] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse[AdminDonorResponse]:
        """List and filter donors for administrative review."""
        page = max(1, page)
        size = max(1, min(size, 100))
        offset = (page - 1) * size

        query = select(DonorProfile).join(DonorProfile.user)
        count_query = select(func.count(DonorProfile.id)).join(DonorProfile.user)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                (User.name.ilike(search_pattern)) | (User.mobile.like(search_pattern))
            )
            count_query = count_query.where(
                (User.name.ilike(search_pattern)) | (User.mobile.like(search_pattern))
            )

        if blood_group:
            query = query.where(DonorProfile.blood_group == blood_group)
            count_query = count_query.where(DonorProfile.blood_group == blood_group)

        if location_id:
            query = query.where(DonorProfile.location_id == location_id)
            count_query = count_query.where(DonorProfile.location_id == location_id)

        if is_active is not None:
            query = query.where(DonorProfile.is_active == is_active)
            count_query = count_query.where(DonorProfile.is_active == is_active)

        if is_available is not None:
            query = query.where(DonorProfile.is_available == is_available)
            count_query = count_query.where(DonorProfile.is_available == is_available)

        if is_otp_verified is not None:
            query = query.where(DonorProfile.is_otp_verified == is_otp_verified)
            count_query = count_query.where(DonorProfile.is_otp_verified == is_otp_verified)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0
        pages = math.ceil(total / size) if total > 0 else 1

        query = query.order_by(DonorProfile.created_at.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        donors = result.scalars().all()

        items: List[AdminDonorResponse] = []
        for d in donors:
            # Count reports filed against this donor
            rep_count_stmt = select(func.count(Report.id)).where(Report.donor_id == d.id)
            rep_count = (await db.execute(rep_count_stmt)).scalar() or 0

            items.append(
                AdminDonorResponse(
                    id=d.id,
                    user_id=d.user_id,
                    name=d.user.name,
                    mobile=d.user.mobile,
                    date_of_birth=d.date_of_birth,
                    blood_group=d.blood_group,
                    location=LocationResponse.model_validate(d.location),
                    is_available=d.is_available,
                    is_active=d.is_active,
                    is_otp_verified=d.is_otp_verified,
                    contact_consent=d.contact_consent,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                    reports_count=rep_count
                )
            )

        return PaginatedResponse[AdminDonorResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def activate_donor(
        self,
        db: AsyncSession,
        admin_user: User,
        donor_id: uuid.UUID
    ) -> AdminDonorResponse:
        """Activate a donor profile."""
        stmt = select(DonorProfile).where(DonorProfile.id == donor_id)
        result = await db.execute(stmt)
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found."
            )

        donor.is_active = True
        now = datetime.now(timezone.utc)

        audit = AdminAction(
            admin_id=admin_user.id,
            action=AdminActionType.ACTIVATE_DONOR.value,
            target_type="donor_profile",
            target_id=str(donor.id),
            details={"name": donor.user.name, "mobile": donor.user.mobile},
            created_at=now
        )
        db.add(audit)
        await db.commit()
        await db.refresh(donor)

        return AdminDonorResponse(
            id=donor.id,
            user_id=donor.user_id,
            name=donor.user.name,
            mobile=donor.user.mobile,
            date_of_birth=donor.date_of_birth,
            blood_group=donor.blood_group,
            location=LocationResponse.model_validate(donor.location),
            is_available=donor.is_available,
            is_active=donor.is_active,
            is_otp_verified=donor.is_otp_verified,
            contact_consent=donor.contact_consent,
            created_at=donor.created_at,
            updated_at=donor.updated_at
        )

    async def deactivate_donor(
        self,
        db: AsyncSession,
        admin_user: User,
        donor_id: uuid.UUID
    ) -> AdminDonorResponse:
        """Deactivate a donor profile."""
        stmt = select(DonorProfile).where(DonorProfile.id == donor_id)
        result = await db.execute(stmt)
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found."
            )

        donor.is_active = False
        now = datetime.now(timezone.utc)

        audit = AdminAction(
            admin_id=admin_user.id,
            action=AdminActionType.DEACTIVATE_DONOR.value,
            target_type="donor_profile",
            target_id=str(donor.id),
            details={"name": donor.user.name, "mobile": donor.user.mobile},
            created_at=now
        )
        db.add(audit)
        await db.commit()
        await db.refresh(donor)

        return AdminDonorResponse(
            id=donor.id,
            user_id=donor.user_id,
            name=donor.user.name,
            mobile=donor.user.mobile,
            date_of_birth=donor.date_of_birth,
            blood_group=donor.blood_group,
            location=LocationResponse.model_validate(donor.location),
            is_available=donor.is_available,
            is_active=donor.is_active,
            is_otp_verified=donor.is_otp_verified,
            contact_consent=donor.contact_consent,
            created_at=donor.created_at,
            updated_at=donor.updated_at
        )

    async def update_donor_availability(
        self,
        db: AsyncSession,
        admin_user: User,
        donor_id: uuid.UUID,
        is_available: bool
    ) -> AdminDonorResponse:
        """Admin updates a donor's availability."""
        stmt = select(DonorProfile).where(DonorProfile.id == donor_id)
        result = await db.execute(stmt)
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found."
            )

        donor.is_available = is_available
        now = datetime.now(timezone.utc)

        audit = AdminAction(
            admin_id=admin_user.id,
            action=AdminActionType.UPDATE_AVAILABILITY.value,
            target_type="donor_profile",
            target_id=str(donor.id),
            details={"is_available": is_available},
            created_at=now
        )
        db.add(audit)
        await db.commit()
        await db.refresh(donor)

        return AdminDonorResponse(
            id=donor.id,
            user_id=donor.user_id,
            name=donor.user.name,
            mobile=donor.user.mobile,
            date_of_birth=donor.date_of_birth,
            blood_group=donor.blood_group,
            location=LocationResponse.model_validate(donor.location),
            is_available=donor.is_available,
            is_active=donor.is_active,
            is_otp_verified=donor.is_otp_verified,
            contact_consent=donor.contact_consent,
            created_at=donor.created_at,
            updated_at=donor.updated_at
        )

    async def delete_donor(
        self,
        db: AsyncSession,
        admin_user: User,
        donor_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Delete an inappropriate, fake, or spam donor registration."""
        stmt = select(DonorProfile).where(DonorProfile.id == donor_id)
        result = await db.execute(stmt)
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found."
            )

        details = {
            "deleted_donor_id": str(donor.id),
            "user_id": str(donor.user_id),
            "name": donor.user.name,
            "mobile": donor.user.mobile,
            "blood_group": donor.blood_group.value
        }

        # Delete donor profile
        await db.delete(donor)

        # Audit log
        audit = AdminAction(
            admin_id=admin_user.id,
            action=AdminActionType.DELETE_DONOR.value,
            target_type="donor_profile",
            target_id=str(donor_id),
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        db.add(audit)
        await db.commit()

        return {
            "success": True,
            "message": "Donor registration deleted successfully.",
            "deleted_id": str(donor_id)
        }

    async def list_requests(
        self,
        db: AsyncSession,
        status_filter: Optional[RequestStatus] = None,
        blood_group: Optional[BloodGroup] = None,
        location_id: Optional[int] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse[BloodRequestResponse]:
        """Admin view of all blood requests."""
        page = max(1, page)
        size = max(1, min(size, 100))
        offset = (page - 1) * size

        query = select(BloodRequest).order_by(BloodRequest.created_at.desc())
        count_query = select(func.count(BloodRequest.id))

        if status_filter:
            query = query.where(BloodRequest.status == status_filter)
            count_query = count_query.where(BloodRequest.status == status_filter)

        if blood_group:
            query = query.where(BloodRequest.blood_group == blood_group)
            count_query = count_query.where(BloodRequest.blood_group == blood_group)

        if location_id:
            query = query.where(BloodRequest.location_id == location_id)
            count_query = count_query.where(BloodRequest.location_id == location_id)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0
        pages = math.ceil(total / size) if total > 0 else 1

        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        requests = result.scalars().all()

        items = [
            BloodRequestResponse(
                id=r.id,
                requester_id=r.requester_id,
                donor_id=r.donor_id,
                blood_group=r.blood_group,
                location=LocationResponse.model_validate(r.location),
                message=r.message,
                status=r.status,
                created_at=r.created_at,
                responded_at=r.responded_at,
                donor_name=r.donor.user.name if r.donor else "Unknown",
                donor_mobile=r.donor.user.mobile if r.donor else "Unknown",
                requester_name=r.requester.name if r.requester else "Unknown",
                requester_mobile=r.requester.mobile if r.requester else "Unknown"
            )
            for r in requests
        ]

        return PaginatedResponse[BloodRequestResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def get_statistics(self, db: AsyncSession) -> AdminStatisticsResponse:
        """Compute aggregate system metrics for admin dashboard."""
        # 1. Total & Filtered Donors
        total_donors = (await db.execute(select(func.count(DonorProfile.id)))).scalar() or 0
        available_donors = (
            await db.execute(
                select(func.count(DonorProfile.id)).where(
                    DonorProfile.is_available.is_(True),
                    DonorProfile.is_active.is_(True)
                )
            )
        ).scalar() or 0
        active_donors = (
            await db.execute(
                select(func.count(DonorProfile.id)).where(DonorProfile.is_active.is_(True))
            )
        ).scalar() or 0
        verified_donors = (
            await db.execute(
                select(func.count(DonorProfile.id)).where(DonorProfile.is_otp_verified.is_(True))
            )
        ).scalar() or 0

        # 2. Donors by Blood Group
        bg_stmt = select(DonorProfile.blood_group, func.count(DonorProfile.id)).group_by(DonorProfile.blood_group)
        bg_res = await db.execute(bg_stmt)
        donors_by_blood_group = {bg.value: count for bg, count in bg_res.all()}

        # 3. Donors by Location
        loc_stmt = (
            select(Location.name, func.count(DonorProfile.id))
            .join(DonorProfile, DonorProfile.location_id == Location.id)
            .group_by(Location.name)
        )
        loc_res = await db.execute(loc_stmt)
        donors_by_location = {loc_name: count for loc_name, count in loc_res.all()}

        # 4. Requests Stats
        req_pending = (await db.execute(select(func.count(BloodRequest.id)).where(BloodRequest.status == RequestStatus.PENDING))).scalar() or 0
        req_accepted = (await db.execute(select(func.count(BloodRequest.id)).where(BloodRequest.status == RequestStatus.ACCEPTED))).scalar() or 0
        req_rejected = (await db.execute(select(func.count(BloodRequest.id)).where(BloodRequest.status == RequestStatus.REJECTED))).scalar() or 0
        req_total = req_pending + req_accepted + req_rejected

        # 5. Reports Stats
        rep_open = (await db.execute(select(func.count(Report.id)).where(Report.status == ReportStatus.OPEN))).scalar() or 0
        rep_reviewing = (await db.execute(select(func.count(Report.id)).where(Report.status == ReportStatus.REVIEWING))).scalar() or 0
        rep_resolved = (await db.execute(select(func.count(Report.id)).where(Report.status == ReportStatus.RESOLVED))).scalar() or 0
        rep_dismissed = (await db.execute(select(func.count(Report.id)).where(Report.status == ReportStatus.DISMISSED))).scalar() or 0
        rep_total = rep_open + rep_reviewing + rep_resolved + rep_dismissed

        return AdminStatisticsResponse(
            total_registered_donors=total_donors,
            available_donors=available_donors,
            active_donors=active_donors,
            verified_donors=verified_donors,
            donors_by_blood_group=donors_by_blood_group,
            donors_by_location=donors_by_location,
            requests=RequestStats(
                pending=req_pending,
                accepted=req_accepted,
                rejected=req_rejected,
                total=req_total
            ),
            reports=ReportStats(
                open=rep_open,
                reviewing=rep_reviewing,
                resolved=rep_resolved,
                dismissed=rep_dismissed,
                total=rep_total
            )
        )

    async def list_audit_logs(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 50
    ) -> PaginatedResponse[AdminAuditLogResponse]:
        """Fetch audit trail of administrative actions."""
        page = max(1, page)
        size = max(1, min(size, 100))
        offset = (page - 1) * size

        count_res = await db.execute(select(func.count(AdminAction.id)))
        total = count_res.scalar() or 0
        pages = math.ceil(total / size) if total > 0 else 1

        query = select(AdminAction).order_by(AdminAction.created_at.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        actions = result.scalars().all()

        items = [
            AdminAuditLogResponse(
                id=a.id,
                admin_id=a.admin_id,
                admin_name=a.admin.name if a.admin else "System/Admin",
                action=a.action,
                target_type=a.target_type,
                target_id=a.target_id,
                details=a.details,
                created_at=a.created_at
            )
            for a in actions
        ]

        return PaginatedResponse[AdminAuditLogResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def manage_admins(
        self,
        db: AsyncSession,
        auth_context: AdminAuthContext,
        request: AdminManagementRequest
    ) -> AdminManagementResponse:
        """
        Dynamically manage platform administrators: PROMOTE, DEMOTE, or LIST.
        Supports both Admin JWT and break-glass X-Admin-Secret.
        Enforces last-administrator lockout protection and creates audit logs.
        """
        actor_id = auth_context.admin_user.id if auth_context.admin_user else None
        actor_type = "admin_user" if auth_context.admin_user else "bootstrap_secret"

        if request.action == AdminManagementAction.LIST:
            stmt = select(User).where(User.role == UserRole.ADMIN).order_by(User.created_at.asc())
            result = await db.execute(stmt)
            admins = result.scalars().all()
            admin_summaries = [AdminUserSummary.model_validate(a) for a in admins]
            return AdminManagementResponse(
                success=True,
                message="Administrators retrieved successfully.",
                action=AdminManagementAction.LIST,
                admins=admin_summaries
            )

        # PROMOTE, DEMOTE, or UPDATE_NAME requires mutation lock
        mobile = request.mobile
        now = datetime.now(timezone.utc)

        async with self._mutation_lock:
            # 1. UPDATE_NAME Action
            if request.action == AdminManagementAction.UPDATE_NAME:
                if request.user_id:
                    stmt = select(User).where(User.id == request.user_id)
                else:
                    stmt = select(User).where(User.mobile == mobile)
                res = await db.execute(stmt)
                user = res.scalar_one_or_none()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Administrator not found."
                    )
                if user.role != UserRole.ADMIN:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"User {user.mobile} is not an administrator."
                    )
                new_name = request.name.strip() if request.name else ""
                if not new_name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Name cannot be empty."
                    )
                old_name = user.name
                user.name = new_name
                audit = AdminAction(
                    admin_id=actor_id,
                    action="UPDATE_ADMIN_NAME",
                    target_type="user",
                    target_id=str(user.id),
                    details={
                        "mobile": user.mobile,
                        "old_name": old_name,
                        "new_name": new_name,
                        "actor_type": actor_type,
                    },
                    created_at=now
                )
                db.add(audit)
                await db.commit()
                await db.refresh(user)

                return AdminManagementResponse(
                    success=True,
                    message=f"Administrator name updated from '{old_name}' to '{new_name}'.",
                    action=AdminManagementAction.UPDATE_NAME,
                    user=AdminUserSummary.model_validate(user)
                )

            # 2. Lookup User for PROMOTE or DEMOTE
            stmt = select(User).where(User.mobile == mobile)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()

            if request.action == AdminManagementAction.PROMOTE:
                if not user:
                    # Directly create/provision new user as ADMIN even if not existing as donor/requester
                    new_name = request.name.strip() if request.name and request.name.strip() else "Administrator"
                    user = User(
                        name=new_name,
                        mobile=mobile,
                        role=UserRole.ADMIN,
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()

                    audit = AdminAction(
                        admin_id=actor_id,
                        action="ADD_ADMIN",
                        target_type="user",
                        target_id=str(user.id),
                        details={
                            "mobile": user.mobile,
                            "name": user.name,
                            "actor_type": actor_type,
                            "provisioned_directly": True,
                        },
                        created_at=now
                    )
                    db.add(audit)
                    await db.commit()
                    await db.refresh(user)

                    return AdminManagementResponse(
                        success=True,
                        message=f"Administrator '{user.name}' (+91 {user.mobile}) added successfully.",
                        action=AdminManagementAction.PROMOTE,
                        user=AdminUserSummary.model_validate(user)
                    )

                # Existing user -> promote and update name if provided
                if request.name and request.name.strip():
                    user.name = request.name.strip()

                if user.role == UserRole.ADMIN:
                    user.is_active = True
                    await db.commit()
                    await db.refresh(user)
                    return AdminManagementResponse(
                        success=True,
                        message=f"Administrator '{user.name}' (+91 {user.mobile}) details updated successfully.",
                        action=AdminManagementAction.PROMOTE,
                        user=AdminUserSummary.model_validate(user)
                    )

                user.role = UserRole.ADMIN
                user.is_active = True
                audit = AdminAction(
                    admin_id=actor_id,
                    action="PROMOTE",
                    target_type="user",
                    target_id=str(user.id),
                    details={
                        "mobile": user.mobile,
                        "name": user.name,
                        "actor_type": actor_type,
                        "previous_role": UserRole.DONOR.value if user.donor_profile else UserRole.REQUESTER.value,
                    },
                    created_at=now
                )
                db.add(audit)
                await db.commit()
                await db.refresh(user)

                return AdminManagementResponse(
                    success=True,
                    message=f"User '{user.name}' ({user.mobile}) has been successfully promoted to administrator.",
                    action=AdminManagementAction.PROMOTE,
                    user=AdminUserSummary.model_validate(user)
                )

            elif request.action == AdminManagementAction.DEMOTE:
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found."
                    )
                if user.role != UserRole.ADMIN:
                    return AdminManagementResponse(
                        success=True,
                        message=f"User {user.mobile} is not an administrator.",
                        action=AdminManagementAction.DEMOTE,
                        user=AdminUserSummary.model_validate(user)
                    )

                # Prevent demoting the last remaining active administrator
                count_stmt = select(func.count(User.id)).where(
                    User.role == UserRole.ADMIN,
                    User.is_active == True
                )
                admin_count = (await db.execute(count_stmt)).scalar() or 0
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot demote the last remaining administrator."
                    )

                new_role = UserRole.DONOR if user.donor_profile else UserRole.REQUESTER
                user.role = new_role
                audit = AdminAction(
                    admin_id=actor_id,
                    action="DEMOTE",
                    target_type="user",
                    target_id=str(user.id),
                    details={
                        "mobile": user.mobile,
                        "name": user.name,
                        "actor_type": actor_type,
                        "new_role": new_role.value,
                    },
                    created_at=now
                )
                db.add(audit)
                await db.commit()
                await db.refresh(user)

                return AdminManagementResponse(
                    success=True,
                    message=f"Administrator '{user.name}' ({user.mobile}) demoted to {new_role.value.lower()}.",
                    action=AdminManagementAction.DEMOTE,
                    user=AdminUserSummary.model_validate(user)
                )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported action: {request.action}"
        )

    async def test_whatsapp(
        self,
        db: AsyncSession,
        auth_context: AdminAuthContext,
        recipient_mobile: str,
        template_name: str = "hello_world",
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> AdminWhatsAppTestResponse:
        """Send a diagnostic test template message via WhatsApp Meta Cloud API without exposing credentials."""
        from app.core.config import settings
        from app.services.whatsapp_service import MetaWhatsAppProvider, get_whatsapp_provider

        actor_id = auth_context.admin_user.id if auth_context.admin_user else None
        actor_name = auth_context.admin_user.name if auth_context.admin_user else "Bootstrap Secret"

        is_token_set = bool(settings.META_WA_ACCESS_TOKEN and settings.META_WA_ACCESS_TOKEN.strip())
        is_phone_set = bool(settings.META_WA_PHONE_NUMBER_ID and settings.META_WA_PHONE_NUMBER_ID.strip())

        # Auto-populate components for known BloodConnect templates if not explicitly passed
        if components is None:
            if template_name in [settings.WHATSAPP_TEMPLATE_BLOOD_REQUEST, "bloodconnect_blood_request"]:
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "O+"},
                            {"type": "text", "text": "Coimbatore"},
                            {"type": "text", "text": "KG Hospital"},
                            {"type": "text", "text": "Emergency Patient"}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [{"type": "payload", "payload": f"ACCEPT:test-{uuid.uuid4().hex[:8]}"}]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [{"type": "payload", "payload": f"REJECT:test-{uuid.uuid4().hex[:8]}"}]
                    }
                ]
            elif template_name in [settings.WHATSAPP_TEMPLATE_AUTH_OTP, "bloodconnect_auth_otp"]:
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "123456"}
                        ]
                    }
                ]
            elif template_name in [settings.WHATSAPP_TEMPLATE_REQUEST_ACCEPTED, "bloodconnect_request_accepted"]:
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "Arun Kumar"},
                            {"type": "text", "text": "O+"},
                            {"type": "text", "text": "+91 9876543201"}
                        ]
                    }
                ]
            elif template_name in [settings.WHATSAPP_TEMPLATE_REQUEST_REJECTED, "bloodconnect_request_rejected"]:
                components = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "Rahul Sharma"},
                            {"type": "text", "text": "A+"}
                        ]
                    }
                ]

        # In test mode or when NOTIFICATION_PROVIDER is explicitly 'mock', use get_whatsapp_provider()
        if settings.is_testing or settings.NOTIFICATION_PROVIDER == "mock":
            provider = get_whatsapp_provider()
        elif is_token_set and is_phone_set:
            provider = MetaWhatsAppProvider()
        else:
            provider = get_whatsapp_provider()

        result = await provider.send_template(
            to_mobile=recipient_mobile,
            template_name=template_name,
            language_code=language_code,
            components=components
        )
        if not result.success and components and len(components) > 1 and result.error_message and ("components" in result.error_message.lower() or "button" in result.error_message.lower()):
            retry_res = await provider.send_template(
                to_mobile=recipient_mobile,
                template_name=template_name,
                language_code=language_code,
                components=[components[0]]
            )
            if retry_res.success:
                result = retry_res

        # Audit log the diagnostic test attempt
        now = datetime.now(timezone.utc)
        masked_mobile = f"+91 {recipient_mobile[:2]}******{recipient_mobile[-2:]}" if len(recipient_mobile) == 10 else f"{recipient_mobile[:4]}******{recipient_mobile[-2:]}"

        audit = AdminAction(
            admin_id=actor_id,
            action="TEST_WHATSAPP_DISPATCH",
            target_type="whatsapp",
            target_id=masked_mobile,
            details={
                "actor": actor_name,
                "provider": result.provider,
                "success": result.success,
                "provider_message_id": result.provider_message_id,
                "error_message": result.error_message,
                "template_name": template_name,
            },
            created_at=now
        )
        db.add(audit)
        await db.commit()

        status_msg = (
            f"Test template '{template_name}' sent successfully via {result.provider}."
            if result.success
            else f"WhatsApp test dispatch failed via {result.provider}: {result.error_message}"
        )

        return AdminWhatsAppTestResponse(
            success=result.success,
            message=status_msg,
            provider=result.provider,
            provider_message_id=result.provider_message_id,
            recipient=masked_mobile,
            template_used=template_name,
            phone_number_id_configured=is_phone_set,
            access_token_configured=is_token_set,
            details=result.details,
            error_message=result.error_message
        )


admin_service = AdminService()


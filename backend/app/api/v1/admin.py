from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminAuthContext, require_admin, require_admin_or_bootstrap_secret
from app.database.session import get_db
from app.models.enums import BloodGroup, ReportReason, ReportStatus, RequestStatus
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminDonorResponse,
    AdminManagementRequest,
    AdminManagementResponse,
    AdminStatisticsResponse,
    AdminUpdateReportRequest,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.donor import DonorAvailabilityUpdateRequest
from app.schemas.report import ReportResponse
from app.schemas.request import BloodRequestResponse
from app.services.admin_service import admin_service
from app.services.report_service import report_service

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.get(
    "/donors",
    response_model=PaginatedResponse[AdminDonorResponse],
    summary="List and filter all registered donors",
    description="Administrative list of all registered donors with search, filtering, and reports count."
)
async def list_donors(
    search: Optional[str] = Query(None, description="Search by donor name or mobile"),
    blood_group: Optional[BloodGroup] = Query(None, description="Filter by blood group"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    is_otp_verified: Optional[bool] = Query(None, description="Filter by OTP verification status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_donors(
        db=db,
        search=search,
        blood_group=blood_group,
        location_id=location_id,
        is_active=is_active,
        is_available=is_available,
        is_otp_verified=is_otp_verified,
        page=page,
        size=size
    )


@router.patch(
    "/donors/{donor_id}/activate",
    response_model=AdminDonorResponse,
    summary="Activate a donor profile",
    description="Sets donor profile is_active to true and writes an audit log."
)
async def activate_donor(
    donor_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.activate_donor(db, current_admin, donor_id)


@router.patch(
    "/donors/{donor_id}/deactivate",
    response_model=AdminDonorResponse,
    summary="Deactivate a donor profile",
    description="Sets donor profile is_active to false and writes an audit log."
)
async def deactivate_donor(
    donor_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.deactivate_donor(db, current_admin, donor_id)


@router.patch(
    "/donors/{donor_id}/availability",
    response_model=AdminDonorResponse,
    summary="Manage donor availability",
    description="Updates a donor's donation availability and writes an audit log."
)
async def update_donor_availability(
    donor_id: uuid.UUID,
    request: DonorAvailabilityUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.update_donor_availability(
        db, current_admin, donor_id, request.is_available
    )


@router.delete(
    "/donors/{donor_id}",
    response_model=APIResponse[dict],
    summary="Delete a donor registration",
    description="Permanently deletes an inappropriate or fake donor profile and writes an audit log."
)
async def delete_donor(
    donor_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await admin_service.delete_donor(db, current_admin, donor_id)
    return APIResponse[dict](
        success=True,
        message=result["message"],
        data={"deleted_id": result["deleted_id"]}
    )


@router.get(
    "/requests",
    response_model=PaginatedResponse[BloodRequestResponse],
    summary="List all blood requests across the platform",
    description="Provides administrative oversight for all submitted blood requests."
)
async def list_requests(
    status: Optional[RequestStatus] = Query(None, description="Filter by status"),
    blood_group: Optional[BloodGroup] = Query(None, description="Filter by blood group"),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_requests(
        db=db,
        status_filter=status,
        blood_group=blood_group,
        location_id=location_id,
        page=page,
        size=size
    )


@router.get(
    "/reports",
    response_model=PaginatedResponse[ReportResponse],
    summary="List all reported donor profiles",
    description="Fetches reported donor records with optional status and reason filters."
)
async def list_reports(
    status: Optional[ReportStatus] = Query(None, description="Filter by report status"),
    reason: Optional[ReportReason] = Query(None, description="Filter by report reason"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await report_service.get_reports(
        db=db,
        status_filter=status,
        reason_filter=reason,
        page=page,
        size=size
    )


@router.patch(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="Resolve or dismiss a report",
    description="Updates a report's status and records the decision in the administrative audit log."
)
async def update_report(
    report_id: uuid.UUID,
    request: AdminUpdateReportRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await report_service.update_report(
        db=db,
        admin_user=current_admin,
        report_id=report_id,
        new_status=request.status,
        notes=request.notes
    )


@router.get(
    "/statistics",
    response_model=AdminStatisticsResponse,
    summary="Platform aggregate statistics",
    description="Computes real-time counts of donors by blood group, donors by location, request lifecycle metrics, and open reports."
)
@router.get(
    "/stats",
    response_model=AdminStatisticsResponse,
    include_in_schema=False,
)
async def get_statistics(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_statistics(db)


@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AdminAuditLogResponse],
    summary="Administrative audit trail",
    description="Returns an immutable chronological audit trail of all moderation and administrative operations."
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_audit_logs(db, page=page, size=size)


@router.post(
    "/manage-admins",
    response_model=AdminManagementResponse,
    summary="Dynamic Administrator Management (PROMOTE, DEMOTE, LIST)",
    description="Allows authenticated administrators (via JWT) or emergency bootstrap recovery (via X-Admin-Secret) to promote, demote, or list platform administrators."
)
async def manage_admins(
    request: AdminManagementRequest,
    auth_context: AdminAuthContext = Depends(require_admin_or_bootstrap_secret),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.manage_admins(
        db=db,
        auth_context=auth_context,
        request=request
    )


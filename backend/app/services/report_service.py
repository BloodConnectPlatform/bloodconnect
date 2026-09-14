from datetime import datetime, timezone
import math
from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_action import AdminAction
from app.models.donor import DonorProfile
from app.models.enums import AdminActionType, ReportReason, ReportStatus
from app.models.report import Report
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.report import CreateReportRequest, ReportResponse


class ReportService:
    async def create_report(
        self,
        db: AsyncSession,
        reporter: User,
        data: CreateReportRequest
    ) -> ReportResponse:
        """Submit a new report against a donor profile."""
        # 1. Verify target donor exists
        stmt = select(DonorProfile).where(DonorProfile.id == data.donor_id)
        result = await db.execute(stmt)
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor profile not found."
            )

        # 2. Prevent self-reporting
        if donor.user_id == reporter.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot report your own donor profile."
            )

        # 3. Create Report entity
        report = Report(
            donor_id=donor.id,
            reporter_id=reporter.id,
            reason=data.reason,
            description=data.description.strip() if data.description else None,
            status=ReportStatus.OPEN,
            created_at=datetime.now(timezone.utc)
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        return ReportResponse(
            id=report.id,
            donor_id=report.donor_id,
            donor_name=donor.user.name,
            donor_mobile=donor.user.mobile,
            reporter_id=report.reporter_id,
            reporter_name=reporter.name,
            reason=report.reason,
            description=report.description,
            status=report.status,
            created_at=report.created_at,
            resolved_at=report.resolved_at
        )

    async def get_reports(
        self,
        db: AsyncSession,
        status_filter: Optional[ReportStatus] = None,
        reason_filter: Optional[ReportReason] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse[ReportResponse]:
        """Fetch paginated reports for administrators."""
        page = max(1, page)
        size = max(1, min(size, 100))
        offset = (page - 1) * size

        query = select(Report).order_by(Report.created_at.desc())
        count_query = select(func.count(Report.id))

        if status_filter:
            query = query.where(Report.status == status_filter)
            count_query = count_query.where(Report.status == status_filter)

        if reason_filter:
            query = query.where(Report.reason == reason_filter)
            count_query = count_query.where(Report.reason == reason_filter)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0
        pages = math.ceil(total / size) if total > 0 else 1

        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        reports = result.scalars().all()

        items = [
            ReportResponse(
                id=r.id,
                donor_id=r.donor_id,
                donor_name=r.donor.user.name if r.donor else "Unknown",
                donor_mobile=r.donor.user.mobile if r.donor else "Unknown",
                reporter_id=r.reporter_id,
                reporter_name=r.reporter.name if r.reporter else "Unknown",
                reason=r.reason,
                description=r.description,
                status=r.status,
                created_at=r.created_at,
                resolved_at=r.resolved_at
            )
            for r in reports
        ]

        return PaginatedResponse[ReportResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def update_report(
        self,
        db: AsyncSession,
        admin_user: User,
        report_id: uuid.UUID,
        new_status: ReportStatus,
        notes: Optional[str] = None
    ) -> ReportResponse:
        """Admin updates report status and writes an audit log record."""
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found."
            )

        now = datetime.now(timezone.utc)
        report.status = new_status
        if new_status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
            report.resolved_at = now

        # Write admin audit action
        action_name = (
            AdminActionType.RESOLVE_REPORT.value
            if new_status == ReportStatus.RESOLVED
            else AdminActionType.DISMISS_REPORT.value
        )
        audit_action = AdminAction(
            admin_id=admin_user.id,
            action=action_name,
            target_type="report",
            target_id=str(report.id),
            details={"status": new_status.value, "notes": notes},
            created_at=now
        )
        db.add(audit_action)

        await db.commit()
        await db.refresh(report)

        return ReportResponse(
            id=report.id,
            donor_id=report.donor_id,
            donor_name=report.donor.user.name if report.donor else "Unknown",
            donor_mobile=report.donor.user.mobile if report.donor else "Unknown",
            reporter_id=report.reporter_id,
            reporter_name=report.reporter.name if report.reporter else "Unknown",
            reason=report.reason,
            description=report.description,
            status=report.status,
            created_at=report.created_at,
            resolved_at=report.resolved_at
        )


report_service = ReportService()

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.report import CreateReportRequest, ReportResponse
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a donor profile",
    description="Submit an issue report regarding a donor profile (e.g. incorrect blood group, fake profile, spam)."
)
async def report_donor(
    request: CreateReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await report_service.create_report(db, current_user, request)

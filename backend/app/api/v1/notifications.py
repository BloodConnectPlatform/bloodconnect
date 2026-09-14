import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get user notifications",
    description="Retrieves in-app notifications for the authenticated user with total and unread counters.",
    status_code=status.HTTP_200_OK
)
async def get_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    description="Updates a single notification status to read.",
    status_code=status.HTTP_200_OK
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await notification_service.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id
    )


@router.patch(
    "/read-all",
    response_model=APIResponse[dict],
    summary="Mark all notifications as read",
    description="Marks all unread notifications for the current user as read.",
    status_code=status.HTTP_200_OK
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    count = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    return APIResponse[dict](
        success=True,
        message=f"Marked {count} notification(s) as read.",
        data={"updated_count": count}
    )

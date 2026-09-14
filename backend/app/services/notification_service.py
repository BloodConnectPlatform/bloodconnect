from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.schemas.notification import NotificationListResponse, NotificationResponse


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str
    ) -> Notification:
        """Create a new in-app notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            is_read=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> NotificationListResponse:
        """Retrieve user's notifications along with total unread count."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        result = await db.execute(query)
        notifications = result.scalars().all()

        # Unread count
        unread_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        unread_res = await db.execute(unread_stmt)
        unread_count = unread_res.scalar() or 0

        total_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
        )
        total_res = await db.execute(total_stmt)
        total_count = total_res.scalar() or 0

        items = [NotificationResponse.model_validate(n) for n in notifications]

        return NotificationListResponse(
            items=items,
            unread_count=unread_count,
            total=total_count
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> NotificationResponse:
        """Mark an individual notification as read."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found."
            )

        notification.is_read = True
        await db.commit()
        await db.refresh(notification)
        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> int:
        """Mark all unread notifications for a user as read."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0


notification_service = NotificationService()

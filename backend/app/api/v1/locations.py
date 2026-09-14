from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.donor import LocationResponse
from app.services.donor_service import donor_service

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get(
    "",
    response_model=List[LocationResponse],
    summary="List predefined donation locations",
    description="Returns all active predefined locations available for search and donor registration.",
    status_code=status.HTTP_200_OK
)
async def list_locations(
    db: AsyncSession = Depends(get_db)
):
    return await donor_service.list_locations(db)

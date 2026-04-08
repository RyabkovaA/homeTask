from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.services.analytics_service import get_analytics
from app.schemas.analytics import AnalyticsOut
from app.models.member import HouseMember
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.get("/houses/{house_id}/analytics", response_model=AnalyticsOut)
async def analytics(
    house_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    return await get_analytics(db, house_id, days)

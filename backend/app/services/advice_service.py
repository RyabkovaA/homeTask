from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.advice import Advice
import uuid


async def get_active_advice(db: AsyncSession) -> list[Advice]:
    result = await db.execute(
        select(Advice).where(Advice.is_active == True)
    )
    return result.scalars().all()


async def get_advice_for_room(db: AsyncSession, room_name: str) -> list[Advice]:
    result = await db.execute(
        select(Advice).where(Advice.is_active == True)
    )
    all_advice = result.scalars().all()
    return [a for a in all_advice if room_name in a.room_names]

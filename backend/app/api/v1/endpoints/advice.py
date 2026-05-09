from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.models.advice import Advice
from app.models.member import HouseMember, MemberRole
from app.schemas.advice import AdviceCreate, AdviceUpdate, AdviceOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


def _require_admin(member: HouseMember) -> None:
    if member.role != MemberRole.admin:
        raise HTTPException(403, "Admin role required")


@router.get("/advice", response_model=list[AdviceOut])
async def list_advice(
    room: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    result = await db.execute(
        select(Advice).where(
            Advice.is_active == True,
            or_(Advice.house_id == None, Advice.house_id == current_member.house_id),
        )
    )
    all_advice = result.scalars().all()
    if room:
        all_advice = [a for a in all_advice if room in a.room_names]
    return all_advice


@router.post("/advice", response_model=AdviceOut, status_code=201)
async def create_advice(
    payload: AdviceCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    _require_admin(current_member)
    data = payload.model_dump()
    # Advice created via the API is always scoped to the creator's house.
    # Global tips (house_id = NULL) come only from seed scripts.
    data["house_id"] = current_member.house_id
    advice = Advice(**data)
    db.add(advice)
    await db.commit()
    await db.refresh(advice)
    return advice


@router.patch("/advice/{advice_id}", response_model=AdviceOut)
async def update_advice(
    advice_id: UUID,
    payload: AdviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    _require_admin(current_member)
    advice = await db.get(Advice, advice_id)
    if not advice:
        raise HTTPException(404, "Advice not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(advice, field, value)
    await db.commit()
    await db.refresh(advice)
    return advice


@router.delete("/advice/{advice_id}", status_code=204)
async def delete_advice(
    advice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    _require_admin(current_member)
    advice = await db.get(Advice, advice_id)
    if not advice:
        raise HTTPException(404)
    advice.is_active = False
    await db.commit()

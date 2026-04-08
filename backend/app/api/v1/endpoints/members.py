from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.core.database import get_db
from app.models.member import HouseMember
from app.schemas.member import MemberUpdate, MemberOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.get("/houses/{house_id}/members", response_model=list[MemberOut])
async def list_members(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    result = await db.execute(
        select(HouseMember)
        .where(HouseMember.house_id == house_id)
        .options(selectinload(HouseMember.user))
    )
    return result.scalars().all()


@router.patch("/members/{member_id}", response_model=MemberOut)
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    member = await db.get(HouseMember, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/members/{member_id}", status_code=204)
async def remove_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    member = await db.get(HouseMember, member_id)
    if not member:
        raise HTTPException(404)
    await db.delete(member)
    await db.commit()

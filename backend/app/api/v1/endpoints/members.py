from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.member import HouseMember, MemberRole
from app.models.user import User
from app.schemas.member import MemberUpdate, MemberOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


class InvitePayload(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.member
    color: str = "#4A7C59"


def _require_admin(member: HouseMember) -> None:
    if member.role != MemberRole.admin:
        raise HTTPException(403, "Admin role required")


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


@router.post("/houses/{house_id}/members/invite", response_model=MemberOut, status_code=201)
async def invite_member(
    house_id: UUID,
    payload: InvitePayload,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    """Invite an existing user (by email) to the house. Admin only."""
    _require_admin(current_member)
    user_result = await db.execute(select(User).where(User.email == payload.email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User with this email not found")

    existing = await db.execute(
        select(HouseMember).where(
            HouseMember.house_id == house_id,
            HouseMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "User is already a member of this house")

    member = HouseMember(
        house_id=house_id,
        user_id=user.id,
        role=payload.role,
        color=payload.color,
    )
    db.add(member)
    await db.commit()
    result = await db.execute(
        select(HouseMember)
        .where(HouseMember.id == member.id)
        .options(selectinload(HouseMember.user))
    )
    return result.scalar_one()


@router.patch("/members/{member_id}", response_model=MemberOut)
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    if payload.role is not None or payload.allowed_room_ids is not None:
        _require_admin(current_member)
    member = await db.get(HouseMember, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    if member.house_id != current_member.house_id:
        raise HTTPException(403, "Member does not belong to your house")
    data = payload.model_dump(exclude_unset=True)
    if "allowed_room_ids" in data and data["allowed_room_ids"] is not None:
        data["allowed_room_ids"] = [str(r) for r in data["allowed_room_ids"]]
    for field, value in data.items():
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
    _require_admin(current_member)
    member = await db.get(HouseMember, member_id)
    if not member:
        raise HTTPException(404)
    await db.delete(member)
    await db.commit()

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.house import House
from app.models.member import HouseMember, MemberRole
from app.models.user import User
from app.schemas.house import HouseCreate, HouseUpdate, HouseOut, JoinHousePayload
from app.api.v1.endpoints.auth import get_current_user, get_current_member, oauth2_scheme

router = APIRouter()


@router.post("/houses", response_model=HouseOut, status_code=201)
async def create_house(
    payload: HouseCreate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Create a house and assign the creator as admin member."""
    user: User = await get_current_user(token, db)
    house = House(name=payload.name)
    db.add(house)
    await db.flush()

    member = HouseMember(house_id=house.id, user_id=user.id, role=MemberRole.admin)
    db.add(member)
    await db.commit()
    await db.refresh(house)
    return house


@router.post("/houses/join", response_model=HouseOut)
async def join_house(
    payload: JoinHousePayload,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Join an existing house by invite code. Caller gets role 'member'."""
    user: User = await get_current_user(token, db)

    result = await db.execute(
        select(House).where(House.invite_code == payload.invite_code.upper())
    )
    house = result.scalar_one_or_none()
    if not house:
        raise HTTPException(404, "Invalid invite code")

    existing = await db.execute(
        select(HouseMember).where(
            HouseMember.house_id == house.id,
            HouseMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already a member of this house")

    member = HouseMember(house_id=house.id, user_id=user.id, role=MemberRole.member)
    db.add(member)
    await db.commit()
    await db.refresh(house)
    return house


@router.get("/houses/{house_id}", response_model=HouseOut)
async def get_house(
    house_id: UUID,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    user: User = await get_current_user(token, db)
    # Verify user is a member
    result = await db.execute(
        select(HouseMember).where(
            HouseMember.house_id == house_id,
            HouseMember.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(403, "Not a member of this house")
    house = await db.get(House, house_id)
    if not house:
        raise HTTPException(404, "House not found")
    return house


@router.patch("/houses/{house_id}", response_model=HouseOut)
async def update_house(
    house_id: UUID,
    payload: HouseUpdate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    user: User = await get_current_user(token, db)
    result = await db.execute(
        select(HouseMember).where(
            HouseMember.house_id == house_id,
            HouseMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(403, "Not a member of this house")
    if member.role != MemberRole.admin:
        raise HTTPException(403, "Admin role required")

    house = await db.get(House, house_id)
    if not house:
        raise HTTPException(404, "House not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(house, field, value)
    await db.commit()
    await db.refresh(house)
    return house

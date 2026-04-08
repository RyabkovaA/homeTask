from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.models.room import Room
from app.models.member import HouseMember
from app.schemas.room import RoomCreate, RoomUpdate, RoomOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.get("/houses/{house_id}/rooms", response_model=list[RoomOut])
async def list_rooms(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    result = await db.execute(select(Room).where(Room.house_id == house_id))
    return result.scalars().all()


@router.post("/houses/{house_id}/rooms", response_model=RoomOut, status_code=201)
async def create_room(
    house_id: UUID,
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    room = Room(**payload.model_dump(), house_id=house_id)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.patch("/rooms/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: UUID,
    payload: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    await db.commit()
    await db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(404)
    await db.delete(room)
    await db.commit()

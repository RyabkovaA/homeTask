from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from typing import Optional
from app.core.database import get_db
from app.models.task_event import TaskEvent, EventStatus
from app.models.task import Task
from app.models.member import HouseMember
from app.models.room import Room
from app.models.user import User
from app.schemas.task_event import EventCreate, EventOut, EventHistoryOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    existing = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id == payload.task_id,
                TaskEvent.occurrence_date == payload.occurrence_date
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Event for this occurrence already exists")

    event = TaskEvent(**payload.model_dump(), actor_id=current_member.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/houses/{house_id}/events", response_model=list[EventHistoryOut])
async def list_events(
    house_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[EventStatus] = None,
    room_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    q = (
        select(TaskEvent, Task, Room, HouseMember, User)
        .join(Task, TaskEvent.task_id == Task.id)
        .join(HouseMember, TaskEvent.actor_id == HouseMember.id)
        .join(User, HouseMember.user_id == User.id)
        .outerjoin(Room, Task.room_id == Room.id)
        .where(Task.house_id == house_id)
    )

    if from_date:
        q = q.where(TaskEvent.occurrence_date >= from_date)
    if to_date:
        q = q.where(TaskEvent.occurrence_date <= to_date)
    if status:
        q = q.where(TaskEvent.status == status)
    if room_id:
        q = q.where(Task.room_id == room_id)

    result = await db.execute(
        q.order_by(TaskEvent.created_at.desc(), TaskEvent.occurrence_date.desc())
    )
    rows = result.all()

    return [
        EventHistoryOut(
            id=event.id,
            task_id=event.task_id,
            actor_id=event.actor_id,
            occurrence_date=event.occurrence_date,
            status=event.status,
            moved_to=event.moved_to,
            note=event.note,
            created_at=event.created_at,
            task_title=task.title,
            task_priority=task.priority,
            room_id=room.id if room else None,
            room_name=room.name if room else None,
            room_icon=room.icon if room else None,
            actor_name=user.name,
            actor_color=member.color,
        )
        for event, task, room, member, user in rows
    ]
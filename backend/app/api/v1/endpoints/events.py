from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from typing import Optional
from app.core.database import get_db
from app.models.task_event import TaskEvent
from app.models.task import Task
from app.models.member import HouseMember
from app.schemas.task_event import EventCreate, EventOut
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


@router.get("/houses/{house_id}/events", response_model=list[EventOut])
async def list_events(
    house_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    q = select(TaskEvent).join(Task).where(Task.house_id == house_id)
    if from_date:
        q = q.where(TaskEvent.occurrence_date >= from_date)
    if to_date:
        q = q.where(TaskEvent.occurrence_date <= to_date)
    result = await db.execute(q.order_by(TaskEvent.occurrence_date.desc()))
    return result.scalars().all()

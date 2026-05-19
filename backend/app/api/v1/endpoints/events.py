from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from typing import Optional
from app.core.database import get_db
from app.models.task_event import TaskEvent, EventStatus
from app.models.task import Task
from app.models.member import HouseMember, MemberRole
from app.models.room import Room
from app.models.user import User
from app.schemas.task_event import EventCreate, EventOut, EventHistoryOut, EventPatch
from app.api.v1.endpoints.auth import get_current_member, get_house_member
from app.services import push_service

router = APIRouter()


@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = await db.get(Task, payload.task_id)
    if not task or task.house_id != current_member.house_id:
        raise HTTPException(403, "Task does not belong to your house")

    if current_member.role == MemberRole.limited and current_member.allowed_room_ids:
        if str(task.room_id) not in [str(r) for r in current_member.allowed_room_ids]:
            raise HTTPException(403, "Limited members can only act on tasks in their assigned rooms")

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

    if payload.status == EventStatus.done:
        background_tasks.add_task(
            push_service.check_and_notify_all_done,
            current_member.id,
            current_member.house_id,
        )

    return event


@router.patch("/events/{task_id}/{occurrence_date}", response_model=EventOut)
async def update_event(
    task_id: UUID,
    occurrence_date: date,
    payload: EventPatch,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """Update status/moved_to of an existing event (e.g. re-do a skipped task)."""
    task = await db.get(Task, task_id)
    if not task or task.house_id != current_member.house_id:
        raise HTTPException(403, "Task does not belong to your house")

    result = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id == task_id,
                TaskEvent.occurrence_date == occurrence_date,
            )
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")

    event.status = payload.status
    event.moved_to = payload.moved_to
    if payload.note is not None:
        event.note = payload.note
    event.actor_id = current_member.id
    await db.commit()
    await db.refresh(event)

    if payload.status == EventStatus.done:
        background_tasks.add_task(
            push_service.check_and_notify_all_done,
            current_member.id,
            current_member.house_id,
        )

    return event


@router.get("/houses/{house_id}/events", response_model=list[EventHistoryOut])
async def list_events(
    house_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[EventStatus] = None,
    room_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_house_member)
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

    if current_member.role == MemberRole.limited:
        if not current_member.allowed_room_ids:
            return []
        q = q.where(Task.room_id.in_(current_member.allowed_room_ids))

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

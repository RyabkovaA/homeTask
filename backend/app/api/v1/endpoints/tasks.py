from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.models.task import Task
from app.models.member import HouseMember, MemberRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.api.v1.endpoints.auth import get_house_member, get_current_member
from app.services.recurrence_service import build_rrule
from app.services import push_service

router = APIRouter()


def _require_not_limited(member: HouseMember) -> None:
    if member.role == MemberRole.limited:
        raise HTTPException(403, "Limited members cannot create or modify tasks")


@router.get("/houses/{house_id}/tasks", response_model=list[TaskOut])
async def list_tasks(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_house_member)
):
    if current_member.role == MemberRole.limited:
        if not current_member.allowed_room_ids:
            return []
        q = select(Task).where(
            Task.house_id == house_id,
            Task.is_active == True,
            Task.room_id.in_(current_member.allowed_room_ids)
        )
    else:
        q = select(Task).where(Task.house_id == house_id, Task.is_active == True)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/houses/{house_id}/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    house_id: UUID,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_house_member)
):
    _require_not_limited(current_member)
    task = Task(**payload.model_dump(), house_id=house_id, created_by=current_member.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    _require_not_limited(current_member)
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.house_id != current_member.house_id:
        raise HTTPException(403, "Task does not belong to your house")

    old_assignee_id = task.assignee_id
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)

    # Notify newly assigned member (skip if assigning to yourself)
    new_assignee_id = task.assignee_id
    if (
        "assignee_id" in payload.model_dump(exclude_unset=True)
        and new_assignee_id
        and new_assignee_id != old_assignee_id
        and new_assignee_id != current_member.id
    ):
        background_tasks.add_task(push_service.notify_task_assigned, new_assignee_id, task.title)

    return task


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    _require_not_limited(current_member)
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404)
    if task.house_id != current_member.house_id:
        raise HTTPException(403, "Task does not belong to your house")
    task.is_active = False
    await db.commit()


@router.get("/tasks/{task_id}/rrule")
async def get_task_rrule(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    """Returns the iCalendar RRULE string for a task (RFC 5545)."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.house_id != current_member.house_id:
        raise HTTPException(403, "Task does not belong to your house")
    return {
        "task_id": str(task_id),
        "rrule": build_rrule(task),
        "dtstart": str(task.start_date),
        "window_days": task.window_days,
        "skip_policy": task.skip_policy,
    }

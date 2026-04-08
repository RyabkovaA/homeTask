from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.models.task import Task
from app.models.member import HouseMember
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.get("/houses/{house_id}/tasks", response_model=list[TaskOut])
async def list_tasks(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    result = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    return result.scalars().all()


@router.post("/houses/{house_id}/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    house_id: UUID,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = Task(**payload.model_dump(), house_id=house_id, created_by=current_member.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404)
    task.is_active = False
    await db.commit()

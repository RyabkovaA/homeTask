from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task
from app.models.member import HouseMember
from app.schemas.task import TaskCreate, TaskUpdate
import uuid


async def create_task(db: AsyncSession, payload: TaskCreate, house_id: uuid.UUID, member: HouseMember) -> Task:
    task = Task(**payload.model_dump(), house_id=house_id, created_by=member.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_tasks(db: AsyncSession, house_id: uuid.UUID) -> list[Task]:
    result = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    return result.scalars().all()

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.task import Frequency, SkipPolicy, Priority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    room_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    priority: Priority = Priority.medium
    frequency: Frequency = Frequency.once
    skip_policy: SkipPolicy = SkipPolicy.overdue
    start_date: date
    days_of_week: Optional[list[int]] = None
    custom_interval_days: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    room_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    priority: Optional[Priority] = None
    frequency: Optional[Frequency] = None
    skip_policy: Optional[SkipPolicy] = None
    days_of_week: Optional[list[int]] = None
    custom_interval_days: Optional[int] = None
    is_active: Optional[bool] = None


class TaskOut(BaseModel):
    id: UUID
    house_id: UUID
    room_id: Optional[UUID]
    assignee_id: Optional[UUID]
    title: str
    description: str
    priority: Priority
    frequency: Frequency
    skip_policy: SkipPolicy
    start_date: date
    days_of_week: Optional[list[int]]
    custom_interval_days: Optional[int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

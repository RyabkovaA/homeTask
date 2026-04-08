from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.task_event import EventStatus
from app.models.task import Priority


class EventCreate(BaseModel):
    task_id: UUID
    occurrence_date: date
    status: EventStatus
    moved_to: Optional[date] = None
    note: Optional[str] = None


class EventOut(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: UUID
    occurrence_date: date
    status: EventStatus
    moved_to: Optional[date]
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EventHistoryOut(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: UUID
    occurrence_date: date
    status: EventStatus
    moved_to: Optional[date]
    note: Optional[str]
    created_at: datetime

    task_title: str
    task_priority: Priority
    room_id: Optional[UUID] = None
    room_name: Optional[str] = None
    room_icon: Optional[str] = None

    actor_name: str
    actor_color: str

    model_config = {"from_attributes": True}
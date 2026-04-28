import uuid
import enum
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, Date, Integer, Float, JSON, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Frequency(str, enum.Enum):
    once = "once"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    custom = "custom"


class SkipPolicy(str, enum.Enum):
    move = "move"
    overdue = "overdue"
    skip = "skip"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"))

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    frequency: Mapped[Frequency] = mapped_column(SAEnum(Frequency), default=Frequency.once)
    skip_policy: Mapped[SkipPolicy] = mapped_column(SAEnum(SkipPolicy), default=SkipPolicy.overdue)

    start_date: Mapped[date] = mapped_column(Date)
    days_of_week: Mapped[list | None] = mapped_column(JSON, nullable=True)
    custom_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_days: Mapped[int] = mapped_column(Integer, default=0)
    effort_hours: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    house: Mapped["House"] = relationship(back_populates="tasks")
    room: Mapped["Room"] = relationship(back_populates="tasks")
    events: Mapped[list["TaskEvent"]] = relationship(back_populates="task", cascade="all, delete-orphan")

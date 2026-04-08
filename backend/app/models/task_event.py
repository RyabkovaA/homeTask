import uuid
import enum
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class EventStatus(str, enum.Enum):
    done = "done"
    skipped = "skipped"
    overdue = "overdue"
    moved = "moved"


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"))

    occurrence_date: Mapped[date] = mapped_column(Date)
    status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus))
    moved_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="events")

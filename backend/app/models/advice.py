import uuid
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Advice(Base):
    __tablename__ = "advice"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(2000))
    steps: Mapped[list] = mapped_column(JSON, default=list)
    room_names: Mapped[list] = mapped_column(JSON, default=list)
    task_keywords: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

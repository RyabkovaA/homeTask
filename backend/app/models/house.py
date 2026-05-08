import uuid
import secrets
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def _generate_invite_code() -> str:
    return secrets.token_hex(4).upper()


class House(Base):
    __tablename__ = "houses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    invite_code: Mapped[str] = mapped_column(String(8), unique=True, default=_generate_invite_code)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["HouseMember"]] = relationship(back_populates="house", cascade="all, delete-orphan")
    rooms: Mapped[list["Room"]] = relationship(back_populates="house", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="house", cascade="all, delete-orphan")

import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(10), default="🏠")
    color: Mapped[str] = mapped_column(String(7), default="#8DB596")

    house: Mapped["House"] = relationship(back_populates="rooms")
    tasks: Mapped[list["Task"]] = relationship(back_populates="room")

import uuid
import enum
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class MemberRole(str, enum.Enum):
    admin = "admin"
    member = "member"
    limited = "limited"


class HouseMember(Base):
    __tablename__ = "house_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[MemberRole] = mapped_column(SAEnum(MemberRole), default=MemberRole.member)
    color: Mapped[str] = mapped_column(String(7), default="#4A7C59")
    allowed_room_ids: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    house: Mapped["House"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")

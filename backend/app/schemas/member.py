from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from app.models.member import MemberRole
from app.schemas.user import UserOut


class MemberCreate(BaseModel):
    user_id: UUID
    role: MemberRole = MemberRole.member
    color: str = "#4A7C59"


class MemberUpdate(BaseModel):
    role: Optional[MemberRole] = None
    color: Optional[str] = None
    allowed_room_ids: Optional[list[UUID]] = None


class MemberOut(BaseModel):
    id: UUID
    house_id: UUID
    user_id: UUID
    role: MemberRole
    color: str
    allowed_room_ids: list[UUID] = Field(default_factory=list)
    user: Optional[UserOut] = None

    model_config = {"from_attributes": True}

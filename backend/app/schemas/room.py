from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = "🏠"
    color: str = "#8DB596"


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class RoomOut(BaseModel):
    id: UUID
    house_id: UUID
    name: str
    icon: str
    color: str

    model_config = {"from_attributes": True}

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class HouseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class HouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class HouseOut(BaseModel):
    id: UUID
    name: str
    invite_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JoinHousePayload(BaseModel):
    invite_code: str = Field(..., min_length=8, max_length=8)

from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class AdviceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., max_length=2000)
    steps: list[str] = []
    room_names: list[str] = []
    task_keywords: list[str] = []
    season: Optional[str] = None       # null | "spring" | "summer" | "autumn" | "winter"
    category: str = "regular"          # "regular" | "deep" | "prevention" | "storage" | "nonobvious"


class AdviceUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    steps: Optional[list[str]] = None
    room_names: Optional[list[str]] = None
    task_keywords: Optional[list[str]] = None
    season: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class AdviceOut(BaseModel):
    id: UUID
    title: str
    content: str
    steps: list[str]
    room_names: list[str]
    task_keywords: list[str]
    season: Optional[str]
    category: str
    is_active: bool

    model_config = {"from_attributes": True}

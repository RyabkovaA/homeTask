from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

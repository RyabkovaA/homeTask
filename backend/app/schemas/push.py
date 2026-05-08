from pydantic import BaseModel, Field
from typing import Optional


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeIn(BaseModel):
    endpoint: str = Field(..., max_length=2048)
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = Field(None, max_length=512)


class PushSubscriptionOut(BaseModel):
    subscribed: bool
    message: str


class VapidPublicKeyOut(BaseModel):
    public_key: str

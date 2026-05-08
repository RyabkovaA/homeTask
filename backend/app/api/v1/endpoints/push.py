from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.models.member import HouseMember
from app.schemas.push import PushSubscribeIn, PushSubscriptionOut, VapidPublicKeyOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.get("/push/vapid-public-key", response_model=VapidPublicKeyOut)
async def get_vapid_public_key(
    current_member: HouseMember = Depends(get_current_member),
):
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(503, "Push notifications are not configured on this server")
    return VapidPublicKeyOut(public_key=settings.VAPID_PUBLIC_KEY)


@router.post("/push/subscribe", response_model=PushSubscriptionOut, status_code=200)
async def subscribe_push(
    payload: PushSubscribeIn,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        raise HTTPException(503, "Push notifications are not configured on this server")

    # Upsert: update if endpoint already exists for this member
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.member_id == current_member.id,
            PushSubscription.endpoint == payload.endpoint,
        )
    )
    sub = result.scalar_one_or_none()

    if sub:
        sub.p256dh = payload.keys.p256dh
        sub.auth = payload.keys.auth
        sub.user_agent = payload.user_agent
        sub.is_active = True
        msg = "Подписка обновлена"
    else:
        sub = PushSubscription(
            member_id=current_member.id,
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            user_agent=payload.user_agent,
            is_active=True,
        )
        db.add(sub)
        msg = "Подписка оформлена"

    await db.commit()
    return PushSubscriptionOut(subscribed=True, message=msg)


@router.delete("/push/unsubscribe", response_model=PushSubscriptionOut)
async def unsubscribe_push(
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.member_id == current_member.id,
            PushSubscription.is_active == True,
        )
    )
    subs = result.scalars().all()
    for sub in subs:
        sub.is_active = False
    await db.commit()
    return PushSubscriptionOut(subscribed=False, message=f"Отписано {len(subs)} устройств")

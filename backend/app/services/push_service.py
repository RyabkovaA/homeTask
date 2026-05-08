from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

try:
    from pywebpush import webpush, WebPushException  # type: ignore[import]
    _PUSH_AVAILABLE = True
except ImportError:
    _PUSH_AVAILABLE = False


def _get_private_pem() -> Optional[str]:
    if not settings.VAPID_PRIVATE_KEY:
        return None
    try:
        return base64.b64decode(settings.VAPID_PRIVATE_KEY).decode()
    except Exception:
        return None


def _send_sync(
    endpoint: str,
    p256dh: str,
    auth: str,
    payload: dict,
    private_pem: str,
    claim_email: str,
) -> Optional[bool]:
    """Synchronous push — called from asyncio.to_thread().

    Returns:
        True  — delivered successfully
        None  — subscription expired (HTTP 404/410); caller must deactivate
        False — temporary failure (network, rate-limit, etc.); keep subscription
    """
    sub_info = {
        "endpoint": endpoint,
        "keys": {"p256dh": p256dh, "auth": auth},
    }
    try:
        webpush(
            subscription_info=sub_info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=private_pem,
            vapid_claims={"sub": f"mailto:{claim_email}"},
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            return None  # expired subscription — must deactivate
        logger.warning("Push failed for endpoint %s: %s", endpoint[:60], exc)
        return False
    except Exception as exc:
        logger.warning("Push error: %s", exc)
        return False


async def send_push_notification(
    db: AsyncSession,
    member_id: UUID,
    payload: dict,
) -> int:
    """
    Send push notification to all active subscriptions of a member.
    Returns count of successfully delivered messages.
    """
    if not _PUSH_AVAILABLE:
        return 0

    private_pem = _get_private_pem()
    if not private_pem:
        return 0

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.member_id == member_id,
            PushSubscription.is_active == True,
        )
    )
    subscriptions = result.scalars().all()
    if not subscriptions:
        return 0

    sent = 0
    expired_any = False
    for sub in subscriptions:
        result = await asyncio.to_thread(
            _send_sync,
            sub.endpoint,
            sub.p256dh,
            sub.auth,
            payload,
            private_pem,
            settings.VAPID_CLAIM_EMAIL,
        )
        if result is True:
            sent += 1
        elif result is None:
            # Subscription expired (HTTP 404/410) — deactivate to stop retrying
            sub.is_active = False
            expired_any = True
        # result is False → temporary failure; keep subscription active

    if expired_any:
        await db.commit()

    return sent


async def notify_task_assigned(member_id: UUID, task_title: str) -> None:
    """Background task: notify a member that a task was assigned to them."""
    async with AsyncSessionLocal() as db:
        await send_push_notification(
            db,
            member_id,
            {
                "title": "HomeTask — новое назначение",
                "body": f"Вам назначена задача: {task_title}",
                "data": {"url": "/tasks"},
            },
        )

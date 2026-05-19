"""
Daily push-notification scheduler (APScheduler).

Jobs:
  - send_daily_reminders():  runs every day at 09:00 server time.
    For each active task with an assignee that is due today or overdue (unpaid),
    sends a push notification to the assignee — unless a terminal event
    (done/skipped/moved) already exists for that occurrence.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.services.recurrence_service import get_occurrences, is_due_today
from app.services.push_service import send_push_notification

logger = logging.getLogger(__name__)

_TERMINAL = {EventStatus.done, EventStatus.skipped}


async def _get_existing_events(
    db: AsyncSession,
    task_id,
    from_date: date,
    to_date: date,
) -> dict[date, EventStatus]:
    """Return {occurrence_date: status} for a task in the given date range."""
    result = await db.execute(
        select(TaskEvent.occurrence_date, TaskEvent.status).where(
            TaskEvent.task_id == task_id,
            TaskEvent.occurrence_date >= from_date,
            TaskEvent.occurrence_date <= to_date,
        )
    )
    return {row.occurrence_date: row.status for row in result}


async def send_daily_reminders() -> None:
    """
    Scheduled job: notify assignees about due-today and overdue tasks.
    Runs daily; skips occurrences that already have a terminal event.
    """
    today = date.today()
    overdue_window_start = today - timedelta(days=7)  # look back up to 7 days

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).where(Task.is_active == True, Task.assignee_id != None)  # noqa: E711
        )
        tasks = result.scalars().all()

        for task in tasks:
            try:
                await _process_task(db, task, today, overdue_window_start)
            except Exception:
                logger.exception("Notification error for task %s", task.id)


async def _process_task(
    db: AsyncSession,
    task: Task,
    today: date,
    overdue_from: date,
) -> None:
    # Collect all occurrence dates in the window [overdue_from, today]
    dates = get_occurrences(task, overdue_from, today)
    if not dates:
        return

    events = await _get_existing_events(db, task.id, overdue_from, today)

    notified = False
    for occ_date in dates:
        existing_status = events.get(occ_date)
        if existing_status in _TERMINAL:
            continue  # already handled — skip

        is_today = occ_date == today
        is_overdue = occ_date < today

        if is_today:
            if task.priority == "high":
                title = "HomeTask — важная задача на сегодня ⚡"
            else:
                title = "HomeTask — задача на сегодня"
            body = f"Напоминание: {task.title}"
        elif is_overdue:
            days_late = (today - occ_date).days
            title = "HomeTask — просроченная задача"
            body = f"Просрочено на {days_late} д.: {task.title}"
        else:
            continue

        await send_push_notification(
            db,
            task.assignee_id,
            {"title": title, "body": body, "data": {"url": "/tasks"}},
        )
        notified = True
        break  # one notification per task per run is enough

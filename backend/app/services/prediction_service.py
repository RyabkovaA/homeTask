"""
Completion Probability & Smart Nudge service.

Estimates the probability that a task occurrence will be completed using
a weighted combination of historical signals (pure Python, no ML deps):

  P(complete | task, member, day) =
    w1 * task_rate        — this task's personal completion rate
    w2 * member_rate      — member's general completion rate
    w3 * weekday_rate     — member's completion rate on this weekday
    w4 * room_rate        — room-level adherence

Nudge: identifies whether the current moment is a good time to remind
based on the member's best-performing time window and due tasks count.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.models.member import HouseMember
from app.services.recurrence_service import build_occurrences, OccurrenceStatus


# Feature weights (must sum to 1.0)
_W_TASK = 0.40
_W_MEMBER = 0.25
_W_WEEKDAY = 0.20
_W_ROOM = 0.15


async def get_completion_probability(
    db: AsyncSession,
    task: Task,
    member: HouseMember,
    target_date: date | None = None,
) -> dict:
    """
    Return completion probability [0..1] for the task on target_date (default: today).

    Returns:
        probability: float [0..1]
        confidence: "high" | "medium" | "low"  — based on how much history exists
        signals: dict with individual feature values
        reason: human-readable Russian explanation
    """
    if target_date is None:
        target_date = date.today()

    from_date = target_date - timedelta(days=90)
    today = date.today()

    # Load all task events for this house
    house_task_ids_q = await db.execute(
        select(Task.id).where(Task.house_id == task.house_id, Task.is_active == True)
    )
    all_task_ids = [row[0] for row in house_task_ids_q.all()]

    events_q = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id.in_(all_task_ids),
                TaskEvent.occurrence_date >= from_date,
                TaskEvent.occurrence_date <= today,
            )
        )
    )
    events: list[TaskEvent] = events_q.scalars().all()

    # ----- task-specific rate (this task, any member) -----
    task_events = [e for e in events if e.task_id == task.id]
    task_done = sum(1 for e in task_events if e.status == EventStatus.done)
    task_total = len(task_events)
    task_rate = (task_done / task_total) if task_total >= 2 else 0.65  # prior

    # ----- member global rate -----
    member_events = [e for e in events if e.actor_id == member.id]
    member_done = sum(1 for e in member_events if e.status == EventStatus.done)
    member_total = len(member_events)
    member_rate = (member_done / member_total) if member_total >= 5 else 0.60  # prior

    # ----- weekday rate for this member -----
    target_dow = target_date.weekday()
    dow_events = [
        e for e in member_events
        if e.occurrence_date.weekday() == target_dow
    ]
    dow_done = sum(1 for e in dow_events if e.status == EventStatus.done)
    dow_total = len(dow_events)
    weekday_rate = (dow_done / dow_total) if dow_total >= 3 else member_rate

    # ----- room rate -----
    if task.room_id:
        house_tasks_with_room_q = await db.execute(
            select(Task.id).where(
                and_(Task.house_id == task.house_id, Task.room_id == task.room_id, Task.is_active == True)
            )
        )
        room_task_ids = {row[0] for row in house_tasks_with_room_q.all()}
        room_events = [e for e in events if e.task_id in room_task_ids]
        room_done = sum(1 for e in room_events if e.status == EventStatus.done)
        room_total = len(room_events)
        room_rate = (room_done / room_total) if room_total >= 3 else member_rate
    else:
        room_rate = member_rate

    probability = (
        _W_TASK * task_rate
        + _W_MEMBER * member_rate
        + _W_WEEKDAY * weekday_rate
        + _W_ROOM * room_rate
    )
    probability = round(max(0.05, min(0.98, probability)), 2)

    # Confidence based on total data points
    total_data = task_total + member_total
    if total_data >= 20:
        confidence = "high"
    elif total_data >= 8:
        confidence = "medium"
    else:
        confidence = "low"

    # Human-readable reason
    if probability >= 0.75:
        reason = f"Высокая вероятность: задача выполняется стабильно ({int(task_rate*100)}% личная история)."
    elif probability >= 0.50:
        reason = f"Средняя вероятность: соблюдение в этот день недели составляет {int(weekday_rate*100)}%."
    else:
        reason = f"Низкая вероятность: задача часто пропускается. Личная история выполнения: {int(task_rate*100)}%."

    return {
        "probability": probability,
        "confidence": confidence,
        "signals": {
            "task_rate": round(task_rate, 2),
            "member_rate": round(member_rate, 2),
            "weekday_rate": round(weekday_rate, 2),
            "room_rate": round(room_rate, 2),
        },
        "reason": reason,
    }


async def get_nudge(
    db: AsyncSession,
    house_id: uuid.UUID,
    member: HouseMember,
) -> dict:
    """
    Smart nudge: should the user be reminded to do tasks right now?

    Logic:
    1. Count today's due (not-yet-done) tasks for this member
    2. Find the member's best-performing weekday + hour window from history
    3. Return a nudge if tasks are due AND current conditions are favorable

    Returns:
        should_nudge: bool
        due_count: int
        message: str (Russian motivational message)
        best_weekdays: list[str] — member's historically strong days
    """
    today = date.today()
    from_date = today - timedelta(days=60)

    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks: list[Task] = tasks_q.scalars().all()

    events_q = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id.in_([t.id for t in tasks]),
                TaskEvent.occurrence_date >= from_date,
                TaskEvent.occurrence_date <= today,
            )
        )
    )
    events: list[TaskEvent] = events_q.scalars().all()

    # Count due tasks today (for any assignee or unassigned)
    today_events_map = {
        str(e.task_id): e for e in events
        if str(e.occurrence_date) == str(today)
    }

    due_today = 0
    for t in tasks:
        if t.assignee_id and t.assignee_id != member.id:
            continue  # skip tasks assigned to others
        occ = build_occurrences(t, [e for e in events if e.task_id == t.id], today, today, now=today)
        if occ and occ[0].status in (OccurrenceStatus.pending, OccurrenceStatus.overdue):
            due_today += 1

    # Best weekdays from member history
    _WEEKDAY_RU = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    dow_stats: dict[int, dict] = {i: {"done": 0, "total": 0} for i in range(7)}
    for e in events:
        if e.actor_id != member.id:
            continue
        dow = e.occurrence_date.weekday()
        dow_stats[dow]["total"] += 1
        if e.status == EventStatus.done:
            dow_stats[dow]["done"] += 1

    best_dows = sorted(
        [d for d in range(7) if dow_stats[d]["total"] >= 2],
        key=lambda d: dow_stats[d]["done"] / dow_stats[d]["total"],
        reverse=True,
    )[:3]
    best_weekdays = [_WEEKDAY_RU[d] for d in best_dows]

    today_dow = today.weekday()
    is_good_day = today_dow in best_dows

    # Build nudge
    should_nudge = due_today > 0
    if due_today == 0:
        message = "Все задачи на сегодня выполнены. Отличная работа!"
    elif due_today == 1:
        message = "У вас 1 невыполненная задача на сегодня."
    else:
        message = f"У вас {due_today} невыполненных задач на сегодня."

    if should_nudge and is_good_day:
        message += " Сегодня ваш продуктивный день — отличное время их сделать!"
    elif should_nudge and best_weekdays:
        message += f" Ваши самые продуктивные дни: {', '.join(best_weekdays)}."

    return {
        "should_nudge": should_nudge,
        "due_count": due_today,
        "message": message,
        "best_weekdays": best_weekdays,
        "is_productive_day": is_good_day,
    }

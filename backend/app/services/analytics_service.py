"""
Analytics service — user behaviour analysis.

Uses the BuildOccurrences algorithm (recurrence_service) to resolve
occurrence statuses according to each task's skip_policy and window_days,
then computes:
  - global adherence, streak, completion ratio, overdue rate
  - consistency score (stability of daily adherence)
  - per-day trend
  - load distribution by member
  - breakdown by room
"""
from __future__ import annotations

import math
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.models.member import HouseMember
from app.models.room import Room
from app.models.user import User
from app.services.recurrence_service import build_occurrences, OccurrenceStatus
from app.schemas.analytics import (
    MetricsOut, LoadDistributionItem, DailyPoint,
    RoomAnalyticsItem, AnalyticsOut,
)


async def get_analytics(
    db: AsyncSession,
    house_id: uuid.UUID,
    days: int = 30,
) -> AnalyticsOut:
    today = date.today()
    from_date = today - timedelta(days=days - 1)

    # ------------------------------------------------------------------ data
    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks: list[Task] = tasks_q.scalars().all()

    task_ids = [t.id for t in tasks]
    events_q = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id.in_(task_ids),
                TaskEvent.occurrence_date >= from_date,
                TaskEvent.occurrence_date <= today,
            )
        )
    )
    events: list[TaskEvent] = events_q.scalars().all()

    members_q = await db.execute(
        select(HouseMember, User)
        .join(User, HouseMember.user_id == User.id)
        .where(HouseMember.house_id == house_id)
    )
    members_with_users = members_q.all()

    rooms_q = await db.execute(
        select(Room).where(Room.house_id == house_id)
    )
    rooms: list[Room] = rooms_q.scalars().all()
    room_map = {r.id: r for r in rooms}

    # ----------------------------------------- BuildOccurrences for all tasks
    total_planned = 0
    total_done = 0
    total_overdue = 0
    daily: dict[date, dict[str, int]] = {}

    # room-level counters  {room_id_or_None: {"planned": 0, "done": 0, "overdue": 0}}
    room_counters: dict[str | None, dict[str, int]] = {}

    for task in tasks:
        task_events = [e for e in events if e.task_id == task.id]
        occurrences = build_occurrences(task, task_events, from_date, today, now=today)

        room_key = str(task.room_id) if task.room_id else None
        rc = room_counters.setdefault(room_key, {"planned": 0, "done": 0, "overdue": 0})

        for occ in occurrences:
            total_planned += 1
            rc["planned"] += 1

            d_data = daily.setdefault(occ.occurrence_date, {"done": 0, "total": 0})
            d_data["total"] += 1

            if occ.status == OccurrenceStatus.done:
                total_done += 1
                rc["done"] += 1
                d_data["done"] += 1
            elif occ.status in (OccurrenceStatus.overdue,):
                total_overdue += 1
                rc["overdue"] += 1

    # ---------------------------------------------------------------- metrics
    adherence = round(total_done / total_planned * 100, 1) if total_planned else 0.0
    completion = adherence
    overdue_rate = round(total_overdue / total_planned * 100, 1) if total_planned else 0.0

    # streak: consecutive days (ending yesterday) where at least one task was done
    streak = 0
    check = today - timedelta(days=1)
    while True:
        day_data = daily.get(check)
        if day_data and day_data["done"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # consistency score: 100 − coefficient of variation of daily adherence rates
    # A perfectly consistent routine (same rate every day) → score = 100
    rates: list[float] = []
    for i in range(days):
        dd = from_date + timedelta(days=i)
        d_data = daily.get(dd, {"done": 0, "total": 0})
        r = (d_data["done"] / d_data["total"] * 100) if d_data["total"] else 0.0
        rates.append(r)

    if len(rates) > 1:
        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        std_dev = math.sqrt(variance)
        # normalise: max possible std for [0,100] values is 50
        consistency_score = round(max(0.0, 100.0 - (std_dev / 50.0) * 100.0), 1)
    else:
        consistency_score = 100.0 if (rates and rates[0] > 0) else 0.0

    # ---------------------------------------------------------- daily trend
    daily_trend = []
    for i in range(days):
        dd = from_date + timedelta(days=i)
        d_data = daily.get(dd, {"done": 0, "total": 0})
        rate = round(d_data["done"] / d_data["total"] * 100, 1) if d_data["total"] else 0.0
        daily_trend.append(DailyPoint(
            date=str(dd),
            done=d_data["done"],
            total=d_data["total"],
            rate=rate,
        ))

    # ------------------------------------------------------- load distribution
    load_map: dict[str, int] = {}
    for event in events:
        if event.status == EventStatus.done:
            load_map[str(event.actor_id)] = load_map.get(str(event.actor_id), 0) + 1

    total_done_all = sum(load_map.values()) or 1
    load_distribution = []
    for member, user in members_with_users:
        count = load_map.get(str(member.id), 0)
        load_distribution.append(LoadDistributionItem(
            member_id=str(member.id),
            member_name=user.name,
            color=member.color,
            done_count=count,
            percentage=round(count / total_done_all * 100, 1),
        ))

    # ---------------------------------------------------------- room stats
    room_stats: list[RoomAnalyticsItem] = []
    for room_key, rc in room_counters.items():
        if room_key and uuid.UUID(room_key) in room_map:
            room = room_map[uuid.UUID(room_key)]
            r_name = room.name
            r_icon = room.icon
            r_id = room_key
        else:
            r_name = "Без комнаты"
            r_icon = "📋"
            r_id = None

        r_adherence = (
            round(rc["done"] / rc["planned"] * 100, 1) if rc["planned"] else 0.0
        )
        room_stats.append(RoomAnalyticsItem(
            room_id=r_id,
            room_name=r_name,
            room_icon=r_icon,
            total_planned=rc["planned"],
            total_done=rc["done"],
            total_overdue=rc["overdue"],
            adherence_rate=r_adherence,
        ))

    room_stats.sort(key=lambda x: x.adherence_rate, reverse=True)

    return AnalyticsOut(
        metrics=MetricsOut(
            adherence_rate=adherence,
            streak=streak,
            completion_ratio=completion,
            overdue_rate=overdue_rate,
            total_planned=total_planned,
            total_done=total_done,
            total_overdue=total_overdue,
            consistency_score=consistency_score,
        ),
        daily_trend=daily_trend,
        load_distribution=load_distribution,
        room_stats=room_stats,
    )

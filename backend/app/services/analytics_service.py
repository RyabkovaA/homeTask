from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.models.member import HouseMember
from app.models.user import User
from app.services.recurrence_service import get_occurrences
from app.schemas.analytics import MetricsOut, LoadDistributionItem, DailyPoint, AnalyticsOut
import uuid


async def get_analytics(
    db: AsyncSession,
    house_id: uuid.UUID,
    days: int = 30
) -> AnalyticsOut:
    today = date.today()
    from_date = today - timedelta(days=days - 1)

    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks = tasks_q.scalars().all()

    events_q = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id.in_([t.id for t in tasks]),
                TaskEvent.occurrence_date >= from_date,
                TaskEvent.occurrence_date <= today
            )
        )
    )
    events = events_q.scalars().all()
    events_by_key = {(str(e.task_id), str(e.occurrence_date)): e for e in events}

    total_planned = 0
    total_done = 0
    total_overdue = 0
    daily: dict[date, dict] = {}

    for task in tasks:
        occurrences = get_occurrences(task, from_date, today)
        for occ_date in occurrences:
            total_planned += 1
            event = events_by_key.get((str(task.id), str(occ_date)))
            d = daily.setdefault(occ_date, {"done": 0, "total": 0})
            d["total"] += 1
            if event and event.status == EventStatus.done:
                total_done += 1
                d["done"] += 1
            elif event and event.status == EventStatus.overdue:
                total_overdue += 1
            elif not event and occ_date < today:
                total_overdue += 1

    adherence = round(total_done / total_planned * 100, 1) if total_planned else 0
    completion = round(total_done / total_planned * 100, 1) if total_planned else 0
    overdue_rate = round(total_overdue / total_planned * 100, 1) if total_planned else 0

    streak = 0
    check = today - timedelta(days=1)
    while True:
        day_data = daily.get(check)
        if day_data and day_data["done"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    daily_trend = []
    for i in range(days):
        dd = from_date + timedelta(days=i)
        data = daily.get(dd, {"done": 0, "total": 0})
        rate = round(data["done"] / data["total"] * 100, 1) if data["total"] else 0
        daily_trend.append(DailyPoint(
            date=str(dd),
            done=data["done"],
            total=data["total"],
            rate=rate
        ))

    members_q = await db.execute(
        select(HouseMember, User)
        .join(User, HouseMember.user_id == User.id)
        .where(HouseMember.house_id == house_id)
    )
    members_with_users = members_q.all()

    load_map: dict[str, int] = {}
    for event in events:
        if event.status == EventStatus.done:
            key = str(event.actor_id)
            load_map[key] = load_map.get(key, 0) + 1

    total_done_all = sum(load_map.values()) or 1
    load_distribution = []
    for member, user in members_with_users:
        count = load_map.get(str(member.id), 0)
        load_distribution.append(LoadDistributionItem(
            member_id=str(member.id),
            member_name=user.name,
            color=member.color,
            done_count=count,
            percentage=round(count / total_done_all * 100, 1)
        ))

    return AnalyticsOut(
        metrics=MetricsOut(
            adherence_rate=adherence,
            streak=streak,
            completion_ratio=completion,
            overdue_rate=overdue_rate,
            total_planned=total_planned,
            total_done=total_done,
            total_overdue=total_overdue
        ),
        daily_trend=daily_trend,
        load_distribution=load_distribution
    )

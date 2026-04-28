"""
Habit analysis service — BPMN flow (thesis §2, Figure):

1. User requests report → extract events from journal, filter by house/member
2. Calculate metrics: adherence, streaks, completion/overdue share, load distribution
3. If low adherence detected → subprocess:
   - Identify problem areas (room, weekday, task)
   - Build context query
   - RAG retrieval from knowledge base
   - Generate recommendations for routine adjustment
   - Log fact of delivery (traceability)
4. Return insights + recommendations

Insight types:
  - "low_adherence_room"   — room with adherence < threshold
  - "worst_weekday"        — weekday with worst performance
  - "most_overdue_task"    — task with most overdue events
  - "declining_trend"      — adherence dropped vs prior period
  - "good_streak"          — positive reinforcement when doing well
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.models.member import HouseMember
from app.models.room import Room
from app.models.user import User
from app.services.recurrence_service import build_occurrences, OccurrenceStatus
from app.services.rag_service import rag_recommend_by_query


# ---------------------------------------------------------------------------
# Default thresholds — overridden by adaptive values per user below
# ---------------------------------------------------------------------------
DEFAULT_LOW_ADHERENCE_THRESHOLD = 0.55
DEFAULT_DECLINING_TREND_DROP = 15.0
DEFAULT_WORST_WEEKDAY_THRESHOLD = 0.45
POSITIVE_STREAK_THRESHOLD = 5        # streak >= 5 days is noteworthy


def _adaptive_thresholds(personal_baseline: float) -> dict:
    """
    Derive adaptive thresholds from the member's personal baseline completion rate.

    A member who consistently achieves 80% is held to a higher bar than one
    who is still building habits at 40%. This prevents false negatives for
    high performers and false positives for beginners.
    """
    low_adherence = max(0.25, personal_baseline - 0.20)
    worst_weekday = max(0.15, personal_baseline - 0.25)
    declining_drop = max(8.0, personal_baseline * 100 * 0.25)  # 25% relative drop
    return {
        "low_adherence": low_adherence,
        "worst_weekday": worst_weekday,
        "declining_drop": declining_drop,
    }


_WEEKDAY_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


@dataclass
class HabitInsight:
    type: str
    severity: str          # "info" | "warning" | "critical"
    title: str
    description: str
    metric: float
    advice: Optional[dict] = None   # RagAdvice dict when available


async def get_habit_insights(
    db: AsyncSession,
    house_id: uuid.UUID,
    member: HouseMember,
    days: int = 30,
) -> dict:
    """
    Main entry point for habit analysis.

    Returns:
      adherence_summary: str
      overall_status: "good" | "attention" | "critical"
      insights: list[HabitInsight]
    """
    today = date.today()
    from_date = today - timedelta(days=days - 1)
    mid_date = today - timedelta(days=days // 2)   # split period for trend

    # ------------------------------------------------------------------ data
    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks: list[Task] = tasks_q.scalars().all()
    task_map = {t.id: t for t in tasks}

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

    # Compute personal baseline from last 90 days (broader window than analysis period)
    baseline_from = today - timedelta(days=90)
    baseline_events_q = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id.in_([t.id for t in tasks]),
                TaskEvent.actor_id == member.id,
                TaskEvent.occurrence_date >= baseline_from,
                TaskEvent.occurrence_date <= today,
            )
        )
    )
    baseline_events: list[TaskEvent] = baseline_events_q.scalars().all()
    baseline_done = sum(1 for e in baseline_events if e.status == EventStatus.done)
    baseline_total = len(baseline_events)
    personal_baseline = (baseline_done / baseline_total) if baseline_total >= 5 else DEFAULT_LOW_ADHERENCE_THRESHOLD
    thresholds = _adaptive_thresholds(personal_baseline)

    rooms_q = await db.execute(select(Room).where(Room.house_id == house_id))
    rooms: list[Room] = rooms_q.scalars().all()
    room_map = {r.id: r for r in rooms}

    # -------- BuildOccurrences for all tasks (apply policies + window) -----
    # room_stats: {room_id_or_None: {"planned": 0, "done": 0, "overdue": 0}}
    room_stats: dict[Optional[uuid.UUID], dict] = defaultdict(lambda: {"planned": 0, "done": 0, "overdue": 0})
    task_stats: dict[uuid.UUID, dict] = defaultdict(lambda: {"planned": 0, "done": 0, "overdue": 0, "title": ""})
    weekday_stats: dict[int, dict] = {i: {"planned": 0, "done": 0} for i in range(7)}
    period1_done, period1_planned = 0, 0    # first half
    period2_done, period2_planned = 0, 0    # second half (more recent)

    for task in tasks:
        task_events = [e for e in events if e.task_id == task.id]
        occurrences = build_occurrences(task, task_events, from_date, today, now=today)
        task_stats[task.id]["title"] = task.title
        room_key = task.room_id  # may be None

        for occ in occurrences:
            d = occ.occurrence_date
            room_stats[room_key]["planned"] += 1
            task_stats[task.id]["planned"] += 1
            weekday_stats[d.weekday()]["planned"] += 1

            is_done = occ.status == OccurrenceStatus.done
            is_overdue = occ.status == OccurrenceStatus.overdue

            if is_done:
                room_stats[room_key]["done"] += 1
                task_stats[task.id]["done"] += 1
                weekday_stats[d.weekday()]["done"] += 1
            if is_overdue:
                room_stats[room_key]["overdue"] += 1
                task_stats[task.id]["overdue"] += 1

            if d < mid_date:
                period1_planned += 1
                if is_done:
                    period1_done += 1
            else:
                period2_planned += 1
                if is_done:
                    period2_done += 1

    # ---------------------------------------------------------------- global
    total_planned = sum(s["planned"] for s in room_stats.values())
    total_done = sum(s["done"] for s in room_stats.values())
    global_adherence = total_done / total_planned * 100 if total_planned else 0.0

    adherence1 = period1_done / period1_planned * 100 if period1_planned else 0.0
    adherence2 = period2_done / period2_planned * 100 if period2_planned else 0.0
    trend_delta = adherence2 - adherence1  # positive = improving

    # ---------------------------------------------------------------- streak
    event_map = {(str(e.task_id), str(e.occurrence_date)): e for e in events}
    streak = 0
    check = today - timedelta(days=1)
    while True:
        day_done = any(
            event_map.get((str(t.id), str(check))) and
            event_map[(str(t.id), str(check))].status == EventStatus.done
            for t in tasks
        )
        if day_done:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # ------------------------------------------------------------- insights
    insights: list[HabitInsight] = []

    # --- 1. Positive streak ---
    if streak >= POSITIVE_STREAK_THRESHOLD:
        insights.append(HabitInsight(
            type="good_streak",
            severity="info",
            title=f"Отличная серия — {streak} дней подряд!",
            description=(
                f"Вы выполняли задачи {streak} дней подряд. "
                "Продолжайте поддерживать этот ритм — стабильность в бытовых задачах формирует полезные привычки."
            ),
            metric=float(streak),
        ))

    # --- 2. Declining trend ---
    if period1_planned > 0 and period2_planned > 0 and trend_delta < -thresholds["declining_drop"]:
        q = f"мотивация регулярность рутина снижение активности {' '.join(t.title for t in tasks[:3])}"
        rag = await rag_recommend_by_query(db, member, q, context_type="analytics")
        insights.append(HabitInsight(
            type="declining_trend",
            severity="warning",
            title=f"Соблюдение снизилось на {abs(trend_delta):.0f}%",
            description=(
                f"За первую половину периода соблюдение составляло {adherence1:.0f}%, "
                f"за вторую — {adherence2:.0f}%. "
                "Возможные причины: смена расписания, накопленная усталость, завышенная частота задач."
            ),
            metric=trend_delta,
            advice=rag,
        ))

    # --- 3. Low adherence by room ---
    for room_id, stats in room_stats.items():
        if stats["planned"] < 3:
            continue
        room_adherence = stats["done"] / stats["planned"]
        if room_adherence < thresholds["low_adherence"]:
            room = room_map.get(room_id)
            room_name = room.name if room else "Без комнаты"
            room_icon = room.icon if room else "📋"
            severity = "critical" if room_adherence < 0.3 else "warning"
            q = f"уборка {room_name} советы регулярность как поддерживать чистоту {room_name}"
            rag = await rag_recommend_by_query(db, member, q, context_type="analytics")
            insights.append(HabitInsight(
                type="low_adherence_room",
                severity=severity,
                title=f"{room_icon} {room_name}: соблюдение {room_adherence*100:.0f}%",
                description=(
                    f"В помещении «{room_name}» выполняется лишь {room_adherence*100:.0f}% запланированных задач "
                    f"({stats['done']} из {stats['planned']}). "
                    f"Просрочено: {stats['overdue']}."
                ),
                metric=round(room_adherence * 100, 1),
                advice=rag,
            ))

    # --- 4. Most overdue task ---
    if task_stats:
        worst_task_id = max(task_stats.keys(), key=lambda k: task_stats[k]["overdue"])
        wt = task_stats[worst_task_id]
        if wt["overdue"] >= 3:
            task_obj = task_map.get(worst_task_id)
            room_name = None
            if task_obj and task_obj.room_id:
                room = room_map.get(task_obj.room_id)
                room_name = room.name if room else None
            q = f"{wt['title']} {room_name or ''} советы выполнение"
            rag = await rag_recommend_by_query(db, member, q, context_type="analytics")
            insights.append(HabitInsight(
                type="most_overdue_task",
                severity="warning",
                title=f"Часто просрочивается: «{wt['title']}»",
                description=(
                    f"Задача «{wt['title']}» имеет {wt['overdue']} просрочки за {days} дней. "
                    "Рассмотрите изменение частоты, назначение другого ответственного или установку окна выполнения."
                ),
                metric=float(wt["overdue"]),
                advice=rag,
            ))

    # --- 5. Worst weekday ---
    worst_dow = None
    worst_dow_rate = 1.0
    for dow, stats in weekday_stats.items():
        if stats["planned"] >= 3:
            rate = stats["done"] / stats["planned"]
            if rate < worst_dow_rate:
                worst_dow_rate = rate
                worst_dow = dow

    if worst_dow is not None and worst_dow_rate < thresholds["worst_weekday"]:
        day_name = _WEEKDAY_RU[worst_dow]
        q = f"планирование {day_name} нагрузка расписание советы распределение задач"
        rag = await rag_recommend_by_query(db, member, q, context_type="analytics")
        insights.append(HabitInsight(
            type="worst_weekday",
            severity="info",
            title=f"{day_name}: слабый день ({worst_dow_rate*100:.0f}%)",
            description=(
                f"В {day_name.lower()} выполняется лишь {worst_dow_rate*100:.0f}% задач. "
                "Возможно, в этот день слишком высокая нагрузка или задачи не соответствуют доступному времени."
            ),
            metric=round(worst_dow_rate * 100, 1),
            advice=rag,
        ))

    # --- 6. General low adherence (no room-specific insight triggered) ---
    if global_adherence < 50 and not any(i.type == "low_adherence_room" for i in insights):
        q = f"регулярность привычки мотивация уборка дом советы рутина"
        rag = await rag_recommend_by_query(db, member, q, context_type="analytics")
        insights.append(HabitInsight(
            type="low_overall_adherence",
            severity="critical",
            title=f"Общее соблюдение низкое: {global_adherence:.0f}%",
            description=(
                f"За {days} дней выполнено лишь {total_done} из {total_planned} запланированных задач. "
                "Рекомендуется пересмотреть объём задач и реалистичность расписания."
            ),
            metric=round(global_adherence, 1),
            advice=rag,
        ))

    await db.commit()

    # Sort: critical → warning → info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: severity_order.get(x.severity, 3))

    # Summary text
    if global_adherence >= 80:
        summary = f"Отличный результат! Соблюдение за {days} дней: {global_adherence:.0f}%."
        overall_status = "good"
    elif global_adherence >= 55:
        summary = f"Хороший результат. Соблюдение: {global_adherence:.0f}%. Есть зоны для улучшения."
        overall_status = "attention"
    else:
        summary = f"Соблюдение низкое: {global_adherence:.0f}%. Рекомендуется скорректировать расписание."
        overall_status = "critical"

    if trend_delta > 5:
        summary += f" Тренд положительный (+{trend_delta:.0f}% vs прошлый период)."
    elif trend_delta < -5:
        summary += f" Тренд снижающийся ({trend_delta:.0f}% vs прошлый период)."

    return {
        "adherence_summary": summary,
        "overall_status": overall_status,
        "global_adherence": round(global_adherence, 1),
        "streak": streak,
        "total_planned": total_planned,
        "total_done": total_done,
        "personal_baseline": round(personal_baseline * 100, 1),
        "insights": [
            {
                "type": i.type,
                "severity": i.severity,
                "title": i.title,
                "description": i.description,
                "metric": i.metric,
                "advice": i.advice,
            }
            for i in insights
        ],
    }

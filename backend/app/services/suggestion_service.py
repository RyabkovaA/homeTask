"""
Task Suggestion service — auto-proposes new tasks based on:
  1. Current season (month-based)
  2. Rooms in the house
  3. Recently overdue/low-adherence tasks (gaps)
  4. LLM generation if configured, otherwise seasonal rule-base

Returns a list of SuggestedTask dicts:
  {title, room_name, frequency, effort_hours, reason}
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task
from app.models.task_event import TaskEvent, EventStatus
from app.models.room import Room
from app.models.member import HouseMember


# ---------------------------------------------------------------------------
# Seasonal rule base — fallback when no LLM configured
# ---------------------------------------------------------------------------

_SEASONAL_TASKS: dict[str, list[dict]] = {
    "winter": [
        {"title": "Проверить отопление", "effort_hours": 0.5, "frequency": "monthly",
         "reason": "Зима — важно убедиться в исправности системы отопления"},
        {"title": "Очистить входную зону от снега", "effort_hours": 0.3, "frequency": "weekly",
         "reason": "Снегопады требуют регулярной уборки входа"},
        {"title": "Проверить окна на сквозняки", "effort_hours": 0.5, "frequency": "monthly",
         "reason": "Зимой важно теплоизоляция окон"},
        {"title": "Генеральная уборка кухни", "effort_hours": 1.5, "frequency": "monthly",
         "reason": "Традиционная зимняя генеральная уборка"},
    ],
    "spring": [
        {"title": "Генеральная уборка после зимы", "effort_hours": 2.0, "frequency": "once",
         "reason": "Весенняя генеральная уборка — ежегодная традиция"},
        {"title": "Помыть окна", "effort_hours": 1.0, "frequency": "once",
         "reason": "Весна — лучшее время для мытья окон"},
        {"title": "Проверить вентиляцию", "effort_hours": 0.5, "frequency": "monthly",
         "reason": "Весной важно обеспечить свежий воздух"},
        {"title": "Разобрать зимние вещи", "effort_hours": 1.0, "frequency": "once",
         "reason": "Сезонная смена гардероба и хранения"},
    ],
    "summer": [
        {"title": "Протереть пыль с вентиляторов", "effort_hours": 0.3, "frequency": "monthly",
         "reason": "Летом вентиляторы работают интенсивно — требуют чистки"},
        {"title": "Почистить холодильник", "effort_hours": 0.5, "frequency": "monthly",
         "reason": "Летняя жара повышает нагрузку на холодильник"},
        {"title": "Уборка балкона/террасы", "effort_hours": 0.5, "frequency": "weekly",
         "reason": "Летом балкон используется чаще"},
        {"title": "Проверить средства от насекомых", "effort_hours": 0.2, "frequency": "monthly",
         "reason": "Сезон активности насекомых"},
    ],
    "autumn": [
        {"title": "Подготовить квартиру к зиме", "effort_hours": 1.5, "frequency": "once",
         "reason": "Осенняя подготовка — утеплить окна, проверить отопление"},
        {"title": "Почистить батареи перед отопительным сезоном", "effort_hours": 0.5, "frequency": "once",
         "reason": "Чистые батареи — эффективный обогрев"},
        {"title": "Разобрать летние вещи", "effort_hours": 1.0, "frequency": "once",
         "reason": "Сезонная смена гардероба"},
        {"title": "Проверить пожарные датчики", "effort_hours": 0.2, "frequency": "monthly",
         "reason": "Осенью начинается отопительный сезон — важна пожарная безопасность"},
    ],
}

_MONTH_TO_SEASON = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}

_GENERAL_TASKS = [
    {"title": "Пылесосить", "effort_hours": 0.4, "frequency": "weekly",
     "reason": "Регулярная уборка поддерживает чистоту"},
    {"title": "Помыть посуду", "effort_hours": 0.2, "frequency": "daily",
     "reason": "Ежедневная необходимость"},
    {"title": "Протереть сантехнику", "effort_hours": 0.3, "frequency": "weekly",
     "reason": "Гигиена ванной комнаты"},
]


def _get_season() -> str:
    return _MONTH_TO_SEASON[date.today().month]


async def suggest_tasks(
    db: AsyncSession,
    house_id: uuid.UUID,
    member: HouseMember,
    max_suggestions: int = 6,
) -> list[dict]:
    """
    Generate task suggestions for the house.

    Priority order:
    1. Gap tasks — tasks that have been consistently overdue (from history)
    2. Seasonal recommendations
    3. LLM-generated suggestions (if provider configured)

    Returns list of:
      {title, room_name, frequency, effort_hours, reason, source}
      source: "gap" | "seasonal" | "llm"
    """
    today = date.today()
    from_date = today - timedelta(days=30)

    # Load data
    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks: list[Task] = tasks_q.scalars().all()
    existing_titles = {t.title.lower() for t in tasks}

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

    rooms_q = await db.execute(select(Room).where(Room.house_id == house_id))
    rooms: list[Room] = rooms_q.scalars().all()
    room_map = {r.id: r for r in rooms}

    suggestions: list[dict] = []

    # --- 1. Gap tasks: tasks with >50% overdue rate in last 30 days ---
    task_stats: dict[uuid.UUID, dict] = defaultdict(lambda: {"done": 0, "overdue": 0, "total": 0, "title": ""})
    for e in events:
        s = task_stats[e.task_id]
        s["total"] += 1
        if e.status == EventStatus.done:
            s["done"] += 1
        elif e.status == EventStatus.overdue:
            s["overdue"] += 1

    for task in tasks:
        stats = task_stats[task.id]
        if stats["total"] >= 3:
            overdue_rate = stats["overdue"] / stats["total"]
            if overdue_rate > 0.5:
                room = room_map.get(task.room_id) if task.room_id else None
                suggestions.append({
                    "title": f"{task.title} (пересмотр частоты)",
                    "room_name": room.name if room else None,
                    "frequency": task.frequency,
                    "effort_hours": task.effort_hours,
                    "reason": (
                        f"Задача «{task.title}» просрочивается в {int(overdue_rate*100)}% случаев. "
                        "Рекомендуется снизить частоту или назначить другого исполнителя."
                    ),
                    "source": "gap",
                    "is_reschedule": True,
                })

    # --- 2. Seasonal suggestions ---
    season = _get_season()
    seasonal = _SEASONAL_TASKS.get(season, [])
    room_names = [r.name.lower() for r in rooms]

    for item in seasonal:
        if item["title"].lower() not in existing_titles:
            # Match to a room if possible
            matched_room = None
            for r in rooms:
                keywords = ["кухн", "ванн", "балкон", "прихожа", "спальн", "гостин"]
                for kw in keywords:
                    if kw in r.name.lower() and kw in item["title"].lower():
                        matched_room = r.name
                        break
            suggestions.append({
                "title": item["title"],
                "room_name": matched_room,
                "frequency": item["frequency"],
                "effort_hours": item["effort_hours"],
                "reason": item["reason"],
                "source": "seasonal",
                "is_reschedule": False,
            })

    # --- 3. LLM suggestions (if configured) ---
    try:
        from app.core.config import settings
        from app.services.llm_service import llm_generate
        if settings.LLM_PROVIDER != "none":
            room_list = ", ".join(r.name for r in rooms) if rooms else "без комнат"
            existing_list = ", ".join(t.title for t in tasks[:10]) if tasks else "нет задач"
            season_ru = {"winter": "зима", "spring": "весна", "summer": "лето", "autumn": "осень"}[season]
            prompt = (
                f"Ты помощник по управлению домашним хозяйством. "
                f"Сейчас {season_ru}. Комнаты в доме: {room_list}. "
                f"Уже существующие задачи: {existing_list}. "
                f"Предложи 3-4 новые домашние задачи, которых ещё нет. "
                f"Для каждой: название задачи | частота (daily/weekly/monthly/once) | трудоёмкость в часах (0.1-3.0) | причина. "
                f"Формат: ЗАДАЧА | ЧАСТОТА | ЧАСЫ | ПРИЧИНА. Одна задача на строку. Только список, без вступления."
            )
            llm_text = await llm_generate(prompt, max_tokens=400)
            if llm_text:
                for line in llm_text.strip().split("\n"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        try:
                            effort = float(parts[2].replace(",", "."))
                        except ValueError:
                            effort = 1.0
                        freq = parts[1].lower()
                        if freq not in ("daily", "weekly", "monthly", "once"):
                            freq = "weekly"
                        title = parts[0].strip("–-•* ")
                        if title and title.lower() not in existing_titles:
                            suggestions.append({
                                "title": title,
                                "room_name": None,
                                "frequency": freq,
                                "effort_hours": round(max(0.1, min(4.0, effort)), 1),
                                "reason": parts[3],
                                "source": "llm",
                                "is_reschedule": False,
                            })
    except Exception:
        pass  # LLM failure is non-fatal

    # Deduplicate by title and cap
    seen: set[str] = set()
    unique: list[dict] = []
    for s in suggestions:
        key = s["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique[:max_suggestions]

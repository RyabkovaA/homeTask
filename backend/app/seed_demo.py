"""
Demo seed — April 2026 history for video demonstration.

Usage:
    docker-compose exec backend python -m app.seed_demo

Creates:
  - Users: andrey@home.ru, maria@home.ru (password: password123)
  - House «Наш дом» with 5 rooms, 12 tasks
  - 30 event records for April 2026 with realistic pattern:
      Week 1 (Apr 1–7):   ~90% done    — good start
      Week 2 (Apr 8–14):  ~55% done    — "Andrey was away", visible dip in analytics
      Week 3 (Apr 15–21): ~85% done    — recovery
      Week 4 (Apr 22–30): ~95% done    — excellent streak

The script is IDEMPOTENT: drops existing andrey/maria accounts and their
house first, then recreates everything from scratch.
"""
from __future__ import annotations

import asyncio
import random
from datetime import date, timedelta

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.advice import Advice
from app.models.advice_delivery import AdviceDelivery
from app.models.house import House
from app.models.member import HouseMember, MemberRole
from app.models.room import Room
from app.models.task import Task, Frequency, SkipPolicy, Priority
from app.models.task_event import TaskEvent, EventStatus
from app.models.user import User
from app.services.recurrence_service import get_occurrences

# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

APRIL_START = date(2026, 4, 1)
APRIL_END   = date(2026, 4, 30)

ROOMS = [
    {"name": "Кухня",    "icon": "🍳",  "color": "#E8A87C"},
    {"name": "Гостиная", "icon": "🛋️", "color": "#8DB596"},
    {"name": "Спальня",  "icon": "🛏️", "color": "#B5A5D5"},
    {"name": "Ванная",   "icon": "🚿",  "color": "#7CB5C4"},
    {"name": "Балкон",   "icon": "🌿",  "color": "#90C67A"},
]

TASK_TEMPLATES = [
    # Кухня
    {"title": "Помыть посуду",        "room": "Кухня",    "freq": Frequency.daily,   "priority": Priority.high,   "owner": "andrey"},
    {"title": "Вынести мусор",         "room": "Кухня",    "freq": Frequency.daily,   "priority": Priority.high,   "owner": "andrey"},
    {"title": "Протереть плиту",       "room": "Кухня",    "freq": Frequency.weekly,  "priority": Priority.medium, "days": [2],      "owner": "maria"},   # среда
    {"title": "Почистить холодильник", "room": "Кухня",    "freq": Frequency.monthly, "priority": Priority.low,    "owner": "maria"},
    # Гостиная
    {"title": "Пропылесосить гостиную","room": "Гостиная", "freq": Frequency.weekly,  "priority": Priority.medium, "days": [0, 4],   "owner": "maria"},   # пн+пт
    {"title": "Протереть пыль",        "room": "Гостиная", "freq": Frequency.weekly,  "priority": Priority.low,    "days": [3],      "owner": "andrey"},  # чт
    {"title": "Помыть окна",           "room": "Гостиная", "freq": Frequency.monthly, "priority": Priority.low,    "owner": "andrey"},
    # Спальня
    {"title": "Сменить постельное бельё","room": "Спальня","freq": Frequency.monthly, "priority": Priority.medium, "owner": "maria"},
    # Ванная
    {"title": "Почистить унитаз",      "room": "Ванная",   "freq": Frequency.weekly,  "priority": Priority.high,   "days": [5],      "owner": "maria"},   # сб
    {"title": "Протереть зеркала",     "room": "Ванная",   "freq": Frequency.weekly,  "priority": Priority.low,    "days": [3],      "owner": "andrey"},  # чт
    # Балкон
    {"title": "Полить растения",       "room": "Балкон",   "freq": Frequency.custom,  "priority": Priority.medium, "interval": 3,    "owner": "maria"},
    {"title": "Разобрать балкон",      "room": "Балкон",   "freq": Frequency.once,    "priority": Priority.low,    "owner": "andrey"},
]

ADVICE_DATA = [
    {
        "title": "Эффективная уборка кухни",
        "content": "Чистая кухня — основа здорового дома. Регулярная уборка предотвращает накопление жира и бактерий.",
        "steps": [
            "Очистите поверхности от крошек и остатков еды",
            "Протрите плиту влажной тряпкой с обезжиривателем",
            "Вымойте раковину с содой",
            "Протрите фасады шкафов",
            "Помойте пол",
        ],
        "rooms": ["Кухня"],
        "keywords": ["кухня", "плита", "посуда", "холодильник"],
    },
    {
        "title": "Как правильно пылесосить",
        "content": "Правильная техника пылесошения удаляет до 99% пыли и аллергенов из ковров и мягкой мебели.",
        "steps": [
            "Уберите мелкие предметы с пола",
            "Двигайтесь систематично — полосами",
            "Пройдитесь каждую полосу дважды",
            "Не забудьте плинтусы и углы",
            "Очистите фильтр пылесоса",
        ],
        "rooms": ["Гостиная", "Спальня"],
        "keywords": ["пылесос", "ковёр", "пыль"],
    },
    {
        "title": "Уход за растениями",
        "content": "Регулярный полив и уход за растениями делают балкон живым и уютным пространством.",
        "steps": [
            "Проверьте влажность почвы пальцем на глубину 2 см",
            "Поливайте у корней, не на листья",
            "Используйте воду комнатной температуры",
            "Удалите засохшие листья и цветы",
            "Раз в месяц подкармливайте удобрением",
        ],
        "rooms": ["Балкон"],
        "keywords": ["растения", "полив", "цветы"],
    },
    {
        "title": "Чистота в ванной",
        "content": "Ванная требует еженедельной чистки для предотвращения плесени и известкового налёта.",
        "steps": [
            "Нанесите чистящее средство на унитаз, дайте постоять 5 минут",
            "Протрите раковину и смеситель",
            "Очистите душевую кабину от налёта",
            "Вымойте зеркало стеклоочистителем",
            "Вымойте пол с дезинфектором",
        ],
        "rooms": ["Ванная"],
        "keywords": ["ванная", "унитаз", "зеркало", "душ"],
    },
    {
        "title": "Порядок в спальне",
        "content": "Чистая спальня улучшает качество сна и снижает уровень стресса.",
        "steps": [
            "Застелите кровать сразу после подъёма",
            "Уберите вещи на свои места",
            "Протрите пыль с поверхностей",
            "Проветрите комнату 10–15 минут",
            "Смените постельное бельё раз в 1–2 недели",
        ],
        "rooms": ["Спальня"],
        "keywords": ["спальня", "бельё", "кровать"],
    },
    {
        "title": "Вынос мусора: правила сортировки",
        "content": "Правильная сортировка мусора снижает объём отходов и упрощает переработку.",
        "steps": [
            "Разделите пластик, бумагу и стекло",
            "Органические отходы — в отдельный пакет",
            "Проверьте наполненность мешков перед выносом",
            "Завяжите пакет и вынесите в контейнер",
        ],
        "rooms": ["Кухня"],
        "keywords": ["мусор", "отходы", "пакет"],
    },
    {
        "title": "Чистка холодильника",
        "content": "Ежемесячная чистка холодильника предотвращает появление запахов и бактерий.",
        "steps": [
            "Выньте все продукты и проверьте срок годности",
            "Протрите полки тёплой водой с пищевой содой",
            "Очистите резиновые уплотнители дверцы",
            "Проверьте морозильную камеру на наледь",
            "Верните продукты, расположив их по категориям",
        ],
        "rooms": ["Кухня"],
        "keywords": ["холодильник", "уборка", "запахи"],
    },
]

# ---------------------------------------------------------------------------
# Probability of "done" by week and owner
# ---------------------------------------------------------------------------

# (done_prob, skip_prob) — остаток идёт в overdue
WEEK_PATTERNS: dict[int, tuple[float, float]] = {
    1: (0.90, 0.06),   # Apr  1–7  : отлично
    2: (0.52, 0.28),   # Apr  8–14 : «Андрей был в командировке»
    3: (0.85, 0.09),   # Apr 15–21 : восстановление
    4: (0.95, 0.03),   # Apr 22–30 : стабильная серия
}


def _week(d: date) -> int:
    if d <= date(2026, 4, 7):
        return 1
    if d <= date(2026, 4, 14):
        return 2
    if d <= date(2026, 4, 21):
        return 3
    return 4


def _pick_status(occ_date: date, owner: str, rng: random.Random) -> EventStatus:
    done_p, skip_p = WEEK_PATTERNS[_week(occ_date)]
    # Andrey performs worse in week 2 (he's away)
    if owner == "andrey" and _week(occ_date) == 2:
        done_p = 0.35
        skip_p = 0.40
    r = rng.random()
    if r < done_p:
        return EventStatus.done
    if r < done_p + skip_p:
        return EventStatus.skipped
    return EventStatus.overdue


# ---------------------------------------------------------------------------
# Cleanup helper
# ---------------------------------------------------------------------------

async def _drop_existing(db: AsyncSession) -> None:
    """
    Explicit delete order respecting FK constraints:
    TaskEvent.actor_id → house_members (no ondelete) must be cleared before
    HouseMember rows are deleted.
    """
    user_rows = (await db.execute(
        select(User).where(User.email.in_(["andrey@home.ru", "maria@home.ru"]))
    )).scalars().all()
    if not user_rows:
        return

    user_ids = [u.id for u in user_rows]
    members = (await db.execute(
        select(HouseMember).where(HouseMember.user_id.in_(user_ids))
    )).scalars().all()
    if not members:
        # Users exist but have no memberships — just delete users
        await db.execute(delete(User).where(User.id.in_(user_ids)))
        await db.flush()
        return

    member_ids = [m.id for m in members]
    house_ids  = list({m.house_id for m in members})

    # Collect task ids for these houses
    task_rows = (await db.execute(
        select(Task.id).where(Task.house_id.in_(house_ids))
    )).scalars().all()
    task_ids = list(task_rows)

    # 1. Delete TaskEvents first (actor_id has no ondelete → must be explicit)
    if task_ids:
        await db.execute(delete(TaskEvent).where(TaskEvent.task_id.in_(task_ids)))

    # 2. Delete AdviceDeliveries (member_id has ondelete=CASCADE but being explicit)
    if member_ids:
        await db.execute(delete(AdviceDelivery).where(AdviceDelivery.member_id.in_(member_ids)))

    # 3. Delete Tasks (and Rooms) for these houses
    if house_ids:
        await db.execute(delete(Task).where(Task.house_id.in_(house_ids)))
        await db.execute(delete(Room).where(Room.house_id.in_(house_ids)))

    # 4. Delete HouseMembers
    if member_ids:
        await db.execute(delete(HouseMember).where(HouseMember.id.in_(member_ids)))

    # 5. Delete Houses
    if house_ids:
        await db.execute(delete(House).where(House.id.in_(house_ids)))

    # 6. Delete Users
    await db.execute(delete(User).where(User.id.in_(user_ids)))

    await db.flush()


# ---------------------------------------------------------------------------
# Main seeder
# ---------------------------------------------------------------------------

async def seed_demo() -> None:
    rng = random.Random(42)  # deterministic for reproducibility

    async with AsyncSessionLocal() as db:
        # 1. Drop previous demo data
        await _drop_existing(db)

        # 2. Users
        andrey = User(
            email="andrey@home.ru",
            name="Андрей",
            hashed_password=hash_password("password123"),
        )
        maria = User(
            email="maria@home.ru",
            name="Мария",
            hashed_password=hash_password("password123"),
        )
        db.add_all([andrey, maria])
        await db.flush()

        # 3. House
        house = House(name="Наш дом")
        db.add(house)
        await db.flush()

        # 4. Members
        m_andrey = HouseMember(
            house_id=house.id, user_id=andrey.id,
            role=MemberRole.admin, color="#4A7C59",
        )
        m_maria = HouseMember(
            house_id=house.id, user_id=maria.id,
            role=MemberRole.member, color="#7C4A6E",
        )
        db.add_all([m_andrey, m_maria])
        await db.flush()

        member_by_key = {"andrey": m_andrey, "maria": m_maria}

        # 5. Rooms
        room_map: dict[str, Room] = {}
        for r in ROOMS:
            room = Room(house_id=house.id, **r)
            db.add(room)
            await db.flush()
            room_map[r["name"]] = room

        # 6. Advice (upsert — skip if already exists by title)
        existing_titles = set(
            (await db.execute(select(Advice.title))).scalars().all()
        )
        for a in ADVICE_DATA:
            if a["title"] not in existing_titles:
                db.add(Advice(
                    title=a["title"],
                    content=a["content"],
                    steps=a["steps"],
                    room_names=a["rooms"],
                    task_keywords=a["keywords"],
                    is_active=True,
                ))

        # 7. Tasks + events
        tasks: list[tuple[Task, str]] = []  # (task, owner_key)
        for tmpl in TASK_TEMPLATES:
            owner_key: str = tmpl.get("owner", "andrey")  # type: ignore[assignment]
            member = member_by_key[owner_key]
            task = Task(
                house_id=house.id,
                room_id=room_map[tmpl["room"]].id,
                assignee_id=member.id,
                created_by=m_andrey.id,
                title=tmpl["title"],
                priority=tmpl["priority"],
                frequency=tmpl["freq"],
                skip_policy=SkipPolicy.overdue,
                start_date=APRIL_START,
                days_of_week=tmpl.get("days"),
                custom_interval_days=tmpl.get("interval"),
            )
            db.add(task)
            await db.flush()
            tasks.append((task, owner_key))

        # 8. April events
        for task, owner_key in tasks:
            occurrences = get_occurrences(task, APRIL_START, APRIL_END)
            for occ in occurrences:
                status = _pick_status(occ, owner_key, rng)
                # Actor = assignee, sometimes the other member (realistic)
                if rng.random() < 0.15:
                    actor = m_maria if owner_key == "andrey" else m_andrey
                else:
                    actor = member_by_key[owner_key]
                db.add(TaskEvent(
                    task_id=task.id,
                    actor_id=actor.id,
                    occurrence_date=occ,
                    status=status,
                ))

        await db.commit()

    print("✅ Demo seed completed — April 2026 history loaded")
    print("   Login:  andrey@home.ru / password123")
    print("   Also:   maria@home.ru  / password123")
    print()
    print("   Week 1 (Apr  1–7):  ~90% done  (сильный старт)")
    print("   Week 2 (Apr  8–14): ~55% done  (Андрей в командировке — провал)")
    print("   Week 3 (Apr 15–21): ~85% done  (восстановление)")
    print("   Week 4 (Apr 22–30): ~95% done  (серия!)")


if __name__ == "__main__":
    asyncio.run(seed_demo())

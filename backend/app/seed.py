"""
Run: python -m app.seed
Seeds test users, house, rooms, tasks, advice and 30 days of event history.

Important:
- database schema must already be created via Alembic
- run: alembic upgrade head
- then: python -m app.seed
"""
import asyncio
import random
from datetime import date, timedelta
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.house import House
from app.models.member import HouseMember, MemberRole
from app.models.room import Room
from app.models.task import Task, Frequency, SkipPolicy, Priority
from app.models.task_event import TaskEvent, EventStatus
from app.models.advice import Advice
from app.services.recurrence_service import get_occurrences

ROOMS = [
    {"name": "Кухня", "icon": "🍳", "color": "#E8A87C"},
    {"name": "Гостиная", "icon": "🛋️", "color": "#8DB596"},
    {"name": "Спальня", "icon": "🛏️", "color": "#B5A5D5"},
    {"name": "Ванная", "icon": "🚿", "color": "#7CB5C4"},
    {"name": "Балкон", "icon": "🌿", "color": "#90C67A"},
]

TASKS_TEMPLATES = [
    {"title": "Помыть посуду", "room": "Кухня", "freq": Frequency.daily, "priority": Priority.high},
    {"title": "Протереть плиту", "room": "Кухня", "freq": Frequency.weekly, "priority": Priority.medium, "days": [2]},
    {"title": "Пропылесосить гостиную", "room": "Гостиная", "freq": Frequency.weekly, "priority": Priority.medium, "days": [0, 4]},
    {"title": "Полить растения", "room": "Балкон", "freq": Frequency.custom, "interval": 3, "priority": Priority.medium},
    {"title": "Вынести мусор", "room": "Кухня", "freq": Frequency.daily, "priority": Priority.high},
    {"title": "Сменить постельное бельё", "room": "Спальня", "freq": Frequency.monthly, "priority": Priority.low},
    {"title": "Почистить унитаз", "room": "Ванная", "freq": Frequency.weekly, "priority": Priority.high, "days": [5]},
    {"title": "Протереть зеркала", "room": "Ванная", "freq": Frequency.weekly, "priority": Priority.low, "days": [3]},
    {"title": "Разобрать балкон", "room": "Балкон", "freq": Frequency.once, "priority": Priority.low},
    {"title": "Помыть окна", "room": "Гостиная", "freq": Frequency.monthly, "priority": Priority.low},
]

ADVICE_DATA = [
    {
        "title": "Эффективная уборка кухни",
        "content": "Чистая кухня — основа здорового дома. Регулярная уборка предотвращает накопление жира и бактерий.",
        "steps": ["Очистите поверхности от крошек и остатков еды", "Протрите плиту влажной тряпкой с обезжиривателем", "Вымойте раковину с содой", "Протрите фасады шкафов", "Помойте пол"],
        "rooms": ["Кухня"],
        "keywords": ["кухня", "плита", "посуда"]
    },
    {
        "title": "Как правильно пылесосить",
        "content": "Правильная техника пылесошения удаляет до 99% пыли и аллергенов из ковров и мягкой мебели.",
        "steps": ["Уберите мелкие предметы с пола", "Двигайтесь систематично — полосами", "Пройдитесь каждую полосу дважды", "Не забудьте плинтусы и углы", "Очистите фильтр пылесоса"],
        "rooms": ["Гостиная", "Спальня"],
        "keywords": ["пылесос", "ковёр", "пыль"]
    },
    {
        "title": "Уход за растениями",
        "content": "Регулярный полив и уход за растениями делают балкон живым и уютным пространством.",
        "steps": ["Проверьте влажность почвы пальцем на глубину 2 см", "Поливайте у корней, не на листья", "Используйте воду комнатной температуры", "Удалите засохшие листья и цветы", "Раз в месяц подкармливайте удобрением"],
        "rooms": ["Балкон"],
        "keywords": ["растения", "полив", "цветы"]
    },
    {
        "title": "Чистота в ванной",
        "content": "Ванная требует еженедельной чистки для предотвращения плесени и известкового налёта.",
        "steps": ["Нанесите чистящее средство на унитаз, дайте постоять 5 минут", "Протрите раковину и смеситель", "Очистите душевую кабину от налёта", "Вымойте зеркало стеклоочистителем", "Вымойте пол с дезинфектором"],
        "rooms": ["Ванная"],
        "keywords": ["ванная", "унитаз", "зеркало", "душ"]
    },
    {
        "title": "Порядок в спальне",
        "content": "Чистая спальня улучшает качество сна и снижает уровень стресса.",
        "steps": ["Застелите кровать сразу после подъёма", "Уберите вещи на свои места", "Протрите пыль с поверхностей", "Проветрите комнату 10–15 минут", "Смените постельное бельё раз в 1–2 недели"],
        "rooms": ["Спальня"],
        "keywords": ["спальня", "бельё", "кровать"]
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        existing_user = await db.execute(
            select(User).where(User.email == "andrey@home.ru")
        )
        if existing_user.scalar_one_or_none():
            print("ℹ️ Seed skipped: demo data already exists")
            return

        andrey = User(email="andrey@home.ru", name="Андрей", hashed_password=hash_password("password123"))
        maria = User(email="maria@home.ru", name="Мария", hashed_password=hash_password("password123"))
        db.add_all([andrey, maria])
        await db.flush()

        house = House(name="Наш дом")
        db.add(house)
        await db.flush()

        member_andrey = HouseMember(house_id=house.id, user_id=andrey.id, role=MemberRole.admin, color="#4A7C59")
        member_maria = HouseMember(house_id=house.id, user_id=maria.id, role=MemberRole.member, color="#7C4A6E")
        db.add_all([member_andrey, member_maria])
        await db.flush()

        room_map = {}
        for r in ROOMS:
            room = Room(house_id=house.id, **r)
            db.add(room)
            await db.flush()
            room_map[r["name"]] = room

        for a in ADVICE_DATA:
            advice = Advice(
                title=a["title"],
                content=a["content"],
                steps=a["steps"],
                room_names=a["rooms"],
                task_keywords=a["keywords"],
                is_active=True
            )
            db.add(advice)

        today = date.today()
        start = today - timedelta(days=30)
        members = [member_andrey, member_maria]
        tasks = []

        for tmpl in TASKS_TEMPLATES:
            task = Task(
                house_id=house.id,
                room_id=room_map[tmpl["room"]].id,
                assignee_id=random.choice(members).id,
                created_by=member_andrey.id,
                title=tmpl["title"],
                priority=tmpl["priority"],
                frequency=tmpl["freq"],
                skip_policy=SkipPolicy.overdue,
                start_date=start,
                days_of_week=tmpl.get("days"),
                custom_interval_days=tmpl.get("interval")
            )
            db.add(task)
            await db.flush()
            tasks.append(task)

        for task in tasks:
            occurrences = get_occurrences(task, start, today - timedelta(days=1))
            for occ in occurrences:
                rand = random.random()
                actor = random.choice(members)
                if rand < 0.78:
                    status = EventStatus.done
                elif rand < 0.90:
                    status = EventStatus.skipped
                else:
                    status = EventStatus.overdue
                event = TaskEvent(
                    task_id=task.id,
                    actor_id=actor.id,
                    occurrence_date=occ,
                    status=status
                )
                db.add(event)

        await db.commit()
        print("✅ Seed completed!")
        print("   Login: andrey@home.ru / password123")
        print(f"   House ID: {house.id}")


if __name__ == "__main__":
    asyncio.run(seed())
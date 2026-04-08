

# Задача: Создать полноценный full-stack проект "HomeTask"

Это интеллектуальная платформа управления бытовыми задачами с FastAPI бэкендом,
PostgreSQL базой данных, React фронтендом. Архитектура должна быть готова к
расширению до PWA (Progressive Web App) в будущем.

---

## ФАЗА 0 — Структура проекта

Создай следующую корневую структуру:

```
hometask/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── tasks.py
│   │   │   │   │   ├── events.py
│   │   │   │   │   ├── rooms.py
│   │   │   │   │   ├── members.py
│   │   │   │   │   ├── analytics.py
│   │   │   │   │   └── advice.py
│   │   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── house.py
│   │   │   ├── room.py
│   │   │   ├── member.py
│   │   │   ├── task.py
│   │   │   ├── task_event.py
│   │   │   └── advice.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── task_event.py
│   │   │   ├── room.py
│   │   │   ├── member.py
│   │   │   ├── analytics.py
│   │   │   └── advice.py
│   │   ├── services/
│   │   │   ├── task_service.py
│   │   │   ├── recurrence_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── advice_service.py
│   │   ├── seed.py
│   │   └── main.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── manifest.json        ← PWA manifest (заготовка)
│   │   └── icons/               ← папка для PWA иконок
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts        ← axios instance
│   │   │   ├── tasks.ts
│   │   │   ├── events.ts
│   │   │   ├── rooms.ts
│   │   │   ├── members.ts
│   │   │   ├── analytics.ts
│   │   │   └── advice.ts
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   ├── Spinner.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   └── StatCard.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Tasks.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── House.tsx
│   │   │   ├── KnowledgeBase.tsx
│   │   │   └── Login.tsx
│   │   ├── hooks/
│   │   │   ├── useTasks.ts
│   │   │   ├── useEvents.ts
│   │   │   ├── useRooms.ts
│   │   │   ├── useMembers.ts
│   │   │   ├── useAnalytics.ts
│   │   │   └── useAdvice.ts
│   │   ├── store/
│   │   │   └── authStore.ts     ← Zustand store для auth
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   ├── dates.ts
│   │   │   └── recurrence.ts    ← клиентская генерация дат для UI
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```

---

## ФАЗА 1 — Backend

### 1.1 requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
pydantic==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
python-dateutil==2.9.0
httpx==0.27.0
```

### 1.2 backend/app/core/config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hometask:hometask@localhost:5432/hometask"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### 1.3 backend/app/core/database.py

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 1.4 backend/app/core/security.py

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

### 1.5 Модели SQLAlchemy

**backend/app/models/user.py**
```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    memberships: Mapped[list["HouseMember"]] = relationship(back_populates="user")
```

**backend/app/models/house.py**
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class House(Base):
    __tablename__ = "houses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["HouseMember"]] = relationship(back_populates="house", cascade="all, delete-orphan")
    rooms: Mapped[list["Room"]] = relationship(back_populates="house", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="house", cascade="all, delete-orphan")
```

**backend/app/models/member.py**
```python
import uuid
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class MemberRole(str, enum.Enum):
    admin = "admin"
    member = "member"
    limited = "limited"

class HouseMember(Base):
    __tablename__ = "house_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[MemberRole] = mapped_column(SAEnum(MemberRole), default=MemberRole.member)
    color: Mapped[str] = mapped_column(String(7), default="#4A7C59")

    house: Mapped["House"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")
```

**backend/app/models/room.py**
```python
import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(10), default="🏠")
    color: Mapped[str] = mapped_column(String(7), default="#8DB596")

    house: Mapped["House"] = relationship(back_populates="rooms")
    tasks: Mapped[list["Task"]] = relationship(back_populates="room")
```

**backend/app/models/task.py**
```python
import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, Date, Integer, JSON, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class Frequency(str, enum.Enum):
    once = "once"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    custom = "custom"

class SkipPolicy(str, enum.Enum):
    move = "move"
    overdue = "overdue"
    skip = "skip"

class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"))

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    frequency: Mapped[Frequency] = mapped_column(SAEnum(Frequency), default=Frequency.once)
    skip_policy: Mapped[SkipPolicy] = mapped_column(SAEnum(SkipPolicy), default=SkipPolicy.overdue)

    start_date: Mapped[date] = mapped_column(Date)
    days_of_week: Mapped[list | None] = mapped_column(JSON, nullable=True)   # [0..6] для weekly
    custom_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    house: Mapped["House"] = relationship(back_populates="tasks")
    room: Mapped["Room"] = relationship(back_populates="tasks")
    events: Mapped[list["TaskEvent"]] = relationship(back_populates="task", cascade="all, delete-orphan")
```

**backend/app/models/task_event.py**
```python
import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class EventStatus(str, enum.Enum):
    done = "done"
    skipped = "skipped"
    overdue = "overdue"
    moved = "moved"

class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id"))

    occurrence_date: Mapped[date] = mapped_column(Date)   # плановая дата экземпляра
    status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus))
    moved_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="events")
```

**backend/app/models/advice.py**
```python
import uuid
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Advice(Base):
    __tablename__ = "advice"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(2000))
    steps: Mapped[list] = mapped_column(JSON, default=list)
    room_names: Mapped[list] = mapped_column(JSON, default=list)   # ['Кухня', 'Гостиная']
    task_keywords: Mapped[list] = mapped_column(JSON, default=list) # ['пылесос', 'уборка']
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### 1.6 Schemas (Pydantic)

**backend/app/schemas/task.py**
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.task import Frequency, SkipPolicy, Priority

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    room_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    priority: Priority = Priority.medium
    frequency: Frequency = Frequency.once
    skip_policy: SkipPolicy = SkipPolicy.overdue
    start_date: date
    days_of_week: Optional[list[int]] = None
    custom_interval_days: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    room_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    priority: Optional[Priority] = None
    frequency: Optional[Frequency] = None
    skip_policy: Optional[SkipPolicy] = None
    days_of_week: Optional[list[int]] = None
    custom_interval_days: Optional[int] = None
    is_active: Optional[bool] = None

class TaskOut(BaseModel):
    id: UUID
    house_id: UUID
    room_id: Optional[UUID]
    assignee_id: Optional[UUID]
    title: str
    description: str
    priority: Priority
    frequency: Frequency
    skip_policy: SkipPolicy
    start_date: date
    days_of_week: Optional[list[int]]
    custom_interval_days: Optional[int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

**backend/app/schemas/task_event.py**
```python
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.task_event import EventStatus

class EventCreate(BaseModel):
    task_id: UUID
    occurrence_date: date
    status: EventStatus
    moved_to: Optional[date] = None
    note: Optional[str] = None

class EventOut(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: UUID
    occurrence_date: date
    status: EventStatus
    moved_to: Optional[date]
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
```

**backend/app/schemas/analytics.py**
```python
from pydantic import BaseModel
from typing import Optional

class MetricsOut(BaseModel):
    adherence_rate: float      # % выполненных от запланированных
    streak: int                # текущая серия дней
    completion_ratio: float    # % задач со статусом done
    overdue_rate: float        # % просроченных
    total_planned: int
    total_done: int
    total_overdue: int

class LoadDistributionItem(BaseModel):
    member_id: str
    member_name: str
    color: str
    done_count: int
    percentage: float

class DailyPoint(BaseModel):
    date: str
    done: int
    total: int
    rate: float

class AnalyticsOut(BaseModel):
    metrics: MetricsOut
    daily_trend: list[DailyPoint]
    load_distribution: list[LoadDistributionItem]
```

Создай аналогичные схемы для user.py, room.py, member.py, advice.py по образцу выше.

### 1.7 Services

**backend/app/services/recurrence_service.py**
```python
from datetime import date, timedelta
from app.models.task import Task, Frequency

def get_occurrences(task: Task, from_date: date, to_date: date) -> list[date]:
    """Генерирует список дат экземпляров задачи в диапазоне [from_date, to_date]"""
    if task.frequency == Frequency.once:
        if from_date <= task.start_date <= to_date:
            return [task.start_date]
        return []

    dates = []
    current = max(task.start_date, from_date)

    while current <= to_date:
        if task.frequency == Frequency.daily:
            dates.append(current)
            current += timedelta(days=1)

        elif task.frequency == Frequency.weekly:
            days = task.days_of_week or [task.start_date.weekday()]
            if current.weekday() in days:
                dates.append(current)
            current += timedelta(days=1)

        elif task.frequency == Frequency.monthly:
            if current.day == task.start_date.day:
                dates.append(current)
            # перейти к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        elif task.frequency == Frequency.custom:
            interval = task.custom_interval_days or 1
            dates.append(current)
            current += timedelta(days=interval)

    return dates

def is_due_today(task: Task, today: date) -> bool:
    return bool(get_occurrences(task, today, today))
```

**backend/app/services/analytics_service.py**
```python
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.task import Task, Frequency
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

    # Загружаем все активные задачи дома
    tasks_q = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    tasks = tasks_q.scalars().all()

    # Загружаем все события за период
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

    # Подсчёт метрик
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

    # Серия (streak) — последовательные дни с хотя бы одной выполненной задачей
    streak = 0
    check = today - timedelta(days=1)
    while True:
        day_data = daily.get(check)
        if day_data and day_data["done"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # Daily trend
    daily_trend = []
    for d in range(days):
        dd = from_date + timedelta(days=d)
        data = daily.get(dd, {"done": 0, "total": 0})
        rate = round(data["done"] / data["total"] * 100, 1) if data["total"] else 0
        daily_trend.append(DailyPoint(
            date=str(dd),
            done=data["done"],
            total=data["total"],
            rate=rate
        ))

    # Load distribution
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
```

### 1.8 API Endpoints

**backend/app/api/v1/endpoints/tasks.py**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.models.task import Task
from app.models.member import HouseMember
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()

@router.get("/houses/{house_id}/tasks", response_model=list[TaskOut])
async def list_tasks(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    result = await db.execute(
        select(Task).where(Task.house_id == house_id, Task.is_active == True)
    )
    return result.scalars().all()

@router.post("/houses/{house_id}/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    house_id: UUID,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = Task(**payload.model_dump(), house_id=house_id, created_by=current_member.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404)
    task.is_active = False
    await db.commit()
```

**backend/app/api/v1/endpoints/events.py**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from app.core.database import get_db
from app.models.task_event import TaskEvent, EventStatus
from app.models.task import Task
from app.models.member import HouseMember
from app.schemas.task_event import EventCreate, EventOut
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()

@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    # Проверяем, нет ли уже события для этой пары task+date
    existing = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id == payload.task_id,
                TaskEvent.occurrence_date == payload.occurrence_date
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Event for this occurrence already exists")

    event = TaskEvent(**payload.model_dump(), actor_id=current_member.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.get("/houses/{house_id}/events", response_model=list[EventOut])
async def list_events(
    house_id: UUID,
    from_date: date = None,
    to_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    q = select(TaskEvent).join(Task).where(Task.house_id == house_id)
    if from_date:
        q = q.where(TaskEvent.occurrence_date >= from_date)
    if to_date:
        q = q.where(TaskEvent.occurrence_date <= to_date)
    result = await db.execute(q.order_by(TaskEvent.occurrence_date.desc()))
    return result.scalars().all()
```

**backend/app/api/v1/endpoints/auth.py**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, decode_token
from app.models.user import User
from app.models.member import HouseMember
from app.schemas.user import UserCreate, UserOut, TokenOut
from pydantic import BaseModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class RegisterPayload(BaseModel):
    email: str
    name: str
    password: str

@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterPayload, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/auth/login", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401)
    return user

async def get_current_member(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> HouseMember:
    """Возвращает первый HouseMember текущего пользователя (MVP: один дом)"""
    user = await get_current_user(token, db)
    result = await db.execute(
        select(HouseMember).where(HouseMember.user_id == user.id).limit(1)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(403, "Not a member of any house")
    return member
```

**backend/app/api/v1/endpoints/analytics.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.services.analytics_service import get_analytics
from app.schemas.analytics import AnalyticsOut
from app.models.member import HouseMember
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()

@router.get("/houses/{house_id}/analytics", response_model=AnalyticsOut)
async def analytics(
    house_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member)
):
    return await get_analytics(db, house_id, days)
```

Создай аналогичные endpoints для rooms.py, members.py, advice.py по образцу tasks.py.

**backend/app/api/v1/router.py**
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, tasks, events, rooms, members, analytics, advice

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, tags=["auth"])
router.include_router(tasks.router, tags=["tasks"])
router.include_router(events.router, tags=["events"])
router.include_router(rooms.router, tags=["rooms"])
router.include_router(members.router, tags=["members"])
router.include_router(analytics.router, tags=["analytics"])
router.include_router(advice.router, tags=["advice"])
```

### 1.9 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import router

app = FastAPI(title="HomeTask API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 1.10 Seed данных (backend/app/seed.py)

```python
"""
Запуск: python -m app.seed
Создаёт тестового пользователя, дом, комнаты, задачи и 30 дней истории событий
"""
import asyncio
import uuid
from datetime import date, timedelta
import random
from app.core.database import AsyncSessionLocal, engine, Base
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Пользователи
        alex = User(email="alex@home.ru", name="Алекс", hashed_password=hash_password("password123"))
        maria = User(email="maria@home.ru", name="Мария", hashed_password=hash_password("password123"))
        db.add_all([alex, maria])
        await db.flush()

        # Дом
        house = House(name="Наш дом")
        db.add(house)
        await db.flush()

        # Участники
        member_alex = HouseMember(house_id=house.id, user_id=alex.id, role=MemberRole.admin, color="#4A7C59")
        member_maria = HouseMember(house_id=house.id, user_id=maria.id, role=MemberRole.member, color="#7C4A6E")
        db.add_all([member_alex, member_maria])
        await db.flush()

        # Комнаты
        room_map = {}
        for r in ROOMS:
            room = Room(house_id=house.id, **r)
            db.add(room)
            await db.flush()
            room_map[r["name"]] = room

        # Советы
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

        # Задачи
        today = date.today()
        start = today - timedelta(days=30)
        members = [member_alex, member_maria]
        tasks = []

        for tmpl in TASKS_TEMPLATES:
            task = Task(
                house_id=house.id,
                room_id=room_map[tmpl["room"]].id,
                assignee_id=random.choice(members).id,
                created_by=member_alex.id,
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

        # Историческии события (последние 30 дней, ~80% выполнение)
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
        print(f"   Login: alex@home.ru / password123")
        print(f"   House ID: {house.id}")

if __name__ == "__main__":
    asyncio.run(seed())
```

### 1.11 Alembic

Инициализируй alembic: `alembic init alembic`

В alembic/env.py добавь:
```python
from app.core.config import settings
from app.core.database import Base
# Импортируй все модели для автодетекции:
from app.models import user, house, room, member, task, task_event, advice

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))
target_metadata = Base.metadata
```

Создай первую миграцию: `alembic revision --autogenerate -m "initial"`

---

## ФАЗА 2 — Frontend

### 2.1 package.json (frontend)

```json
{
  "name": "hometask-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "axios": "^1.7.0",
    "recharts": "^2.12.0",
    "lucide-react": "^0.383.0",
    "react-hot-toast": "^2.4.1",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.40.0",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### 2.2 vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### 2.3 tailwind.config.js

```javascript
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        beige: {
          50:  '#FDFAF4',
          100: '#F5F0E8',
          200: '#EDE5D5',
          300: '#DDD3BC',
        },
        forest: {
          50:  '#EBF3EE',
          100: '#C9DFD0',
          200: '#8DB596',
          300: '#5C9A6A',
          400: '#4A7C59',
          500: '#2D5A3D',
          600: '#1E3D29',
        },
        sage: '#8DB596',
        bark:  '#6B5744',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body:    ['"DM Sans"', 'sans-serif'],
      },
      borderRadius: {
        xl2: '1.25rem',
        xl3: '1.5rem',
      },
      boxShadow: {
        card: '0 2px 16px 0 rgba(74,124,89,0.08)',
        hover: '0 4px 24px 0 rgba(74,124,89,0.15)',
      }
    },
  },
  plugins: [],
}
```

### 2.4 index.html

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#4A7C59" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
  <title>HomeTask</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

### 2.5 public/manifest.json (PWA-заготовка)

```json
{
  "name": "HomeTask — управление домом",
  "short_name": "HomeTask",
  "description": "Интеллектуальная платформа управления бытовыми задачами",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F5F0E8",
  "theme_color": "#4A7C59",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 2.6 src/types/index.ts

```typescript
export type Frequency = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'
export type SkipPolicy = 'move' | 'overdue' | 'skip'
export type Priority = 'low' | 'medium' | 'high'
export type MemberRole = 'admin' | 'member' | 'limited'
export type EventStatus = 'done' | 'skipped' | 'overdue' | 'moved'

export interface User {
  id: string
  email: string
  name: string
}

export interface Room {
  id: string
  house_id: string
  name: string
  icon: string
  color: string
}

export interface Member {
  id: string
  house_id: string
  user_id: string
  role: MemberRole
  color: string
  user?: User
}

export interface Task {
  id: string
  house_id: string
  room_id: string | null
  assignee_id: string | null
  title: string
  description: string
  priority: Priority
  frequency: Frequency
  skip_policy: SkipPolicy
  start_date: string
  days_of_week: number[] | null
  custom_interval_days: number | null
  is_active: boolean
  created_at: string
}

export interface TaskEvent {
  id: string
  task_id: string
  actor_id: string
  occurrence_date: string
  status: EventStatus
  moved_to: string | null
  note: string | null
  created_at: string
}

export interface Advice {
  id: string
  title: string
  content: string
  steps: string[]
  room_names: string[]
  task_keywords: string[]
  is_active: boolean
}

export interface DailyPoint {
  date: string
  done: number
  total: number
  rate: number
}

export interface Metrics {
  adherence_rate: number
  streak: number
  completion_ratio: number
  overdue_rate: number
  total_planned: number
  total_done: number
  total_overdue: number
}

export interface LoadItem {
  member_id: string
  member_name: string
  color: string
  done_count: number
  percentage: number
}

export interface Analytics {
  metrics: Metrics
  daily_trend: DailyPoint[]
  load_distribution: LoadItem[]
}

// Для формы
export interface TaskFormData {
  title: string
  description: string
  room_id: string
  assignee_id: string
  priority: Priority
  frequency: Frequency
  skip_policy: SkipPolicy
  start_date: string
  days_of_week: number[]
  custom_interval_days: number
}
```

### 2.7 src/api/client.ts

```typescript
import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
```

### 2.8 src/api/* — все API-файлы

Создай по образцу:

**src/api/tasks.ts**
```typescript
import client from './client'
import type { Task, TaskFormData } from '../types'

export const tasksApi = {
  list: (houseId: string) =>
    client.get<Task[]>(`/houses/${houseId}/tasks`).then(r => r.data),

  create: (houseId: string, data: Partial<TaskFormData>) =>
    client.post<Task>(`/houses/${houseId}/tasks`, data).then(r => r.data),

  update: (taskId: string, data: Partial<TaskFormData>) =>
    client.patch<Task>(`/tasks/${taskId}`, data).then(r => r.data),

  delete: (taskId: string) =>
    client.delete(`/tasks/${taskId}`)
}
```

Создай аналогично: events.ts, rooms.ts, members.ts, analytics.ts, advice.ts.

**src/api/auth.ts**
```typescript
import client from './client'
import type { User } from '../types'

export const authApi = {
  login: (email: string, password: string) =>
    client.post<{ access_token: string }>('/auth/login', null, {
      params: { username: email, password },
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(r => r.data),

  register: (email: string, name: string, password: string) =>
    client.post<User>('/auth/register', { email, name, password }).then(r => r.data),

  me: () => client.get<User>('/auth/me').then(r => r.data)
}
```

### 2.9 src/store/authStore.ts

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  houseId: string | null
  memberId: string | null
  userName: string | null
  setAuth: (token: string, houseId: string, memberId: string, userName: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    set => ({
      token: null,
      houseId: null,
      memberId: null,
      userName: null,
      setAuth: (token, houseId, memberId, userName) =>
        set({ token, houseId, memberId, userName }),
      logout: () => set({ token: null, houseId: null, memberId: null, userName: null })
    }),
    { name: 'hometask-auth' }
  )
)
```

### 2.10 src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-beige-100 font-body text-neutral-800 antialiased;
  }
  h1, h2, h3 {
    @apply font-display;
  }
}

@layer components {
  .card {
    @apply bg-beige-50 rounded-xl3 shadow-card border border-beige-200 p-5;
  }
  .btn-primary {
    @apply bg-forest-400 hover:bg-forest-500 text-white font-body font-medium
           px-5 py-2.5 rounded-xl transition-all duration-200
           shadow-sm hover:shadow-md active:scale-95;
  }
  .btn-secondary {
    @apply bg-beige-200 hover:bg-beige-300 text-forest-500 font-body font-medium
           px-5 py-2.5 rounded-xl transition-all duration-200 active:scale-95;
  }
  .btn-ghost {
    @apply text-forest-400 hover:bg-forest-50 font-medium
           px-4 py-2 rounded-lg transition-colors duration-150;
  }
  .input {
    @apply w-full bg-beige-50 border border-beige-300 rounded-xl px-4 py-2.5
           font-body text-sm focus:outline-none focus:ring-2 focus:ring-forest-300
           focus:border-forest-400 transition-all placeholder-neutral-400;
  }
  .label {
    @apply block text-xs font-medium text-neutral-500 mb-1.5 uppercase tracking-wide;
  }
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { @apply bg-beige-300 rounded-full; }

/* Анимации */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fade-in { animation: fadeIn 0.25s ease both; }
```

### 2.11 src/components/Layout.tsx

```tsx
import { NavLink, Outlet } from 'react-router-dom'
import { Home, CheckSquare, BarChart2, Building2, BookOpen, LogOut } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const NAV = [
  { to: '/',           icon: Home,        label: 'Главная'    },
  { to: '/tasks',      icon: CheckSquare, label: 'Задачи'     },
  { to: '/analytics',  icon: BarChart2,   label: 'Аналитика'  },
  { to: '/house',      icon: Building2,   label: 'Дом'        },
  { to: '/knowledge',  icon: BookOpen,    label: 'База знаний'},
]

export default function Layout() {
  const { userName, logout } = useAuthStore()

  return (
    <div className="flex min-h-screen bg-beige-100">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex flex-col w-60 bg-beige-50 border-r border-beige-200 fixed inset-y-0 z-20">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-beige-200">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">🏡</span>
            <span className="font-display text-xl text-forest-500 font-semibold">HomeTask</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-forest-400 text-white shadow-sm'
                    : 'text-neutral-600 hover:bg-beige-200 hover:text-forest-500'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t border-beige-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-forest-200 flex items-center justify-center text-forest-600 font-semibold text-sm">
              {userName?.[0] ?? '?'}
            </div>
            <span className="text-sm font-medium text-neutral-700 flex-1 truncate">{userName}</span>
            <button
              onClick={() => { logout(); toast.success('До свидания!') }}
              className="text-neutral-400 hover:text-forest-500 transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 md:ml-60 flex flex-col min-h-screen">
        <div className="flex-1 px-4 md:px-8 py-6 animate-fade-in">
          <Outlet />
        </div>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 inset-x-0 bg-beige-50 border-t border-beige-200 flex justify-around py-2 z-20">
          {NAV.slice(0, 4).map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg text-xs transition-colors ${
                isActive ? 'text-forest-400 font-semibold' : 'text-neutral-400'
              }`
            }>
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>
      </main>
    </div>
  )
}
```

### 2.12 src/pages/Dashboard.tsx

Реализуй полностью. Включает:
- Заголовок "Доброе утро, {userName}!" с текущей датой
- ProgressBar дня: `done / total задач на сегодня`
- Список задач на сегодня (фильтруй через recurrence.ts на клиенте)
- Каждая TaskCard с кнопками Готово / Пропустить / Перенести
- Блок метрик: Серия (streak) и Уровень соблюдения
- Блок "Совет дня" — рандомный активный совет из базы

TaskCard для Dashboard:
```tsx
// Бежевая карточка, левая полоса цвета приоритета (high=forest-400, medium=sage, low=beige-300)
// Название задачи, иконка+название комнаты, маленький бейдж частоты
// Справа: три кнопки icon-only (Check, X, ArrowRight) с tooltip
// При нажатии — POST /events → обновить список через React Query invalidate
```

### 2.13 src/pages/Analytics.tsx

- 4 StatCard вверху: Adherence Rate (%), Серия (дней), Completion Ratio (%), Overdue Rate (%)
- LineChart (Recharts) тренд выполнения за N дней — зелёный градиент под линией
- PieChart распределения нагрузки по участникам (цвета из member.color)
- BarChart задач по комнатам
- Переключатель периода: [7 дней] [30 дней] [90 дней] — кнопки-пилюли

### 2.14 src/pages/Tasks.tsx

- Поиск по названию
- Фильтры: Комната (select), Приоритет (radio-пилюли), Статус (active/all)
- Таблица/список задач с колонками: Название, Комната, Приоритет, Частота, Ответственный, Действия
- FAB кнопка "+" открывает TaskForm modal
- Клик на задачу открывает TaskForm с предзаполненными данными

### 2.15 src/components/TaskForm.tsx

Модальная форма в createPortal:
```
Поля:
- title (input)
- description (textarea)  
- room_id (select — с цветными иконками комнат)
- priority (3 кнопки-карточки: 🟢 Низкий / 🟡 Средний / 🔴 Высокий)
- frequency (tabs: Разово / Ежедневно / Еженедельно / Ежемесячно / Кастомный)
  - если weekly: сетка дней недели (Пн Вт Ср Чт Пт Сб Вс) — toggle кнопки
  - если custom: input "Каждые N дней"
- skip_policy (radio: Перенести / Просрочить / Пропустить)
- start_date (input type=date)
- assignee_id (select участников с аватаром-инициалами)
```

### 2.16 src/pages/House.tsx

Две секции:
1. **Комнаты** — grid карточки с иконкой и именем, кнопки редактирования/удаления, "Добавить комнату"
2. **Участники** — список с аватаром (инициалы + color), именем, email, ролью (badge), кнопка смены роли для admin

### 2.17 src/pages/KnowledgeBase.tsx

- Поиск по советам
- Карточки сгруппированные по room_names
- Каждая карточка: заголовок, краткое описание, раскрывающийся список шагов (accordion)
- Бейджи комнат

### 2.18 src/pages/Login.tsx

Красивая страница без sidebar:
```
Логотип 🏡 HomeTask по центру
Вкладки: Войти / Зарегистрироваться
Форма входа: email, password → POST /auth/login → save token → redirect /
Форма регистрации: email, name, password → POST /auth/register → auto-login
Показывать тост при ошибках
```

После логина: получить /auth/me, сохранить user данные в authStore.

### 2.19 src/App.tsx

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Analytics from './pages/Analytics'
import House from './pages/House'
import KnowledgeBase from './pages/KnowledgeBase'
import Login from './pages/Login'

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } }
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{
          style: { background: '#FDFAF4', border: '1px solid #EDE5D5', fontFamily: 'DM Sans' }
        }} />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="house" element={<House />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

---

## ФАЗА 3 — Docker и инфраструктура

### docker-compose.yml

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: hometask
      POSTGRES_PASSWORD: hometask
      POSTGRES_DB: hometask
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hometask"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://hometask:hometask@postgres:5432/hometask
      SECRET_KEY: dev-secret-key-change-in-prod
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  pgdata:
```

### backend/Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
```

### backend/.env.example

```
DATABASE_URL=postgresql+asyncpg://hometask:hometask@localhost:5432/hometask
SECRET_KEY=change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=["http://localhost:5173"]
```

---

## ФАЗА 4 — README.md

```markdown
# 🏡 HomeTask — Платформа управления бытовыми задачами

## Быстрый старт

### Вариант A: Docker (рекомендуется)
```bash
docker-compose up --build
# В новом терминале:
docker-compose exec backend python -m app.seed
```
Открой: http://localhost:5173
Логин: alex@home.ru / password123

### Вариант B: Локально

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # при необходимости отредактируй
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Стек
- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic
- **Frontend**: React 18 + TypeScript + Tailwind CSS + React Query
- **Auth**: JWT (jose) + bcrypt
- **PWA**: manifest.json готов; Service Worker добавить в следующей итерации

## API Документация
После запуска бэкенда: http://localhost:8000/docs

## Архитектура
Модульная: api/ → services/ → models/ → database
Event-log подход: все изменения задач фиксируются как TaskEvent

## PWA roadmap
- [ ] Service Worker (Workbox) для офлайн-кэша
- [ ] Push-уведомления (Web Push API)
- [ ] Background Sync для офлайн-очереди событий
- [ ] Install prompt
```

---

## ИТОГОВЫЕ ИНСТРУКЦИИ ДЛЯ CLAUDE CODE

1. Создай структуру директорий командой mkdir -p
2. Создай все файлы бэкенда согласно фазе 1
3. Создай все файлы фронтенда согласно фазе 2
4. Создай docker-compose.yml и Dockerfile'ы согласно фазе 3
5. Создай README.md согласно фазе 4
6. Для каждого файла, не описанного подробно (например rooms.py endpoint, advice.py endpoint, схемы для rooms/members) — реализуй по аналогии с tasks.py и TaskOut
7. Проверь, что все импорты корректны и перекрёстные ссылки между моделями работают
8. Убедись, что backend/app/models/__init__.py импортирует все модели (для Alembic)
9. Добавь endpoint GET /auth/me в auth.py
10. После создания всех файлов выполни:
    ```bash
    cd backend && pip install -r requirements.txt
    cd ../frontend && npm install && npm run build
    ```
    и исправь все TypeScript и Python ошибки до нулевого количества
11. Итоговый вывод: инструкция запуска через docker-compose и через локальный старт
```

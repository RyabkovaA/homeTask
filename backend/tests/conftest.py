"""
Общие фабрики и фикстуры для unit-тестов.
Все объекты создаются через MagicMock без подключения к базе данных.
"""
import uuid
from datetime import date
from unittest.mock import MagicMock

from app.models.task import Frequency, SkipPolicy
from app.models.task_event import EventStatus


def make_task(
    frequency: Frequency = Frequency.once,
    start_date: date = date(2025, 1, 1),
    days_of_week=None,
    custom_interval_days: int = None,
    skip_policy: SkipPolicy = SkipPolicy.overdue,
    window_days: int = 0,
    task_id: str = None,
) -> MagicMock:
    task = MagicMock()
    task.id = task_id or str(uuid.uuid4())
    task.frequency = frequency
    task.start_date = start_date
    task.days_of_week = days_of_week
    task.custom_interval_days = custom_interval_days
    task.skip_policy = skip_policy
    task.window_days = window_days
    return task


def make_event(task_id: str, occurrence_date: date, status: EventStatus, moved_to: date = None) -> MagicMock:
    ev = MagicMock()
    ev.task_id = task_id
    ev.occurrence_date = occurrence_date
    ev.status = status
    ev.moved_to = moved_to
    return ev


def make_advice(advice_id: str, title: str, content: str,
                room_names=None, task_keywords=None, steps=None) -> MagicMock:
    a = MagicMock()
    a.id = advice_id
    a.title = title
    a.content = content
    a.steps = steps or []
    a.room_names = room_names or []
    a.task_keywords = task_keywords or []
    a.is_active = True
    return a

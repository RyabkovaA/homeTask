"""
Тесты для recurrence_service — Algorithm 2 (Алгоритм 2 ВКР).

Покрывает:
  - get_occurrences: все типы частоты (once / daily / weekly / monthly / custom)
  - build_rrule: генерация RRULE-строк RFC 5545
  - build_occurrences: политики пропуска (overdue / skip / move), window_days,
    применение событий из журнала
"""
from datetime import date, timedelta

import pytest

from tests.conftest import make_event, make_task
from app.models.task import Frequency, SkipPolicy
from app.models.task_event import EventStatus
from app.services.recurrence_service import (
    OccurrenceStatus,
    build_occurrences,
    build_rrule,
    get_occurrences,
    is_due_today,
)

TASK_ID = "11111111-0000-0000-0000-000000000001"


# ─────────────────────────────────────────────────────────
# get_occurrences — once
# ─────────────────────────────────────────────────────────

class TestGetOccurrencesOnce:
    def test_once_in_range(self):
        task = make_task(Frequency.once, date(2025, 5, 10))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert result == [date(2025, 5, 10)]

    def test_once_on_start_boundary(self):
        task = make_task(Frequency.once, date(2025, 5, 1))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert result == [date(2025, 5, 1)]

    def test_once_on_end_boundary(self):
        task = make_task(Frequency.once, date(2025, 5, 31))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert result == [date(2025, 5, 31)]

    def test_once_before_range_returns_empty(self):
        task = make_task(Frequency.once, date(2025, 4, 15))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert result == []

    def test_once_after_range_returns_empty(self):
        task = make_task(Frequency.once, date(2025, 6, 1))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert result == []


# ─────────────────────────────────────────────────────────
# get_occurrences — daily
# ─────────────────────────────────────────────────────────

class TestGetOccurrencesDaily:
    def test_daily_generates_consecutive_dates(self):
        task = make_task(Frequency.daily, date(2025, 5, 1))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 3))
        assert result == [date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 3)]

    def test_daily_count_equals_days(self):
        task = make_task(Frequency.daily, date(2025, 5, 1))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 10))
        assert len(result) == 10

    def test_daily_start_after_from_date(self):
        # task starts May 5, range starts May 1 → 6 dates (5..10)
        task = make_task(Frequency.daily, date(2025, 5, 5))
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 10))
        assert result[0] == date(2025, 5, 5)
        assert len(result) == 6


# ─────────────────────────────────────────────────────────
# get_occurrences — weekly
# ─────────────────────────────────────────────────────────

class TestGetOccurrencesWeekly:
    def test_weekly_specific_days_mon_wed(self):
        # Неделя 2025-05-05 (Пн) … 2025-05-11 (Вс); дни: Пн=0, Ср=2
        task = make_task(Frequency.weekly, date(2025, 5, 5), days_of_week=[0, 2])
        result = get_occurrences(task, date(2025, 5, 5), date(2025, 5, 11))
        assert date(2025, 5, 5) in result   # понедельник
        assert date(2025, 5, 7) in result   # среда
        assert date(2025, 5, 6) not in result  # вторник
        assert date(2025, 5, 8) not in result  # четверг

    def test_weekly_no_days_of_week_uses_start_weekday(self):
        # start_date = 2025-05-07 (среда, weekday=2) → только среды
        task = make_task(Frequency.weekly, date(2025, 5, 7), days_of_week=None)
        result = get_occurrences(task, date(2025, 5, 5), date(2025, 5, 25))
        assert all(d.weekday() == 2 for d in result)
        assert len(result) == 3  # 7, 14, 21 мая

    def test_weekly_returns_only_specified_days(self):
        # Только пятница (4)
        task = make_task(Frequency.weekly, date(2025, 5, 2), days_of_week=[4])
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 31))
        assert all(d.weekday() == 4 for d in result)


# ─────────────────────────────────────────────────────────
# get_occurrences — monthly
# ─────────────────────────────────────────────────────────

class TestGetOccurrencesMonthly:
    def test_monthly_same_day_three_months(self):
        task = make_task(Frequency.monthly, date(2025, 1, 15))
        result = get_occurrences(task, date(2025, 1, 1), date(2025, 3, 31))
        assert date(2025, 1, 15) in result
        assert date(2025, 2, 15) in result
        assert date(2025, 3, 15) in result

    def test_monthly_generates_one_per_month(self):
        task = make_task(Frequency.monthly, date(2025, 1, 10))
        result = get_occurrences(task, date(2025, 1, 1), date(2025, 12, 31))
        assert len(result) == 12


# ─────────────────────────────────────────────────────────
# get_occurrences — custom interval
# ─────────────────────────────────────────────────────────

class TestGetOccurrencesCustom:
    def test_custom_interval_3_days(self):
        task = make_task(Frequency.custom, date(2025, 5, 1), custom_interval_days=3)
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 10))
        assert date(2025, 5, 1) in result
        assert date(2025, 5, 4) in result
        assert date(2025, 5, 7) in result
        assert date(2025, 5, 10) in result
        assert date(2025, 5, 2) not in result

    def test_custom_interval_1_is_like_daily(self):
        task = make_task(Frequency.custom, date(2025, 5, 1), custom_interval_days=1)
        result = get_occurrences(task, date(2025, 5, 1), date(2025, 5, 5))
        assert len(result) == 5


# ─────────────────────────────────────────────────────────
# is_due_today
# ─────────────────────────────────────────────────────────

class TestIsDueToday:
    def test_due_today_once(self):
        today = date.today()
        task = make_task(Frequency.once, today)
        assert is_due_today(task, today) is True

    def test_not_due_today_once_yesterday(self):
        yesterday = date.today() - timedelta(days=1)
        task = make_task(Frequency.once, yesterday)
        assert is_due_today(task, date.today()) is False


# ─────────────────────────────────────────────────────────
# build_rrule
# ─────────────────────────────────────────────────────────

class TestBuildRRule:
    def test_once_returns_empty(self):
        task = make_task(Frequency.once, date(2025, 1, 1))
        assert build_rrule(task) == ""

    def test_daily(self):
        task = make_task(Frequency.daily, date(2025, 1, 1))
        assert build_rrule(task) == "FREQ=DAILY"

    def test_weekly_mon_wed(self):
        task = make_task(Frequency.weekly, date(2025, 5, 5), days_of_week=[0, 2])
        rrule = build_rrule(task)
        assert rrule.startswith("FREQ=WEEKLY")
        assert "MO" in rrule
        assert "WE" in rrule

    def test_weekly_single_day(self):
        task = make_task(Frequency.weekly, date(2025, 5, 2), days_of_week=[4])  # пятница
        rrule = build_rrule(task)
        assert "FR" in rrule

    def test_monthly_15th(self):
        task = make_task(Frequency.monthly, date(2025, 3, 15))
        assert build_rrule(task) == "FREQ=MONTHLY;BYMONTHDAY=15"

    def test_monthly_1st(self):
        task = make_task(Frequency.monthly, date(2025, 1, 1))
        assert build_rrule(task) == "FREQ=MONTHLY;BYMONTHDAY=1"

    def test_custom_7_days(self):
        task = make_task(Frequency.custom, date(2025, 1, 1), custom_interval_days=7)
        assert build_rrule(task) == "FREQ=DAILY;INTERVAL=7"

    def test_custom_3_days(self):
        task = make_task(Frequency.custom, date(2025, 1, 1), custom_interval_days=3)
        assert build_rrule(task) == "FREQ=DAILY;INTERVAL=3"


# ─────────────────────────────────────────────────────────
# build_occurrences — journal events
# ─────────────────────────────────────────────────────────

class TestBuildOccurrencesEvents:
    def test_done_event_marks_done(self):
        task = make_task(Frequency.daily, date(2025, 5, 1), task_id=TASK_ID)
        ev = make_event(TASK_ID, date(2025, 5, 1), EventStatus.done)
        result = build_occurrences(task, [ev], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 2))
        assert len(result) == 1
        assert result[0].status == OccurrenceStatus.done

    def test_skipped_event_marks_skipped(self):
        task = make_task(Frequency.daily, date(2025, 5, 1), task_id=TASK_ID)
        ev = make_event(TASK_ID, date(2025, 5, 1), EventStatus.skipped)
        result = build_occurrences(task, [ev], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 2))
        assert result[0].status == OccurrenceStatus.skipped

    def test_moved_event_marks_moved(self):
        task = make_task(Frequency.daily, date(2025, 5, 1), task_id=TASK_ID)
        ev = make_event(TASK_ID, date(2025, 5, 1), EventStatus.moved, moved_to=date(2025, 5, 5))
        result = build_occurrences(task, [ev], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 2))
        assert result[0].status == OccurrenceStatus.moved
        assert result[0].moved_to == date(2025, 5, 5)

    def test_overdue_event_marks_overdue(self):
        task = make_task(Frequency.daily, date(2025, 5, 1), task_id=TASK_ID)
        ev = make_event(TASK_ID, date(2025, 5, 1), EventStatus.overdue)
        result = build_occurrences(task, [ev], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 2))
        assert result[0].status == OccurrenceStatus.overdue


# ─────────────────────────────────────────────────────────
# build_occurrences — skip_policy
# ─────────────────────────────────────────────────────────

class TestBuildOccurrencesSkipPolicy:
    def test_overdue_policy_past_window(self):
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.overdue, window_days=0, task_id=TASK_ID)
        result = build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 6))
        assert result[0].status == OccurrenceStatus.overdue

    def test_skip_policy_past_window(self):
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.skip, window_days=0, task_id=TASK_ID)
        result = build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 6))
        assert result[0].status == OccurrenceStatus.skipped_auto

    def test_move_policy_past_window(self):
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.move, window_days=0, task_id=TASK_ID)
        result = build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 6))
        assert result[0].status == OccurrenceStatus.moved
        assert result[0].moved_to is not None
        assert result[0].moved_to > date(2025, 5, 5)  # перенесена в будущее

    def test_active_within_window(self):
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.overdue, window_days=5, task_id=TASK_ID)
        # occurrence 1 мая, now = 3 мая, окно = 5 дней → ещё активна
        result = build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 3))
        assert result[0].status == OccurrenceStatus.active

    def test_overdue_exactly_at_window_boundary(self):
        # window_days=2: дата + 2 = граница. now = дата + 3 → просрочена
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.overdue, window_days=2, task_id=TASK_ID)
        result = build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1), now=date(2025, 5, 4))
        assert result[0].status == OccurrenceStatus.overdue

    def test_auto_move_events_out_populated(self):
        task = make_task(Frequency.daily, date(2025, 5, 1),
                         skip_policy=SkipPolicy.move, window_days=0, task_id=TASK_ID)
        auto_moves: list = []
        build_occurrences(task, [], date(2025, 5, 1), date(2025, 5, 1),
                          now=date(2025, 5, 6), auto_move_events_out=auto_moves)
        assert len(auto_moves) == 1
        assert auto_moves[0]["task_id"] == TASK_ID

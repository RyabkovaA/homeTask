"""
Recurrence service — Algorithm 2 (thesis):
BuildOccurrences(Template T, Journal E, Date from, Date to)

Generates occurrence dates from task RRULE and resolves statuses
using the event journal and the task's skip_policy:

  OVERDUE      — mark past-window occurrences as overdue (no rescheduling)
  SKIP_NO_DEBT — auto-skip past-window occurrences without creating debt
  MOVE_FORWARD — reschedule past-window occurrence to nearest allowed future date
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.models.task import Task, Frequency, SkipPolicy
from app.models.task_event import TaskEvent, EventStatus


# ---------------------------------------------------------------------------
# Occurrence status vocabulary
# ---------------------------------------------------------------------------

class OccurrenceStatus(str, enum.Enum):
    active      = "active"        # within execution window, no event yet
    done        = "done"          # has a 'done' event
    skipped     = "skipped"       # manually skipped
    overdue     = "overdue"       # past window, policy = OVERDUE
    skipped_auto = "skipped_auto" # past window, policy = SKIP_NO_DEBT
    moved       = "moved"         # moved (manually or by MOVE_FORWARD policy)


@dataclass
class Occurrence:
    task_id: str
    occurrence_date: date
    status: OccurrenceStatus
    moved_to: Optional[date] = None


# ---------------------------------------------------------------------------
# Raw date generation (GenerateRRULE step of the algorithm)
# ---------------------------------------------------------------------------

def get_occurrences(task: Task, from_date: date, to_date: date) -> list[date]:
    """
    GenerateRRULE(T.RRULE, from, to) — generate raw occurrence dates
    for the task in [from_date, to_date].  Linear in number of dates.
    """
    if task.frequency == Frequency.once:
        if from_date <= task.start_date <= to_date:
            return [task.start_date]
        return []

    dates: list[date] = []
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
            # advance by one month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
            # seek the target day-of-month within the new month
            import calendar
            target_day = task.start_date.day
            last_day = calendar.monthrange(current.year, current.month)[1]
            current = current.replace(day=min(target_day, last_day))
            continue  # already advanced

        elif task.frequency == Frequency.custom:
            interval = task.custom_interval_days or 1
            dates.append(current)
            current += timedelta(days=interval)

        else:
            break

    return dates


def is_due_today(task: Task, today: date) -> bool:
    return bool(get_occurrences(task, today, today))


# ---------------------------------------------------------------------------
# iCalendar RRULE generation (RFC 5545 compatible)
# ---------------------------------------------------------------------------

_DOW_MAP = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}


def build_rrule(task: Task) -> str:
    """
    Return an iCalendar RRULE string for the task.
    Returns empty string for one-time (once) tasks.

    Examples:
      daily              → "FREQ=DAILY"
      weekly Mon+Wed     → "FREQ=WEEKLY;BYDAY=MO,WE"
      monthly on the 15th→ "FREQ=MONTHLY;BYMONTHDAY=15"
      every 3 days       → "FREQ=DAILY;INTERVAL=3"
    """
    if task.frequency == Frequency.once:
        return ""

    if task.frequency == Frequency.daily:
        return "FREQ=DAILY"

    if task.frequency == Frequency.weekly:
        days = task.days_of_week or [task.start_date.weekday()]
        byday = ",".join(_DOW_MAP[d] for d in sorted(days))
        return f"FREQ=WEEKLY;BYDAY={byday}"

    if task.frequency == Frequency.monthly:
        return f"FREQ=MONTHLY;BYMONTHDAY={task.start_date.day}"

    if task.frequency == Frequency.custom:
        interval = task.custom_interval_days or 1
        return f"FREQ=DAILY;INTERVAL={interval}"

    return ""


# ---------------------------------------------------------------------------
# NearestAllowedDateAfter helper
# ---------------------------------------------------------------------------

def _nearest_allowed_after(now: date, task: Task) -> date:
    """
    NearestAllowedDateAfter(Now, T): find the first occurrence date of
    the task strictly after `now`.  Searches up to 366 days ahead.
    For `once` tasks returns now+1 (fallback; once-tasks should not trigger MOVE_FORWARD).
    """
    if task.frequency == Frequency.once:
        return now + timedelta(days=1)

    candidate = now + timedelta(days=1)
    horizon = now + timedelta(days=366)
    while candidate <= horizon:
        if get_occurrences(task, candidate, candidate):
            return candidate
        candidate += timedelta(days=1)

    return now + timedelta(days=1)  # safety fallback


# ---------------------------------------------------------------------------
# Full BuildOccurrences algorithm (Algorithm 2 of the thesis)
# ---------------------------------------------------------------------------

def build_occurrences(
    task: Task,
    events: list[TaskEvent],
    from_date: date,
    to_date: date,
    now: Optional[date] = None,
    auto_move_events_out: Optional[list[dict]] = None,
) -> list[Occurrence]:
    """
    Algorithm BuildOccurrences(T, E, from, to):

    For each date d in GenerateRRULE(T.RRULE, from, to):
      1. If Exists(E, occ, "done")      → DONE
      2. If Exists(E, occ, "skipped")   → SKIPPED
      3. If Exists(E, occ, "moved")     → MOVED
      4. If Exists(E, occ, "overdue")   → OVERDUE  (explicit journal entry)
      5. If Now ≤ d + T.window_days     → ACTIVE
      6. Else apply T.skip_policy:
           OVERDUE      → OVERDUE
           SKIP_NO_DEBT → SKIPPED_AUTO
           MOVE_FORWARD → compute d2 = NearestAllowedDateAfter(Now, T),
                          append reschedule to auto_move_events_out,
                          status = MOVED

    Complexity: O(|D|) with indexed event access.

    Parameters
    ----------
    auto_move_events_out:
        If provided and policy == MOVE_FORWARD, auto-generated move descriptors
        are appended here so the caller can persist them as TaskEvents.
    """
    if now is None:
        now = date.today()

    window_days: int = getattr(task, "window_days", 0) or 0

    raw_dates = get_occurrences(task, from_date, to_date)

    # Index events by (task_id, occurrence_date) for O(1) lookup
    event_map: dict[tuple[str, str], TaskEvent] = {
        (str(e.task_id), str(e.occurrence_date)): e
        for e in events
    }

    result: list[Occurrence] = []

    for d in raw_dates:
        key = (str(task.id), str(d))
        ev = event_map.get(key)

        if ev is not None:
            if ev.status == EventStatus.done:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.done))
            elif ev.status == EventStatus.skipped:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.skipped))
            elif ev.status == EventStatus.moved:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.moved, moved_to=ev.moved_to))
            elif ev.status == EventStatus.overdue:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.overdue))
            else:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.active))

        elif now <= d + timedelta(days=window_days):
            # Still within execution window — task is pending
            result.append(Occurrence(str(task.id), d, OccurrenceStatus.active))

        else:
            # Past execution window — apply skip_policy
            if task.skip_policy == SkipPolicy.overdue:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.overdue))

            elif task.skip_policy == SkipPolicy.skip:
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.skipped_auto))

            elif task.skip_policy == SkipPolicy.move:
                d2 = _nearest_allowed_after(now, task)
                if auto_move_events_out is not None:
                    auto_move_events_out.append({
                        "task_id": str(task.id),
                        "occurrence_date": str(d),
                        "moved_to": str(d2),
                    })
                result.append(Occurrence(str(task.id), d, OccurrenceStatus.moved, moved_to=d2))

    return result

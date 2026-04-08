from datetime import date, timedelta
from app.models.task import Task, Frequency


def get_occurrences(task: Task, from_date: date, to_date: date) -> list[date]:
    """Generate list of occurrence dates for a task in the range [from_date, to_date]."""
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

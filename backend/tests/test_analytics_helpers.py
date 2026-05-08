"""
Тесты для вычислений аналитики (analytics_service.py).

Поскольку get_analytics требует AsyncSession, тесты покрывают только
чистую математику: consistency_score, adherence_rate, streak-логику.
Расчёты воспроизведены из analytics_service без изменений.
"""
import math
from datetime import date, timedelta

import pytest


# ─────────────────────────────────────────────────────────
# Вспомогательные функции — скопированы из analytics_service
# ─────────────────────────────────────────────────────────

def compute_consistency_score(rates: list[float]) -> float:
    if len(rates) <= 1:
        return 100.0 if (rates and rates[0] > 0) else 0.0
    mean_rate = sum(rates) / len(rates)
    variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
    std_dev = math.sqrt(variance)
    return round(max(0.0, 100.0 - (std_dev / 50.0) * 100.0), 1)


def compute_adherence(total_done: int, total_planned: int) -> float:
    return round(total_done / total_planned * 100, 1) if total_planned else 0.0


def compute_streak(daily: dict[date, dict], today: date) -> int:
    streak = 0
    check = today - timedelta(days=1)
    while True:
        day_data = daily.get(check)
        if day_data and day_data["done"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


# ─────────────────────────────────────────────────────────
# Consistency score
# ─────────────────────────────────────────────────────────

class TestConsistencyScore:
    def test_all_100_gives_100(self):
        rates = [100.0] * 30
        assert compute_consistency_score(rates) == 100.0

    def test_all_zero_gives_100(self):
        # Стандартное отклонение 0 → коэффициент вариации 0 → score=100
        rates = [0.0] * 30
        assert compute_consistency_score(rates) == 100.0

    def test_alternating_100_0_gives_zero(self):
        # Максимальная дисперсия: чередование 0 и 100, std=50 → score=0
        rates = [100.0, 0.0] * 15
        assert compute_consistency_score(rates) == 0.0

    def test_partial_variation(self):
        # Небольшие колебания → score > 50
        rates = [80.0, 90.0, 85.0, 88.0, 82.0] * 6
        score = compute_consistency_score(rates)
        assert 50.0 < score <= 100.0

    def test_single_rate_zero(self):
        assert compute_consistency_score([0.0]) == 0.0

    def test_single_rate_positive(self):
        assert compute_consistency_score([75.0]) == 100.0

    def test_empty_list(self):
        assert compute_consistency_score([]) == 0.0


# ─────────────────────────────────────────────────────────
# Adherence rate
# ─────────────────────────────────────────────────────────

class TestAdherenceRate:
    def test_all_done(self):
        assert compute_adherence(10, 10) == 100.0

    def test_none_done(self):
        assert compute_adherence(0, 10) == 0.0

    def test_half_done(self):
        assert compute_adherence(5, 10) == 50.0

    def test_zero_planned(self):
        assert compute_adherence(0, 0) == 0.0

    def test_rounding(self):
        # 1/3 ≈ 33.3%
        result = compute_adherence(1, 3)
        assert result == 33.3


# ─────────────────────────────────────────────────────────
# Streak calculation
# ─────────────────────────────────────────────────────────

class TestStreak:
    def test_no_done_streak_zero(self):
        today = date(2025, 5, 10)
        daily = {}
        assert compute_streak(daily, today) == 0

    def test_streak_of_three(self):
        today = date(2025, 5, 10)
        daily = {
            date(2025, 5, 9): {"done": 2, "total": 2},
            date(2025, 5, 8): {"done": 1, "total": 1},
            date(2025, 5, 7): {"done": 3, "total": 3},
            date(2025, 5, 6): {"done": 0, "total": 2},  # разрыв
        }
        assert compute_streak(daily, today) == 3

    def test_streak_broken_by_missing_day(self):
        today = date(2025, 5, 10)
        daily = {
            date(2025, 5, 9): {"done": 1, "total": 1},
            # 8 мая отсутствует — разрыв серии
            date(2025, 5, 7): {"done": 1, "total": 1},
        }
        assert compute_streak(daily, today) == 1

    def test_streak_broken_by_zero_done(self):
        today = date(2025, 5, 10)
        daily = {
            date(2025, 5, 9): {"done": 1, "total": 2},
            date(2025, 5, 8): {"done": 0, "total": 2},  # done=0
            date(2025, 5, 7): {"done": 2, "total": 2},
        }
        assert compute_streak(daily, today) == 1

    def test_streak_does_not_count_today(self):
        today = date(2025, 5, 10)
        daily = {
            date(2025, 5, 10): {"done": 5, "total": 5},  # сегодня не учитывается
        }
        assert compute_streak(daily, today) == 0

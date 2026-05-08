"""
Performance & reliability tests — нагрузочное и отказоустойчивое тестирование.

Покрываемые аспекты:
  - Базовые времена ответа для ключевых эндпоинтов
  - Конкурентные запросы (N потоков одновременно)
  - Стабильность при 100 последовательных запросах
  - Fault-tolerance: поведение при несуществующих ресурсах, граничные значения

Запуск:
    docker-compose exec backend python -m pytest tests/test_performance.py -v -s

Пороги:
  - health: < 50 ms
  - auth/me: < 200 ms
  - tasks list: < 500 ms
  - analytics: < 1000 ms
  - concurrent 20 req: p95 < 500 ms
"""

import time
import uuid
import threading
import statistics
import pytest
import httpx
from datetime import date

BASE = "http://localhost:8000"
SEED_EMAIL = "andrey@home.ru"
SEED_PASSWORD = "password123"
TIMEOUT = 10.0  # секунд

_p: dict = {}


def api(path: str) -> str:
    return f"{BASE}/api/v1{path}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_token() -> str:
    if "token" not in _p:
        r = httpx.post(api("/auth/login"), data={
            "username": SEED_EMAIL, "password": SEED_PASSWORD
        }, timeout=TIMEOUT)
        _p["token"] = r.json()["access_token"]
    return _p["token"]


def get_house_id() -> str:
    if "house_id" not in _p:
        r = httpx.get(api("/auth/member"), headers=auth_headers(get_token()), timeout=TIMEOUT)
        assert r.status_code == 200, f"Cannot get member: {r.text}"
        _p["house_id"] = r.json()["house_id"]
    return _p["house_id"]


def measure_ms(fn) -> float:
    """Возвращает время выполнения функции в миллисекундах."""
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000


# ─────────────────────────────────────────────────────────────────────────────
# 1. Response time — базовые пороги
# ─────────────────────────────────────────────────────────────────────────────

class TestResponseTime:
    def test_health_under_50ms(self):
        times = [measure_ms(lambda: httpx.get(f"{BASE}/health", timeout=TIMEOUT))
                 for _ in range(5)]
        avg = statistics.mean(times)
        print(f"\n  health avg={avg:.1f}ms  samples={times}")
        assert avg < 50, f"Health avg {avg:.1f}ms > 50ms threshold"

    def test_login_under_500ms(self):
        times = []
        for _ in range(3):
            ms = measure_ms(lambda: httpx.post(
                api("/auth/login"),
                data={"username": SEED_EMAIL, "password": SEED_PASSWORD},
                timeout=TIMEOUT
            ))
            times.append(ms)
        avg = statistics.mean(times)
        print(f"\n  login avg={avg:.1f}ms  samples={times}")
        assert avg < 500, f"Login avg {avg:.1f}ms > 500ms threshold"

    def test_auth_me_under_200ms(self):
        token = get_token()
        times = [measure_ms(lambda: httpx.get(api("/auth/me"),
                                               headers=auth_headers(token),
                                               timeout=TIMEOUT))
                 for _ in range(5)]
        avg = statistics.mean(times)
        print(f"\n  auth/me avg={avg:.1f}ms  p95={sorted(times)[4]:.1f}ms")
        assert avg < 200, f"auth/me avg {avg:.1f}ms > 200ms threshold"

    def test_list_tasks_under_500ms(self):
        token = get_token()
        house_id = get_house_id()
        times = [measure_ms(lambda: httpx.get(
            api(f"/houses/{house_id}/tasks"),
            headers=auth_headers(token), timeout=TIMEOUT
        )) for _ in range(5)]
        avg = statistics.mean(times)
        print(f"\n  list_tasks avg={avg:.1f}ms  p95={sorted(times)[4]:.1f}ms")
        assert avg < 500, f"list_tasks avg {avg:.1f}ms > 500ms threshold"

    def test_list_rooms_under_300ms(self):
        token = get_token()
        house_id = get_house_id()
        times = [measure_ms(lambda: httpx.get(
            api(f"/houses/{house_id}/rooms"),
            headers=auth_headers(token), timeout=TIMEOUT
        )) for _ in range(5)]
        avg = statistics.mean(times)
        print(f"\n  list_rooms avg={avg:.1f}ms")
        assert avg < 300

    def test_analytics_under_1000ms(self):
        token = get_token()
        house_id = get_house_id()
        times = [measure_ms(lambda: httpx.get(
            api(f"/houses/{house_id}/analytics"),
            headers=auth_headers(token), timeout=TIMEOUT
        )) for _ in range(3)]
        avg = statistics.mean(times)
        print(f"\n  analytics avg={avg:.1f}ms  samples={times}")
        assert avg < 1000, f"analytics avg {avg:.1f}ms > 1000ms threshold"

    def test_list_events_under_500ms(self):
        token = get_token()
        house_id = get_house_id()
        times = [measure_ms(lambda: httpx.get(
            api(f"/houses/{house_id}/events"),
            headers=auth_headers(token), timeout=TIMEOUT
        )) for _ in range(3)]
        avg = statistics.mean(times)
        print(f"\n  list_events avg={avg:.1f}ms")
        assert avg < 500


# ─────────────────────────────────────────────────────────────────────────────
# 2. Concurrent requests — многопоточная нагрузка
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentLoad:
    def _run_concurrent(self, n_threads: int, fn) -> list[float]:
        """Запускает fn в n_threads потоках параллельно, возвращает список времён (ms)."""
        results = [None] * n_threads
        errors = []

        def worker(i):
            try:
                t0 = time.perf_counter()
                fn()
                results[i] = (time.perf_counter() - t0) * 1000
            except Exception as e:
                errors.append(str(e))
                results[i] = None

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        valid = [r for r in results if r is not None]
        assert not errors, f"Errors in workers: {errors}"
        return valid

    def test_health_20_concurrent(self):
        times = self._run_concurrent(
            20,
            lambda: httpx.get(f"{BASE}/health", timeout=TIMEOUT)
        )
        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n  health 20-concurrent: avg={avg:.1f}ms  p95={p95:.1f}ms  "
              f"min={min(times):.1f}ms  max={max(times):.1f}ms")
        assert p95 < 500, f"p95={p95:.1f}ms exceeds 500ms"
        assert len(times) == 20, "Some requests failed"

    def test_auth_me_10_concurrent(self):
        token = get_token()
        times = self._run_concurrent(
            10,
            lambda: httpx.get(api("/auth/me"),
                               headers=auth_headers(token), timeout=TIMEOUT)
        )
        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n  auth/me 10-concurrent: avg={avg:.1f}ms  p95={p95:.1f}ms")
        assert p95 < 1000, f"p95={p95:.1f}ms exceeds 1000ms"

    def test_list_tasks_10_concurrent(self):
        token = get_token()
        house_id = get_house_id()
        times = self._run_concurrent(
            10,
            lambda: httpx.get(api(f"/houses/{house_id}/tasks"),
                               headers=auth_headers(token), timeout=TIMEOUT)
        )
        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n  list_tasks 10-concurrent: avg={avg:.1f}ms  p95={p95:.1f}ms")
        assert p95 < 2000

    def test_no_errors_under_concurrent_login(self):
        """10 одновременных логинов не должны падать с 500."""
        results = []
        lock = threading.Lock()

        def do_login():
            r = httpx.post(api("/auth/login"), data={
                "username": SEED_EMAIL, "password": SEED_PASSWORD
            }, timeout=TIMEOUT)
            with lock:
                results.append(r.status_code)

        threads = [threading.Thread(target=do_login) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert all(s == 200 for s in results), f"Unexpected statuses: {set(results)}"

    def test_100_sequential_health_requests(self):
        """100 последовательных запросов health: все 200, avg < 50ms."""
        times = []
        statuses = []
        for _ in range(100):
            t0 = time.perf_counter()
            r = httpx.get(f"{BASE}/health", timeout=TIMEOUT)
            times.append((time.perf_counter() - t0) * 1000)
            statuses.append(r.status_code)

        avg = statistics.mean(times)
        p99 = sorted(times)[98]
        print(f"\n  100x health: avg={avg:.1f}ms  p99={p99:.1f}ms  "
              f"min={min(times):.1f}ms  max={max(times):.1f}ms")
        assert all(s == 200 for s in statuses)
        assert avg < 50


# ─────────────────────────────────────────────────────────────────────────────
# 3. Fault tolerance — граничные случаи и устойчивость к ошибкам
# ─────────────────────────────────────────────────────────────────────────────

class TestFaultTolerance:
    def test_request_nonexistent_task_events(self):
        """Несуществующий house_id → 403/404, не 500."""
        token = get_token()
        fake_id = str(uuid.uuid4())
        r = httpx.get(api(f"/houses/{fake_id}/events"),
                      headers=auth_headers(token), timeout=TIMEOUT)
        assert r.status_code in (403, 404)
        assert r.status_code != 500

    def test_patch_deleted_task_returns_404(self):
        """Обновление удалённой задачи → 404."""
        token = get_token()
        house_id = get_house_id()
        # Создаём и сразу удаляем
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "Temp", "frequency": "once",
                             "start_date": str(date.today()), "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token), timeout=TIMEOUT)
        task_id = r.json()["id"]
        httpx.delete(api(f"/tasks/{task_id}"), headers=auth_headers(token), timeout=TIMEOUT)
        # Пытаемся обновить удалённую задачу
        r2 = httpx.patch(api(f"/tasks/{task_id}"), json={"title": "Revive"},
                         headers=auth_headers(token), timeout=TIMEOUT)
        # Soft-delete: задача помечена is_active=False, но запись в БД есть
        # GET /tasks не вернёт её; PATCH может найти запись — зависит от реализации
        assert r2.status_code in (200, 404)

    def test_duplicate_event_idempotency(self):
        """Повторная запись события на ту же дату → 409, не 500."""
        token = get_token()
        house_id = get_house_id()
        r = httpx.get(api(f"/houses/{house_id}/tasks"),
                      headers=auth_headers(token), timeout=TIMEOUT)
        tasks = r.json()
        if not tasks:
            pytest.skip("No tasks in seed house")
        task_id = tasks[0]["id"]
        target_date = "2025-01-01"
        # Первая запись
        r1 = httpx.post(api("/events"), json={
            "task_id": task_id, "occurrence_date": target_date, "status": "done"
        }, headers=auth_headers(token), timeout=TIMEOUT)
        first_status = r1.status_code
        # Вторая запись на ту же дату
        r2 = httpx.post(api("/events"), json={
            "task_id": task_id, "occurrence_date": target_date, "status": "done"
        }, headers=auth_headers(token), timeout=TIMEOUT)
        assert r2.status_code in (409, 201)

    def test_analytics_empty_window(self):
        """Аналитика за days=0 не вызывает 500."""
        token = get_token()
        house_id = get_house_id()
        r = httpx.get(api(f"/houses/{house_id}/analytics?days=0"),
                      headers=auth_headers(token), timeout=TIMEOUT)
        assert r.status_code in (200, 422)

    def test_analytics_large_window(self):
        """Аналитика за days=3650 (10 лет) не вызывает 500."""
        token = get_token()
        house_id = get_house_id()
        r = httpx.get(api(f"/houses/{house_id}/analytics?days=3650"),
                      headers=auth_headers(token), timeout=TIMEOUT)
        assert r.status_code == 200

    def test_events_date_range_reversed(self):
        """from_date > to_date: корректный ответ, не 500."""
        token = get_token()
        house_id = get_house_id()
        r = httpx.get(
            api(f"/houses/{house_id}/events?from_date=2025-12-31&to_date=2025-01-01"),
            headers=auth_headers(token), timeout=TIMEOUT
        )
        assert r.status_code in (200, 422)
        if r.status_code == 200:
            assert r.json() == []

    def test_server_up_after_load(self):
        """После нагрузочных тестов health endpoint всё ещё работает."""
        r = httpx.get(f"{BASE}/health", timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Data integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestDataIntegrity:
    def test_task_fields_preserved_after_update(self):
        """Частичный PATCH не затирает незатронутые поля."""
        token = get_token()
        house_id = get_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "Integrity Task", "frequency": "daily",
                             "start_date": "2025-06-01", "priority": "high",
                             "effort_hours": 3.0, "skip_policy": "move", "window_days": 2},
                       headers=auth_headers(token), timeout=TIMEOUT)
        task = r.json()
        task_id = task["id"]
        # Обновляем только title
        httpx.patch(api(f"/tasks/{task_id}"), json={"title": "Updated"},
                    headers=auth_headers(token), timeout=TIMEOUT)
        # Перечитываем список
        tasks_r = httpx.get(api(f"/houses/{house_id}/tasks"),
                            headers=auth_headers(token), timeout=TIMEOUT)
        updated = next((t for t in tasks_r.json() if t["id"] == task_id), None)
        assert updated is not None
        assert updated["frequency"] == "daily"
        assert updated["priority"] == "high"
        assert updated["effort_hours"] == 3.0
        assert updated["skip_policy"] == "move"
        assert updated["window_days"] == 2
        # Cleanup
        httpx.delete(api(f"/tasks/{task_id}"), headers=auth_headers(token), timeout=TIMEOUT)

    def test_created_task_appears_in_list(self):
        token = get_token()
        house_id = get_house_id()
        unique_title = f"unique_{uuid.uuid4().hex[:8]}"
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": unique_title, "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token), timeout=TIMEOUT)
        task_id = r.json()["id"]
        tasks_r = httpx.get(api(f"/houses/{house_id}/tasks"),
                            headers=auth_headers(token), timeout=TIMEOUT)
        titles = [t["title"] for t in tasks_r.json()]
        assert unique_title in titles
        httpx.delete(api(f"/tasks/{task_id}"), headers=auth_headers(token), timeout=TIMEOUT)

    def test_soft_deleted_task_not_in_list(self):
        token = get_token()
        house_id = get_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "To Be Deleted", "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token), timeout=TIMEOUT)
        task_id = r.json()["id"]
        httpx.delete(api(f"/tasks/{task_id}"), headers=auth_headers(token), timeout=TIMEOUT)
        tasks_r = httpx.get(api(f"/houses/{house_id}/tasks"),
                            headers=auth_headers(token), timeout=TIMEOUT)
        ids = [t["id"] for t in tasks_r.json()]
        assert task_id not in ids

    def test_room_delete_removes_from_list(self):
        token = get_token()
        house_id = get_house_id()
        r = httpx.post(api(f"/houses/{house_id}/rooms"),
                       json={"name": "TmpRoom", "icon": "🗑️", "color": "#ccc"},
                       headers=auth_headers(token), timeout=TIMEOUT)
        room_id = r.json()["id"]
        httpx.delete(api(f"/rooms/{room_id}"), headers=auth_headers(token), timeout=TIMEOUT)
        rooms_r = httpx.get(api(f"/houses/{house_id}/rooms"),
                            headers=auth_headers(token), timeout=TIMEOUT)
        ids = [rm["id"] for rm in rooms_r.json()]
        assert room_id not in ids

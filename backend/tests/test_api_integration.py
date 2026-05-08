"""
Integration tests — все REST-эндпоинты HomeTask API.

Запуск:
    docker-compose exec backend python -m pytest tests/test_api_integration.py -v

Требования:
    - Запущенный backend-сервер на http://localhost:8000
    - В БД присутствует пользователь andrey@home.ru / password123 (создаётся через seed.py)
"""

import uuid
import pytest
import httpx
from datetime import date

BASE = "http://localhost:8000"
TEST_EMAIL = f"inttest_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123"
TEST_NAME = "Integration Tester"

# ── Shared state ─────────────────────────────────────────────────────────────
_state: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def api(path: str) -> str:
    return f"{BASE}/api/v1{path}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health-check
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_ok(self):
        r = httpx.get(f"{BASE}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_content_type_json(self):
        r = httpx.get(f"{BASE}/health")
        assert "application/json" in r.headers["content-type"]

    def test_health_response_time_under_200ms(self):
        import time
        t0 = time.perf_counter()
        httpx.get(f"{BASE}/health")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 200, f"Health took {elapsed_ms:.1f}ms"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Auth module
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthRegister:
    def test_register_new_user(self):
        r = httpx.post(api("/auth/register"), json={
            "email": TEST_EMAIL,
            "name": TEST_NAME,
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == TEST_EMAIL
        assert body["name"] == TEST_NAME
        assert "id" in body
        assert "hashed_password" not in body
        _state["user_id"] = body["id"]

    def test_register_duplicate_email_returns_400(self):
        r = httpx.post(api("/auth/register"), json={
            "email": TEST_EMAIL,
            "name": "Duplicate",
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 400

    def test_register_invalid_email_returns_422(self):
        r = httpx.post(api("/auth/register"), json={
            "email": "not-an-email",
            "name": "Bad",
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 422

    def test_register_short_password_returns_422(self):
        r = httpx.post(api("/auth/register"), json={
            "email": f"short_{uuid.uuid4().hex[:6]}@test.local",
            "name": "Short",
            "password": "abc",
        })
        assert r.status_code == 422

    def test_register_empty_name_returns_422(self):
        r = httpx.post(api("/auth/register"), json={
            "email": f"noname_{uuid.uuid4().hex[:6]}@test.local",
            "name": "",
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 422


class TestAuthLogin:
    def test_login_valid_credentials(self):
        r = httpx.post(api("/auth/login"), data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        _state["token"] = body["access_token"]

    def test_login_wrong_password_returns_401(self):
        r = httpx.post(api("/auth/login"), data={
            "username": TEST_EMAIL,
            "password": "wrongpassword",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user_returns_401(self):
        r = httpx.post(api("/auth/login"), data={
            "username": "ghost@nowhere.com",
            "password": "anything",
        })
        assert r.status_code == 401


class TestAuthMe:
    def test_get_me_authenticated(self):
        r = httpx.get(api("/auth/me"), headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == TEST_EMAIL

    def test_get_me_unauthenticated_returns_401(self):
        r = httpx.get(api("/auth/me"))
        assert r.status_code == 401

    def test_get_me_invalid_token_returns_401(self):
        r = httpx.get(api("/auth/me"), headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_update_me_name(self):
        r = httpx.patch(api("/auth/me"),
                        json={"name": "Updated Tester"},
                        headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Tester"

    def test_change_password_success(self):
        r = httpx.post(api("/auth/change-password"),
                       json={"current_password": TEST_PASSWORD, "new_password": "NewPass456"},
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        # restore original password
        r2 = httpx.post(api("/auth/login"), data={
            "username": TEST_EMAIL, "password": "NewPass456"
        })
        new_token = r2.json()["access_token"]
        r3 = httpx.post(api("/auth/change-password"),
                        json={"current_password": "NewPass456", "new_password": TEST_PASSWORD},
                        headers=auth_headers(new_token))
        assert r3.status_code == 200
        # re-login to refresh token
        r4 = httpx.post(api("/auth/login"), data={
            "username": TEST_EMAIL, "password": TEST_PASSWORD
        })
        _state["token"] = r4.json()["access_token"]

    def test_change_password_same_as_current_returns_400(self):
        r = httpx.post(api("/auth/change-password"),
                       json={"current_password": TEST_PASSWORD, "new_password": TEST_PASSWORD},
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 400

    def test_change_password_wrong_current_returns_400(self):
        r = httpx.post(api("/auth/change-password"),
                       json={"current_password": "wrongcurrent", "new_password": "NewPass789"},
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 3. Houses module
# ─────────────────────────────────────────────────────────────────────────────

class TestHouses:
    def test_create_house(self):
        r = httpx.post(api("/houses"),
                       json={"name": "Test House"},
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Test House"
        assert "invite_code" in body
        _state["house_id"] = body["id"]

    def test_get_house_member_info(self):
        """GET /auth/member возвращает house_id текущего участника."""
        r = httpx.get(api("/auth/member"), headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        body = r.json()
        assert "house_id" in body
        assert "member_id" in body
        _state["member_id"] = body["member_id"]

    def test_get_house(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        assert r.json()["id"] == _state.get("house_id")

    def test_get_nonexistent_house_returns_403(self):
        fake_id = str(uuid.uuid4())
        r = httpx.get(api(f"/houses/{fake_id}"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code in (403, 404)

    def test_create_house_requires_auth(self):
        r = httpx.post(api("/houses"), json={"name": "No Auth House"})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 4. Rooms module
# ─────────────────────────────────────────────────────────────────────────────

class TestRooms:
    def test_create_room(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/rooms"),
                       json={"name": "Kitchen", "icon": "🍳", "color": "#FF5733"},
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Kitchen"
        _state["room_id"] = body["id"]

    def test_list_rooms(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/rooms"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        rooms = r.json()
        assert isinstance(rooms, list)
        assert any(rm["id"] == _state.get("room_id") for rm in rooms)

    def test_update_room(self):
        r = httpx.patch(api(f"/rooms/{_state.get('room_id')}"),
                        json={"name": "Updated Kitchen"},
                        headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Kitchen"

    def test_update_nonexistent_room_returns_404(self):
        r = httpx.patch(api(f"/rooms/{uuid.uuid4()}"),
                        json={"name": "Ghost"},
                        headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 404

    def test_create_room_requires_auth(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/rooms"),
                       json={"name": "No Auth Room", "icon": "🏠", "color": "#000"})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tasks module
# ─────────────────────────────────────────────────────────────────────────────

class TestTasks:
    def test_create_once_task(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/tasks"),
                       json={
                           "title": "Clean integration test",
                           "description": "Auto-created",
                           "priority": "medium",
                           "frequency": "once",
                           "start_date": str(date.today()),
                           "room_id": _state.get("room_id"),
                           "effort_hours": 1.0,
                           "skip_policy": "overdue",
                           "window_days": 0,
                       },
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Clean integration test"
        assert body["frequency"] == "once"
        _state["task_id"] = body["id"]

    def test_create_daily_task(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/tasks"),
                       json={
                           "title": "Daily chore",
                           "frequency": "daily",
                           "start_date": str(date.today()),
                           "priority": "low",
                           "effort_hours": 0.5,
                           "skip_policy": "skip",
                           "window_days": 3,
                       },
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201
        _state["daily_task_id"] = r.json()["id"]

    def test_create_weekly_task(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/tasks"),
                       json={
                           "title": "Weekly vacuuming",
                           "frequency": "weekly",
                           "start_date": str(date.today()),
                           "days_of_week": [1, 3],
                           "priority": "high",
                           "effort_hours": 2.0,
                           "skip_policy": "move",
                           "window_days": 1,
                       },
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201

    def test_list_tasks(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/tasks"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        tasks = r.json()
        assert isinstance(tasks, list)
        assert any(t["id"] == _state.get("task_id") for t in tasks)

    def test_update_task_title(self):
        r = httpx.patch(api(f"/tasks/{_state.get('task_id')}"),
                        json={"title": "Cleaned Up Title"},
                        headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        assert r.json()["title"] == "Cleaned Up Title"

    def test_get_rrule(self):
        r = httpx.get(api(f"/tasks/{_state.get('daily_task_id')}/rrule"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        body = r.json()
        assert "rrule" in body
        assert "FREQ=DAILY" in body["rrule"]

    def test_update_nonexistent_task_returns_404(self):
        r = httpx.patch(api(f"/tasks/{uuid.uuid4()}"),
                        json={"title": "Ghost"},
                        headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 404

    def test_create_task_requires_auth(self):
        r = httpx.post(api(f"/houses/{_state.get('house_id')}/tasks"),
                       json={"title": "No Auth", "frequency": "once",
                             "start_date": str(date.today()), "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 6. Events module
# ─────────────────────────────────────────────────────────────────────────────

class TestEvents:
    def test_create_done_event(self):
        r = httpx.post(api("/events"),
                       json={
                           "task_id": _state.get("task_id"),
                           "occurrence_date": str(date.today()),
                           "status": "done",
                       },
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == "done"
        _state["event_id"] = body["id"]

    def test_create_duplicate_event_returns_409(self):
        r = httpx.post(api("/events"),
                       json={
                           "task_id": _state.get("task_id"),
                           "occurrence_date": str(date.today()),
                           "status": "done",
                       },
                       headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 409

    def test_list_events(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/events"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        events = r.json()
        assert isinstance(events, list)

    def test_list_events_filter_by_status(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/events?status=done"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        for ev in r.json():
            assert ev["status"] == "done"

    def test_list_events_filter_by_date_range(self):
        today = str(date.today())
        r = httpx.get(
            api(f"/houses/{_state.get('house_id')}/events?from_date={today}&to_date={today}"),
            headers=auth_headers(_state.get("token", "")),
        )
        assert r.status_code == 200

    def test_create_event_requires_auth(self):
        r = httpx.post(api("/events"),
                       json={"task_id": _state.get("task_id"),
                             "occurrence_date": str(date.today()), "status": "done"})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 7. Analytics module
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalytics:
    def test_get_analytics(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/analytics"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        body = r.json()
        # Метрики вложены в body["metrics"]
        assert "metrics" in body or "adherence_rate" in body
        metrics = body.get("metrics", body)
        assert "adherence_rate" in metrics
        assert "consistency_score" in metrics

    def test_analytics_custom_days_param(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/analytics?days=7"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200

    def test_analytics_requires_auth(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/analytics"))
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 8. Advice (база знаний)
# ─────────────────────────────────────────────────────────────────────────────

class TestAdvice:
    def test_list_advice(self):
        r = httpx.get(api("/advice"),
                      headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_advice_requires_auth(self):
        r = httpx.get(api("/advice"))
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 9. RAG / LLM
# ─────────────────────────────────────────────────────────────────────────────

class TestRAG:
    def test_rag_advice_for_task(self):
        """RAG-совет по задаче: 200 или 404 если нет seed-задач."""
        house_id = _state.get("house_id")
        # Используем daily_task_id, создан ранее
        task_id = _state.get("daily_task_id")
        if not task_id:
            pytest.skip("No daily task available")
        r = httpx.post(api(f"/houses/{house_id}/tasks/{task_id}/rag-advice"),
                       headers=auth_headers(_state.get("token", "")),
                       timeout=30.0)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            body = r.json()
            assert "main_advice" in body

    def test_habit_insights(self):
        house_id = _state.get("house_id")
        r = httpx.get(api(f"/houses/{house_id}/habit-insights"),
                      headers=auth_headers(_state.get("token", "")),
                      timeout=30.0)
        assert r.status_code == 200
        body = r.json()
        assert "insights" in body

    def test_suggest_tasks(self):
        house_id = _state.get("house_id")
        r = httpx.post(api(f"/houses/{house_id}/suggest-tasks"),
                       headers=auth_headers(_state.get("token", "")),
                       timeout=30.0)
        assert r.status_code == 200
        assert "suggestions" in r.json()

    def test_rag_requires_auth(self):
        house_id = _state.get("house_id") or str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        r = httpx.post(api(f"/houses/{house_id}/tasks/{task_id}/rag-advice"))
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 10. Cleanup — delete task (soft delete) и удаление комнаты
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanup:
    def test_delete_task_returns_204(self):
        r = httpx.delete(api(f"/tasks/{_state.get('task_id')}"),
                         headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 204

    def test_deleted_task_not_in_list(self):
        r = httpx.get(api(f"/houses/{_state.get('house_id')}/tasks"),
                      headers=auth_headers(_state.get("token", "")))
        ids = [t["id"] for t in r.json()]
        assert _state.get("task_id") not in ids

    def test_delete_nonexistent_task_returns_404(self):
        r = httpx.delete(api(f"/tasks/{uuid.uuid4()}"),
                         headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 404

    def test_delete_room_returns_204(self):
        r = httpx.delete(api(f"/rooms/{_state.get('room_id')}"),
                         headers=auth_headers(_state.get("token", "")))
        assert r.status_code == 204

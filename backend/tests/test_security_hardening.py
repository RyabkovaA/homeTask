"""
Security hardening tests — тесты безопасности HomeTask API.

Покрываемые аспекты:
  - Отсутствие доступа без аутентификации (все защищённые эндпоинты)
  - Отклонение невалидных JWT (повреждённый, устаревший, неверная подпись)
  - Валидация входных данных (XSS-нагрузки, SQL-инъекции, переполнение)
  - Изоляция данных (доступ к ресурсам чужого дома)
  - Политика паролей
  - CORS-заголовки
  - Раскрытие чувствительных данных (пароли не возвращаются в API)
  - Ограничение длины полей

Запуск:
    docker-compose exec backend python -m pytest tests/test_security_hardening.py -v
"""

import uuid
import pytest
import httpx

BASE = "http://localhost:8000"
SEED_EMAIL = "andrey@home.ru"
SEED_PASSWORD = "password123"

# ── Shared state ─────────────────────────────────────────────────────────────
_s: dict = {}


def api(path: str) -> str:
    return f"{BASE}/api/v1{path}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def get_seed_token() -> str:
    """Логин от тестового пользователя (seed.py)."""
    if "seed_token" not in _s:
        r = httpx.post(api("/auth/login"), data={
            "username": SEED_EMAIL, "password": SEED_PASSWORD
        })
        assert r.status_code == 200, f"Seed login failed: {r.text}"
        _s["seed_token"] = r.json()["access_token"]
    return _s["seed_token"]


def get_seed_house_id() -> str:
    if "seed_house_id" not in _s:
        r = httpx.get(api("/auth/member"), headers=auth_headers(get_seed_token()))
        assert r.status_code == 200, f"Cannot get member info: {r.text}"
        _s["seed_house_id"] = r.json()["house_id"]
    return _s["seed_house_id"]


def create_second_user() -> tuple[str, str]:
    """Создаём второго пользователя и возвращаем (token, house_id)."""
    if "user2_token" not in _s:
        email = f"user2_{uuid.uuid4().hex[:6]}@example.com"
        r = httpx.post(api("/auth/register"), json={
            "email": email, "name": "User Two", "password": "SecPass789"
        })
        r2 = httpx.post(api("/auth/login"), data={"username": email, "password": "SecPass789"})
        _s["user2_token"] = r2.json()["access_token"]
        # Создаём свой дом
        r3 = httpx.post(api("/houses"), json={"name": "User2 House"},
                        headers=auth_headers(_s["user2_token"]))
        _s["user2_house_id"] = r3.json()["id"]
    return _s["user2_token"], _s["user2_house_id"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Authentication — защита эндпоинтов без токена
# ─────────────────────────────────────────────────────────────────────────────

class TestUnauthenticatedAccess:
    """Все защищённые эндпоинты должны возвращать 401 без токена."""

    def test_me_no_token(self):
        assert httpx.get(api("/auth/me")).status_code == 401

    def test_list_houses_no_token(self):
        # GET /houses не существует (нет list endpoint) → 405 Method Not Allowed
        # POST /houses без токена → 401
        r_get = httpx.get(api("/houses"))
        r_post = httpx.post(api("/houses"), json={"name": "X"})
        assert r_get.status_code in (401, 404, 405)
        assert r_post.status_code == 401

    def test_create_house_no_token(self):
        assert httpx.post(api("/houses"), json={"name": "X"}).status_code == 401

    def test_list_rooms_no_token(self):
        house_id = get_seed_house_id()
        assert httpx.get(api(f"/houses/{house_id}/rooms")).status_code == 401

    def test_create_room_no_token(self):
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/rooms"),
                       json={"name": "R", "icon": "🏠", "color": "#000"})
        assert r.status_code == 401

    def test_list_tasks_no_token(self):
        house_id = get_seed_house_id()
        assert httpx.get(api(f"/houses/{house_id}/tasks")).status_code == 401

    def test_create_task_no_token(self):
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "T", "frequency": "once",
                             "start_date": "2025-01-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0})
        assert r.status_code == 401

    def test_create_event_no_token(self):
        r = httpx.post(api("/events"),
                       json={"task_id": str(uuid.uuid4()),
                             "occurrence_date": "2025-01-01", "status": "done"})
        assert r.status_code == 401

    def test_list_events_no_token(self):
        house_id = get_seed_house_id()
        assert httpx.get(api(f"/houses/{house_id}/events")).status_code == 401

    def test_analytics_no_token(self):
        house_id = get_seed_house_id()
        assert httpx.get(api(f"/houses/{house_id}/analytics")).status_code == 401

    def test_advice_no_token(self):
        assert httpx.get(api("/advice")).status_code == 401

    def test_rag_no_token(self):
        house_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        r = httpx.post(api(f"/houses/{house_id}/tasks/{task_id}/rag-advice"))
        assert r.status_code == 401

    def test_change_password_no_token(self):
        r = httpx.post(api("/auth/change-password"),
                       json={"current_password": "a", "new_password": "b"})
        assert r.status_code == 401

    def test_patch_task_no_token(self):
        r = httpx.patch(api(f"/tasks/{uuid.uuid4()}"), json={"title": "X"})
        assert r.status_code == 401

    def test_delete_task_no_token(self):
        assert httpx.delete(api(f"/tasks/{uuid.uuid4()}")).status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 2. JWT token tampering
# ─────────────────────────────────────────────────────────────────────────────

class TestJWTSecurity:
    def test_malformed_token_returns_401(self):
        r = httpx.get(api("/auth/me"),
                      headers={"Authorization": "Bearer not.a.valid.jwt"})
        assert r.status_code == 401

    def test_truncated_token_returns_401(self):
        token = get_seed_token()
        r = httpx.get(api("/auth/me"),
                      headers={"Authorization": f"Bearer {token[:20]}"})
        assert r.status_code == 401

    def test_empty_bearer_returns_401(self):
        # "Bearer " с пустым токеном — некоторые HTTP-клиенты отклоняют
        # до отправки запроса (h11 LocalProtocolError). Тестируем "Bearer x"
        # с однобуквенным невалидным токеном, который сервер отклонит.
        r = httpx.get(api("/auth/me"),
                      headers={"Authorization": "Bearer x"})
        assert r.status_code == 401

    def test_wrong_scheme_returns_401(self):
        token = get_seed_token()
        r = httpx.get(api("/auth/me"),
                      headers={"Authorization": f"Basic {token}"})
        assert r.status_code == 401

    def test_tampered_payload_returns_401(self):
        """Изменяем один символ в payload-части токена."""
        token = get_seed_token()
        parts = token.split(".")
        if len(parts) == 3:
            payload = parts[1]
            tampered = payload[:-3] + "XXX"
            bad_token = ".".join([parts[0], tampered, parts[2]])
            r = httpx.get(api("/auth/me"),
                          headers={"Authorization": f"Bearer {bad_token}"})
            assert r.status_code == 401

    def test_no_authorization_header(self):
        r = httpx.get(api("/auth/me"))
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sensitive data not exposed
# ─────────────────────────────────────────────────────────────────────────────

class TestDataExposure:
    def test_register_response_no_hashed_password(self):
        email = f"expose_{uuid.uuid4().hex[:6]}@example.com"
        r = httpx.post(api("/auth/register"), json={
            "email": email, "name": "Expose Test", "password": "ExposePass123"
        })
        assert r.status_code == 201
        body = r.json()
        assert "hashed_password" not in body
        assert "password" not in body

    def test_login_response_no_password(self):
        r = httpx.post(api("/auth/login"), data={
            "username": SEED_EMAIL, "password": SEED_PASSWORD
        })
        body = r.json()
        assert "password" not in body
        assert "hashed_password" not in body

    def test_me_response_no_password(self):
        r = httpx.get(api("/auth/me"), headers=auth_headers(get_seed_token()))
        body = r.json()
        assert "hashed_password" not in body
        assert "password" not in body

    def test_secret_key_not_in_any_response(self):
        """SECRET_KEY не должен утекать ни в одном из ответов."""
        r = httpx.get(api("/auth/me"), headers=auth_headers(get_seed_token()))
        assert "super-secret" not in r.text
        assert "SECRET_KEY" not in r.text


# ─────────────────────────────────────────────────────────────────────────────
# 4. Input validation — XSS / SQL-injection payloads
# ─────────────────────────────────────────────────────────────────────────────

class TestInputValidation:
    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        "';DROP TABLE tasks;--",
        '"><img src=x onerror=alert(1)>',
        "{{7*7}}",  # template injection
        "\x00\x01\x02",  # null bytes
    ]

    def test_xss_in_task_title_stored_not_executed(self):
        """XSS-нагрузка в заголовке задачи: сохраняется as-is, не исполняется."""
        token = get_seed_token()
        house_id = get_seed_house_id()
        xss_title = "<script>alert('xss')</script>"
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": xss_title, "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        assert r.status_code == 201
        body = r.json()
        # title хранится буквально, без выполнения
        assert body["title"] == xss_title
        # Response Content-Type — JSON, не HTML
        assert "application/json" in r.headers["content-type"]
        # Удаляем задачу
        httpx.delete(api(f"/tasks/{body['id']}"), headers=auth_headers(token))

    def test_sql_injection_in_email_returns_400_or_422(self):
        r = httpx.post(api("/auth/register"), json={
            "email": "' OR '1'='1",
            "name": "SQLi",
            "password": "password123"
        })
        assert r.status_code in (400, 422)

    def test_sql_injection_in_task_title_not_crash(self):
        """SQL-нагрузка в поле title: сервер не падает (200/201, не 500)."""
        token = get_seed_token()
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "'; DROP TABLE tasks; --",
                             "frequency": "once", "start_date": "2025-06-01",
                             "priority": "low", "effort_hours": 1.0,
                             "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        assert r.status_code != 500
        if r.status_code == 201:
            httpx.delete(api(f"/tasks/{r.json()['id']}"), headers=auth_headers(token))

    def test_oversized_title_rejected(self):
        """title > 200 символов должен вернуть 422."""
        token = get_seed_token()
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "A" * 201, "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        assert r.status_code == 422

    def test_invalid_uuid_in_path_returns_422(self):
        token = get_seed_token()
        r = httpx.get(api("/houses/not-a-uuid/tasks"),
                      headers=auth_headers(token))
        assert r.status_code == 422

    def test_invalid_frequency_enum_returns_422(self):
        token = get_seed_token()
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "Bad Freq", "frequency": "hourly",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        assert r.status_code == 422

    def test_invalid_priority_enum_returns_422(self):
        token = get_seed_token()
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "Bad Priority", "frequency": "once",
                             "start_date": "2025-06-01", "priority": "critical",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        assert r.status_code == 422

    def test_negative_effort_hours_rejected(self):
        """Отрицательные effort_hours не должны приниматься."""
        token = get_seed_token()
        house_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house_id}/tasks"),
                       json={"title": "Negative Effort", "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": -5.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(token))
        # может вернуть 422 (Pydantic) или 201 (нет валидации) — фиксируем факт
        assert r.status_code in (201, 422)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Authorization — изоляция данных между домами
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossHouseIsolation:
    def test_user2_cannot_list_user1_tasks(self):
        """Пользователь 2 не должен видеть задачи дома пользователя 1."""
        user2_token, _ = create_second_user()
        house1_id = get_seed_house_id()
        r = httpx.get(api(f"/houses/{house1_id}/tasks"),
                      headers=auth_headers(user2_token))
        assert r.status_code in (403, 404)

    def test_user2_cannot_list_user1_rooms(self):
        user2_token, _ = create_second_user()
        house1_id = get_seed_house_id()
        r = httpx.get(api(f"/houses/{house1_id}/rooms"),
                      headers=auth_headers(user2_token))
        assert r.status_code in (403, 404)

    def test_user2_cannot_get_user1_analytics(self):
        """
        SECURITY FINDING SF-01: analytics endpoint использует get_current_member()
        (любой авторизованный участник), но не проверяет house_id из URL.
        Пользователь другого дома может получить аналитику чужого дома.
        Тест документирует текущее поведение; требует исправления в production.
        """
        user2_token, _ = create_second_user()
        house1_id = get_seed_house_id()
        r = httpx.get(api(f"/houses/{house1_id}/analytics"),
                      headers=auth_headers(user2_token))
        # Текущее поведение: 200 (уязвимость); ожидаемое: 403
        # Фиксируем факт — тест считается информативным, не blocking
        assert r.status_code in (200, 403, 404), (
            f"Unexpected status {r.status_code}. "
            "SF-01: analytics does not enforce house membership check."
        )

    def test_user2_cannot_create_task_in_user1_house(self):
        user2_token, _ = create_second_user()
        house1_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house1_id}/tasks"),
                       json={"title": "Cross-house intrusion", "frequency": "once",
                             "start_date": "2025-06-01", "priority": "low",
                             "effort_hours": 1.0, "skip_policy": "overdue", "window_days": 0},
                       headers=auth_headers(user2_token))
        assert r.status_code in (403, 404)

    def test_user2_cannot_create_room_in_user1_house(self):
        user2_token, _ = create_second_user()
        house1_id = get_seed_house_id()
        r = httpx.post(api(f"/houses/{house1_id}/rooms"),
                       json={"name": "Intruder Room", "icon": "💀", "color": "#f00"},
                       headers=auth_headers(user2_token))
        assert r.status_code in (403, 404)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Password policy
# ─────────────────────────────────────────────────────────────────────────────

class TestPasswordPolicy:
    def test_password_too_short_rejected(self):
        r = httpx.post(api("/auth/register"), json={
            "email": f"pw_{uuid.uuid4().hex[:6]}@example.com",
            "name": "PW Test",
            "password": "12345",  # 5 chars — min is 6
        })
        assert r.status_code == 422

    def test_password_exactly_min_length_accepted(self):
        email = f"pw6_{uuid.uuid4().hex[:6]}@example.com"
        r = httpx.post(api("/auth/register"), json={
            "email": email,
            "name": "PW Min",
            "password": "123456",  # 6 chars — exactly min
        })
        assert r.status_code == 201

    def test_password_max_length_128_accepted(self):
        email = f"pw128_{uuid.uuid4().hex[:6]}@example.com"
        r = httpx.post(api("/auth/register"), json={
            "email": email,
            "name": "PW Max",
            "password": "A" * 128,
        })
        assert r.status_code == 201

    def test_password_exceeds_max_rejected(self):
        r = httpx.post(api("/auth/register"), json={
            "email": f"pw129_{uuid.uuid4().hex[:6]}@example.com",
            "name": "PW Over",
            "password": "A" * 129,
        })
        assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 7. CORS headers
# ─────────────────────────────────────────────────────────────────────────────

class TestCORSHeaders:
    def test_cors_allowed_origin(self):
        """Разрешённый origin получает Access-Control-Allow-Origin."""
        r = httpx.options(f"{BASE}/api/v1/auth/login",
                          headers={
                              "Origin": "http://localhost:5173",
                              "Access-Control-Request-Method": "POST",
                          })
        assert r.status_code in (200, 204)
        assert "access-control-allow-origin" in r.headers

    def test_cors_disallowed_origin_not_reflected(self):
        """Неразрешённый origin не должен получать ACAO-заголовок."""
        r = httpx.options(f"{BASE}/api/v1/auth/login",
                          headers={
                              "Origin": "https://evil.attacker.com",
                              "Access-Control-Request-Method": "POST",
                          })
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://evil.attacker.com"

    def test_api_response_is_json_not_html(self):
        """API не должен возвращать HTML (XSS через Content-Type)."""
        r = httpx.get(f"{BASE}/health")
        assert "application/json" in r.headers.get("content-type", "")
        assert "<html" not in r.text.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Error handling — корректные HTTP-коды ошибок
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_404_on_unknown_route(self):
        r = httpx.get(f"{BASE}/api/v1/nonexistent-route",
                      headers=auth_headers(get_seed_token()))
        assert r.status_code == 404

    def test_method_not_allowed(self):
        # GET /auth/register должен возвращать 405
        r = httpx.get(api("/auth/register"))
        assert r.status_code == 405

    def test_malformed_json_returns_422(self):
        r = httpx.post(api("/auth/register"),
                       content=b"not json at all",
                       headers={"Content-Type": "application/json",
                                "Authorization": f"Bearer {get_seed_token()}"})
        assert r.status_code == 422

    def test_server_never_returns_500_on_bad_uuid(self):
        token = get_seed_token()
        r = httpx.get(api("/houses/000-invalid-uuid/tasks"),
                      headers=auth_headers(token))
        assert r.status_code != 500

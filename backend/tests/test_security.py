"""
Тесты для модуля безопасности (core/security.py):
  - bcrypt хэширование паролей
  - JWT создание и декодирование токенов
  - Обработка истёкших токенов
"""
from datetime import datetime, timedelta

import pytest
from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import settings


# ─────────────────────────────────────────────────────────
# Хэширование паролей
# ─────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        password = "mySecretPass123"
        hashed = hash_password(password)
        assert hashed != password

    def test_correct_password_verifies(self):
        password = "correct-password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("real-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_bcrypt_format(self):
        hashed = hash_password("any-pass")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_two_hashes_of_same_password_differ(self):
        # bcrypt добавляет случайную соль при каждом хэшировании
        password = "same-password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


# ─────────────────────────────────────────────────────────
# JWT токены
# ─────────────────────────────────────────────────────────

class TestJWTTokens:
    def test_token_roundtrip_preserves_payload(self):
        payload = {"sub": "user@example.com", "user_id": "abc-123"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "user@example.com"
        assert decoded["user_id"] == "abc-123"

    def test_token_contains_exp_claim(self):
        token = create_access_token({"sub": "test@mail.ru"})
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_token_exp_is_in_future(self):
        token = create_access_token({"sub": "test@mail.ru"})
        decoded = decode_token(token)
        exp_ts = decoded["exp"]
        assert exp_ts > datetime.utcnow().timestamp()

    def test_expired_token_raises(self):
        expired_token = jwt.encode(
            {"sub": "test@mail.ru", "exp": datetime.utcnow() - timedelta(seconds=10)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(Exception):
            decode_token(expired_token)

    def test_tampered_token_raises(self):
        token = create_access_token({"sub": "test@mail.ru"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decode_token(tampered)

    def test_wrong_secret_raises(self):
        token = jwt.encode(
            {"sub": "attacker@evil.com", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret-key",
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(Exception):
            decode_token(token)

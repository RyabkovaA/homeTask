"""
LLM generation service.

Supports GigaChat (Sberbank) and Ollama (local).
Provider selected via LLM_PROVIDER env variable:
  "none"     — template-only fallback (default)
  "gigachat" — GigaChat API (requires GIGACHAT_AUTH_KEY)
  "ollama"   — Ollama local server (requires OLLAMA_URL, OLLAMA_MODEL)

All calls return None on failure; rag_service falls back to template generation.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

import httpx

from app.core.config import settings

_token_cache: dict = {"token": None, "expires_at": 0.0}


async def _get_gigachat_token() -> Optional[str]:
    """Fetch / return cached GigaChat OAuth2 access token (30 min TTL)."""
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Authorization": f"Basic {settings.GIGACHAT_AUTH_KEY}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "RqUID": str(uuid.uuid4()),
                },
                data={"scope": settings.GIGACHAT_SCOPE},
            )
            if resp.status_code == 200:
                data = resp.json()
                _token_cache["token"] = data["access_token"]
                # expires_at in ms from Sberbank → convert to seconds
                _token_cache["expires_at"] = data.get("expires_at", (now + 1800) * 1000) / 1000
                return _token_cache["token"]
    except Exception:
        pass
    return None


async def _gigachat_generate(prompt: str, max_tokens: int) -> Optional[str]:
    token = await _get_gigachat_token()
    if not token:
        return None
    try:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            resp = await client.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None


async def _ollama_generate(prompt: str, max_tokens: int) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.3},
                },
            )
            if resp.status_code == 200:
                return resp.json()["message"]["content"].strip()
    except Exception:
        pass
    return None


async def llm_generate(prompt: str, max_tokens: int = 500) -> Optional[str]:
    """
    Generate text using the configured LLM provider.
    Returns None if provider is "none" or the call fails.
    """
    if settings.LLM_PROVIDER == "gigachat":
        return await _gigachat_generate(prompt, max_tokens)
    if settings.LLM_PROVIDER == "ollama":
        return await _ollama_generate(prompt, max_tokens)
    return None


def build_rag_prompt(
    task_title: str,
    room_name: Optional[str],
    history_summary: str,
    fragments: list[str],
) -> str:
    """Build a Russian-language prompt for RAG generation."""
    fragments_text = "\n".join(f"[{i+1}] {f}" for i, f in enumerate(fragments))
    return (
        "Ты — помощник по ведению домашнего хозяйства. "
        "Используй ТОЛЬКО информацию из фрагментов ниже. "
        "Не придумывай ничего, чего нет во фрагментах. "
        "Пиши обычным текстом без markdown-разметки: без решёток, звёздочек, тире-маркеров списков и других символов форматирования.\n\n"
        f"Задача: «{task_title}»"
        + (f"\nПомещение: {room_name}" if room_name else "")
        + (f"\nИстория: {history_summary}" if history_summary else "")
        + f"\n\nФрагменты из базы знаний:\n{fragments_text}\n\n"
        "Дай краткий практический совет (2–4 предложения) по выполнению этой задачи, "
        "опираясь строго на фрагменты выше. Только текст, никакого форматирования."
    )

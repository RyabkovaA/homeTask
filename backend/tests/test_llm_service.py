"""
Тесты для llm_service.py:
  - build_rag_prompt: корректное включение параметров в промпт
  - Инструкция без markdown-разметки
  - Граничные случаи: room=None, пустая история
"""
from app.services.llm_service import build_rag_prompt


class TestBuildRagPrompt:
    def test_prompt_contains_task_title(self):
        prompt = build_rag_prompt("Мыть посуду", "Кухня", "", ["Совет 1"])
        assert "Мыть посуду" in prompt

    def test_prompt_contains_room_name(self):
        prompt = build_rag_prompt("Уборка", "Ванная комната", "", ["Совет"])
        assert "Ванная комната" in prompt

    def test_prompt_skips_room_when_none(self):
        prompt = build_rag_prompt("Задача", None, "", ["Совет"])
        assert "None" not in prompt
        assert "Помещение" not in prompt

    def test_prompt_includes_history_when_provided(self):
        prompt = build_rag_prompt("Задача", None, "Последнее выполнение: 3 дня назад", ["Совет"])
        assert "3 дня назад" in prompt

    def test_prompt_skips_history_when_empty(self):
        prompt = build_rag_prompt("Задача", None, "", ["Совет"])
        assert "История" not in prompt

    def test_prompt_contains_all_fragments(self):
        fragments = ["Уникальный совет Alpha", "Уникальный совет Beta"]
        prompt = build_rag_prompt("Задача", None, "", fragments)
        assert "Уникальный совет Alpha" in prompt
        assert "Уникальный совет Beta" in prompt

    def test_prompt_numbers_fragments(self):
        fragments = ["Первый", "Второй"]
        prompt = build_rag_prompt("Задача", None, "", fragments)
        assert "[1]" in prompt
        assert "[2]" in prompt

    def test_prompt_contains_no_markdown_instruction(self):
        prompt = build_rag_prompt("Задача", None, "", ["Совет"])
        lower = prompt.lower()
        # Проверяем, что промпт явно запрещает форматирование
        assert "markdown" in lower or "разметк" in lower

    def test_prompt_is_russian(self):
        prompt = build_rag_prompt("Уборка", "Кухня", "", ["Совет"])
        # Основные инструкции должны быть на русском
        assert "помощник" in prompt.lower()

    def test_prompt_requests_short_advice(self):
        prompt = build_rag_prompt("Задача", None, "", ["Совет"])
        # Должен просить краткий совет
        assert "совет" in prompt.lower() or "предложение" in prompt.lower()

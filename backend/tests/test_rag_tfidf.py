"""
Тесты для TF-IDF ретривера из rag_service.py.

Покрывает:
  - _tokenize: токенизация русского/латинского текста
  - TfidfCorpusIndex: построение индекса, ретривал, персонализация
"""
import pytest

from tests.conftest import make_advice
from app.services.rag_service import TfidfCorpusIndex, _tokenize


# ─────────────────────────────────────────────────────────
# Токенизация
# ─────────────────────────────────────────────────────────

class TestTokenize:
    def test_russian_words(self):
        tokens = _tokenize("Мыть посуду каждый день")
        assert "мыть" in tokens
        assert "посуду" in tokens
        assert "каждый" in tokens
        assert "день" in tokens

    def test_latin_words(self):
        tokens = _tokenize("clean bathroom daily")
        assert "clean" in tokens
        assert "bathroom" in tokens

    def test_removes_punctuation(self):
        tokens = _tokenize("Привет, мир!")
        assert "," not in tokens
        assert "!" not in tokens
        assert "привет" in tokens
        assert "мир" in tokens

    def test_lowercase_output(self):
        tokens = _tokenize("Уборка КУХНИ Пылесосом")
        assert all(t == t.lower() for t in tokens)

    def test_empty_string(self):
        tokens = _tokenize("")
        assert tokens == []

    def test_mixed_russian_latin(self):
        tokens = _tokenize("уборка kitchen ежедневно")
        assert "уборка" in tokens
        assert "kitchen" in tokens
        assert "ежедневно" in tokens


# ─────────────────────────────────────────────────────────
# TfidfCorpusIndex
# ─────────────────────────────────────────────────────────

KITCHEN_ADVICE = make_advice(
    "1", "Чистка кухни", "Протереть плиту раковину мойку",
    room_names=["Кухня"], task_keywords=["уборка", "чистка"]
)
BATHROOM_ADVICE = make_advice(
    "2", "Уборка ванной", "Мыть унитаз раковину ванной комнаты",
    room_names=["Ванная"], task_keywords=["уборка", "гигиена"]
)
BEDROOM_ADVICE = make_advice(
    "3", "Уборка спальни", "Пылесосить ковёр и менять постельное",
    room_names=["Спальня"], task_keywords=["уборка", "сон"]
)


class TestTfidfCorpusIndex:
    def test_empty_corpus_returns_empty(self):
        index = TfidfCorpusIndex([])
        result = index.retrieve_top_n("уборка кухня", n=3)
        assert result == []

    def test_single_doc_is_returned(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE])
        result = index.retrieve_top_n("плита", n=3)
        assert len(result) == 1
        assert result[0][1].advice_id == "1"

    def test_relevant_doc_scores_higher(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE, BATHROOM_ADVICE])
        # Запрос про кухню → первый результат должен быть про кухню
        result = index.retrieve_top_n("плита кухня чистить", n=2)
        assert result[0][1].advice_id == "1"

    def test_bathroom_query_returns_bathroom(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE, BATHROOM_ADVICE, BEDROOM_ADVICE])
        result = index.retrieve_top_n("унитаз ванная мыть", n=1)
        assert result[0][1].advice_id == "2"

    def test_results_sorted_by_score_desc(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE, BATHROOM_ADVICE, BEDROOM_ADVICE])
        result = index.retrieve_top_n("уборка", n=3)
        scores = [r[0] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limits_results(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE, BATHROOM_ADVICE, BEDROOM_ADVICE])
        result = index.retrieve_top_n("уборка", n=2)
        assert len(result) == 2

    def test_personalization_downranks(self):
        index = TfidfCorpusIndex([KITCHEN_ADVICE, BATHROOM_ADVICE])
        # Без персонализации кухня выигрывает на запросе "плита кухня"
        no_mult = index.retrieve_top_n("плита кухня", n=2)
        kitchen_score_no_mult = next(s for s, d in no_mult if d.advice_id == "1")

        # Downrank кухни в 0.1 раза
        with_mult = index.retrieve_top_n("плита кухня", n=2,
                                          personalization_multipliers={"1": 0.1})
        kitchen_score_with_mult = next(s for s, d in with_mult if d.advice_id == "1")

        assert kitchen_score_with_mult < kitchen_score_no_mult

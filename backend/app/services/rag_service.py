"""
RAG-Recommend service — Algorithm 1 (thesis):

RAG_Recommend(Task t, Member u, History H, Index I, K):
  q  ← BuildQuery(t, u, H)
  vq ← Embed(q)
  C  ← RetrieveTopN(I, vq, N)
  P  ← BuildPrompt(t, u, H, C)
  r  ← Generate(P)
  A  ← PostProcess(r)
  SaveAdviceDelivery(u, t, A, C)
  return TopK(A)

Retrieval: TF-IDF cosine similarity (pure Python, RFC Dense Passage Retrieval principle).
Generation: constrained template generation — only retrieved fragments are used as context,
            format is normalised by PostProcess. Corresponds to "ограниченная генерация" in thesis.
"""
from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.advice import Advice
from app.models.advice_delivery import AdviceDelivery
from app.models.task import Task, Priority
from app.models.task_event import TaskEvent, EventStatus
from app.models.member import HouseMember
from app.models.room import Room


# ---------------------------------------------------------------------------
# TF-IDF index (pure Python, no external ML dependencies)
# Implements the "dual encoder / dense retriever" principle from thesis §2.1.2
# using sparse TF-IDF vectors for compatibility with the reference corpus size.
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Tokenise Russian/Latin text into lowercase word tokens."""
    return re.findall(r'[а-яёa-z0-9]+', text.lower())


@dataclass
class _IndexedDoc:
    advice_id: str
    advice: Advice
    tokens: list[str]
    tfidf_vec: dict[str, float] = field(default_factory=dict)


class TfidfCorpusIndex:
    """
    In-memory TF-IDF index for the knowledge base corpus.

    Each Advice item is represented as a document formed by concatenating:
      title + content + steps + room_names + task_keywords
    This ensures queries on any of these axes retrieve relevant fragments.
    """

    def __init__(self, advice_items: list[Advice]) -> None:
        self._docs: list[_IndexedDoc] = []
        for a in advice_items:
            text = " ".join([
                a.title,
                a.content,
                " ".join(a.steps or []),
                " ".join(a.room_names or []),
                " ".join(a.task_keywords or []),
            ])
            self._docs.append(_IndexedDoc(
                advice_id=str(a.id),
                advice=a,
                tokens=_tokenize(text),
            ))

        self._idf = self._build_idf()
        for doc in self._docs:
            doc.tfidf_vec = self._tfidf_vec(doc.tokens)

    def _build_idf(self) -> dict[str, float]:
        N = len(self._docs)
        df: dict[str, int] = {}
        for doc in self._docs:
            for word in set(doc.tokens):
                df[word] = df.get(word, 0) + 1
        # Smooth IDF: log((N+1)/(df+1)) + 1  (sklearn-compatible smoothing)
        return {word: math.log((N + 1) / (cnt + 1)) + 1.0 for word, cnt in df.items()}

    def _tfidf_vec(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        total = len(tokens) or 1
        return {
            w: (tf[w] / total) * self._idf.get(w, 1.0)
            for w in tf
        }

    def _cosine(self, va: dict[str, float], vb: dict[str, float]) -> float:
        common = set(va) & set(vb)
        if not common:
            return 0.0
        dot = sum(va[k] * vb[k] for k in common)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0

    def retrieve_top_n(self, query: str, n: int = 3) -> list[tuple[float, _IndexedDoc]]:
        """
        RetrieveTopN(I, vq, N):
        Embed query → cosine similarity → return top-N ranked fragments.
        """
        q_tokens = _tokenize(query)
        q_vec = self._tfidf_vec(q_tokens)
        scored = [
            (self._cosine(q_vec, doc.tfidf_vec), doc)
            for doc in self._docs
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:n]


# ---------------------------------------------------------------------------
# BuildQuery — формирование поискового запроса из контекста
# ---------------------------------------------------------------------------

@dataclass
class HistorySummary:
    total_occurrences: int
    done_count: int
    skipped_count: int
    overdue_count: int
    completion_rate: float     # done / total
    last_done_days_ago: Optional[int]   # None = never done in period


def build_history_summary(
    events: list[TaskEvent],
    task_id: uuid.UUID,
    days: int = 30,
) -> HistorySummary:
    today = date.today()
    cutoff = today - timedelta(days=days)
    task_events = [
        e for e in events
        if e.task_id == task_id and e.occurrence_date >= cutoff
    ]
    total = len(task_events)
    done = sum(1 for e in task_events if e.status == EventStatus.done)
    skipped = sum(1 for e in task_events if e.status == EventStatus.skipped)
    overdue = sum(1 for e in task_events if e.status == EventStatus.overdue)

    last_done_days_ago: Optional[int] = None
    done_events = [e for e in task_events if e.status == EventStatus.done]
    if done_events:
        latest = max(e.occurrence_date for e in done_events)
        last_done_days_ago = (today - latest).days

    return HistorySummary(
        total_occurrences=total,
        done_count=done,
        skipped_count=skipped,
        overdue_count=overdue,
        completion_rate=done / total if total > 0 else 0.0,
        last_done_days_ago=last_done_days_ago,
    )


def build_query(
    task: Task,
    room_name: Optional[str],
    history: HistorySummary,
) -> str:
    """
    BuildQuery(t, u, H):
    Compose a retrieval query from task context + room + history.

    The query is a bag-of-words phrase that covers:
      - task title tokens (most relevant signal)
      - room name
      - priority level token
      - problem-area tokens when history is poor
    """
    parts = [task.title]
    if room_name:
        parts.append(room_name)
    if task.priority == Priority.high:
        parts.append("важно срочно высокий приоритет")
    if history.completion_rate < 0.5 and history.total_occurrences > 0:
        parts.append("не выполняется пропуск просрочка советы мотивация")
    if history.overdue_count > 2:
        parts.append("просрочено накопилось регулярность")
    if task.description:
        parts.append(task.description)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Generate + PostProcess — constrained generation from retrieved fragments
# ---------------------------------------------------------------------------

def _priority_warning(priority: Priority, history: HistorySummary) -> list[str]:
    warnings = []
    if priority == Priority.high:
        warnings.append("Задача имеет высокий приоритет — выполните её как можно скорее.")
    if history.total_occurrences > 0 and history.completion_rate < 0.4:
        pct = int(history.completion_rate * 100)
        warnings.append(
            f"Задача выполняется лишь в {pct}% случаев. "
            "Возможно, стоит скорректировать расписание или снизить частоту."
        )
    if history.overdue_count >= 3:
        warnings.append(
            f"За последний месяц задача накопила {history.overdue_count} просрочки. "
            "Рекомендуется пересмотреть политику переноса или приоритет."
        )
    if history.last_done_days_ago is not None and history.last_done_days_ago > 14:
        warnings.append(
            f"Задача не выполнялась уже {history.last_done_days_ago} дней. "
            "Проверьте актуальность её включения в расписание."
        )
    return warnings


def generate(
    task: Task,
    room_name: Optional[str],
    history: HistorySummary,
    retrieved: list[tuple[float, _IndexedDoc]],
) -> dict:
    """
    Generate(P) — constrained template generation.

    Only retrieved fragments are used as context (no hallucination beyond corpus).
    Produces: main_advice, steps, warnings.
    """
    if not retrieved or retrieved[0][0] < 0.01:
        # No relevant fragment found — return context-only advice
        main_advice = (
            f"Для задачи «{task.title}»"
            + (f" в помещении «{room_name}»" if room_name else "")
            + " в базе знаний не найдено специфических инструкций. "
            "Ориентируйтесь на общие принципы регулярного обслуживания помещения."
        )
        return {
            "main_advice": main_advice,
            "steps": [],
            "warnings": _priority_warning(task.priority, history),
        }

    top_score, top_doc = retrieved[0]
    top_advice = top_doc.advice

    # Primary advice: top retrieved fragment content
    main_advice = top_advice.content

    # Steps: from top fragment (guaranteed to be from corpus)
    steps = list(top_advice.steps or [])

    # If secondary fragments add unique steps, include them (max 2 extra)
    extra_steps_added = 0
    for _, doc in retrieved[1:]:
        for step in (doc.advice.steps or []):
            if step not in steps and extra_steps_added < 2:
                steps.append(step)
                extra_steps_added += 1

    warnings = _priority_warning(task.priority, history)

    # Low similarity warning
    if top_score < 0.05:
        warnings.append(
            "Совет подобран по косвенным признакам — проверьте его применимость к конкретной задаче."
        )

    return {
        "main_advice": main_advice,
        "steps": steps,
        "warnings": warnings,
    }


def post_process(generated: dict) -> dict:
    """
    PostProcess(r) — normalize: remove duplicates, ensure brevity, clean empty items.
    """
    steps = [s.strip() for s in generated.get("steps", []) if s.strip()]
    warnings = list(dict.fromkeys(  # preserve order, deduplicate
        w.strip() for w in generated.get("warnings", []) if w.strip()
    ))
    main_advice = (generated.get("main_advice") or "").strip()
    # Truncate main advice at 600 chars
    if len(main_advice) > 600:
        main_advice = main_advice[:597] + "..."

    return {
        "main_advice": main_advice,
        "steps": steps[:8],      # max 8 steps
        "warnings": warnings[:4],  # max 4 warnings
    }


# ---------------------------------------------------------------------------
# SaveAdviceDelivery — traceability log
# ---------------------------------------------------------------------------

async def save_advice_delivery(
    db: AsyncSession,
    member_id: uuid.UUID,
    task_id: Optional[uuid.UUID],
    context_type: str,
    query_text: str,
    retrieved: list[tuple[float, _IndexedDoc]],
    result_summary: str,
) -> AdviceDelivery:
    """
    SaveAdviceDelivery(u, t, A, C) — persist fact of advice delivery.
    Records member, task, query, retrieved fragment IDs, and result summary.
    """
    delivery = AdviceDelivery(
        member_id=member_id,
        task_id=task_id,
        context_type=context_type,
        query_text=query_text[:1000],
        retrieved_advice_ids=[doc.advice_id for _, doc in retrieved],
        result_summary=result_summary[:2000],
    )
    db.add(delivery)
    await db.flush()
    return delivery


# ---------------------------------------------------------------------------
# Full RAG_Recommend pipeline
# ---------------------------------------------------------------------------

async def rag_recommend(
    db: AsyncSession,
    task: Task,
    member: HouseMember,
    room_name: Optional[str],
    top_k: int = 3,
) -> dict:
    """
    Main entry point: RAG_Recommend(t, u, H, I, K).

    Returns dict with keys: main_advice, steps, warnings, sources, delivery_id.
    """
    # Load all active advice for corpus index
    result = await db.execute(select(Advice).where(Advice.is_active == True))
    advice_items: list[Advice] = result.scalars().all()

    if not advice_items:
        return {
            "main_advice": "База знаний пуста. Добавьте советы для получения рекомендаций.",
            "steps": [],
            "warnings": [],
            "sources": [],
            "delivery_id": None,
        }

    # Load recent events for history summary
    events_result = await db.execute(
        select(TaskEvent).where(
            and_(
                TaskEvent.task_id == task.id,
                TaskEvent.occurrence_date >= date.today() - timedelta(days=30),
            )
        )
    )
    events: list[TaskEvent] = events_result.scalars().all()

    # Algorithm steps
    history = build_history_summary(events, task.id)
    query = build_query(task, room_name, history)

    index = TfidfCorpusIndex(advice_items)
    retrieved = index.retrieve_top_n(query, n=top_k)

    generated = generate(task, room_name, history, retrieved)
    normalized = post_process(generated)

    sources = [
        {"id": doc.advice_id, "title": doc.advice.title, "score": round(score, 3)}
        for score, doc in retrieved
        if score > 0.001
    ]

    result_summary = normalized["main_advice"]

    delivery = await save_advice_delivery(
        db=db,
        member_id=member.id,
        task_id=task.id,
        context_type="task",
        query_text=query,
        retrieved=retrieved,
        result_summary=result_summary,
    )
    await db.commit()

    return {
        **normalized,
        "sources": sources,
        "delivery_id": str(delivery.id),
        "query_used": query,
        "history": {
            "total": history.total_occurrences,
            "done": history.done_count,
            "overdue": history.overdue_count,
            "completion_rate": round(history.completion_rate * 100, 1),
        },
    }


async def rag_recommend_by_query(
    db: AsyncSession,
    member: HouseMember,
    query_text: str,
    context_type: str = "analytics",
    top_k: int = 3,
) -> dict:
    """
    RAG retrieval by arbitrary query text (used by habit analysis).
    No task context, no history summary — pure retrieval + generation.
    """
    result = await db.execute(select(Advice).where(Advice.is_active == True))
    advice_items: list[Advice] = result.scalars().all()

    if not advice_items:
        return {"main_advice": "", "steps": [], "warnings": [], "sources": [], "delivery_id": None}

    index = TfidfCorpusIndex(advice_items)
    retrieved = index.retrieve_top_n(query_text, n=top_k)

    if not retrieved or retrieved[0][0] < 0.01:
        main_advice = "По данной теме в базе знаний не найдено релевантных советов."
        steps, warnings = [], []
    else:
        top_score, top_doc = retrieved[0]
        main_advice = top_doc.advice.content
        steps = list(top_doc.advice.steps or [])
        warnings = []
        if top_score < 0.05:
            warnings.append("Совет подобран по косвенным признакам — проверьте применимость.")

    sources = [
        {"id": doc.advice_id, "title": doc.advice.title, "score": round(score, 3)}
        for score, doc in retrieved if score > 0.001
    ]

    delivery = await save_advice_delivery(
        db=db,
        member_id=member.id,
        task_id=None,
        context_type=context_type,
        query_text=query_text[:1000],
        retrieved=retrieved,
        result_summary=main_advice[:2000],
    )
    # Don't commit here — caller commits (may be batching)

    return {
        "main_advice": main_advice,
        "steps": steps[:6],
        "warnings": warnings,
        "sources": sources,
        "delivery_id": str(delivery.id),
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.task import Task
from app.models.room import Room
from app.models.member import HouseMember
from app.models.advice_delivery import AdviceDelivery
from app.schemas.rag import (
    RagAdviceOut, HabitInsightsOut,
    RatePayload, RateOut,
    TaskSuggestionsOut, SuggestedTaskItem,
    CompletionProbabilityOut, CompletionSignals,
    NudgeOut,
)
from app.services.rag_service import rag_recommend
from app.services.habit_analysis_service import get_habit_insights
from app.services.prediction_service import get_completion_probability, get_nudge
from app.services.suggestion_service import suggest_tasks
from app.api.v1.endpoints.auth import get_current_member

router = APIRouter()


@router.post(
    "/houses/{house_id}/tasks/{task_id}/rag-advice",
    response_model=RagAdviceOut,
)
async def get_task_rag_advice(
    house_id: UUID,
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    RAG_Recommend endpoint — Algorithm 1.

    Generates contextual advice for a specific task occurrence using:
    - TF-IDF retrieval from knowledge base corpus
    - Personalized re-ranking (liked/disliked/recently-shown/room-boost)
    - Optional LLM prose generation (GigaChat / Ollama)
    - Saves delivery fact for traceability and future feedback
    """
    task = await db.get(Task, task_id)
    if not task or task.house_id != house_id:
        raise HTTPException(404, "Task not found")

    room_name: str | None = None
    if task.room_id:
        room = await db.get(Room, task.room_id)
        room_name = room.name if room else None

    result = await rag_recommend(
        db=db,
        task=task,
        member=current_member,
        room_name=room_name,
    )

    return RagAdviceOut(
        main_advice=result["main_advice"],
        steps=result["steps"],
        warnings=result["warnings"],
        sources=[
            {"id": s["id"], "title": s["title"], "score": s["score"]}
            for s in result["sources"]
        ],
        delivery_id=result.get("delivery_id"),
        query_used=result.get("query_used"),
        history=result.get("history"),
    )


@router.get(
    "/houses/{house_id}/habit-insights",
    response_model=HabitInsightsOut,
)
async def get_house_habit_insights(
    house_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    Habit analysis endpoint — BPMN flow.

    Uses adaptive thresholds calibrated to the member's personal 90-day baseline.
    Returns insights ordered by severity (critical → warning → info).
    """
    result = await get_habit_insights(
        db=db,
        house_id=house_id,
        member=current_member,
        days=days,
    )

    return HabitInsightsOut(
        adherence_summary=result["adherence_summary"],
        overall_status=result["overall_status"],
        global_adherence=result["global_adherence"],
        streak=result["streak"],
        total_planned=result["total_planned"],
        total_done=result["total_done"],
        personal_baseline=result.get("personal_baseline"),
        insights=[
            {
                "type": i["type"],
                "severity": i["severity"],
                "title": i["title"],
                "description": i["description"],
                "metric": i["metric"],
                "advice": (
                    RagAdviceOut(
                        main_advice=i["advice"]["main_advice"],
                        steps=i["advice"]["steps"],
                        warnings=i["advice"]["warnings"],
                        sources=[
                            {"id": s["id"], "title": s["title"], "score": s["score"]}
                            for s in i["advice"]["sources"]
                        ],
                        delivery_id=i["advice"].get("delivery_id"),
                    )
                    if i.get("advice")
                    else None
                ),
            }
            for i in result["insights"]
        ],
    )


@router.post(
    "/rag/deliveries/{delivery_id}/rate",
    response_model=RateOut,
)
async def rate_advice_delivery(
    delivery_id: UUID,
    payload: RatePayload,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    Feedback loop — member rates a RAG advice delivery.

    rating=1 (like) → up-rank this advice in future RAG retrievals for member
    rating=-1 (dislike) → down-rank this advice in future retrievals
    rating=0 → reset to neutral

    This implements the feedback-loop described in thesis §2 (Feedback loop component).
    """
    delivery = await db.get(AdviceDelivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Delivery not found")
    if delivery.member_id != current_member.id:
        raise HTTPException(403, "Not your delivery")

    delivery.rating = payload.rating
    await db.commit()
    return RateOut(delivery_id=str(delivery_id), rating=payload.rating)


@router.post(
    "/houses/{house_id}/suggest-tasks",
    response_model=TaskSuggestionsOut,
)
async def suggest_house_tasks(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    Auto-suggest new tasks based on:
    - Seasonal patterns (rule-based fallback)
    - Gap analysis (overdue tasks needing rescheduling)
    - LLM generation if configured (GigaChat / Ollama)
    """
    from datetime import date
    from app.services.suggestion_service import _get_season

    suggestions = await suggest_tasks(
        db=db,
        house_id=house_id,
        member=current_member,
    )
    season = _get_season()

    return TaskSuggestionsOut(
        season=season,
        suggestions=[SuggestedTaskItem(**s) for s in suggestions],
    )


@router.get(
    "/houses/{house_id}/tasks/{task_id}/completion-probability",
    response_model=CompletionProbabilityOut,
)
async def get_task_completion_probability(
    house_id: UUID,
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    Predict probability of task completion for today.

    Uses weighted combination of historical signals:
    task_rate, member_rate, weekday_rate, room_rate.
    No external ML dependencies — pure statistical model.
    """
    task = await db.get(Task, task_id)
    if not task or task.house_id != house_id:
        raise HTTPException(404, "Task not found")

    result = await get_completion_probability(db=db, task=task, member=current_member)
    return CompletionProbabilityOut(
        probability=result["probability"],
        confidence=result["confidence"],
        signals=CompletionSignals(**result["signals"]),
        reason=result["reason"],
    )


@router.get(
    "/houses/{house_id}/nudge",
    response_model=NudgeOut,
)
async def get_smart_nudge(
    house_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_member: HouseMember = Depends(get_current_member),
):
    """
    Smart nudge: should the user be reminded right now?

    Returns due task count, motivational message, and the member's
    historically best-performing weekdays.
    """
    result = await get_nudge(db=db, house_id=house_id, member=current_member)
    return NudgeOut(**result)

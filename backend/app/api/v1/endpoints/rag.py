from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.task import Task
from app.models.room import Room
from app.models.member import HouseMember
from app.schemas.rag import RagAdviceOut, HabitInsightsOut
from app.services.rag_service import rag_recommend
from app.services.habit_analysis_service import get_habit_insights
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
    - Constrained template generation with retrieved fragments
    - Execution history analysis for personalisation
    - Saves delivery fact for traceability
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

    Analyses execution journal for the house, detects behavioural patterns
    (low room adherence, declining trend, worst weekday, chronic overdue tasks),
    and generates RAG-based recommendations for each detected insight.
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

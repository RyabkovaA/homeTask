from pydantic import BaseModel
from typing import Optional


class AdviceSourceItem(BaseModel):
    id: str
    title: str
    score: float


class HistorySummaryOut(BaseModel):
    total: int
    done: int
    overdue: int
    completion_rate: float


class RagAdviceOut(BaseModel):
    main_advice: str
    steps: list[str]
    warnings: list[str]
    sources: list[AdviceSourceItem]
    delivery_id: Optional[str]
    query_used: Optional[str] = None
    history: Optional[HistorySummaryOut] = None


class HabitInsightOut(BaseModel):
    type: str
    severity: str
    title: str
    description: str
    metric: float
    advice: Optional[RagAdviceOut] = None


class HabitInsightsOut(BaseModel):
    adherence_summary: str
    overall_status: str
    global_adherence: float
    streak: int
    total_planned: int
    total_done: int
    insights: list[HabitInsightOut]

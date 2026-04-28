from pydantic import BaseModel, Field
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
    personal_baseline: Optional[float] = None
    insights: list[HabitInsightOut]


# ---- Feedback ----

class RatePayload(BaseModel):
    rating: int = Field(..., ge=-1, le=1)   # -1 dislike, 0 neutral, 1 like


class RateOut(BaseModel):
    delivery_id: str
    rating: int


# ---- Task suggestions ----

class SuggestedTaskItem(BaseModel):
    title: str
    room_name: Optional[str]
    frequency: str
    effort_hours: float
    reason: str
    source: str          # "gap" | "seasonal" | "llm"
    is_reschedule: bool = False


class TaskSuggestionsOut(BaseModel):
    season: str
    suggestions: list[SuggestedTaskItem]


# ---- Completion probability ----

class CompletionSignals(BaseModel):
    task_rate: float
    member_rate: float
    weekday_rate: float
    room_rate: float


class CompletionProbabilityOut(BaseModel):
    probability: float
    confidence: str   # "high" | "medium" | "low"
    signals: CompletionSignals
    reason: str


# ---- Nudge ----

class NudgeOut(BaseModel):
    should_nudge: bool
    due_count: int
    message: str
    best_weekdays: list[str]
    is_productive_day: bool

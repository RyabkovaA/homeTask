from pydantic import BaseModel


class MetricsOut(BaseModel):
    adherence_rate: float
    streak: int
    completion_ratio: float
    overdue_rate: float
    total_planned: int
    total_done: int
    total_overdue: int
    consistency_score: float   # 0–100: stability of daily completion rate


class LoadDistributionItem(BaseModel):
    member_id: str
    member_name: str
    color: str
    done_count: int
    percentage: float


class DailyPoint(BaseModel):
    date: str
    done: int
    total: int
    rate: float


class RoomAnalyticsItem(BaseModel):
    room_id: str | None
    room_name: str
    room_icon: str
    total_planned: int
    total_done: int
    total_overdue: int
    adherence_rate: float


class AnalyticsOut(BaseModel):
    metrics: MetricsOut
    daily_trend: list[DailyPoint]
    load_distribution: list[LoadDistributionItem]
    room_stats: list[RoomAnalyticsItem]

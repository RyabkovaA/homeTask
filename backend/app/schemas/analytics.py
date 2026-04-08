from pydantic import BaseModel


class MetricsOut(BaseModel):
    adherence_rate: float
    streak: int
    completion_ratio: float
    overdue_rate: float
    total_planned: int
    total_done: int
    total_overdue: int


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


class AnalyticsOut(BaseModel):
    metrics: MetricsOut
    daily_trend: list[DailyPoint]
    load_distribution: list[LoadDistributionItem]

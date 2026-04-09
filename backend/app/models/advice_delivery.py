"""
AdviceDelivery — traceability record for each RAG advice generation event.

Stores: who received advice, for which task/context, what query was used,
which knowledge fragments were retrieved, and what result was produced.
Corresponds to: SaveAdviceDelivery(u, t, A, C) in Algorithm 1.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class AdviceDelivery(Base):
    __tablename__ = "advice_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("house_members.id", ondelete="CASCADE"))
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    # "task" — advice for a specific task occurrence
    # "analytics" — advice triggered by low-adherence habit analysis
    context_type: Mapped[str] = mapped_column(String(20), default="task")

    query_text: Mapped[str] = mapped_column(String(1000))
    retrieved_advice_ids: Mapped[list] = mapped_column(JSON, default=list)   # [uuid, ...]
    result_summary: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

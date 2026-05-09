"""add house_id to advice for per-house isolation of personal tips

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2026-05-10

Adds nullable house_id FK to the advice table.
NULL  → global knowledge base (visible to every house)
non-NULL → private to that house only
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "g3h4i5j6k7l8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "advice",
        sa.Column(
            "house_id",
            UUID(as_uuid=True),
            sa.ForeignKey("houses.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_advice_house_id", "advice", ["house_id"])


def downgrade() -> None:
    op.drop_index("ix_advice_house_id", table_name="advice")
    op.drop_column("advice", "house_id")

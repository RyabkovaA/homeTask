"""add advice_deliveries table

Revision ID: d7e3c1f9b05a
Revises: b3f2a9c01e45
Create Date: 2026-04-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7e3c1f9b05a'
down_revision: Union[str, None] = 'b3f2a9c01e45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'advice_deliveries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('member_id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=True),
        sa.Column('context_type', sa.String(length=20), nullable=False, server_default='task'),
        sa.Column('query_text', sa.String(length=1000), nullable=False),
        sa.Column('retrieved_advice_ids', sa.JSON(), nullable=False),
        sa.Column('result_summary', sa.String(length=2000), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['house_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_advice_deliveries_member_id', 'advice_deliveries', ['member_id'])
    op.create_index('ix_advice_deliveries_task_id', 'advice_deliveries', ['task_id'])


def downgrade() -> None:
    op.drop_index('ix_advice_deliveries_task_id', 'advice_deliveries')
    op.drop_index('ix_advice_deliveries_member_id', 'advice_deliveries')
    op.drop_table('advice_deliveries')

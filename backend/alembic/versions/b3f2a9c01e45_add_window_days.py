"""add window_days to tasks

Revision ID: b3f2a9c01e45
Revises: 7a08a38830c0
Create Date: 2026-04-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3f2a9c01e45'
down_revision: Union[str, None] = '7a08a38830c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('window_days', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tasks', 'window_days')

"""add effort_hours to tasks

Revision ID: a1b2c3d4e5f6
Revises: e9a4c2d8f301
Create Date: 2026-04-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e9a4c2d8f301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('effort_hours', sa.Float(), nullable=False, server_default='1.0'))


def downgrade() -> None:
    op.drop_column('tasks', 'effort_hours')

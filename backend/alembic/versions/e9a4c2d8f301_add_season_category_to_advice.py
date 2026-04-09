"""add season and category to advice

Revision ID: e9a4c2d8f301
Revises: d7e3c1f9b05a
Create Date: 2026-04-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9a4c2d8f301'
down_revision: Union[str, None] = 'd7e3c1f9b05a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('advice', sa.Column('season', sa.String(length=10), nullable=True))
    op.add_column('advice', sa.Column('category', sa.String(length=20),
                                      nullable=False, server_default='regular'))


def downgrade() -> None:
    op.drop_column('advice', 'category')
    op.drop_column('advice', 'season')

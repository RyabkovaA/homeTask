"""Add rating to advice_deliveries

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'advice_deliveries',
        sa.Column('rating', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column('advice_deliveries', 'rating')

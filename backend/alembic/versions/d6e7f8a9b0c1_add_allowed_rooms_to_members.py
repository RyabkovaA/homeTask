"""add allowed_room_ids to house_members

Revision ID: d6e7f8a9b0c1
Revises: c3d4e5f6a7b8
Create Date: 2026-05-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'd6e7f8a9b0c1'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'house_members',
        sa.Column('allowed_room_ids', JSONB, nullable=False, server_default='[]')
    )


def downgrade() -> None:
    op.drop_column('house_members', 'allowed_room_ids')

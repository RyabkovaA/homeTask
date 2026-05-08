"""add push_subscriptions

Revision ID: e1f2a3b4c5d6
Revises: d6e7f8a9b0c1
Create Date: 2026-05-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'e1f2a3b4c5d6'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'push_subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('member_id', UUID(as_uuid=True), sa.ForeignKey('house_members.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('endpoint', sa.String(2048), nullable=False),
        sa.Column('p256dh', sa.String(512), nullable=False),
        sa.Column('auth', sa.String(256), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('member_id', 'endpoint', name='uq_push_sub_member_endpoint'),
    )


def downgrade() -> None:
    op.drop_table('push_subscriptions')

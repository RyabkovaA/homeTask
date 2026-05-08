"""add invite_code to houses

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import secrets


revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('houses', sa.Column('invite_code', sa.String(8), nullable=True))

    # Populate existing rows
    connection = op.get_bind()
    houses = connection.execute(sa.text("SELECT id FROM houses")).fetchall()
    for (house_id,) in houses:
        code = secrets.token_hex(4).upper()
        connection.execute(
            sa.text("UPDATE houses SET invite_code = :code WHERE id = :id"),
            {"code": code, "id": str(house_id)},
        )

    op.alter_column('houses', 'invite_code', nullable=False)
    op.create_unique_constraint('uq_houses_invite_code', 'houses', ['invite_code'])


def downgrade() -> None:
    op.drop_constraint('uq_houses_invite_code', 'houses', type_='unique')
    op.drop_column('houses', 'invite_code')

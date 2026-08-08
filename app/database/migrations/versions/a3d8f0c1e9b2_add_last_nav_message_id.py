"""add last_nav_message_id to users

Revision ID: a3d8f0c1e9b2
Revises: f1b96bce661e
Create Date: 2026-08-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3d8f0c1e9b2'
down_revision = 'f1b96bce661e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_nav_message_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_nav_message_id')

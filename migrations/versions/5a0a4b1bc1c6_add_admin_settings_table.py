"""Add admin settings table for configurable rules and toggles.

Revision ID: 5a0a4b1bc1c6
Revises: c5e2f4e1833c
Create Date: 2025-12-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5a0a4b1bc1c6'
down_revision = 'c5e2f4e1833c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'admin_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )


def downgrade():
    op.drop_table('admin_settings')

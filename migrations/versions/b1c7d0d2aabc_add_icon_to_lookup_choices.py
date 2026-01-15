"""add_icon_to_lookup_choices

Revision ID: b1c7d0d2aabc
Revises: 7096a3dabeaf
Create Date: 2026-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c7d0d2aabc'
down_revision = '7096a3dabeaf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('lookup_choices', sa.Column('icon', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('lookup_choices', 'icon')

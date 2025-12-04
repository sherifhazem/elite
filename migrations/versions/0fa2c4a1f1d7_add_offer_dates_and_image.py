"""Add start_date and image_url to offers

Revision ID: 0fa2c4a1f1d7
Revises: 9a3653a3cfa7
Create Date: 2025-10-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fa2c4a1f1d7'
down_revision = '9a3653a3cfa7'
branch_labels = None
depends_on = None


def upgrade():
    """Add optional scheduling and media fields to offers."""
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=True))


def downgrade():
    """Remove scheduling and media fields from offers."""
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.drop_column('image_url')
        batch_op.drop_column('start_date')

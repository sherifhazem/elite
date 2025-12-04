"""Add status to offers for portal controls

Revision ID: 2c89c6439943
Revises: 9a3653a3cfa7
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c89c6439943'
down_revision = '0a3b21a1b397'
branch_labels = None
depends_on = None


def upgrade():
    """Add status column to offers to manage lifecycle states."""
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active')
        )
    # Drop the server default after backfilling existing rows.
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.alter_column('status', server_default=None)


def downgrade():
    """Remove the status column added in upgrade()."""
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.drop_column('status')

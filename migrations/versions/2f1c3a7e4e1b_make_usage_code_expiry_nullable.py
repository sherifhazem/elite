"""Make usage code expiry nullable.

Revision ID: 2f1c3a7e4e1b
Revises: f680e1031b1b
Create Date: 2025-11-05 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2f1c3a7e4e1b"
down_revision = "f680e1031b1b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usage_codes", schema=None) as batch_op:
        batch_op.alter_column("expires_at", existing_type=sa.DateTime(), nullable=True)


def downgrade():
    with op.batch_alter_table("usage_codes", schema=None) as batch_op:
        batch_op.alter_column("expires_at", existing_type=sa.DateTime(), nullable=False)

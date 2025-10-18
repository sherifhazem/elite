"""Add base_discount to Offer

Revision ID: 9a3653a3cfa7
Revises: 96563a71f564
Create Date: 2025-10-18 14:42:53.238538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a3653a3cfa7'
down_revision = '96563a71f564'
branch_labels = None
depends_on = None


def upgrade():
    """Apply the schema changes for introducing dynamic offer discounts."""

    # Replace the static discount column with the new base discount value.
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_discount', sa.Float(), nullable=False))
        batch_op.drop_column('discount_percent')


def downgrade():
    """Revert the schema changes applied in upgrade()."""

    # Restore the original static discount column when rolling back.
    with op.batch_alter_table('offers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_percent', sa.FLOAT(), nullable=False))
        batch_op.drop_column('base_discount')

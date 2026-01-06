"""Add offer classifications table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f4e3f6b0f2a'
down_revision = '5a0a4b1bc1c6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offer_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('offer_id', 'classification', name='uq_offer_classifications_offer_id')
    )


def downgrade():
    op.drop_table('offer_classifications')

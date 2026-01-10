"""add usage codes and usage logs

Revision ID: cf8c67f3a5b9
Revises: 5cb6d2330330
Create Date: 2025-10-30 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cf8c67f3a5b9"
down_revision = "5cb6d2330330"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usage_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=5), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_uses_per_window", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["companies.id"]),
    )
    op.create_index(op.f("ix_usage_codes_code"), "usage_codes", ["code"], unique=False)

    with op.batch_alter_table("activity_log", schema=None) as batch_op:
        batch_op.alter_column("admin_id", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("company_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("member_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("partner_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("offer_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("code_used", sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column("result", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_activity_log_member_id_users",
            "users",
            ["member_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_activity_log_partner_id_companies",
            "companies",
            ["partner_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_activity_log_offer_id_offers",
            "offers",
            ["offer_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("activity_log", schema=None) as batch_op:
        batch_op.drop_constraint("fk_activity_log_offer_id_offers", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_activity_log_partner_id_companies", type_="foreignkey"
        )
        batch_op.drop_constraint("fk_activity_log_member_id_users", type_="foreignkey")
        batch_op.drop_column("created_at")
        batch_op.drop_column("result")
        batch_op.drop_column("code_used")
        batch_op.drop_column("offer_id")
        batch_op.drop_column("partner_id")
        batch_op.drop_column("member_id")
        batch_op.alter_column("company_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("admin_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index(op.f("ix_usage_codes_code"), table_name="usage_codes")
    op.drop_table("usage_codes")
